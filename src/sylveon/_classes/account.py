from bs4 import BeautifulSoup
import requests

from sylveon._classes._scrape_helpers import scrape_courses_info
from sylveon._classes._assignment_helpers import (
    check_page_auth,
    get_assignments_instructor_view,
    get_assignments_student_view,
    get_submission_files,
)


class Account:

    def __init__(self, session):
        self.session = session

    def get_courses(self) -> dict:
        courses = {"instructor": {}, "student": {}}

        endpoint = "https://www.gradescope.com/account"

        # get main page
        response = self.session.get(endpoint)
        soup = BeautifulSoup(response.text, "html.parser")

        # get instructor courses
        instructor_courses = scrape_courses_info(
            self.session, soup, "Instructor Courses"
        )
        courses["instructor"] = instructor_courses

        # get student courses
        student_courses = scrape_courses_info(self.session, soup, "Student Courses")
        courses["student"] = student_courses

        return courses

    def get_assignments(self, course_id: int):
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
    ) -> List[Dict[str, List[str]]]:
        """
        Returns list of dicts mapping AWS links for all submissions to each submission id
        Note: Not recommended for use, since this makes a GET request for every submission -> very slow!
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
        submission_links = []
        for submission_id in submission_ids:  # doesn't support image submissions yet
            aws_links = get_submission_files(
                session, course_id, assignment_id, submission_id
            )
            submission_links.append({submission_id: aws_links})
        return submission_links

    def get_assignment_submission(self, student_email, course_id, assignment_id):
        # so far only accessible for teachers, not for students to get their own submission
        # get_assignment_submission(token, student_id, course_id, assignment_id)
        # -> link(s) to download file or actual files themselves
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
