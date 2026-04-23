import requests

from gradescopeapi import DEFAULT_GRADESCOPE_BASE_URL
from gradescopeapi.classes._helpers._login_helpers import (
    get_auth_token_init_gradescope_session,
    login_set_session_cookies,
    logout_session,
)
from gradescopeapi.classes.account import Account


class GSConnection:
    def __init__(self, gradescope_base_url: str = DEFAULT_GRADESCOPE_BASE_URL):
        self.session = requests.Session()
        self.gradescope_base_url = gradescope_base_url
        self.logged_in = False
        self.account = None

    def login(self, email, password):
        # go to homepage to parse hidden authenticity token and to set initial "_gradescope_session" cookie
        auth_token = get_auth_token_init_gradescope_session(
            self.session, self.gradescope_base_url
        )

        # login and set cookies in session. Result bool on whether login was success
        login_success = login_set_session_cookies(
            self.session, email, password, auth_token, self.gradescope_base_url
        )
        if login_success:
            self.logged_in = True
            self.account = Account(self.session, self.gradescope_base_url)
        else:
            raise ValueError("Invalid credentials.")

    def logout(self):
        """Call Gradescope /logout to terminate the session and clear local state."""
        logout_session(self.session, self.gradescope_base_url)
        self.session = requests.Session()
        self.logged_in = False
        self.account = None
