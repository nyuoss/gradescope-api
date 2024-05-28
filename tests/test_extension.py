from datetime import datetime, timedelta

import pytest
from custom_skips import instructor
from gradescopeapi.classes.extensions import get_extensions, update_student_extension


@instructor
def test_get_extensions(create_session):
    """Test fetching extensions for an assignment."""
    # create test session
    test_session = create_session("instructor")

    course_id = "753413"
    assignment_id = "4330410"

    extensions = get_extensions(test_session, course_id, assignment_id)
    assert (
        len(extensions) > 0
    ), f"Got 0 extensions for course {course_id} and assignment {assignment_id}"


@instructor
def test_valid_change_extension(create_session):
    """Test granting a valid extension for a student."""
    # create test session
    test_session = create_session("instructor")

    course_id = "753413"
    assignment_id = "4330410"
    user_id = "6515875"
    release_date = datetime(2024, 4, 15)
    due_date = release_date + timedelta(days=1)
    late_due_date = due_date + timedelta(days=1)

    result = update_student_extension(
        test_session,
        course_id,
        assignment_id,
        user_id,
        release_date,
        due_date,
        late_due_date,
    )
    assert result, "Failed to update student extension"


@instructor
def test_invalid_change_extension(create_session):
    """Test granting an invalid extension for a student due to invalid dates."""
    # create test session
    test_session = create_session("instructor")

    course_id = "753413"
    assignment_id = "4330410"
    user_id = "6515875"
    release_date = datetime(2024, 4, 15)
    due_date = release_date + timedelta(days=-1)
    late_due_date = due_date + timedelta(days=-1)

    with pytest.raises(
        ValueError,
        match="Dates must be in order: release_date <= due_date <= late_due_date",
    ):
        update_student_extension(
            test_session,
            course_id,
            assignment_id,
            user_id,
            release_date,
            due_date,
            late_due_date,
        )


@instructor
def test_invalid_user_id(create_session):
    """Test granting an invalid extension for a student due to invalid user ID."""
    test_session = create_session("instructor")

    course_id = "753413"
    assignment_id = "4330410"
    invalid_user_id = "9999999"  # Assuming this is an invalid ID

    # Attempt to change the extension with an invalid user ID
    result = update_student_extension(
        test_session,
        course_id,
        assignment_id,
        invalid_user_id,
        datetime.now(),
        datetime.now() + timedelta(days=1),
        datetime.now() + timedelta(days=2),
    )

    # Check the function returns False for non-existent user ID
    assert not result, "Function should indicate failure when given an invalid user ID"


@instructor
def test_invalid_assignment_id(create_session):
    """Test extension handling with an invalid assignment ID."""
    test_session = create_session("instructor")
    course_id = "753413"
    invalid_assignment_id = "9999999"

    # Attempt to fetch extensions with an invalid assignment ID
    with pytest.raises(RuntimeError, match="Failed to get extensions"):
        get_extensions(test_session, course_id, invalid_assignment_id)


@instructor
def test_invalid_course_id(create_session):
    """Test extension handling with an invalid course ID."""
    test_session = create_session("instructor")
    invalid_course_id = "9999999"

    # Attempt to fetch or modify extensions with an invalid course ID
    with pytest.raises(RuntimeError, match="Failed to get extensions"):
        get_extensions(test_session, invalid_course_id, "4330410")
