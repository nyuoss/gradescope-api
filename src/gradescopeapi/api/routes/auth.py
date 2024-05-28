from typing import Annotated
from uuid import UUID, uuid4

import gradescopeapi.classes.connection
import requests
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# TODO: Clear sessions after a certain amount of time
sessions = {}


def check_session(session_id: UUID | None):
    if session_id not in sessions or session_id is None:
        raise HTTPException(status_code=401, detail=f"Invalid session ID: {session_id}")
    return sessions[session_id]


async def get_current_session(token: Annotated[UUID, Depends(oauth2_scheme)]):
    session = sessions.get(token, None)
    if session is None:
        raise HTTPException(
            status_code=401, detail=f"Invalid session ID{token=} {session=}"
        )
    return session


@router.post("/token")
def login(credentials: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """
    Logs in the user using the provided credentials.

    Args:
        credentials (Credentials): An object containing the user's email and password.

    Returns:
        dict or str: If the login is successful, returns a dictionary with a session ID.
                    If the login fails due to invalid credentials, returns the string "Invalid credentials".
    """
    try:
        session = gradescopeapi.classes.connection.login(
            credentials.username, credentials.password
        )
        session_id = str(uuid4())
        sessions[session_id] = session

        return {"access_token": session_id, "token_type": "bearer"}
    except ValueError as e:
        return HTTPException(status_code=401, detail=f"Invalid credentials. Error {e}")


@router.get("/")
def read_root(session: Annotated[requests.Session, Depends(get_current_session)]):
    return "Successfully logged in"
