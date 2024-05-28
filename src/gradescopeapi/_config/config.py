"""config.py
Configuration file for FastAPI. Specifies the specific objects and data models used in our api
"""

import io
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserSession(BaseModel):
    user_email: str
    session_token: str


class LoginRequestModel(BaseModel):
    email: str
    password: str


class CourseID(BaseModel):
    course_id: str


class AssignmentID(BaseModel):
    course_id: str
    assignment_id: str


class StudentSubmission(BaseModel):
    student_email: str
    course_id: str
    assignment_id: str


class ExtensionData(BaseModel):
    course_id: str
    assignment_id: str


class UpdateExtensionData(BaseModel):
    course_id: str
    assignment_id: str
    user_id: str
    release_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    late_due_date: Optional[datetime] = None


class AssignmentDates(BaseModel):
    course_id: str
    assignment_id: str
    release_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    late_due_date: Optional[datetime] = None


class FileUploadModel(BaseModel, arbitrary_types_allowed=True):
    file: io.TextIOWrapper


class AssignmentUpload(BaseModel):
    course_id: str
    assignment_id: str
    leaderboard_name: Optional[str] = None
