"""config.py
Configuration file for FastAPI. Specifies the specific objects and data models used in our api
"""

import enum
import io
from datetime import datetime

from pydantic import BaseModel, field_validator, model_validator


class SubmissionType(enum.Enum):
    """Gradescope submission type.

    VARIABLE corresponds to image-based submissions (student uploads images).
    FIXED corresponds to PDF template submissions (fixed-format PDF).
    """

    VARIABLE = "image"
    FIXED = "pdf"


class WhenToCreateRubric(enum.Enum):
    """When the rubric should be made available on Gradescope."""

    WHILE_GRADING = "while_grading"
    BEFORE_SUBMISSIONS = "before_submissions"


class RubricLockingSetting(enum.Enum):
    """Who can edit the rubric on Gradescope."""

    ALL_EDIT = "all_edit"
    INSTRUCTOR_EDIT = "instructor_edit"
    NO_EDIT = "no_edit"


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
    release_date: datetime | None = None
    due_date: datetime | None = None
    late_due_date: datetime | None = None


class AssignmentDates(BaseModel):
    course_id: str
    assignment_id: str
    release_date: datetime | None = None
    due_date: datetime | None = None
    late_due_date: datetime | None = None


class FileUploadModel(BaseModel, arbitrary_types_allowed=True):
    file: io.TextIOWrapper


class AssignmentUpload(BaseModel):
    course_id: str
    assignment_id: str
    leaderboard_name: str | None = None


class StudentSubmissionSettings(BaseModel):
    release_date: datetime
    due_date: datetime
    allow_late_submissions: bool
    late_due_date: datetime | None = None
    time_limit_in_minutes: int | None = None
    submission_type: SubmissionType
    group_submission: bool = False
    group_size: int | None = None
    template_visible_to_students: bool = False

    @model_validator(mode="after")
    def _validate_dates_and_tz(self):
        if self.due_date < self.release_date:
            raise ValueError("due_date must be after release_date")
        if self.late_due_date is not None:
            if not self.allow_late_submissions:
                raise ValueError(
                    "late_due_date can only be set when allow_late_submissions is True"
                )
            if self.late_due_date <= self.due_date:
                raise ValueError("late_due_date must be after due_date")
        return self

    @field_validator("group_size")
    @classmethod
    def _validate_group_size(cls, v):
        if v is not None and v < 2:
            raise ValueError("group_size must be at least 2")
        return v

    @field_validator("time_limit_in_minutes")
    @classmethod
    def _validate_time_limit(cls, v):
        if v is not None and v <= 0:
            raise ValueError("time_limit_in_minutes must be positive")
        return v


class CreateAssignment(BaseModel):
    course_id: str
    title: str
    submissions_anonymized: bool = False
    student_submission: bool = False
    student_submission_settings: StudentSubmissionSettings | None = None
    when_to_create_rubric: WhenToCreateRubric = WhenToCreateRubric.WHILE_GRADING
    rubric_locking_setting: RubricLockingSetting = RubricLockingSetting.ALL_EDIT

    @model_validator(mode="after")
    def _validate_student_submission_settings(self):
        if self.student_submission_settings is not None and not self.student_submission:
            raise ValueError(
                "student_submission_settings can only be set when student_submission is True"
            )
        if self.student_submission and self.student_submission_settings is None:
            raise ValueError(
                "student_submission is True but no config is passed in "
                "(student_submission_settings is required)"
            )
        return self
