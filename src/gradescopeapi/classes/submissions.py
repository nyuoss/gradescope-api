"""Functions for downloading submission zips (single and export all) and listing submissions."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from gradescopeapi import DEFAULT_GRADESCOPE_BASE_URL
from gradescopeapi.classes._helpers._download_helpers import download_url
from gradescopeapi.classes._helpers._export_helpers import (
    get_export_all_download_url,
    get_submission_download_url,
    _review_grades_url,
)
from gradescopeapi.classes._helpers._submission_helpers import parse_submissions_table


@dataclass
class Submission:
    """One row from the assignment review_grades submissions table.

    submission_url is None when the student has no submission; then graded/viewed/score/
    canvas_linked/submitted_at/late are all None/False.
    """

    submission_url: str | None
    student_name: str
    email: str
    sections: list[str] = field(default_factory=list)
    score: float | None = None
    graded: bool = False
    viewed: bool = False
    canvas_linked: bool = False
    submitted_at: datetime | None = None
    late: bool = False


def _row_dict_to_submission(d: dict) -> Submission:
    """Map parsed row dict from _submission_helpers to Submission."""
    student_name = d.get("student_name")
    email = d.get("email")
    if not student_name or not str(student_name).strip():
        raise ValueError("Submission row missing required student_name")
    if not email or not str(email).strip():
        raise ValueError("Submission row missing required email")
    return Submission(
        submission_url=d.get("submission_url"),
        student_name=str(student_name),
        email=str(email),
        sections=d.get("sections", []),
        score=d.get("score"),
        graded=bool(d.get("graded", False)),
        viewed=bool(d.get("viewed", False)),
        canvas_linked=bool(d.get("canvas_linked", False)),
        submitted_at=d.get("submitted_at"),
        late=d.get("late", False),
    )


def get_submissions_list(
    session: requests.Session,
    course_id: str,
    assignment_id: str,
    gradescope_base_url: str = DEFAULT_GRADESCOPE_BASE_URL,
) -> list[Submission]:
    """
    Fetch the review_grades page and return a list of submissions (one per table row).

    Parsing (time, late, sections, score) is done in _submission_helpers; this maps to Submission.
    """
    url = _review_grades_url(gradescope_base_url, course_id, assignment_id)
    r = session.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    rows = parse_submissions_table(soup, gradescope_base_url, course_id, assignment_id)
    return [_row_dict_to_submission(row) for row in rows]


def download_submission(
    session: requests.Session,
    course_id: str,
    assignment_id: str,
    submission_id: str,
    output_dir: str | Path = ".",
    filename: str | None = None,
    gradescope_base_url: str = DEFAULT_GRADESCOPE_BASE_URL,
) -> Path:
    """Download a single submission as a zip file. Available to instructors and students (own submission)."""
    output_dir = Path(output_dir)
    path = output_dir / (filename or f"submission_{submission_id}.zip")
    url = get_submission_download_url(
        gradescope_base_url,
        course_id,
        assignment_id,
        str(submission_id),
    )
    download_url(session, url, path)
    return path


def download_all_submissions(
    session: requests.Session,
    course_id: str,
    assignment_id: str,
    output_dir: str | Path = ".",
    poll_interval: float = 5,
    poll_max: int | None = None,
    filename: str | None = None,
    gradescope_base_url: str = DEFAULT_GRADESCOPE_BASE_URL,
) -> Path:
    """Export all submissions for an assignment as one zip (instructor only)."""
    output_dir = Path(output_dir)
    path = output_dir / (filename or "submissions.zip")
    url = get_export_all_download_url(
        session,
        gradescope_base_url,
        course_id,
        assignment_id,
        poll_interval=poll_interval,
        poll_max=poll_max,
    )
    download_url(session, url, path)
    return path
