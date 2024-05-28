import json

from bs4 import BeautifulSoup
from gradescopeapi.classes._data_model import Course, Member


def get_courses_info(
    soup: BeautifulSoup, user_type: str
) -> tuple[dict[str, Course], bool]:
    """
    Scrape all course info from the main page of Gradescope.

    Args:
        soup (BeautifulSoup): BeautifulSoup object with parsed HTML.
        user_type (str): The user type to scrape courses for (Instructor or Student courses).

    Returns:
        tuple:
            dict: A dictionary mapping course IDs to Course objects containing all course info.
            bool: Flag indicating if the user is an instructor or not.

        For example:
        {
            "123456": Course(
                name="CS 1134",
                full_name="Data Structures and Algorithms",
                semester="Fall",
                year="2021",
                num_grades_published="0",
                num_assignments="5"
            )
        }
    """

    # initalize dictionary to store all courses
    all_courses = {}

    # find heading for defined user_type's courses
    courses = soup.find("h1", class_="pageHeading", string=user_type)

    # if no courses found, return empty dictionary
    if courses is None:
        return all_courses, False

    # use button to check if user is an instructor or not
    button = courses.find_next("button")
    if button.text == " Create a new course":  # intentional space before Create
        is_instructor = True
    else:
        is_instructor = False

    # find next div with class courseList
    course_list = courses.find_next("div", class_="courseList")

    for term in course_list.find_all("div", class_="courseList--term"):
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

            # fetch semester and year
            time_of_year = term.text.split(" ")
            semester = time_of_year[0]
            year = time_of_year[1]

            # fetch number of grades published and number of assignments
            if user_type == "Instructor Courses" or is_instructor:
                # find number of grades published and number of assignments
                # if they exist
                num_grades_published = course.find(
                    "div", class_="courseBox--noGradesPublised"
                )
                if num_grades_published is not None:
                    num_grades_published = num_grades_published.text

                num_assignments = course.find(
                    "div",
                    class_="courseBox--assignments courseBox--assignments-unpublished",
                )
                if num_assignments is not None:
                    num_assignments = num_assignments.text

            else:
                # students do not have number of grades published, so set to None
                num_grades_published = None
                num_assignments = course.find("div", class_="courseBox--assignments")
                num_assignments = num_assignments.text

            # create Course object with all relevant info
            course_info = Course(
                name=short_name,
                full_name=full_name,
                semester=semester,
                year=year,
                num_grades_published=num_grades_published,
                num_assignments=num_assignments,
            )

            # store info for this course
            all_courses[course_id] = course_info

            # find next course, or "a" tag
            course = course.find_next_sibling("a")

    return all_courses, is_instructor


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

    member_list = []

    # maps role id to role name
    id_to_role = {"0": "Student", "1": "Instructor", "2": "TA", "3": "Reader"}

    # find all rows with class rosterRow (each row is a member)
    roster_rows = soup.find_all("tr", class_="rosterRow")

    for row in roster_rows:
        # get all table data for each row
        cells = row.find_all("td")

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

        # fetch other attributes: email, id, role, and section
        # from data attributes in button
        email = data_button.get("data-email")
        id = data_button.get("data-id")
        role = id_to_role[data_button.get("data-role")]
        sections = data_button.get("data-sections")  # TODO: check if this is correct

        # fetch number of submissions from 4th cell
        num_submissions = int(cells[3].text)

        # create Member object with all relevant info
        member = Member(
            full_name=full_name,
            first_name=first_name,
            last_name=last_name,
            sid=sid,
            email=email,
            role=role,
            id=id,
            num_submissions=num_submissions,
            sections=sections,
            course_id=course_id,
        )

        member_list.append(member)

    return member_list
