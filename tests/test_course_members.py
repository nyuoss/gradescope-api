"""Tests for roster parsing in get_course_members.

These are offline tests against fixture HTML, so they need no Gradescope credentials.
"""

from bs4 import BeautifulSoup

from gradescopeapi.classes._helpers._course_helpers import get_course_members

COURSE_ID = "753413"


def _roster(rows: str) -> BeautifulSoup:
    html = f"""
    <table class="js-rosterTable">
      <tr><th>Name</th><th>Email</th><th>Role</th><th>Sections</th>
          <th>Submissions</th><th>Edit</th><th>Remove</th></tr>
      {rows}
    </table>"""
    return BeautifulSoup(html, "html.parser")


def _row(data_cm: str, role: str, name_button: str, submissions: str) -> str:
    return f"""
    <tr class="rosterRow">
      <td>
        <button class="rosterCell--editIcon" data-cm='{data_cm}'
                data-email="member@example.edu" data-role="{role}"
                data-sections="A01"></button>
        {name_button}
      </td>
      <td>e</td><td>r</td><td>s</td><td>{submissions}</td><td>edit</td><td>remove</td>
    </tr>"""


STUDENT_CM = '{"full_name":"Test Student","first_name":"Test","last_name":"Student","sid":"912345678"}'
STAFF_CM = '{"full_name":"Test Instructor","first_name":"Test","last_name":"Instructor","sid":null}'


def test_student_row_parses_user_id_and_submissions():
    """A student row has a gradebook data-url, which is where user_id comes from."""
    name_button = (
        '<button class="js-rosterName" '
        f'data-url="/courses/{COURSE_ID}/gradebook.json?user_id=6515875"></button>'
    )
    (member,) = get_course_members(
        _roster(_row(STUDENT_CM, "0", name_button, "7")), COURSE_ID
    )

    assert member.full_name == "Test Student"
    assert member.role == "Student"
    assert member.sid == "912345678"
    assert member.user_id == "6515875"
    assert member.num_submissions == 7


def test_staff_row_without_name_button_has_no_user_id():
    """Only student accounts expose a user_id, and staff submission cells are blank."""
    (member,) = get_course_members(_roster(_row(STAFF_CM, "1", "", "")), COURSE_ID)

    assert member.full_name == "Test Instructor"
    assert member.role == "Instructor"
    assert member.user_id is None
    assert member.num_submissions == 0


def test_name_button_without_data_url_has_no_user_id():
    """A js-rosterName button need not carry a data-url; that must not raise."""
    name_button = '<button class="js-rosterName" data-name="Test Instructor"></button>'
    (member,) = get_course_members(
        _roster(_row(STAFF_CM, "2", name_button, "&mdash;")), COURSE_ID
    )

    assert member.role == "TA"
    assert member.user_id is None
    assert member.num_submissions == 0


def test_unrecognised_role_id_passes_through():
    """A role id outside the known set must not sink the roster."""
    (member,) = get_course_members(_roster(_row(STAFF_CM, "9", "", "")), COURSE_ID)

    assert member.role == "9"
    assert member.full_name == "Test Instructor"


def test_mixed_roster_returns_every_member():
    """One unparseable row used to sink the whole roster."""
    student_button = (
        '<button class="js-rosterName" '
        f'data-url="/courses/{COURSE_ID}/gradebook.json?user_id=6515875"></button>'
    )
    rows = _row(STUDENT_CM, "0", student_button, "7") + _row(STAFF_CM, "1", "", "")
    members = get_course_members(_roster(rows), COURSE_ID)

    assert [m.role for m in members] == ["Student", "Instructor"]
    assert [m.user_id for m in members] == ["6515875", None]
