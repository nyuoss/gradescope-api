import json
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup

DEFAULT_POLL_INTERVAL = 1


def get_submission_download_url(
    base_url: str,
    course_id: str,
    assignment_id: str,
    submission_id: str,
) -> str:
    return f"{base_url}/courses/{course_id}/assignments/{assignment_id}/submissions/{submission_id}.zip"


def _review_grades_url(base_url: str, course_id: str, assignment_id: str) -> str:
    return f"{base_url}/courses/{course_id}/assignments/{assignment_id}/review_grades"


def _find_submission_zip_link_on_assignment_page(
    soup: BeautifulSoup, base_url: str
) -> str | None:
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if "/submissions/" in href and href.endswith(".zip"):
            return href if href.startswith("http") else urljoin(base_url, href)
    return None


def get_latest_submission_download_url(
    session,
    base_url: str,
    course_id: str,
    assignment_id: str,
) -> str:
    url = f"{base_url}/courses/{course_id}/assignments/{assignment_id}"
    r = session.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    link = _find_submission_zip_link_on_assignment_page(soup, base_url)
    if link:
        return link
    raise ValueError("No 'Download Submission' link found on the assignment page.")


def _find_generated_file_link(soup: BeautifulSoup, base_url: str) -> str | None:
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if "/generated_files/" in href and href.endswith(".zip"):
            return href if href.startswith("http") else urljoin(base_url, href)
    return None


def _poll_generated_file_until_ready(
    session,
    base_url: str,
    course_id: str,
    file_id: int,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    poll_max: int | None = None,
) -> str:
    status_url = f"{base_url}/courses/{course_id}/generated_files/{file_id}.json"
    headers = {"Accept": "application/json", "X-Requested-With": "XMLHttpRequest"}
    attempt = 0
    while poll_max is None or attempt < poll_max:
        attempt += 1
        r = session.get(status_url, headers=headers)
        r.raise_for_status()
        try:
            data = r.json()
        except json.JSONDecodeError:
            raise ValueError(f"Unexpected response from {status_url}") from None
        status = (data.get("status") or "").strip()
        if status == "completed":
            return f"{base_url}/courses/{course_id}/generated_files/{file_id}.zip"
        if status not in ("processing", "unprocessed"):
            raise ValueError(f"Export status: {status}")
        time.sleep(poll_interval)
    raise TimeoutError("Export did not complete in time.")


def _get_export_csrf_and_headers(soup: BeautifulSoup) -> tuple[str | None, dict]:
    """Return (csrf_token or None, headers) for the export request."""
    csrf_meta = soup.find("meta", {"name": "csrf-token"})
    token = (csrf_meta.get("content") if csrf_meta else None) or (
        (soup.find("input", {"name": "authenticity_token"}) or {}).get("value")
    )
    headers = {
        "Accept": "application/json, text/html",
        "X-Requested-With": "XMLHttpRequest",
    }
    if token:
        headers["X-CSRF-Token"] = token
    return (token, headers)


def _get_file_id_from_export_response(r) -> int | None:
    """Parse export response; return generated file id if present."""
    content_type = (r.headers.get("content-type") or "").strip().lower()
    if "application/json" not in content_type:
        return None
    try:
        data = r.json()
        file_id = data.get("id") or data.get("generated_file_id")
        if file_id is not None:
            return int(file_id)
    except (json.JSONDecodeError, ValueError, AttributeError, TypeError):
        pass
    return None


def get_export_all_download_url(
    session,
    base_url: str,
    course_id: str,
    assignment_id: str,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    poll_max: int | None = None,
) -> str:
    """Return the URL of the assignment export submissions zip file. This is not an idempotent operation.

    If a zip is already available (e.g. from a prior export), returns its URL
    immediately. Otherwise triggers export, waits until the file exists on the
    server, then returns that URL. Later calls may be faster or slower depending
    on whether the file is still available.
    """
    submissions_url = _review_grades_url(base_url, course_id, assignment_id)
    r = session.get(submissions_url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    download_link = _find_generated_file_link(soup, base_url)
    if download_link:
        return download_link

    export_url = f"{base_url}/courses/{course_id}/assignments/{assignment_id}/export"
    token, headers = _get_export_csrf_and_headers(soup)
    if token:
        r = session.post(
            export_url,
            data={"authenticity_token": token},
            headers=headers,
            allow_redirects=False,
        )
    else:
        r = session.get(export_url, headers=headers, allow_redirects=False)
    r.raise_for_status()

    # TODO: Before release, confirm whether export ever returns zip in response body.
    # No logs or HAR evidence so far. Based on test results: uncomment zip-in-body block
    # (restore return (None, r), return type tuple, branching in download_all_submissions)
    # or remove it; and refine the ValueError message below if we see a specific failure shape.
    # if r.headers.get("content-type", "").strip().startswith("application/zip"):
    #     return (None, r)

    file_id = _get_file_id_from_export_response(r)
    if file_id is not None:
        return _poll_generated_file_until_ready(
            session,
            base_url,
            course_id,
            file_id,
            poll_interval=poll_interval,
            poll_max=poll_max,
        )

    raise ValueError("Export request did not return a usable response.")
