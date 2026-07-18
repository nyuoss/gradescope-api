from datetime import datetime

import requests
from fastapi import Depends, FastAPI, Form, HTTPException, UploadFile, status

from gradescopeapi._config.config import (
    CreateAssignment,
    FileUploadModel,
    LoginRequestModel,
    RubricLockingSetting,
    StudentSubmissionSettings,
    WhenToCreateRubric,
)
from gradescopeapi.classes.account import Account
from gradescopeapi.classes.assignments import (
    Assignment,
    AssignmentUpdateError,
    create_assignment,
    update_assignment_date,
)
from gradescopeapi.classes.connection import GSConnection
from gradescopeapi.classes.courses import Course
from gradescopeapi.classes.extensions import get_extensions, update_student_extension
from gradescopeapi.classes.member import Member
from gradescopeapi.classes.upload import upload_assignment

app = FastAPI()

# Create instance of GSConnection, to be used where needed
connection = GSConnection()


def get_gs_connection():
    """
    Returns the GSConnection instance

    Returns:
        connection (GSConnection): an instance of the GSConnection class,
            containing the session object used to make HTTP requests,
            a boolean defining True/False if the user is logged in, and
            the user's Account object.
    """
    return connection


def get_gs_connection_session():
    """
    Returns session of the the GSConnection instance

    Returns:
        connection.session (GSConnection.session): an instance of the GSConnection class' session object used to make HTTP requests
    """
    return connection.session


def get_account():
    """
    Returns the user's Account object

    Returns:
        Account (Account): an instance of the Account class, containing
            methods for interacting with the user's courses and assignments.
    """
    return Account(session=get_gs_connection_session)


# Create instance of GSConnection, to be used where needed
connection = GSConnection()

account = None


@app.get("/")
def root():
    return {"message": "Hello World"}


@app.post("/login", name="login")
def login(
    login_data: LoginRequestModel,
    gs_connection: GSConnection = Depends(get_gs_connection),
):
    """Login to Gradescope, with correct credentials

    Args:
        username (str): email address of user attempting to log in
        password (str): password of user attempting to log in

    Raises:
        HTTPException: If the request to login fails, with a 404 Unauthorized Error status code and the error message "Account not found".
    """
    user_email = login_data.email
    password = login_data.password

    try:
        connection.login(user_email, password)
        global account
        account = connection.account
        return {"message": "Login successful", "status_code": status.HTTP_200_OK}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"Account not found. Error {e}")


@app.post("/logout", name="logout")
def logout(gs_connection: GSConnection = Depends(get_gs_connection)):
    """Log out from Gradescope and clear the connection state."""
    gs_connection.logout()
    global account
    account = None
    return {"message": "Logout successful", "status_code": status.HTTP_200_OK}


@app.post("/courses", response_model=dict[str, dict[str, Course]])
def get_courses():
    """Get all courses for the user

    Args:
        account (Account): Account object containing the user's courses

    Returns:
        dict: dictionary of dictionaries

    Raises:
        HTTPException: If the request to get courses fails, with a 500 Internal Server Error status code and the error message.
    """
    try:
        course_list = account.get_courses()
        return course_list
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/course_users", response_model=list[Member])
def get_course_users(course_id: str):
    """Get all users for a course. ONLY FOR INSTRUCTORS.

    Args:
        course_id (str): The ID of the course.

    Returns:
        dict: dictionary of dictionaries

    Raises:
        HTTPException: If the request to get courses fails, with a 500 Internal Server Error status code and the error message.
    """
    try:
        course_list = connection.account.get_course_users(course_id)
        print(course_list)
        return course_list
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/assignments", response_model=list[Assignment])
def get_assignments(course_id: str):
    """Get all assignments for a course. ONLY FOR INSTRUCTORS.
        list: list of user emails

    Raises:
        HTTPException: If the request to get course users fails, with a 500 Internal Server Error status code and the error message.
    """
    try:
        course_users = connection.account.get_assignments(course_id)
        return course_users
    except RuntimeError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get course users. Error {e}"
        )


@app.post("/assignment_submissions", response_model=dict[str, list[str]])
def get_assignment_submissions(
    course_id: str,
    assignment_id: str,
):
    """Get all assignment submissions for an assignment. ONLY FOR INSTRUCTORS.

    Args:
        course_id (str): The ID of the course.
        assignment_id (str): The ID of the assignment.

    Returns:
        list: list of Assignment objects

    Raises:
        HTTPException: If the request to get assignments fails, with a 500 Internal Server Error status code and the error message.
    """
    try:
        assignment_list = connection.account.get_assignment_submissions(
            course_id=course_id, assignment_id=assignment_id
        )
        return assignment_list
    except RuntimeError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get assignments. Error: {e}"
        )


