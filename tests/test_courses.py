from custom_skips import instructor, student, ta
from gradescopeapi.classes.courses import get_course_users, get_courses


@student
def test_get_courses_student(create_session):
    # fetch student account
    session = create_session("student")

    # get student courses
    courses = get_courses(session)

    assert courses["instructor"] == {} and courses["student"] != {}


@instructor
def test_get_courses_instructor(create_session):
    # fetch instructor account
    session = create_session("instructor")

    # get instructor courses
    courses = get_courses(session)

    assert courses["instructor"] != {} and courses["student"] == {}


@ta
def test_get_courses_ta(create_session):
    # fetch ta account
    session = create_session("ta")

    # get ta courses
    courses = get_courses(session)

    assert courses["instructor"] != {} and courses["student"] != {}


@instructor
def test_membership_invalid(create_session):
    # fetch instructor account
    session = create_session("instructor")

    invalid_course_id = "1111111"

    # get course members
    members = get_course_users(session, invalid_course_id)

    assert members is None


@instructor
def test_membership(create_session):
    # fetch instructor account
    session = create_session("instructor")

    course_id = "753413"

    # get course members
    members = get_course_users(session, course_id)

    assert members is not None and len(members) > 0
