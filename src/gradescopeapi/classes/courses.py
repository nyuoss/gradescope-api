import requests
from bs4 import BeautifulSoup

from gradescopeapi.classes._data_model import Member
from gradescopeapi.classes._helpers._assignment_helpers import (
    check_page_auth,
)
from gradescopeapi.classes._helpers._course_helpers import (
    get_course_members,
    get_courses_info,
)


def get_courses(session: requests.Session) -> dict:
    """Gets all courses for the user, including both instructor and student courses

    Returns:
        dict: A dictionary of dictionaries, where keys are "instructor" and "student" and values are
        dictionaries containing all courses, where keys are course IDs and values are Course objects.

        For example:
            {
            'instructor': {
                "123456": Course(...),
                "234567": Course(...)
            },
            'student': {
                "654321": Course(...),
                "765432": Course(...)
            }
            }

    Raises:
        RuntimeError: If request to account page fails.
    """

    endpoint = "https://www.gradescope.com/account"

    # get main page
    response = session.get(endpoint)

    if response.status_code != 200:
        raise RuntimeError(
            "Failed to access account page on Gradescope. Status code: {response.status_code}"
        )

    soup = BeautifulSoup(response.text, "html.parser")

    # see if user is solely a student or instructor
    user_courses, is_instructor = get_courses_info(soup, "Your Courses")

    # if the user is indeed solely a student or instructor
    # return the appropriate set of courses
    if user_courses:
        if is_instructor:
            return {"instructor": user_courses, "student": {}}
        else:
            return {"instructor": {}, "student": user_courses}

    # if user is both a student and instructor, get both sets of courses
    courses = {"instructor": {}, "student": {}}

    # get instructor courses
    instructor_courses, _ = get_courses_info(soup, "Instructor Courses")
    courses["instructor"] = instructor_courses

    # get student courses
    student_courses, _ = get_courses_info(soup, "Student Courses")
    courses["student"] = student_courses

    return courses


def get_course_users(session: requests.Session, course_id: str) -> list[Member]:
    """
    Get a list of all users in a course
    Returns:
        list: A list of users in the course (Member objects)
    Raises:
        Exceptions:
        "One or more invalid parameters": if course_id is null or empty value
        "You must be logged in to access this page.": if no user is logged in
    """

    membership_endpoint = f"https://www.gradescope.com/courses/{course_id}/memberships"

    # check that course_id is valid (not empty)
    if not course_id:
        raise Exception("Invalid Course ID")

    try:
        # scrape page
        membership_resp = check_page_auth(session, membership_endpoint)
        membership_soup = BeautifulSoup(membership_resp.text, "html.parser")

        # get all users in the course
        users = get_course_members(membership_soup, course_id)

        return users
    except Exception:
        return None
