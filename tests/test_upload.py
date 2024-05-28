from custom_skips import student
from gradescopeapi.classes.upload import upload_assignment


@student
def test_valid_upload(create_session):
    # create test session
    test_session = create_session("student")

    course_id = "753413"
    assignment_id = "4455030"

    with (
        open("tests/test_upload_files/text_file.txt", "rb") as text_file,
        open("tests/test_upload_files/markdown_file.md", "rb") as markdown_file,
        open("tests/test_upload_files/python_file.py", "rb") as python_file,
    ):
        submission_link = upload_assignment(
            test_session,
            course_id,
            assignment_id,
            text_file,
            markdown_file,
            python_file,
            leaderboard_name="test",
        )

    assert (
        submission_link is not None
    ), "Failed to upload assignment. Double check due dates on Gradescope to ensure the assignment is still open."


@student
def test_invalid_upload(create_session):
    # create test session
    test_session = create_session("student")

    course_id = "753413"
    invalid_assignment_id = "1111111"

    with (
        open("tests/test_upload_files/text_file.txt", "rb") as text_file,
        open("tests/test_upload_files/markdown_file.md", "rb") as markdown_file,
        open("tests/test_upload_files/python_file.py", "rb") as python_file,
    ):
        submission_link = upload_assignment(
            test_session,
            course_id,
            invalid_assignment_id,
            text_file,
            markdown_file,
            python_file,
        )

    assert submission_link is None


@student
def test_upload_with_no_files(create_session):
    test_session = create_session("student")
    course_id = "753413"
    assignment_id = "4455030"
    # No files are passed
    submission_link = upload_assignment(test_session, course_id, assignment_id)
    assert submission_link is None, "Should handle missing files gracefully"
