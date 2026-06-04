"""Unit tests for get_submission_files — no network/credentials required.

A fake session returns a canned submission JSON so we can exercise each
submission shape (autograder text_files, PDF/image submissions via
pdf_attachment, and image_attachments).
"""
import json

import pytest

from gradescopeapi.classes._helpers._assignment_helpers import get_submission_files


class _FakeResp:
    status_code = 200

    def __init__(self, payload):
        self.text = json.dumps(payload)


class _FakeSession:
    def __init__(self, payload):
        self._payload = payload

    def get(self, url):
        return _FakeResp(self._payload)


def _call(payload):
    return get_submission_files(_FakeSession(payload), "1", "2", "3")


def test_text_files_submission():
    links = _call({"text_files": [{"file": {"url": "https://aws/a.py"}}]})
    assert links == ["https://aws/a.py"]


def test_pdf_attachment_submission():
    # PDF/image submission: no autograder text_files, just a combined PDF
    links = _call(
        {"text_files": [], "pdf_attachment": {"url": "https://aws/orig.pdf"}}
    )
    assert links == ["https://aws/orig.pdf"]


def test_image_attachments_submission():
    links = _call(
        {
            "text_files": [],
            "pdf_attachment": {},
            "image_attachments": [
                {"url": "https://aws/1.jpg"},
                {"url": "https://aws/2.jpg"},
            ],
        }
    )
    assert links == ["https://aws/1.jpg", "https://aws/2.jpg"]


def test_no_files_raises():
    with pytest.raises(NotImplementedError):
        _call({"text_files": [], "pdf_attachment": {}, "image_attachments": []})
