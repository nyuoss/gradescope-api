"""Unit tests for account dashboard course-list parsing (no live Gradescope session)."""

from bs4 import BeautifulSoup

from gradescopeapi.classes._helpers._course_helpers import get_courses_info

# Staff dashboard: two terms in one courseList; courses live in sibling coursesForTerm divs.
_ACCOUNT_STAFF_ONE_LIST = """
<div id="account-show">
  <button class="js-createNewCourse"></button>
  <div class="courseList">
    <h2 class="courseList--term">Fall 2025</h2>
    <div class="courseList--coursesForTerm">
      <a class="courseBox" href="/courses/123456">
        <h3 class="courseBox--shortname">CS 1134</h3>
        <div class="courseBox--name">Intro to Example Course (Fall 2025)</div>
        <div class="courseBox--assignments">3 assignments</div>
      </a>
    </div>
    <h2 class="courseList--term">Spring 2026</h2>
    <div class="courseList--coursesForTerm">
      <a class="courseBox" href="/courses/234567">
        <h3 class="courseBox--shortname">MATH 2000</h3>
        <div class="courseBox--name">Sample Mathematics (Spring 2026)</div>
        <div class="courseBox--assignments">1 assignment</div>
      </a>
      <a class="courseBox" href="/courses/345678">
        <h3 class="courseBox--shortname">PHYS 1100</h3>
        <div class="courseBox--name">Example Physics (Spring 2026)</div>
        <div class="courseBox--assignments">2 assignments</div>
      </a>
    </div>
  </div>
</div>
"""

# User is staff and student: pageHeading switches role; each role has its own courseList block.
_ACCOUNT_STAFF_AND_STUDENT = """
<div id="account-show">
  <button class="js-createNewCourse"></button>
  <h2 class="pageHeading">Instructor Courses</h2>
  <div class="courseList">
    <h2 class="courseList--term">Fall 2025</h2>
    <div class="courseList--coursesForTerm">
      <a class="courseBox" href="/courses/111111">
        <h3 class="courseBox--shortname">STAFF 101</h3>
        <div class="courseBox--name">Staff Course (Fall 2025)</div>
        <div class="courseBox--assignments">4 assignments</div>
      </a>
    </div>
  </div>
  <h2 class="pageHeading">Student Courses</h2>
  <div class="courseList">
    <h2 class="courseList--term">Fall 2025</h2>
    <div class="courseList--coursesForTerm">
      <a class="courseBox" href="/courses/222222">
        <h3 class="courseBox--shortname">STU 201</h3>
        <div class="courseBox--name">Student Enrollment (Fall 2025)</div>
        <div class="courseBox--assignments">5 assignments</div>
      </a>
    </div>
    <h2 class="courseList--term">Spring 2026</h2>
    <div class="courseList--coursesForTerm">
      <a class="courseBox" href="/courses/333333">
        <h3 class="courseBox--shortname">STU 202</h3>
        <div class="courseBox--name">Another Enrollment (Spring 2026)</div>
        <div class="courseBox--assignments">6 assignments</div>
      </a>
    </div>
  </div>
</div>
"""


def test_get_courses_info_multiple_terms_in_one_course_list():
    soup = BeautifulSoup(_ACCOUNT_STAFF_ONE_LIST, "html.parser")
    courses = get_courses_info(soup)

    assert set(courses["instructor"]) == {"123456", "234567", "345678"}
    assert courses["student"] == {}

    fall = courses["instructor"]["123456"]
    assert fall.semester == "Fall" and fall.year == "2025"

    spring = courses["instructor"]["234567"]
    assert spring.semester == "Spring" and spring.year == "2026"


def test_get_courses_info_instructor_and_student_course_lists():
    soup = BeautifulSoup(_ACCOUNT_STAFF_AND_STUDENT, "html.parser")
    courses = get_courses_info(soup)

    assert set(courses["instructor"]) == {"111111"}
    assert set(courses["student"]) == {"222222", "333333"}

    assert courses["instructor"]["111111"].name == "STAFF 101"
    assert courses["student"]["222222"].semester == "Fall"
    assert courses["student"]["333333"].year == "2026"