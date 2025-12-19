import json

from bs4 import BeautifulSoup
import bs4

from gradescopeapi.classes.courses import Course
from gradescopeapi.classes.member import Member


def get_courses_info(soup: BeautifulSoup) -> dict[str, dict[str, Course]]:
    """
    Scrape all course info from the main page of Gradescope.

    Args:
        soup (BeautifulSoup): BeautifulSoup object with parsed HTML.
        user_type (str): The user type to scrape courses for (Instructor or Student courses).

    Returns:
        dict: A dictionary mapping course IDs to Course objects containing all course info.

        For example:
        {
            "instructor": {
                "123456": Course(
                    name="CS 1134",
                    full_name="Data Structures and Algorithms",
                    semester="Fall",
                    year="2021",
                    num_grades_published="0",
                    num_assignments="5"
                )
            },
            "student": {}
        }
    """

    # initialize dictionary to store all courses
    all_courses = {"student": {}, "instructor": {}}

    # find heading for courses
    courses = soup.select_one("div#account-show")

    # use "Create Course" button to check if user is a staff user in any course
    button = soup.select_one("button.js-createNewCourse")
    is_staff = button is not None

    # parse through course sections and add courses to appropriate account type
    sectionType = "instructor" if is_staff else "student"
    courses = soup.select_one("div#account-show")
    sections = courses.find_all()
    for section in sections:
        # only need to switch to student courses if user is both staff role and student role in different courses
        if section.name == "h2" and "pageHeading" in section.get("class", []):
            # check if there is a label
            if section.text == "Student Courses":
                sectionType = "student"
            # else:
        elif section.name == "div" and "courseList" in section.get("class", []):
            for term in section.find_all("div", class_="courseList--term"):
                # find first "a" -> course
                course = term.find_next("a")
                while course is not None:
                    # fetch course id and create new dictionary for each course
                    course_id = course["href"].split("/")[-1]

                    # fetch short name
                    course_name = course.find("h3", class_="courseBox--shortname")
                    short_name = course_name.text

                    # fetch full name
                    course_full_name = course.find("div", class_="courseBox--name")
                    full_name = course_full_name.text

                    # fetch basic course info
                    time_of_year = term.text.split(" ")
                    semester = time_of_year[0]
                    year = time_of_year[1]
                    num_assignments = course.find(
                        "div", class_="courseBox--assignments"
                    )
                    num_assignments = num_assignments.text

                    # create Course object with all relevant info
                    course_info = Course(
                        name=short_name,
                        full_name=full_name,
                        semester=semester,
                        year=year,
                        num_grades_published=None,  # this info is no longer available on the course homepage
                        num_assignments=num_assignments,
                    )

                    # store info for this course
                    all_courses[sectionType][course_id] = course_info

                    # find next course, or "a" tag
                    course = course.find_next_sibling("a")

    return all_courses


def get_course_members(soup: BeautifulSoup, course_id: str) -> list[Member]:
    """
    Scrape all course members from the membership page of a Gradescope course.

    Args:
        soup (BeautifulSoup): BeautifulSoup object with parsed HTML.
        course_id (str): The course ID to which the members belong.

    Returns:
        List: A list of Member objects containing all course members' info.

        For example:
        [
            Member(...),
            Member(...)
        ]
    """

    # assumed ordering
    # name, email, role, sections?, submissions, edit, remove
    # if course has sections, section column is added before number of submissions column
    headers = soup.find("table", class_="js-rosterTable").find_all("th")
    num_submissions_column = -1
    for i, h in enumerate(headers):
        if h.text.lower().startswith("submissions"):
            num_submissions_column = i
            break

    member_list = []

    # maps role id to role name
    id_to_role = {"0": "Student", "1": "Instructor", "2": "TA", "3": "Reader"}

    # find all rows with class rosterRow (each row is a member)
    roster_rows: bs4.ResultSet[bs4.element.Tag] = soup.find_all(
        "tr", class_="rosterRow"
    )

    for row in roster_rows:
        # get all table data for each row
        cells: bs4.ResultSet[bs4.element.Tag] = row.find_all("td")

        # get data from first cell
        cell = cells[0]

        data_button = cell.find("button", class_="rosterCell--editIcon")

        # fetch full name from data-cm attribute in button
        data_cm = data_button.get("data-cm")
        json_data_cm = json.loads(data_cm)  # convert to json
        full_name = json_data_cm.get("full_name")

        # fetch LMS related attributes
        first_name = json_data_cm.get("first_name")
        last_name = json_data_cm.get("last_name")
        sid = json_data_cm.get("sid")

        # fetch other attributes: email, role, and section
        # from data attributes in button
        email = data_button.get("data-email")
        role = id_to_role[data_button.get("data-role")]
        sections = data_button.get("data-sections")  # TODO: check if this is correct

        # fetch user_id, only available on 'student' accounts
        # <button name="button" type="button" class="js-rosterName" data-url="/courses/753413/gradebook.json?user_id=6515875" data-name="Gradescope API - CI Student Testing Account">Gradescope API - CI Student Testing Account</button>
        rosterName_button = cell.find("button", class_="js-rosterName")
        user_id = None
        if rosterName_button is not None:
            # data-url="/courses/753413/gradebook.json?user_id=6515875"
            data_url: str = rosterName_button.get("data-url", None)
            user_id = data_url.split("user_id=")[-1]

        # fetch number of submissions from table cell
        num_submissions = (
            0 if num_submissions_column < 0 else int(cells[num_submissions_column].text)
        )

        # create Member object with all relevant info
        member_list.append(
            Member(
                full_name=full_name,
                first_name=first_name,
                last_name=last_name,
                sid=sid,
                email=email,
                role=role,
                user_id=user_id,
                num_submissions=num_submissions,
                sections=sections,
                course_id=course_id,
            )
        )

    return member_list
