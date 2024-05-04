import requests
import json


def check_page_auth(session, endpoint):
    """
    raises Exception if user not logged in or doesn't have appropriate authorities
    Returns response if otherwise good
    """
    submissions_resp = session.get(endpoint)
    # check if page is valid, raise exception if not
    if submissions_resp.status_code == requests.codes.unauthorized:
        # check error type
        # TODO: how should we handle errors so that our API can read them?
        error_msg = [*json.loads(submissions_resp.text).values()][0]
        if error_msg == "You are not authorized to access this page.":
            raise Exception("You are not authorized to access this page.")
        elif error_msg == "You must be logged in to access this page.":
            raise Exception("You must be logged in to access this page.")
    elif submissions_resp.status_code == requests.codes.not_found:
        raise Exception("Page not Found")
    elif submissions_resp.status_code == requests.codes.ok:
        return submissions_resp


def get_assignments_instructor_view(coursepage_soup):
    assignments_list = []
    element_with_props = coursepage_soup.find(
        "div", {"data-react-class": "AssignmentsTable"}
    )
    if element_with_props:
        # Extract the value of the data-react-props attribute
        props_str = element_with_props["data-react-props"]
        # Parse the JSON data
        assignment_json = json.loads(props_str)

        # Extract information for each assignment
        for assignment in assignment_json["table_data"]:
            assignment_dict = {
                "assignment_id": assignment["url"].split("/")[-1],
                "name": assignment["title"],
                "release_date": assignment["submission_window"]["release_date"],
                "due_date": assignment["submission_window"]["due_date"],
                "late_due_date": assignment["submission_window"]["hard_due_date"],
                "submissions_status": None,
                "grade": None,
                "max_grade": str(float(assignment["total_points"])),
            }
            # Add the assignment dictionary to the list
            assignments_list.append(assignment_dict)
    return assignments_list


def get_assignments_student_view(coursepage_soup):
    # parse into list of lists: Assignments[row_elements[]]
    assignment_table = []
    for assignment_row in coursepage_soup.findAll("tr", role="row")[
        1:-1
    ]:  # Skip header row and tail row (dropzonePreview--fileNameHeader)
        row = []
        for th in assignment_row.findAll("th"):
            row.append(th)
        for td in assignment_row.findAll("td"):
            row.append(td)
        assignment_table.append(row)
    assignment_info_list = []

    # Iterate over the list of Tag objects
    for assignment in assignment_table:
        # Extract assignment ID and name
        name = assignment[0].text
        # 3 cases: 1. submitted -> href element, 2. not submitted, submittable -> button element, 3. not submitted, cant submit -> only text
        assignment_a_href = assignment[0].find("a", href=True)
        assignment_button = assignment[0].find("button", class_="js-submitAssignment")
        if assignment_a_href:
            assignment_id = assignment_a_href["href"].split("/")[4]
        elif assignment_button:
            assignment_id = assignment_button["data-assignment-id"]
        else:
            assignment_id = None

        # Extract submission status, grade, max_grade
        try:  # Points not guaranteed
            points = assignment[1].text.split(" / ")
            grade = float(points[0])
            max_grade = float(points[1])
            submission_status = "Submitted"
        except (IndexError, ValueError):
            grade = None
            max_grade = None
            submission_status = assignment[1].text

        # Extract release date, due date, and late due date
        try:  # release date, due date, and late due date not guaranteed to be available
            release_obj = assignment[2].find(class_="submissionTimeChart--releaseDate")
            release_date = release_obj.text.strip() if release_obj else None
            due_date_obj = assignment[2].find(class_="submissionTimeChart--dueDate")
            due_date = due_date_obj.text.strip() if due_date_obj else None
            late_due_date_obj = assignment[2].find(
                class_="submissionTimeChart--dueDate"
            )
            late_due_date = (
                late_due_date_obj.text.strip() if late_due_date_obj else None
            )
        except IndexError:
            release_date = due_date = late_due_date = None

        # Store the extracted information in a dictionary
        assignment_info = {
            "assignment_id": assignment_id,
            "name": name,
            "release_date": release_date,
            "due_date": due_date,
            "late_due_date": late_due_date,
            "submission_status": submission_status,
            "grade": grade,
            "max_grade": max_grade,
        }

        # Append the dictionary to the list
        assignment_info_list.append(assignment_info)
    return assignment_info_list


def get_submission_files(session, course_id, assignment_id, submission_id):
    ASSIGNMENT_ENDPOINT = (
        f"https://www.gradescope.com/courses/{course_id}/assignments/{assignment_id}"
    )

    file_info_link = f"{ASSIGNMENT_ENDPOINT}/submissions/{submission_id}.json?content=react&only_keys[]=text_files&only_keys[]=file_comments"
    file_info_resp = session.get(file_info_link)
    if file_info_resp.status_code == requests.codes.ok:
        file_info_json = json.loads(file_info_resp.text)
        if file_info_json.get("text_files"):
            aws_links = []
            for file_data in file_info_json["text_files"]:
                aws_links.append(file_data["file"]["url"])
        else:
            raise Exception("Image only submissions not yet supported")
        # TODO add support for image questions
    return aws_links
