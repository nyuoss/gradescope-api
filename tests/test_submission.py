from custom_skips import instructor
from gradescopeapi.classes._data_model import Assignment
from gradescopeapi.classes.assignments import get_assignments


@instructor
def test_get_assignments(create_session):
    """Test fetching assignments with valid course ID."""
    session = create_session("instructor")
    course_id = "753413"
    assignments = get_assignments(session, course_id)
    assert isinstance(assignments, list), "Should return a list of assignments"
    assert all(
        isinstance(a, Assignment) for a in assignments
    ), "All items should be Assignment instances"


# def test_get_assignment_submissions(create_session):
#     """Test fetching assignment submissions with valid course and assignment IDs."""
#     session = create_session("instructor")
#     course_id = "753413"
#     assignment_id = "4436170"
#     expected_submissions = {"submission_id": ["aws_link1.com", "aws_link2.com"]}

#     with patch(
#         "gradescopeapi.classes.account.Account.get_assignment_submissions",
#         return_value=expected_submissions,
#     ):
#         submissions = account.get_assignment_submissions(course_id, assignment_id)
#         assert isinstance(
#             submissions, dict
#         ), "Should return a dictionary of submissions"
#         assert (
#             "submission_id" in submissions
#         ), "Dictionary should contain submission IDs"
#         assert all(
#             isinstance(links, list) for links in submissions.values()
#         ), "Each submission ID should map to a list of links"


# def test_get_assignment_submission_valid():
#     """Test fetching a specific assignment submission."""
#     account = get_account("instructor")
#     student_email = GRADESCOPE_CI_STUDENT_EMAIL
#     course_id = "753413"
#     assignment_id = "4436170"
#     expected_links = ["aws_link1.com", "aws_link2.com"]

#     with patch(
#         "gradescopeapi.classes.account.Account.get_assignment_submission",
#         return_value=expected_links,
#     ):
#         submission = account.get_assignment_submission(
#             student_email, course_id, assignment_id
#         )
#         assert isinstance(submission, list), "Should return a list of aws links"
#         assert len(submission) == 2, "List should contain aws links"


# def test_get_assignment_submission_no_submission_found():
#     """Test case when no submission is found for a given student."""
#     account = get_account("instructor")
#     student_email = GRADESCOPE_CI_INSTRUCTOR_EMAIL
#     course_id = "753413"
#     assignment_id = "101010"

#     with patch(
#         "gradescopeapi.classes.account.Account.get_assignment_submission",
#         side_effect=Exception("No submission found"),
#     ):
#         with pytest.raises(Exception, match="No submission found"):
#             account.get_assignment_submission(student_email, course_id, assignment_id)
