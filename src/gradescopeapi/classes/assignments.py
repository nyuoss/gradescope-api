"""Functions for modifying assignment details."""

import datetime
import re
import pathlib
from dataclasses import dataclass, field
from typing import Any, BinaryIO

import requests
from bs4 import BeautifulSoup
from requests_toolbelt.multipart.encoder import MultipartEncoder

from gradescopeapi import DEFAULT_GRADESCOPE_BASE_URL
from gradescopeapi._config.config import (
    RubricLockingSetting,
    StudentSubmissionSettings,
    WhenToCreateRubric,
)


class AssignmentUpdateError(Exception):
    pass


class InvalidTitleName(AssignmentUpdateError):
    pass


@dataclass
class Assignment:
    assignment_id: str
    name: str
    release_date: datetime.datetime
    due_date: datetime.datetime
    late_due_date: datetime.datetime
    submissions_status: str
    grade: str
    max_grade: str


@dataclass
class CropRect:
    x1: int
    x2: int
    y1: int
    y2: int


@dataclass
class QuestionData:
    title: str
    weight: int
    crop_rect_list: list[CropRect] = field(
        default_factory=lambda: [CropRect(x1=0, x2=100, y1=90, y2=100)]
    )


@dataclass
class IdentificationRegions:
    name: str | None = None
    sid: str | None = None


@dataclass
class AssignmentOutline:
    question_data: list[QuestionData]
    identification_regions: IdentificationRegions | None = None


def update_assignment_date(
    session: requests.Session,
    course_id: str,
    assignment_id: str,
    release_date: datetime.datetime | None = None,
    due_date: datetime.datetime | None = None,
    late_due_date: datetime.datetime | None = None,
    gradescope_base_url: str = DEFAULT_GRADESCOPE_BASE_URL,
) -> bool:
    """Update the dates of an assignment on Gradescope.

    Args:
        session (requests.Session): The session object for making HTTP requests.
        course_id (str): The ID of the course.
        assignment_id (str): The ID of the assignment.
        release_date (datetime.datetime | None, optional): The release date of the assignment. Defaults to None.
        due_date (datetime.datetime | None, optional): The due date of the assignment. Defaults to None.
        late_due_date (datetime.datetime | None, optional): The late due date of the assignment. Defaults to None.

    Notes:
        The timezone for dates used in Gradescope is specific to an institution. For example, for NYU, the timezone is America/New_York.
        For datetime objects passed to this function, the timezone should be set to the institution's timezone.

    Raises if session does not have access to configure assignment.

    Returns:
        bool: True if the assignment dates were successfully updated, False otherwise.
    """
    GS_EDIT_ASSIGNMENT_ENDPOINT = (
        f"{gradescope_base_url}/courses/{course_id}/assignments/{assignment_id}/edit"
    )
    GS_POST_ASSIGNMENT_ENDPOINT = (
        f"{gradescope_base_url}/courses/{course_id}/assignments/{assignment_id}"
    )

    # Get auth token
    response = session.get(GS_EDIT_ASSIGNMENT_ENDPOINT)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    auth_token = soup.select_one('input[name="authenticity_token"]')["value"]

    # Setup multipart form data
    multipart = MultipartEncoder(
        fields={
            "utf8": "✓",
            "_method": "patch",
            "authenticity_token": auth_token,
            "assignment[release_date_string]": (
                release_date.strftime("%Y-%m-%dT%H:%M") if release_date else ""
            ),
            "assignment[due_date_string]": (
                due_date.strftime("%Y-%m-%dT%H:%M") if due_date else ""
            ),
            "assignment[allow_late_submissions]": "1" if late_due_date else "0",
            "assignment[hard_due_date_string]": (
                late_due_date.strftime("%Y-%m-%dT%H:%M") if late_due_date else ""
            ),
            "commit": "Save",
        }
    )
    headers = {
        "Content-Type": multipart.content_type,
        "Referer": GS_EDIT_ASSIGNMENT_ENDPOINT,
    }

    response = session.post(
        GS_POST_ASSIGNMENT_ENDPOINT, data=multipart, headers=headers
    )
    response.raise_for_status()

    return response.status_code == 200


