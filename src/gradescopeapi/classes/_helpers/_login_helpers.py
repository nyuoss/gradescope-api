import requests
from bs4 import BeautifulSoup


def get_auth_token_init_gradescope_session(session: requests.Session) -> str:
    """
    Go to homepage to parse hidden authenticity token and to set initial "_gradescope_session" cookie
    """
    GS_LANDING_ENDPOINT = "https://gradescope.com"

    # go to homepage and set initial "_gradescope_session" cookie
    homepage_resp = session.get(GS_LANDING_ENDPOINT)
    homepage_soup = BeautifulSoup(homepage_resp.text, "html.parser")

    # Find the authenticity token using CSS selectors
    auth_token = homepage_soup.select_one(
        'form[action="/login"] input[name="authenticity_token"]'
    )["value"]
    return auth_token


def login_set_session_cookies(
    session: requests.Session, email: str, password: str, auth_token: str
) -> bool:
    GS_LOGIN_ENDPOINT = "https://www.gradescope.com/login"

    # populate params for post request to login endpoint
    login_data = {
        "utf8": "✓",
        "session[email]": email,
        "session[password]": password,
        "session[remember_me]": 0,
        "commit": "Log In",
        "session[remember_me_sso]": 0,
        "authenticity_token": auth_token,
    }

    # login -> Send post request to login endpoint. Sets cookies
    login_resp = session.post(GS_LOGIN_ENDPOINT, params=login_data)

    # success marked with cookies set and a 302 redirect to the accounts page
    if (
        # login_resp.history returns a list of redirects that occurred while handling a request
        len(login_resp.history) != 0
        and login_resp.history[0].status_code == requests.codes.found
    ):
        # update headers with csrf token
        # grab x-csrf-token
        soup = BeautifulSoup(login_resp.text, "html.parser")
        csrf_token = soup.select_one('meta[name="csrf-token"]')["content"]

        # update session headers
        session.cookies.update(login_resp.cookies)
        session.headers.update({"X-CSRF-Token": csrf_token})
        return True
    return False
