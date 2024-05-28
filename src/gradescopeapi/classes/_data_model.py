import datetime
from dataclasses import dataclass


@dataclass
class Course:
    name: str
    full_name: str
    semester: str
    year: str
    num_grades_published: str
    num_assignments: str


@dataclass
class Assignment:
    assignment_id: str
    name: str
    release_date: datetime.datetime
    due_date: datetime.datetime
    late_due_date: datetime.datetime | None
    submissions_status: str | None
    grade: str | None  # change to int?
    max_grade: str | None


@dataclass
class Member:
    full_name: str
    first_name: str
    last_name: str
    sid: str
    email: str
    role: str
    id: str
    num_submissions: int
    sections: str
    course_id: str
