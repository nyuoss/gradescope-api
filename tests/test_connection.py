import requests
import os
from dotenv import load_dotenv

from sylveon._classes._login_helpers import (
    login_set_session_cookies,
    get_auth_token_init_gradescope_session,
)

# load .env file
load_dotenv()

GRADESCOPE_CI_STUDENT_EMAIL = os.getenv("GRADESCOPE_CI_STUDENT_EMAIL")
GRADESCOPE_CI_STUDENT_PASSWORD = os.getenv("GRADESCOPE_CI_STUDENT_PASSWORD")


def test_get_auth_token_init_gradescope_session():
    # create test session
    test_session = requests.Session()

    # call the function
    auth_token = get_auth_token_init_gradescope_session(test_session)

    # check cookies
    cookies = requests.utils.dict_from_cookiejar(test_session.cookies)
    cookie_check = set(cookies.keys()) == {"_gradescope_session"}
    assert auth_token and cookie_check


def test_login_set_session_cookies_correct_creds():
    # create test session
    test_session = requests.Session()

    # assuming test_get_auth_token_init_gradescope_session works
    auth_token = get_auth_token_init_gradescope_session(test_session)

    login_check = login_set_session_cookies(
        test_session,
        GRADESCOPE_CI_STUDENT_EMAIL,
        GRADESCOPE_CI_STUDENT_PASSWORD,
        auth_token,
    )

    # check cookies
    cookies = requests.utils.dict_from_cookiejar(test_session.cookies)
    cookie_check = set(cookies.keys()).issuperset(
        {
            "_gradescope_session",
            "signed_token",
            "remember_me",
        }
    )
    assert login_check and cookie_check


def test_login_set_session_cookies_incorrect_creds():
    FALSE_PASSWORD = "notthepassword"

    # create test session
    test_session = requests.Session()

    # assuming test_get_auth_token_init_gradescope_session works
    auth_token = get_auth_token_init_gradescope_session(test_session)

    login_check = not login_set_session_cookies(
        test_session, GRADESCOPE_CI_STUDENT_EMAIL, FALSE_PASSWORD, auth_token
    )

    # check cookies
    cookies = requests.utils.dict_from_cookiejar(test_session.cookies)
    cookie_check = set(cookies.keys()).issuperset({"_gradescope_session"})

    assert login_check and cookie_check