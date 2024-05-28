from datetime import datetime, timedelta

from custom_skips import instructor
from gradescopeapi.classes.assignments import update_assignment_date


@instructor
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


@instructor
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
