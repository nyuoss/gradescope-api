import requests

from gradescopeapi.classes._helpers._login_helpers import (
    get_auth_token_init_gradescope_session,
    login_set_session_cookies,
)


def login(email: str, password: str) -> requests.Session:
    """Logs into Gradescope and returns the session.

    Args:
        email (str): The email of the user.
        password (str): The password of the user.

    Returns:
        requests.Session: The session object.

    Raises:
        ValueError: If the login credentials are invalid.
    """
    session = requests.Session()

    # go to homepage to parse hidden authenticity token and to set initial "_gradescope_session" cookie
    auth_token = get_auth_token_init_gradescope_session(session)

    # login and set cookies in session. Result bool on whether login was success
    login_success = login_set_session_cookies(session, email, password, auth_token)
    if not login_success:
        raise ValueError("Invalid credentials.")

    return session
