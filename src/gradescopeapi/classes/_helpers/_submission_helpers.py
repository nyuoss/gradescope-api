"""Parse the review_grades submissions table into structured data."""

from datetime import datetime
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

_UTC = ZoneInfo("UTC")

# <time datetime="2025-09-22 08:00:55 -0400"> - offset is in the string.
_DATETIME_FMT = "%Y-%m-%d %H:%M:%S %z"


def _parse_submitted_at(cell) -> datetime | None:
    """Parse submission time from <time datetime="..."> (offset in string). Return UTC or None."""
    if cell is None:
        return None
    time_tag = getattr(cell, "find", lambda *a, **k: None)("time")
    if time_tag is None:
        return None
    dt_attr = time_tag.get("datetime")
    if not dt_attr:
        return None
    try:
        dt = datetime.strptime(dt_attr.strip(), _DATETIME_FMT)
        return dt.astimezone(_UTC)
    except ValueError:
        return None


def _parse_sections_cell(cell) -> list[str]:
    """
    Sections from DOM: .sectionsColumnCell--sectionSpan (one section per span).
    If no spans, return [].
    """
    if cell is None:
        return []
    spans = getattr(cell, "select", lambda *a: [])(".sectionsColumnCell--sectionSpan")
    if not spans:
        return []
    return [s.get_text(strip=True) for s in spans if s.get_text(strip=True)]


def _has_icon(cell, class_substring: str) -> bool:
    """True if cell contains an <i> whose class list includes class_substring (e.g. 'fa-check')."""
    if cell is None:
        return False
    def _class_contains(c):
        if not c:
            return False
        return class_substring in (c if isinstance(c, list) else c.split())
    icon = cell.find("i", class_=_class_contains)
    return icon is not None


def _is_graded(cell) -> bool:
    """True if cell contains i.fa-check (Submission is graded). No fa-* for false in our HTML samples."""
    return _has_icon(cell, "fa-check")


def _is_viewed(cell) -> bool:
    """True if cell contains i.fa-eye (Submission has been viewed). False = no fa-eye (e.g. statusIcon-inactive + 'Submission has not been viewed.')."""
    return _has_icon(cell, "fa-eye")


def _is_canvas_linked(cell) -> bool:
    """True if cell contains i.fa-link (Linked to Canvas), False if i.fa-unlink (No Canvas link)."""
    if cell is None:
        return False
    if _has_icon(cell, "fa-unlink"):
        return False
    return _has_icon(cell, "fa-link")


def _is_late(cell) -> bool:
    """True if the time cell contains the late badge."""
    if cell is None:
        return False
    return cell.select_one(".lateSubmissionBadge") is not None


def _score_from_cell(cell) -> float | None:
    """Parse score cell text as float; None if missing or not a number."""
    if cell is None:
        return None
    text = getattr(cell, "get_text", lambda *a: "")(" ", strip=True)
    if not text or "doesn't have a submission" in text.lower():
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _row_cells_to_dict(tr, base_url: str) -> dict | None:
    """
    Infer each field from the row's cells using DOM structure (tags, classes, attributes).
    Returns a parsed row dict, or None if the row has no cells.
    """
    cells = tr.find_all("td")
    if not cells:
        return None

    # Submission link and student_name: first <a> under the first td.table--primaryLink (First Last column; second is Last, First)
    primary_cells = tr.find_all("td", class_=lambda c: c and "table--primaryLink" in (c if isinstance(c, list) else c.split()))
    first_primary = primary_cells[0] if primary_cells else None
    link = first_primary.find("a", href=True) if first_primary else None
    submission_url: str | None = None
    if link and "/submissions/" in link.get("href", ""):
        href = link.get("href", "")
        submission_url = href if href.startswith("http") else urljoin(base_url, href)
    # Name: link text when we have a submission; else first td.table--primaryLink; when there's no submission that cell has no class, so fall back to first cell
    student_name = (
        link.get_text() if (link and submission_url)
        else (first_primary.get_text() if first_primary else (cells[0].get_text() if cells else None))
    )

    # Email: <td> containing <a href="mailto:...">
    mailto = tr.find("a", href=lambda h: h and h.startswith("mailto:"))
    email_cell = mailto.find_parent("td") if mailto else None

    # Sections: <td> containing .sectionsColumnCell
    sections_cell = next((td for td in cells if td.select_one(".sectionsColumnCell")), None)
    if sections_cell is None:
        # Fallback: cell with comma+slash (section-like content)
        for td in cells:
            text = td.get_text(" ", strip=True)
            if "," in text and "/" in text:
                sections_cell = td
                break

    # Time: <td> containing <time>
    time_cell = next((td for td in cells if td.find("time")), None)

    # Score, graded, viewed, canvas: find by DOM/content
    score_cell = None
    graded_cell = None
    viewed_cell = None
    canvas_cell = None
    for td in cells:
        text = td.get_text(" ", strip=True)
        if _is_graded(td):
            graded_cell = td
        elif _is_viewed(td) or "not been viewed" in text.lower():
            viewed_cell = td
        elif _is_canvas_linked(td):
            canvas_cell = td
        elif _score_from_cell(td) is not None or "doesn't have a submission" in text.lower():
            score_cell = td

    return {
        "submission_url": submission_url,
        "student_name": student_name,
        "email": email_cell.get_text() if email_cell else None,
        "sections": _parse_sections_cell(sections_cell),
        "score": _score_from_cell(score_cell) if submission_url and score_cell else None,
        "graded": _is_graded(graded_cell) if submission_url else False,
        "viewed": _is_viewed(viewed_cell) if submission_url else False,
        "canvas_linked": _is_canvas_linked(canvas_cell) if submission_url else False,
        "submitted_at": _parse_submitted_at(time_cell) if submission_url else None,
        "late": _is_late(time_cell) if submission_url else False,
    }


def parse_submissions_table(
    soup: BeautifulSoup,
    base_url: str,
    course_id: str,
    assignment_id: str,
) -> list[dict]:
    """
    Parse the review_grades submissions table into a list of parsed row dicts.

    Each row is interpreted by inspecting cell content/structure (no header lookup).
    Each dict: submission_url (str | None; null = no submission), student_name, email, sections,
    score (float | None), graded, viewed, canvas_linked (bool), submitted_at (datetime | None), late (bool).
    """
    table = soup.find("table", id="submissions-table") or soup.find("table")
    if not table:
        return []

    tbody = table.find("tbody")
    trs = tbody.find_all("tr") if tbody else table.find_all("tr")[1:]
    rows_data: list[dict] = []
    for tr in trs:
        row = _row_cells_to_dict(tr, base_url)
        if row is not None and row["student_name"] and row["email"]:
            rows_data.append(row)

    return rows_data
