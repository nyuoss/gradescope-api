"""Unit tests for get_course_members — no network/credentials required.

Builds a roster page from crafted HTML and checks that a roster whose
heuristic "# submissions" column is empty still parses (count defaults to 0),
and that a numeric count is read correctly.
"""
import json

from bs4 import BeautifulSoup

from gradescopeapi.classes._helpers._course_helpers import get_course_members


def _roster_html(rows):
    headers = "".join(f"<th>h{i}</th>" for i in range(6))  # -> column index 3
    body = ""
    for r in rows:
        cm = json.dumps({
            "full_name": r["full_name"],
            "first_name": r["first_name"],
            "last_name": r["last_name"],
            "sid": r["sid"],
        })
        # 8 cells; index 3 is the heuristic submissions column
        cells = [
            f'<td><button class="rosterCell--editIcon" data-cm=\'{cm}\' '
            f'data-email="{r["email"]}" data-role="{r["role"]}" data-sections="">'
            f'</button><button class="js-rosterName" '
            f'data-url="/courses/999/gradebook.json?user_id={r["user_id"]}">'
            f'{r["full_name"]}</button></td>',
            "<td>email</td>", "<td>role</td>",
            f'<td>{r["submissions"]}</td>',  # index 3
            "<td></td>", "<td></td>", "<td></td>", "<td></td>",
        ]
        body += f'<tr class="rosterRow">{"".join(cells)}</tr>'
    return f'<table class="js-rosterTable"><thead>{headers}</thead><tbody>{body}</tbody></table>'


def test_empty_submissions_cell_does_not_crash():
    rows = [{
        "full_name": "Ada Lovelace", "first_name": "Ada", "last_name": "Lovelace",
        "sid": "123", "email": "ada@example.edu", "role": "0",
        "user_id": "555", "submissions": "",  # empty submissions cell
    }]
    soup = BeautifulSoup(_roster_html(rows), "html.parser")
    members = get_course_members(soup, "999")
    assert len(members) == 1
    m = members[0]
    assert m.email == "ada@example.edu"
    assert m.role == "Student"
    assert m.full_name == "Ada Lovelace"
    assert m.user_id == "555"
    assert m.num_submissions == 0


def test_numeric_submissions_cell_is_parsed():
    rows = [{
        "full_name": "Alan Turing", "first_name": "Alan", "last_name": "Turing",
        "sid": "9", "email": "alan@example.edu", "role": "2",
        "user_id": "777", "submissions": "5",
    }]
    soup = BeautifulSoup(_roster_html(rows), "html.parser")
    members = get_course_members(soup, "999")
    assert members[0].num_submissions == 5
    assert members[0].role == "TA"