def update_assignment_title(
    session: requests.Session,
    course_id: str,
    assignment_id: str,
    assignment_name: str,
    gradescope_base_url: str = DEFAULT_GRADESCOPE_BASE_URL,
) -> bool:
    """Update the dates of an assignment on Gradescope.

    Args:
        session (requests.Session): The session object for making HTTP requests.
        course_id (str): The ID of the course.
        assignment_id (str): The ID of the assignment.
        assignment_name (str): The name of the assignment to update to.

    Notes:
        Assignment name cannot be all whitespace

    Raises if session does not have access to configure assignment.

    Returns:
        bool: True if the assignment dates were successfully updated, False otherwise.
    """
    GS_EDIT_ASSIGNMENT_ENDPOINT = (
        f"{gradescope_base_url}/courses/{course_id}/assignments/{assignment_id}/edit"
    )
    GS_POST_ASSIGNMENT_ENDPOINT = (
        f"{gradescope_base_url}/courses/{course_id}/assignments/{assignment_id}"
    )

    # Get auth token
    response = session.get(GS_EDIT_ASSIGNMENT_ENDPOINT)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    auth_token = soup.select_one('input[name="authenticity_token"]')["value"]

    # Setup multipart form data
    multipart = MultipartEncoder(
        fields={
            "utf8": "✓",
            "_method": "patch",
            "authenticity_token": auth_token,
            "assignment[title]": assignment_name,
            "commit": "Save",
        }
    )
    headers = {
        "Content-Type": multipart.content_type,
        "Referer": GS_EDIT_ASSIGNMENT_ENDPOINT,
    }

    response = session.post(
        GS_POST_ASSIGNMENT_ENDPOINT, data=multipart, headers=headers
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")
    error = soup.select_one(".form--requiredFieldStar.error")
    if error is not None:
        if error.parent is not None and error.parent.text.startswith("Title"):
            raise InvalidTitleName(f"Assignment title '{assignment_name}' is invalid")
        else:
            raise AssignmentUpdateError(
                "Unknown error occurred trying to update assignment title"
            )

    return response.status_code == 200


def update_autograder_image_name(
    session: requests.Session,
    course_id: str,
    assignment_id: str,
    image_name: str,
    gradescope_base_url: str = DEFAULT_GRADESCOPE_BASE_URL,
) -> bool:
    """Update the Docker Hub image name of an assignment on Gradescope.

    Args:
        session (requests.Session): The session object for making HTTP requests.
        course_id (str): The ID of the course.
        assignment_id (str): The ID of the assignment.
        image_name (str): The Docker Hub Image Name (user-handle/repo:tag)

    Notes:
        In most cases Gradescope does not validate that the image_name provided exists on Docker Hub. Garbage
        values may still successfully return OK. You should test your autograder after updating the image name
        to ensure it works as expected.

        Example image name: 'gradescope/autograder-base:ubuntu-22.04'
        from https://hub.docker.com/layers/gradescope/autograder-base/ubuntu-22.04

    Raises if session does not have access to configure autograder or if assignment does not have an autograder.

    Returns:
        bool: True if the image name was successfully updated, False otherwise.
    """
    GS_EDIT_AUTOGRADER_ASSIGNMENT_ENDPOINT = f"{gradescope_base_url}/courses/{course_id}/assignments/{assignment_id}/configure_autograder"
    GS_POST_ASSIGNMENT_ENDPOINT = (
        f"{gradescope_base_url}/courses/{course_id}/assignments/{assignment_id}"
    )

    # Get auth token
    response = session.get(GS_EDIT_AUTOGRADER_ASSIGNMENT_ENDPOINT)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    auth_token = soup.select_one('input[name="authenticity_token"]')["value"]

    # Setup multipart form data
    multipart = MultipartEncoder(
        fields={
            "utf8": "✓",
            "_method": "patch",
            "authenticity_token": auth_token,
            "source_page": "configure_autograder",
            "assignment[image_name]": image_name,
        }
    )
    headers = {
        "Content-Type": multipart.content_type,
        "Referer": GS_EDIT_AUTOGRADER_ASSIGNMENT_ENDPOINT,
    }

    response = session.post(
        GS_POST_ASSIGNMENT_ENDPOINT, data=multipart, headers=headers
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")
    return response.status_code == 200 and not soup.find(
        string="Docker image not found in your current course!"
    )


def update_assignment_outline(
    session: requests.Session,
    course_id: str,
    assignment_id: str,
    assignment_outline: AssignmentOutline,
    gradescope_base_url: str = DEFAULT_GRADESCOPE_BASE_URL,
) -> bool:
    """Update the outline of an assignment on Gradescope.

    Args:
        session (requests.Session): The session object for making HTTP requests.
        course_id (str): The ID of the course.
        assignment_id (str): The ID of the assignment.
        assignment_outline (AssignmentOutline): The new outline to apply, containing
            the identification regions and question data (titles, weights, and crop
            rectangles).

    Notes:
        Crop rectangle coordinates are percentages (0-100) of the page dimensions.

    Raises:
        AssignmentUpdateError: If the CSRF token is not found on the outline page.
        requests.exceptions.HTTPError: If the request fails (e.g. 401 Unauthorized).

    Returns:
        bool: True if the assignment outline was successfully updated, False otherwise.
    """
    GS_OUTLINE_ENDPOINT_BASE = (
        f"{gradescope_base_url}/courses/{course_id}/assignments/{assignment_id}/outline"
    )
    GS_OUTLINE_ENDPOINT = f"{GS_OUTLINE_ENDPOINT_BASE}/"
    GS_OUTLINE_EDIT_ENDPOINT = f"{GS_OUTLINE_ENDPOINT_BASE}/edit"

    # Get auth token from the outline page
    response = session.get(GS_OUTLINE_EDIT_ENDPOINT, timeout=(5, 30))
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    csrf_meta = soup.select_one('meta[name="csrf-token"]')
    if csrf_meta is None:
        raise AssignmentUpdateError(
            "CSRF token not found on /outline page. "
            "Session may be unauthenticated or the page layout has changed."
        )
    auth_token = csrf_meta["content"]

    body = {
        "assignment": {
            "identification_regions": {
                "name": (
                    assignment_outline.identification_regions.name
                    if assignment_outline.identification_regions
                    else None
                ),
                "sid": (
                    assignment_outline.identification_regions.sid
                    if assignment_outline.identification_regions
                    else None
                ),
            }
        },
        "question_data": [
            {
                "title": question.title,
                "weight": question.weight,
                "crop_rect_list": [
                    {
                        "x1": crop_rect.x1,
                        "x2": crop_rect.x2,
                        "y1": crop_rect.y1,
                        "y2": crop_rect.y2,
                    }
                    for crop_rect in question.crop_rect_list
                ],
            }
            for question in assignment_outline.question_data
        ],
    }

    headers = {"X-CSRF-Token": auth_token, "Referer": GS_OUTLINE_EDIT_ENDPOINT}

    response = session.patch(GS_OUTLINE_ENDPOINT, json=body, headers=headers)
    response.raise_for_status()

    return response.status_code == 200


def create_assignment(
    session: requests.Session,
    course_id: str,
    title: str,
    template_pdf: BinaryIO | None = None,
    template_pdf_filename: str | None = None,
    submissions_anonymized: bool = False,
    student_submission: bool = False,
    student_submission_settings: StudentSubmissionSettings | None = None,
    when_to_create_rubric: WhenToCreateRubric = WhenToCreateRubric.WHILE_GRADING,
    rubric_locking_setting: RubricLockingSetting = RubricLockingSetting.ALL_EDIT,
    gradescope_base_url: str = DEFAULT_GRADESCOPE_BASE_URL,
) -> str | None:
    """Create a new assignment on Gradescope.

    Args:
        session (requests.Session): The session object for making HTTP requests.
        course_id (str): The ID of the course.
        title (str): The title of the new assignment.
        template_pdf (BinaryIO | None, optional): A binary file object for the template PDF. Defaults to None.
        template_pdf_filename (str | None, optional): The original filename of the template PDF.
            Used when template_pdf does not carry a meaningful .name attribute
            (e.g. SpooledTemporaryFile from FastAPI UploadFile). Falls back to
            template_pdf.name if not provided. Defaults to None.
        submissions_anonymized (bool, optional): Whether submissions are anonymized. Defaults to False.
        student_submission (bool, optional): Whether students submit their own work. Defaults to False.
        student_submission_settings (StudentSubmissionSettings | None, optional):
            Submission configuration (dates, submission type, group settings, etc.).
            Required when student_submission is True. Defaults to None.
        when_to_create_rubric (WhenToCreateRubric, optional): When to create the rubric. Defaults to WHILE_GRADING.
        rubric_locking_setting (RubricLockingSetting, optional): Rubric locking setting. Defaults to ALL_EDIT.

    Notes:
        The timezone for dates used in Gradescope is specific to an institution. For example, for NYU, the timezone is America/New_York.
        For datetime objects in student_submission_settings, the timezone should be set to the institution's timezone.

    Raises:
        AssignmentUpdateError: If the CSRF token is not found on the page, if the
            redirect target is unparsable, or if an unexpected non-redirect response
            is received from Gradescope.
        requests.exceptions.HTTPError: If the request fails (e.g. 401 Unauthorized).

    Returns:
        str: The new assignment ID if creation was successful.
    """
    GS_NEW_ASSIGNMENT_ENDPOINT = (
        f"{gradescope_base_url}/courses/{course_id}/assignments/new"
    )
    GS_CREATE_ASSIGNMENT_ENDPOINT = (
        f"{gradescope_base_url}/courses/{course_id}/assignments"
    )

    # Get auth token from the new assignment page
    response = session.get(GS_NEW_ASSIGNMENT_ENDPOINT, timeout=(5, 30))
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    csrf_meta = soup.select_one('meta[name="csrf-token"]')
    if csrf_meta is None:
        raise AssignmentUpdateError(
            "CSRF token not found on /assignments/new page. "
            "Session may be unauthenticated or the page layout has changed."
        )
    auth_token = csrf_meta["content"]

    # Setup multipart form data
    fields: list[tuple[str, str | tuple[str, Any, str]]] = [
        ("utf8", "✓"),
        ("authenticity_token", auth_token),
        ("assignment[title]", title),
        (
            "assignment[submissions_anonymized]",
            "1" if submissions_anonymized else "0",
        ),
        (
            "assignment[student_submission]",
            # Gradescope's form uses "true"/"false" strings for this field
            # (not "1"/"0" like the checkboxes above).
            "true" if student_submission else "false",
        ),
        ("assignment[when_to_create_rubric]", when_to_create_rubric.value),
        ("assignment[rubric_locking_setting]", rubric_locking_setting.value),
        (
            "assignment[release_date_string]",
            student_submission_settings.release_date.strftime("%Y-%m-%dT%H:%M")
            if student_submission_settings
            else "",
        ),
        (
            "assignment[due_date_string]",
            student_submission_settings.due_date.strftime("%Y-%m-%dT%H:%M")
            if student_submission_settings
            else "",
        ),
        (
            "assignment[hard_due_date_string]",
            student_submission_settings.late_due_date.strftime("%Y-%m-%dT%H:%M")
            if student_submission_settings and student_submission_settings.late_due_date
            else "",
        ),
    ]
    if student_submission_settings is not None:
        fields.append(
            (
                "assignment[allow_late_submissions]",
                "1" if student_submission_settings.allow_late_submissions else "0",
            )
        )
        fields.append(
            (
                "assignment[submission_type]",
                student_submission_settings.submission_type.value,
            )
        )
        fields.append(
            (
                "assignment[group_submission]",
                "1" if student_submission_settings.group_submission else "0",
            )
        )
        if student_submission_settings.group_size is not None:
            fields.append(
                ("assignment[group_size]", str(student_submission_settings.group_size))
            )
        fields.append(
            (
                "assignment[template_visible_to_students]",
                "1"
                if student_submission_settings.template_visible_to_students
                else "0",
            )
        )
        if student_submission_settings.time_limit_in_minutes is not None:
            fields.append(("assignment[enforce_time_limit]", "1"))
            fields.append(
                (
                    "assignment[time_limit_in_minutes]",
                    str(student_submission_settings.time_limit_in_minutes),
                )
            )
    if template_pdf is not None:
        pdf_filename = template_pdf_filename or getattr(template_pdf, "name", None)
        fields.append(
            (
                "template_pdf",
                (
                    pathlib.Path(pdf_filename).name if pdf_filename else "template.pdf",
                    template_pdf,
                    "application/pdf",
                ),
            )
        )

    multipart = MultipartEncoder(fields=fields)
    headers = {
        "Content-Type": multipart.content_type,
        "Referer": GS_NEW_ASSIGNMENT_ENDPOINT,
    }

    # Submit the assignment creation form
    response = session.post(
        GS_CREATE_ASSIGNMENT_ENDPOINT,
        data=multipart,
        headers=headers,
        allow_redirects=False,
        timeout=(5, 120),
    )

    # Parse redirect to extract the new assignment ID
    if response.is_redirect:
        redirect_url = response.headers.get("Location", "")
        match = re.search(r"/assignments/(\d+)", redirect_url)
        if not match:
            raise AssignmentUpdateError(
                f"Assignment creation succeeded (redirect received) but could not "
                f"parse assignment ID from redirect target: {redirect_url!r}"
            )
        return match.group(1)

    response.raise_for_status()
    raise AssignmentUpdateError(
        f"Unexpected response from Gradescope: HTTP {response.status_code} "
        f"with no redirect. Assignment may or may not have been created."
    )
