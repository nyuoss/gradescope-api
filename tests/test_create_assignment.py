import uuid
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
import requests
from bs4 import BeautifulSoup
from requests_toolbelt.multipart.encoder import MultipartEncoder

from gradescopeapi import DEFAULT_GRADESCOPE_BASE_URL
from gradescopeapi._config.config import (
    RubricLockingSetting,
    StudentSubmissionSettings,
    SubmissionType,
    WhenToCreateRubric,
)
from gradescopeapi.classes.assignments import (
    AssignmentUpdateError,
    create_assignment,
)


def _delete_assignment(
    session, course_id, assignment_id, base_url=DEFAULT_GRADESCOPE_BASE_URL
):
    """Best-effort cleanup: POST Rails-style delete form. Swallows all errors."""
    try:
        edit_url = f"{base_url}/courses/{course_id}/assignments/{assignment_id}/edit"
        r = session.get(edit_url, timeout=(5, 30))
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        token_input = soup.select_one('input[name="authenticity_token"]')
        if token_input is None:
            return
        token = token_input["value"]
        multipart = MultipartEncoder(
            fields={
                "utf8": "✓",
                "_method": "delete",
                "authenticity_token": token,
                "commit": "Delete",
            }
        )
        session.post(
            f"{base_url}/courses/{course_id}/assignments/{assignment_id}",
            data=multipart,
            headers={"Content-Type": multipart.content_type, "Referer": edit_url},
            allow_redirects=True,
            timeout=(5, 30),
        )
    except Exception:
        pass


def _make_settings():
    """Return a minimal StudentSubmissionSettings for NYU timezone."""
    est = ZoneInfo("America/New_York")
    release = datetime(2025, 7, 18, 12, 0, tzinfo=est)
    due = release + timedelta(days=7)
    return StudentSubmissionSettings(
        release_date=release,
        due_date=due,
        allow_late_submissions=False,
        submission_type=SubmissionType.VARIABLE,
    )


def test_create_assignment_valid(create_session):
    test_session = create_session("instructor")

    course_id = "753413"
    new_title = f"Test Create - {uuid.uuid4()}"

    with open(
        Path(__file__).parent / "upload_files" / "blank_pdf_file.pdf", "rb"
    ) as blank_pdf_file:
        assignment_id = create_assignment(
            test_session, course_id, new_title, template_pdf=blank_pdf_file
        )

    assert assignment_id is not None
    assert assignment_id.isdigit()


def test_create_assignment_invalid_session(create_session):
    test_session = create_session("student")

    course_id = "753413"
    new_title = f"Test Create - {uuid.uuid4()}"

    with pytest.raises((requests.HTTPError, AssignmentUpdateError)) as exc_info:
        create_assignment(test_session, course_id, new_title)

    if isinstance(exc_info.value, requests.HTTPError):
        assert exc_info.value.response is not None
        assert exc_info.value.response.status_code in (401, 403)


def test_create_assignment_valid_submissions_anonymized(create_session):
    test_session = create_session("instructor")
    course_id = "753413"
    new_title = f"Test Create - {uuid.uuid4()}"
    assignment_id = None

    try:
        assignment_id = create_assignment(
            test_session, course_id, new_title, submissions_anonymized=True
        )
        assert assignment_id is not None
        assert assignment_id.isdigit()
    finally:
        if assignment_id is not None:
            _delete_assignment(test_session, course_id, assignment_id)


def test_create_assignment_valid_student_submission(create_session):
    test_session = create_session("instructor")
    course_id = "753413"
    new_title = f"Test Create - {uuid.uuid4()}"
    assignment_id = None

    try:
        assignment_id = create_assignment(
            test_session,
            course_id,
            new_title,
            student_submission=True,
            student_submission_settings=_make_settings(),
        )
        assert assignment_id is not None
        assert assignment_id.isdigit()
    finally:
        if assignment_id is not None:
            _delete_assignment(test_session, course_id, assignment_id)