@app.post("/single_assignment_submission", response_model=list[str])
def get_student_assignment_submission(
    student_email: str, course_id: str, assignment_id: str
):
    """Get a student's assignment submission. ONLY FOR INSTRUCTORS.

    Args:
        student_email (str): The email address of the student.
        course_id (str): The ID of the course.
        assignment_id (str): The ID of the assignment.

    Returns:
        dict: dictionary containing a list of student emails and their corresponding submission IDs

    Raises:
        HTTPException: If the request to get assignment submissions fails, with a 500 Internal Server Error status code and the error message.
    """
    try:
        assignment_submissions = connection.account.get_assignment_submission(
            student_email=student_email,
            course_id=course_id,
            assignment_id=assignment_id,
        )
        return assignment_submissions
    except RuntimeError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get assignment submissions. Error: {e}"
        )


@app.post("/assignments/update_dates")
def update_assignment_dates(
    course_id: str,
    assignment_id: str,
    release_date: datetime,
    due_date: datetime,
    late_due_date: datetime,
):
    """
    Update the release and due dates for an assignment. ONLY FOR INSTRUCTORS.

    Args:
        course_id (str): The ID of the course.
        assignment_id (str): The ID of the assignment.
        release_date (datetime): The release date of the assignment.
        due_date (datetime): The due date of the assignment.
        late_due_date (datetime): The late due date of the assignment.

    Notes:
        The timezone for dates used in Gradescope is specific to an institution. For example, for NYU, the timezone is America/New_York.
        For datetime objects passed to this function, the timezone should be set to the institution's timezone.

    Returns:
        dict: A dictionary with a "message" key indicating if the assignment dates were updated successfully.

    Raises:
        HTTPException: If the assignment dates update fails, with a 400 Bad Request status code and the error message "Failed to update assignment dates".
    """
    try:
        print(f"late due date {late_due_date}")
        success = update_assignment_date(
            session=connection.session,
            course_id=course_id,
            assignment_id=assignment_id,
            release_date=release_date,
            due_date=due_date,
            late_due_date=late_due_date,
        )
        if success:
            return {
                "message": "Assignment dates updated successfully",
                "status_code": status.HTTP_200_OK,
            }
        else:
            raise HTTPException(
                status_code=400, detail="Failed to update assignment dates"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/assignments/extensions", response_model=dict)
def get_assignment_extensions(course_id: str, assignment_id: str):
    """
    Get all extensions for an assignment.

    Args:
        course_id (str): The ID of the course.
        assignment_id (str): The ID of the assignment.

    Returns:
        dict: A dictionary containing the extensions, where the keys are user IDs and the values are Extension objects.

    Raises:
        HTTPException: If the request to get extensions fails, with a 500 Internal Server Error status code and the error message.
    """
    try:
        extensions = get_extensions(
            session=connection.session,
            course_id=course_id,
            assignment_id=assignment_id,
        )
        return extensions
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/assignments/extensions/update")
def update_extension(
    course_id: str,
    assignment_id: str,
    user_id: str,
    release_date: datetime,
    due_date: datetime,
    late_due_date: datetime,
):
    """
    Update the extension for a student on an assignment. ONLY FOR INSTRUCTORS.

    Args:
        course_id (str): The ID of the course.
        assignment_id (str): The ID of the assignment.
        user_id (str): The ID of the student.
        release_date (datetime): The release date of the extension.
        due_date (datetime): The due date of the extension.
        late_due_date (datetime): The late due date of the extension.

    Returns:
        dict: A dictionary with a "message" key indicating if the extension was updated successfully.

    Raises:
        HTTPException: If the extension update fails, with a 400 Bad Request status code and the error message.
        HTTPException: If a ValueError is raised (e.g., invalid date order), with a 400 Bad Request status code and the error message.
        HTTPException: If any other exception occurs, with a 500 Internal Server Error status code and the error message.
    """
    try:
        success = update_student_extension(
            session=connection.session,
            course_id=course_id,
            assignment_id=assignment_id,
            user_id=user_id,
            release_date=release_date,
            due_date=due_date,
            late_due_date=late_due_date,
        )
        if success:
            return {
                "message": "Extension updated successfully",
                "status_code": status.HTTP_200_OK,
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to update extension")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/assignments/upload")
def upload_assignment_files(
    course_id: str, assignment_id: str, leaderboard_name: str, file: FileUploadModel
):
    """
    Upload files for an assignment.

    NOTE: This function within FastAPI is currently nonfunctional, as we did not
    find the datatype for file, which would allow us to upload a file via
    Postman. However, this functionality works correctly if a user
    runs this as a Python package.

    Args:
        course_id (str): The ID of the course on Gradescope.
        assignment_id (str): The ID of the assignment on Gradescope.
        leaderboard_name (str): The name of the leaderboard.
        file (FileUploadModel): The file object to upload.

    Returns:
        dict: A dictionary containing the submission link for the uploaded files.

    Raises:
        HTTPException: If the upload fails, with a 400 Bad Request status code and the error message "Upload unsuccessful".
        HTTPException: If any other exception occurs, with a 500 Internal Server Error status code and the error message.
    """
    try:
        submission_link = upload_assignment(
            session=connection.session,
            course_id=course_id,
            assignment_id=assignment_id,
            files=file,
            leaderboard_name=leaderboard_name,
        )
        if submission_link:
            return {"submission_link": submission_link}
        else:
            raise HTTPException(status_code=400, detail="Upload unsuccessful")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/assignments/create")
def create_new_assignment(
    course_id: str = Form(...),
    title: str = Form(...),
    submissions_anonymized: bool = Form(False),
    student_submission: bool = Form(False),
    student_submission_settings: str | None = Form(None),
    when_to_create_rubric: WhenToCreateRubric = Form(WhenToCreateRubric.WHILE_GRADING),
    rubric_locking_setting: RubricLockingSetting = Form(RubricLockingSetting.ALL_EDIT),
    template_pdf: UploadFile | None = None,
):
    """
    Create a new assignment in a course. The session must have instructor privileges.

    The student_submission_settings field is a JSON string describing the
    StudentSubmissionSettings model (release_date, due_date, submission_type, etc.).

    Args:
        course_id (str): The ID of the course.
        title (str): The title of the new assignment.
        submissions_anonymized (bool, optional): Anonymize submissions. Defaults to False.
        student_submission (bool, optional): Whether students submit. Defaults to False.
        student_submission_settings (str | None, optional): JSON settings. Defaults to None.
        when_to_create_rubric (WhenToCreateRubric, optional): Rubric timing. Defaults to WHILE_GRADING.
        rubric_locking_setting (RubricLockingSetting, optional): Rubric locking. Defaults to ALL_EDIT.
        template_pdf (UploadFile | None, optional): Template PDF file. Defaults to None.

    Returns:
        dict: A dictionary containing the new assignment ID.

    Raises:
        HTTPException: 400 if validation or creation fails, 500 on unexpected errors.
    """
    settings = None
    if student_submission_settings:
        settings = StudentSubmissionSettings.model_validate_json(
            student_submission_settings
        )

    try:
        create_data = CreateAssignment(
            course_id=course_id,
            title=title,
            submissions_anonymized=submissions_anonymized,
            student_submission=student_submission,
            student_submission_settings=settings,
            when_to_create_rubric=when_to_create_rubric,
            rubric_locking_setting=rubric_locking_setting,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    pdf_file = template_pdf.file if template_pdf else None
    pdf_filename = template_pdf.filename if template_pdf else None
    if pdf_file is not None:
        pdf_file.seek(0, 2)  # seek to end to get file size
        file_size = pdf_file.tell()
        pdf_file.seek(0)  # rewind to start
        if file_size > 50 * 1024 * 1024:  # 50 MB limit
            raise HTTPException(
                status_code=413,
                detail=f"Template PDF size {file_size} bytes exceeds 50 MB limit",
            )

    try:
        assignment_id = create_assignment(
            session=connection.session,
            course_id=create_data.course_id,
            title=create_data.title,
            template_pdf=pdf_file,
            template_pdf_filename=pdf_filename,
            submissions_anonymized=create_data.submissions_anonymized,
            student_submission=create_data.student_submission,
            student_submission_settings=create_data.student_submission_settings,
            when_to_create_rubric=create_data.when_to_create_rubric,
            rubric_locking_setting=create_data.rubric_locking_setting,
        )
        return {
            "assignment_id": assignment_id,
            "status_code": status.HTTP_200_OK,
        }
    except AssignmentUpdateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except requests.HTTPError as e:
        raise HTTPException(
            status_code=e.response.status_code
            if e.response is not None
            else status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
