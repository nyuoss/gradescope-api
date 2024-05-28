"""Functions for uploading assignments to Gradescope."""

import io
import mimetypes
import pathlib

import requests
from bs4 import BeautifulSoup
from requests_toolbelt.multipart.encoder import MultipartEncoder


def upload_assignment(
    session: requests.Session,
    course_id: str,
    assignment_id: str,
    *files: io.TextIOWrapper,
    leaderboard_name: str | None = None,
) -> str | None:
    """Uploads given file objects to the specified assignment on Gradescope.

    Args:
        session (requests.Session): The session object to use for making HTTP requests.
        course_id (str): The ID of the course on Gradescope.
        assignment_id (str): The ID of the assignment on Gradescope.
        *files (io.TextIOWrapper): Variable number of file objects to upload.
        leaderboard_name (str | None, optional): The name of the leaderboard. Defaults to None.

    Returns:
        str | None: Link to submission if successful or None if unsuccessful.
    """
    GS_COURSE_ENDPOINT = f"https://www.gradescope.com/courses/{course_id}"
    GS_UPLOAD_ENDPOINT = f"https://www.gradescope.com/courses/{course_id}/assignments/{assignment_id}/submissions"

    # Get auth token
    # TODO: Refactor to helper function since it is needed in multiple places
    response = session.get(GS_COURSE_ENDPOINT)
    soup = BeautifulSoup(response.text, "html.parser")
    auth_token = soup.find("meta", {"name": "csrf-token"})["content"]

    # Format files for upload
    form_files = []
    for file in files:
        form_files.append(
            (
                "submission[files][]",
                (
                    pathlib.Path(file.name).name,  # get the filename from the path
                    file,
                    mimetypes.guess_type(file.name)[0],
                ),
            )
        )

    # Setup multipart form data
    fields = [
        ("utf8", "✓"),
        ("authenticity_token", auth_token),
        ("submission[method]", "upload"),
        *form_files,
    ]
    if leaderboard_name is not None:
        fields.append(("submission[leaderboard_name]", leaderboard_name))

    multipart = MultipartEncoder(fields=fields)

    headers = {
        "Content-Type": multipart.content_type,
        "Referer": GS_COURSE_ENDPOINT,
    }
    response = session.post(GS_UPLOAD_ENDPOINT, data=multipart, headers=headers)

    # Note: Response status code is always 200 even if upload was unsuccessful (e.g. past the due date,
    # missing form fields, etc.). The response from the server either redirects to the submission page (url)
    # if successful, or redirects to the Course homepage if unsuccessful.
    return (
        None
        if response.url == GS_COURSE_ENDPOINT or response.url.endswith("submissions")
        else response.url
    )
