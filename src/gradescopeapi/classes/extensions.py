"""Functions for getting, adding, and changing student extensions on assignments.

This module provides functions for interacting with the Gradescope API to manage student extensions
on assignments. It includes functions to get all extensions for an assignment, update the extension
for a specific student, and remove a student's extension.

The main functions in this module are:
- `get_extensions`: Retrieves all extensions for a specific assignment.
- `update_student_extension`: Updates the extension for a specific student on an assignment.
- `remove_student_extension`: Removes the extension for a specific student.
"""

import datetime
import json
from dataclasses import dataclass

import requests
import zoneinfo
from bs4 import BeautifulSoup


@dataclass
class Extension:
    name: str
    release_date: datetime.datetime
    due_date: datetime.datetime
    late_due_date: datetime.datetime
    delete_path: str


def get_extensions(
    session: requests.Session, course_id: str, assignment_id: str
) -> dict:
    """Get all extensions for an assignment.

    Args:
        session (requests.Session): The session object used for making HTTP requests.
        course_id (str): The ID of the course.
        assignment_id (str): The ID of the assignment.

    Returns:
        dict: A dictionary containing the extensions, where the keys are user IDs and the values are Extension objects.
        For example:

        {
            "123456": Extension(...),
            "654321": Extension(...)
        }

    Raises:
        RuntimeError: If the request to get extensions fails.
    """

    GS_EXTENSIONS_ENDPOINT = f"https://www.gradescope.com/courses/{course_id}/assignments/{assignment_id}/extensions"
    GS_EXTENSIONS_TABLE_CSS_CLASSES = (
        "table js-overridesTable"  # Table containing extensions
    )

    # get the extensions from the page
    response = session.get(GS_EXTENSIONS_ENDPOINT)

    # check if the request was successful
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to get extensions for assignment {assignment_id}. Status code: {response.status_code}"
        )

    # parse the html response
    extensions_soup = BeautifulSoup(response.text, "html.parser")

    extensions_table = extensions_soup.find(
        "table", class_=GS_EXTENSIONS_TABLE_CSS_CLASSES
    )

    extensions = {}

    table_body = extensions_table.find("tbody")
    for row in table_body.find_all("tr"):
        # find relevant data
        user_properties = row.find("div", {"data-react-class": "EditExtension"}).get(
            "data-react-props"
        )
        user_properties = json.loads(user_properties)

        # user id
        user_id = str(user_properties["override"]["user_id"])  # TODO: keep as int?

        # timezone
        timezone = zoneinfo.ZoneInfo(user_properties["timezone"]["identifier"])

        # extension properties
        extension_info = user_properties["override"]["settings"]
        release_date = extension_info.get("release_date", {}).get("value", None)
        due_date = extension_info.get("due_date", {}).get("value", None)
        late_due_date = extension_info.get("hard_due_date", {}).get("value", None)

        # convert dates to datetime objects
        release_date = (
            datetime.datetime.fromisoformat(release_date).replace(tzinfo=timezone)
            if release_date
            else None
        )
        due_date = (
            datetime.datetime.fromisoformat(due_date).replace(tzinfo=timezone)
            if due_date
            else None
        )
        late_due_date = (
            datetime.datetime.fromisoformat(late_due_date).replace(tzinfo=timezone)
            if late_due_date
            else None
        )

        # delete path
        delete_path = user_properties["deletePath"]

        # name
        name = user_properties["studentName"]

        # create extension object
        extension = Extension(
            name=name,
            release_date=release_date,
            due_date=due_date,
            late_due_date=late_due_date,
            delete_path=delete_path,
        )
        extensions[user_id] = extension

    return extensions


def update_student_extension(
    session: requests.Session,
    course_id: str,
    assignment_id: str,
    user_id: str,
    release_date: datetime.datetime | None = None,
    due_date: datetime.datetime | None = None,
    late_due_date: datetime.datetime | None = None,
) -> bool:
    """Updates the extension for a student on an assignment.

    If the user currently has an extension, this will overwrite their
    current extension. If the user does not have an extension, this
    will add an extension for that user. If a date is None, it will
    not be updated.

    Requirements:
        release_date <= due_date <= late_due_date

    Notes:
        Extensions can go "backwards" too. For example, a user can have
        a release date earlier than the normal release date or a due date
        before the normal due date.

    Args:
        session (requests.Session): The session to use for the request
        course_id (str): The course id
        assignment_id (str): The assignment id
        user_id (str): The user id
        release_date (datetime.datetime | None): The release date. If None, it will not be updated
        due_date (datetime.datetime | None): The due date. If None, it will not be updated
        late_due_date (datetime.datetime | None): The late due date. If None, it will not be updated

    Returns:
        bool: True if the extension was successfully updated, False otherwise

    Raises:
        ValueError: If no dates are provided
        ValueError: If the dates are not in order
    """

    # Check if at least 1 date is set
    if release_date is None and due_date is None and late_due_date is None:
        raise ValueError("At least one date must be provided")

    # Check if date requirements are met (in order)
    dates = [
        date for date in [release_date, due_date, late_due_date] if date is not None
    ]
    if dates != sorted(dates):
        raise ValueError(
            "Dates must be in order: release_date <= due_date <= late_due_date"
        )

    def add_to_body(extension_name: str, extension_datetime: datetime.datetime):
        """Update JSON body for POST request"""
        if extension_datetime is not None:
            # convert datetime to UTC
            extension_datetime = extension_datetime.astimezone(datetime.timezone.utc)

            # convert datetime to string ISO 8601 format
            date_str = extension_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")

            # add to request body
            body["override"]["settings"][extension_name] = {
                "type": "absolute",
                "value": date_str,
            }

    # Update release date, due date, and late due date
    body = {"override": {"user_id": user_id, "settings": {}}}
    for extension_name, extension_datetime in [
        ("release_date", release_date),
        ("due_date", due_date),
        ("hard_due_date", late_due_date),
    ]:
        if extension_datetime is not None:
            add_to_body(extension_name, extension_datetime)

    # send the request
    resp = session.post(
        f"https://www.gradescope.com/courses/{course_id}/assignments/{assignment_id}/extensions",
        json=body,
    )
    return resp.status_code == 200


def remove_student_extension(
    session: requests.Session,
    delete_path: str,
) -> bool:
    raise NotImplementedError("Not implemented yet")
