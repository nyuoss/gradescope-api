import os

import pytest
from dotenv import load_dotenv

load_dotenv()

"""
Student: enrolled in courses only as a student
Instructor: enrolled in courses only as an instructor
TA: enrolled in different courses as both a student and instructor
"""

GRADESCOPE_CI_STUDENT_EMAIL = os.getenv("GRADESCOPE_CI_STUDENT_EMAIL")
GRADESCOPE_CI_STUDENT_PASSWORD = os.getenv("GRADESCOPE_CI_STUDENT_PASSWORD")
GRADESCOPE_CI_INSTRUCTOR_EMAIL = os.getenv("GRADESCOPE_CI_INSTRUCTOR_EMAIL")
GRADESCOPE_CI_INSTRUCTOR_PASSWORD = os.getenv("GRADESCOPE_CI_INSTRUCTOR_PASSWORD")
GRADESCOPE_CI_TA_EMAIL = os.getenv("GRADESCOPE_CI_TA_EMAIL")
GRADESCOPE_CI_TA_PASSWORD = os.getenv("GRADESCOPE_CI_TA_PASSWORD")

instructor = pytest.mark.skipif(
    GRADESCOPE_CI_INSTRUCTOR_EMAIL is None or GRADESCOPE_CI_INSTRUCTOR_PASSWORD is None,
    reason="Instructor credentials not provided in environment variables",
)
student = pytest.mark.skipif(
    GRADESCOPE_CI_STUDENT_EMAIL is None or GRADESCOPE_CI_STUDENT_PASSWORD is None,
    reason="Student credentials not provided in environment variables",
)
ta = pytest.mark.skipif(
    GRADESCOPE_CI_TA_EMAIL is None or GRADESCOPE_CI_TA_PASSWORD is None,
    reason="TA credentials not provided in environment variables",
)
