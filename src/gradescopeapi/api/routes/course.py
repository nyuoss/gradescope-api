from typing import Annotated

import gradescopeapi.classes.assignments
import gradescopeapi.classes.courses
from fastapi import APIRouter, Depends, HTTPException
from gradescopeapi.api.routes.auth import get_current_session

router = APIRouter(
    prefix="/courses",
    tags=["courses"],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
def get_courses(session: Annotated[str, Depends(get_current_session)]):
    return gradescopeapi.classes.courses.get_courses(session)


@router.get("/{course_id}")
def get_course(course_id: str, session: Annotated[str, Depends(get_current_session)]):
    return HTTPException(status_code=404, detail="Not implemented")


@router.get("/{course_id}/members")
def get_course_members(
    course_id: str, session: Annotated[str, Depends(get_current_session)]
):
    return gradescopeapi.classes.courses.get_course_users(session, course_id)


@router.get("/{course_id}/assignments")
def get_all_assignments(
    course_id: str, session: Annotated[str, Depends(get_current_session)]
):
    return gradescopeapi.classes.assignments.get_assignments(session, course_id)


@router.get("/{course_id}/assignments/{assignment_id}")
def get_single_assignment(
    course_id: str,
    assignment_id: str,
    session: Annotated[str, Depends(get_current_session)],
):
    raise HTTPException(status_code=404, detail="Not implemented")


@router.get("/{course_id}/assignments/{assignment_id}/submissions")
def get_assingment_all_submissions(
    course_id: str,
    assignment_id: str,
    session: Annotated[str, Depends(get_current_session)],
):
    return gradescopeapi.classes.assignments.get_assignment_submissions(
        session, course_id, assignment_id
    )


@router.get("/{course_id}/assignments/{assignment_id}/submissions/{user_id}")
def get_assignment_single_submission(course_id: str, assignment_id: str, user_id: str):
    raise HTTPException(status_code=404, detail="Not implemented")
