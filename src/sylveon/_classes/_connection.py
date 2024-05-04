from bs4 import BeautifulSoup
import requests

from sylveon._classes._login_helpers import (
    get_auth_token_init_gradescope_session,
    login_set_session_cookies,
)


class GSConnection:

    def __init__(self):
        self.session = requests.Session()
        self.logged_in = False

    def login(self, email, password):
        # go to homepage to parse hidden authenticity token and to set initial "_gradescope_session" cookie
        auth_token = get_auth_token_init_gradescope_session(self.session)

        # login and set cookies in session. Result bool on whether login was success
        login_success = login_set_session_cookies(
            self.session, email, password, auth_token
        )
        if login_success:
            self.logged_in = True
        else:
            raise ValueError("Invalid credentials.")
