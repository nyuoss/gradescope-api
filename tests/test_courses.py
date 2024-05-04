import os
from dotenv import load_dotenv
import pytest

from sylveon._classes._account import Account

# load .env file
load_dotenv()
GRADESCOPE_CI_STUDENT_EMAIL = os.getenv("GRADESCOPE_CI_STUDENT_EMAIL")
GRADESCOPE_CI_STUDENT_PASSWORD = os.getenv("GRADESCOPE_CI_STUDENT_PASSWORD")
GRADESCOPE_CI_INSTRUCTOR_EMAIL = os.getenv("GRADESCOPE_CI_INSTRUCTOR_EMAIL")
GRADESCOPE_CI_INSTRUCTOR_PASSWORD = os.getenv("GRADESCOPE_CI_INSTRUCTOR_PASSWORD")

# TODO:
# - Test for exact course info
# - Test for users that are both instructors and students


def test_get_courses_student():

    # create Account object
    account = Account()

    # login
    account.connection.login(
        GRADESCOPE_CI_STUDENT_EMAIL, GRADESCOPE_CI_STUDENT_PASSWORD
    )

    # get courses
    courses = account.get_courses()

    assert courses["instructor"] == {} and courses["student"] != {}


def test_get_courses_instructor():

    # create Account object
    account = Account()

    # login
    account.connection.login(
        GRADESCOPE_CI_INSTRUCTOR_EMAIL, GRADESCOPE_CI_INSTRUCTOR_PASSWORD
    )

    # get courses
    courses = account.get_courses()

    assert courses["instructor"] != {} and courses["student"] == {}
