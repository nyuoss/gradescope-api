from bs4 import BeautifulSoup
import requests
from typing import List, Dict

from sylveon._classes._connection import GSConnection
from sylveon._classes._scrape_helpers import scrape_courses_info
from sylveon._classes._assignment_helpers import (
    check_page_auth,
    get_assignments_instructor_view,
    get_assignments_student_view,
    get_submission_files,
)


class Account:

    def __init__(self):
        self.connection = GSConnection()

    def get_courses(self) -> dict:
        """
        Get all courses for the user, including both instructor and student courses

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
        session = self.connection.session

        # get main page
        response = session.get(endpoint)

        if response.status_code != 200:
            raise RuntimeError(
                "Failed to access account page on Gradescope. Status code: {response.status_code}"
            )

        soup = BeautifulSoup(response.text, "html.parser")

        # see if user is solely a student or instructor
        user_courses, is_instructor = scrape_courses_info(session, soup, "Your Courses")

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
        instructor_courses, _ = scrape_courses_info(session, soup, "Instructor Courses")
        courses["instructor"] = instructor_courses

        # get student courses
        student_courses, _ = scrape_courses_info(session, soup, "Student Courses")
        courses["student"] = student_courses

        return courses

    def get_assignments(self, course_id: int) -> List[Dict[str, str]]:
        """
        Get a list of detailed assignment information for a course

        Returns:
            list: A list of dictionaries, where the keys are the assignment info name and
            the values is the corresponding assignment information

            Example:
                [
                   {
                        'assignment_id': 'a_id',
                        'name': 'a_name,
                        'release_date': 'a_release_date',
                        'due_date': 'a_due_date',
                        'late_due_date': 'a_late_due_date',
                        'submissions_status': 'a_status',
                        'grade': 'a_grade',
                        'max_grade': 'a_max_grade'
                   }
                ]

        Raises:
            Exceptions:
            "One or more invalid parameters": if course_id or assignment_id is null or empty value
            "You are not authorized to access this page.": if logged in user is unable to access submissions
            "You must be logged in to access this page.": if no user is logged in
        """
        ACCOUNT_PAGE_ENDPOINT = "https://www.gradescope.com/courses"
        course_endpoint = f"{ACCOUNT_PAGE_ENDPOINT}/{course_id}"
        # check that course_id is valid (not empty)
        if not course_id:
            raise Exception("Invalid Course ID")
        session = self.connection.session
        # scrape page
        coursepage_resp = check_page_auth(session, course_endpoint)
        coursepage_soup = BeautifulSoup(coursepage_resp.text, "html.parser")

        # two different helper functions to parse assignment info
        # webpage html structure differs based on if user if instructor or student
        assignment_info_list = get_assignments_instructor_view(coursepage_soup)
        if not assignment_info_list:
            assignment_info_list = get_assignments_student_view(coursepage_soup)

        return assignment_info_list

    def get_assignment_submissions(
        self, course_id: str, assignment_id: str
    ) -> Dict[str, List[str]]:
        """
        Get a list of dicts mapping AWS links for all submissions to each submission id

        Returns:
            dict: A dictionary of submissions, where the keys are the submission ids and the values are
            a list of aws links to the submission pdf

            For example:
                {
                    'submission_id': [
                        'aws_link1.com',
                        'aws_link2.com',
                        ...
                    ],
                    ...
                }

        Raises:
            Exceptions:
                "One or more invalid parameters": if course_id or assignment_id is null or empty value
                "You are not authorized to access this page.": if logged in user is unable to access submissions
                "You must be logged in to access this page.": if no user is logged in
                "Page not Found": When link is invalid: change in url, invalid course_if or assignment id
                "Image only submissions not yet supported": assignment is image submission only, which is not yet supported

        NOTE:
        1. Image submissions not supports, need to find an endpoint to retrieve image pdfs
        2. Not recommended for use, since this makes a GET request for every submission -> very slow!
        """
        ASSIGNMENT_ENDPOINT = f"https://www.gradescope.com/courses/{course_id}/assignments/{assignment_id}"
        ASSIGNMENT_SUBMISSIONS_ENDPOINT = f"{ASSIGNMENT_ENDPOINT}/review_grades"
        if not course_id or not assignment_id:
            raise Exception("One or more invalid parameters")
        session = self.connection.session
        submissions_resp = check_page_auth(session, ASSIGNMENT_SUBMISSIONS_ENDPOINT)
        submissions_soup = BeautifulSoup(submissions_resp.text, "html.parser")
        submissions_a_tags = submissions_soup.select("td.table--primaryLink a")
        submission_ids = [
            a_tag.attrs.get("href").split("/")[-1] for a_tag in submissions_a_tags
        ]
        submission_links = {}
        for submission_id in submission_ids:  # doesn't support image submissions yet
            aws_links = get_submission_files(
                session, course_id, assignment_id, submission_id
            )
            submission_links[submission_id] = aws_links
        return submission_links

    def get_assignment_submission(
        self, student_email: str, course_id: str, assignment_id: str
    ) -> List[str]:
        """
        Get a list of aws links to pdfs of the student's most recent submission to an assignment

        Returns:
            list: A list of aws links as strings

            For example:
                [
                    'aws_link1.com',
                    'aws_link2.com',
                    ...
                ]

        Raises:
             Exceptions:
                "One or more invalid parameters": if course_id or assignment_id is null or empty value
                "You are not authorized to access this page.": if logged in user is unable to access submissions
                "You must be logged in to access this page.": if no user is logged in
                "Page not Found": When link is invalid: change in url, invalid course_if or assignment id
                "Image only submissions not yet supported": assignment is image submission only, which is not yet supported

        NOTE: so far only accessible for teachers, not for students to get their own submission
        """
        # fetch submission id
        ASSIGNMENT_ENDPOINT = f"https://www.gradescope.com/courses/{course_id}/assignments/{assignment_id}"
        ASSIGNMENT_SUBMISSIONS_ENDPOINT = f"{ASSIGNMENT_ENDPOINT}/review_grades"
        if not (student_email and course_id and assignment_id):
            raise Exception("One or more invalid parameters")
        session = self.connection.session
        submissions_resp = check_page_auth(session, ASSIGNMENT_SUBMISSIONS_ENDPOINT)
        submissions_soup = BeautifulSoup(submissions_resp.text, "html.parser")
        td_with_email = submissions_soup.find(
            "td", string=lambda s: student_email in str(s)
        )
        if td_with_email:
            # grab submission from previous td
            submission_td = td_with_email.find_previous_sibling()
            # submission_td will have an anchor element as a child if there is a submission
            a_element = submission_td.find("a")
            if a_element:
                submission_id = a_element.get("href").split("/")[-1]
            else:
                raise Exception("No submission found")
        # call get_submission_files helper function
        aws_links = get_submission_files(
            session, course_id, assignment_id, submission_id
        )
        return aws_links