def test_create_assignment_valid_group_submission(create_session):
    test_session = create_session("instructor")
    course_id = "753413"
    new_title = f"Test Create - {uuid.uuid4()}"
    assignment_id = None

    try:
        settings = _make_settings()
        settings.group_submission = True
        settings.group_size = 2
        assignment_id = create_assignment(
            test_session,
            course_id,
            new_title,
            student_submission=True,
            student_submission_settings=settings,
        )
        assert assignment_id is not None
        assert assignment_id.isdigit()
    finally:
        if assignment_id is not None:
            _delete_assignment(test_session, course_id, assignment_id)


def test_create_assignment_valid_time_limit(create_session):
    test_session = create_session("instructor")
    course_id = "753413"
    new_title = f"Test Create - {uuid.uuid4()}"
    assignment_id = None

    try:
        settings = _make_settings()
        settings.time_limit_in_minutes = 60
        assignment_id = create_assignment(
            test_session,
            course_id,
            new_title,
            student_submission=True,
            student_submission_settings=settings,
        )
        assert assignment_id is not None
        assert assignment_id.isdigit()
    finally:
        if assignment_id is not None:
            _delete_assignment(test_session, course_id, assignment_id)


def test_create_assignment_valid_pdf_submission_type(create_session):
    test_session = create_session("instructor")
    course_id = "753413"
    new_title = f"Test Create - {uuid.uuid4()}"
    assignment_id = None

    try:
        settings = _make_settings()
        settings.submission_type = SubmissionType.FIXED
        with open(
            Path(__file__).parent / "upload_files" / "blank_pdf_file.pdf", "rb"
        ) as blank_pdf_file:
            assignment_id = create_assignment(
                test_session,
                course_id,
                new_title,
                student_submission=True,
                student_submission_settings=settings,
                template_pdf=blank_pdf_file,
            )
        assert assignment_id is not None
        assert assignment_id.isdigit()
    finally:
        if assignment_id is not None:
            _delete_assignment(test_session, course_id, assignment_id)


def test_create_assignment_valid_rubric_before_submissions(create_session):
    test_session = create_session("instructor")
    course_id = "753413"
    new_title = f"Test Create - {uuid.uuid4()}"
    assignment_id = None

    try:
        assignment_id = create_assignment(
            test_session,
            course_id,
            new_title,
            when_to_create_rubric=WhenToCreateRubric.BEFORE_SUBMISSIONS,
        )
        assert assignment_id is not None
        assert assignment_id.isdigit()
    finally:
        if assignment_id is not None:
            _delete_assignment(test_session, course_id, assignment_id)


def test_create_assignment_valid_rubric_locking_no_edit(create_session):
    test_session = create_session("instructor")
    course_id = "753413"
    new_title = f"Test Create - {uuid.uuid4()}"
    assignment_id = None

    try:
        assignment_id = create_assignment(
            test_session,
            course_id,
            new_title,
            rubric_locking_setting=RubricLockingSetting.NO_EDIT,
        )
        assert assignment_id is not None
        assert assignment_id.isdigit()
    finally:
        if assignment_id is not None:
            _delete_assignment(test_session, course_id, assignment_id)


def test_create_assignment_valid_template_pdf_filename_override(create_session):
    test_session = create_session("instructor")
    course_id = "753413"
    new_title = f"Test Create - {uuid.uuid4()}"
    assignment_id = None

    try:
        with open(
            Path(__file__).parent / "upload_files" / "blank_pdf_file.pdf", "rb"
        ) as blank_pdf_file:
            assignment_id = create_assignment(
                test_session,
                course_id,
                new_title,
                template_pdf=blank_pdf_file,
                template_pdf_filename="custom_template.pdf",
            )
        assert assignment_id is not None
        assert assignment_id.isdigit()
    finally:
        if assignment_id is not None:
            _delete_assignment(test_session, course_id, assignment_id)


def test_create_assignment_invalid_course_id(create_session):
    test_session = create_session("instructor")
    nonexistent_course_id = "999999999"
    new_title = f"Test Create - {uuid.uuid4()}"

    try:
        create_assignment(test_session, nonexistent_course_id, new_title)
        assert False, "Incorrectly created assignment with nonexistent course"
    except requests.exceptions.HTTPError as e:
        assert e.response.status_code == 404
