"""Functions for modifying assignment details."""

import datetime
import time

import requests
from bs4 import BeautifulSoup
from requests_toolbelt.multipart.encoder import MultipartEncoder

from gradescopeapi.classes._data_model import Assignment
from gradescopeapi.classes._helpers._assignment_helpers import (
    check_page_auth,
    get_assignments_instructor_view,
    get_assignments_student_view,
    get_submission_files,
)


def update_assignment_date(
    session: requests.Session,
    course_id: str,
    assignment_id: str,
    release_date: datetime.datetime | None = None,
    due_date: datetime.datetime | None = None,
    late_due_date: datetime.datetime | None = None,
):
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

    Returns:
        bool: True if the assignment dates were successfully updated, False otherwise.
    """
    GS_EDIT_ASSIGNMENT_ENDPOINT = f"https://www.gradescope.com/courses/{course_id}/assignments/{assignment_id}/edit"
    GS_POST_ASSIGNMENT_ENDPOINT = (
        f"https://www.gradescope.com/courses/{course_id}/assignments/{assignment_id}"
    )

    # Get auth token
    response = session.get(GS_EDIT_ASSIGNMENT_ENDPOINT)
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

    return response.status_code == 200


def get_assignments(session: requests.Session, course_id: str) -> list[Assignment]:
    """
    Get a list of detailed assignment information for a course
    Returns:
        list: A list of Assignments
    Raises:
        Exceptions:
        "One or more invalid parameters": if course_id or assignment_id is null or empty value
        "You are not authorized to access this page.": if logged in user is unable to access submissions
        "You must be logged in to access this page.": if no user is logged in
    """
    course_endpoint = f"https://www.gradescope.com/courses/{course_id}"
    # check that course_id is valid (not empty)
    if not course_id:
        raise Exception("Invalid Course ID")
    session = session

    # scrape page
    coursepage_resp = check_page_auth(session, course_endpoint)
    coursepage_soup = BeautifulSoup(coursepage_resp.text, "html.parser")

    # two different helper functions to parse assignment info
    # webpage html structure differs based on if user if instructor or student
    assignment_info_list = get_assignments_instructor_view(coursepage_soup)
    if not assignment_info_list:
        assignment_info_list = get_assignments_student_view(coursepage_soup)

    return assignment_info_list


def get_assignment_submissions(
    session, course_id: str, assignment_id: str
) -> dict[str, list[str]]:
    """
    Get a list of dicts mapping AWS links for all submissions to each submission id
    Returns:
        dict: A dictionary of submissions, where the keys are the submission ids and the values are
        a list of aws links to the submission pdf
        For example:
            {
                'submission_id': [
                    'aws_link1.com',
                    'aws_link2.com',
                    ...
                ],
                ...
            }
    Raises:
        Exceptions:
            "One or more invalid parameters": if course_id or assignment_id is null or empty value
            "You are not authorized to access this page.": if logged in user is unable to access submissions
            "You must be logged in to access this page.": if no user is logged in
            "Page not Found": When link is invalid: change in url, invalid course_if or assignment id
            "Image only submissions not yet supported": assignment is image submission only, which is not yet supported
    NOTE:
    1. Image submissions not supports, need to find an endpoint to retrieve image pdfs
    2. Not recommended for use, since this makes a GET request for every submission -> very slow!
    3. so far only accessible for teachers, not for students to get submissions to an assignment
    """
    ASSIGNMENT_ENDPOINT = (
        f"https://www.gradescope.com/courses/{course_id}/assignments/{assignment_id}"
    )
    ASSIGNMENT_SUBMISSIONS_ENDPOINT = f"{ASSIGNMENT_ENDPOINT}/review_grades"
    if not course_id or not assignment_id:
        raise Exception("One or more invalid parameters")
    session = session
    submissions_resp = check_page_auth(session, ASSIGNMENT_SUBMISSIONS_ENDPOINT)
    submissions_soup = BeautifulSoup(submissions_resp.text, "html.parser")
    # select submissions (class of td.table--primaryLink a tag, submission id stored in href link)
    submissions_a_tags = submissions_soup.select("td.table--primaryLink a")
    submission_ids = [
        a_tag.attrs.get("href").split("/")[-1] for a_tag in submissions_a_tags
    ]
    submission_links = {}
    for submission_id in submission_ids:  # doesn't support image submissions yet
        aws_links = get_submission_files(
            session, course_id, assignment_id, submission_id
        )
        submission_links[submission_id] = aws_links
        # sleep for 0.1 seconds to avoid sending too many requests to gradescope
        time.sleep(0.1)
    return submission_links


def get_assignment_submission(
    session, student_email: str, course_id: str, assignment_id: str
) -> list[str]:
    """
    Get a list of aws links to pdfs of the student's most recent submission to an assignment
    Returns:
        list: A list of aws links as strings
        For example:
            [
                'aws_link1.com',
                'aws_link2.com',
                ...
            ]
    Raises:
            Exceptions:
            "One or more invalid parameters": if course_id or assignment_id is null or empty value
            "You are not authorized to access this page.": if logged in user is unable to access submissions
            "You must be logged in to access this page.": if no user is logged in
            "Page not Found": When link is invalid: change in url, invalid course_if or assignment id
            "Image only submissions not yet supported": assignment is image submission only, which is not yet supported
    NOTE: so far only accessible for teachers, not for students to get their own submission
    """
    # fetch submission id
    ASSIGNMENT_ENDPOINT = (
        f"https://www.gradescope.com/courses/{course_id}/assignments/{assignment_id}"
    )
    ASSIGNMENT_SUBMISSIONS_ENDPOINT = f"{ASSIGNMENT_ENDPOINT}/review_grades"
    if not (student_email and course_id and assignment_id):
        raise Exception("One or more invalid parameters")
    session = session
    submissions_resp = check_page_auth(session, ASSIGNMENT_SUBMISSIONS_ENDPOINT)
    submissions_soup = BeautifulSoup(submissions_resp.text, "html.parser")
    td_with_email = submissions_soup.find(
        "td", string=lambda s: student_email in str(s)
    )
    if td_with_email:
        # grab submission from previous td
        submission_td = td_with_email.find_previous_sibling()
        # submission_td will have an anchor element as a child if there is a submission
        a_element = submission_td.find("a")
        if a_element:
            submission_id = a_element.get("href").split("/")[-1]
        else:
            raise Exception("No submission found")
    # call get_submission_files helper function
    aws_links = get_submission_files(session, course_id, assignment_id, submission_id)
    return aws_links
