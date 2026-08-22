from datetime import datetime, timedelta

from gradescopeapi.classes.assignments import (
    update_assignment_date,
    update_assignment_title,
    update_autograder_image_name,
    update_assignment_outline,
    InvalidTitleName,
    AssignmentOutline,
    IdentificationRegions,
    QuestionData,
    CropRect,
)
import requests
import uuid


def test_valid_change_assignment(create_session):
    """Test valid extension for a student."""
    # create test session
    test_session = create_session("instructor")

    course_id = "753413"
    assignment_id = "4436170"
    release_date = datetime(2024, 4, 15)
    due_date = release_date + timedelta(days=1)
    late_due_date = due_date + timedelta(days=1)

    result = update_assignment_date(
        test_session,
        course_id,
        assignment_id,
        release_date,
        due_date,
        late_due_date,
    )
    assert result


def test_boundary_date_assignment(create_session):
    """Test updating assignment with boundary date values."""
    test_session = create_session("instructor")

    course_id = "753413"
    assignment_id = "4436170"
    boundary_date = datetime(1900, 1, 1)  # Very old date

    result = update_assignment_date(
        test_session,
        course_id,
        assignment_id,
        boundary_date,
        boundary_date,
        boundary_date,
    )
    assert result, "Failed to update assignment with boundary dates"


def test_update_assignment_date_invalid_session(create_session):
    """Test updating assignment with student session."""
    test_session = create_session("student")

    course_id = "753413"
    assignment_id = "4436170"
    release_date = datetime(2024, 4, 15)
    due_date = release_date + timedelta(days=1)
    late_due_date = due_date + timedelta(days=1)

    try:
        update_assignment_date(
            test_session,
            course_id,
            assignment_id,
            release_date,
            due_date,
            late_due_date,
        )
        assert False, "Incorrectly updated assignment title with invalid session"
    except requests.exceptions.HTTPError as e:
        assert e.response.status_code == 401  # HTTP 401 Not Authorized


def test_autograder_valid_image_name(create_session):
    """Test updating assignment with valid image name."""
    test_session = create_session("instructor")

    course_id = "753413"
    assignment_id = "7193007"
    image_name = "gradescope/autograder-base:ubuntu-22.04"

    result = update_autograder_image_name(
        test_session,
        course_id,
        assignment_id,
        image_name,
    )
    assert result, "Failed to update autograder image name"


def test_autograder_invalid_image_name(create_session):
    """Test updating assignment with invalid image name."""
    test_session = create_session("instructor")

    course_id = "753413"
    assignment_id = "7193007"
    image_name = "gradescope/autograders:us-prod-docker_image-123456"

    result = update_autograder_image_name(
        test_session,
        course_id,
        assignment_id,
        image_name,
    )
    assert not result, "Incorrectly updated to invalid autograder image name"


def test_autograder_invalid_session(create_session):
    """Test updating assignment with student session."""
    test_session = create_session("student")

    course_id = "753413"
    assignment_id = "7193007"
    image_name = "gradescope/autograder-base:ubuntu-22.04"

    try:
        update_autograder_image_name(
            test_session,
            course_id,
            assignment_id,
            image_name,
        )
        assert False, "Incorrectly updated assignment with invalid session"
    except requests.exceptions.HTTPError as e:
        assert e.response.status_code == 401  # HTTP 401 Not Authorized


def test_autograder_invalid_assignment_type(create_session):
    """Test updating assignment with invalid assignment type."""
    test_session = create_session("instructor")

    course_id = "753413"
    assignment_id = "7205866"
    image_name = "gradescope/autograder-base:ubuntu-22.04"

    try:
        update_autograder_image_name(
            test_session,
            course_id,
            assignment_id,
            image_name,
        )
        assert False, "Incorrectly updated assignment with invalid assignment"
    except requests.exceptions.HTTPError as e:
        assert e.response.status_code == 404  # HTTP 404 Not Found


def test_update_assignment_title_valid_random_title(create_session):
    """Test updating assignment with random name."""
    test_session = create_session("instructor")

    course_id = "753413"
    assignment_id = "7332839"
    new_assignment_name = f"Test Rename - {uuid.uuid4()}"

    result = update_assignment_title(
        test_session,
        course_id,
        assignment_id,
        new_assignment_name,
    )
    assert result, "Failed to update assignment name"


def test_update_assignment_title_invalid_title_whitespace(create_session):
    """Test updating assignment with invalid name containing only whitespace."""
    test_session = create_session("instructor")

    course_id = "753413"
    assignment_id = "7193007"
    new_assignment_name = "  "  # whitespace only not allowed

    try:
        update_assignment_title(
            test_session,
            course_id,
            assignment_id,
            new_assignment_name,
        )
        assert False, "Incorrectly updated to invalid assignment name"
    except InvalidTitleName:
        pass


def test_update_assignment_title_invalid_session(create_session):
    """Test updating assignment with student session."""
    test_session = create_session("student")

    course_id = "753413"
    assignment_id = "7332839"
    new_assignment_name = f"Test Rename - {uuid.uuid4()}"

    try:
        update_assignment_title(
            test_session,
            course_id,
            assignment_id,
            new_assignment_name,
        )
        assert False, "Incorrectly updated assignment title with invalid session"
    except requests.exceptions.HTTPError as e:
        assert e.response.status_code == 401  # HTTP 401 Not Authorized


def test_default_crop_rect(create_session):
    """Test that QuestionData defaults to the standard crop rectangle."""
    question = QuestionData(title="Question 1", weight=5)
    assert question.crop_rect_list == [CropRect(x1=0, x2=100, y1=90, y2=100)]


def test_valid_change_assignment_outline(create_session):
    """Test updating assignment outline with valid question data."""
    test_session = create_session("instructor")

    course_id = "753413"
    assignment_id = "7193007"
    outline = AssignmentOutline(
        question_data=[
            QuestionData(
                title="Question 1",
                weight=5,
                crop_rect_list=[
                    CropRect(x1=0, x2=100, y1=90, y2=100),
                ],
            ),
            QuestionData(
                title="Question 2",
                weight=5,
                crop_rect_list=[
                    CropRect(x1=0, x2=100, y1=90, y2=100),
                ],
            ),
        ],
        identification_regions=IdentificationRegions(name=None, sid=None),
    )

    result = update_assignment_outline(
        test_session,
        course_id,
        assignment_id,
        outline,
    )
    assert result, "Failed to update assignment outline"


def test_update_assignment_outline_invalid_session(create_session):
    """Test updating assignment outline with student session."""
    test_session = create_session("student")

    course_id = "753413"
    assignment_id = "7193007"
    outline = AssignmentOutline(
        question_data=[
            QuestionData(
                title="Question 1",
                weight=5,
                crop_rect_list=[
                    CropRect(x1=0, x2=100, y1=90, y2=100),
                ],
            ),
        ],
    )

    try:
        update_assignment_outline(
            test_session,
            course_id,
            assignment_id,
            outline,
        )
        assert False, "Incorrectly updated assignment outline with invalid session"
    except requests.exceptions.HTTPError as e:
        assert e.response.status_code == 401  # HTTP 401 Not Authorized
