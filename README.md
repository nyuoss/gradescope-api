# Gradescope API

[![PyPI version](https://img.shields.io/pypi/v/gradescopeapi)](https://pypi.org/project/gradescopeapi/) ![Test and lint workflow](https://github.com/nyuoss/gradescope-api/actions/workflows/main.yaml/badge.svg)

## Description

This *unofficial* project serves as a library for programmatically interacting with [Gradescope](https://www.gradescope.com/). The primary purpose of this project is to provide students and instructors tools for interacting with Gradescope without having to use the web interface.

For example:

- Students using this project could automatically query information about their courses and assignments to notify them of upcoming deadlines or new assignments.
- Instructors could use this project bulk edit assignment due dates or sync student extensions with an external system.

## Features

Implemented Features Include:

- Get all courses for a user
- Get a list of all assignments for a course
- Get all extensions for an assignment in a course
- Add/remove/modify extensions for an assignment in a course
- Add/remove/modify dates for an assignment in a course
- Upload submissions to assignments
- API server to interact with library without Python

## Demo

To get a feel for how the API works, we have provided a demo video of the features in-use: [link](https://youtu.be/eK9m4nVjU1A?si=6GTevv23Vym0Mu8V)

Note that we only demo interacting with the API server, you can alternatively use the Python library directly.

## Setup

To use the project you can install the package from PyPI using pip:

```bash
pip install gradescopeapi
```

For additional methods of installation, refer to the [install guide](docs/INSTALL.md)

## Usage

The project is designed to be simple and easy to use. As such, we have provided users with two different options for using this project.

### Option 1: FastAPI

If you do not want to use Python, you can host the API using the integrated FastAPI server. This way, you can interact with Gradescope using different languages by sending HTTP requests to the API server.

**Running  the API Server Locally**

To run the API server locally on your machine, open the project repository on your machine that you have cloned/forked, and:

1. Navigate to the `src.gradescopeapi.api` directory
1. Run the command: `uvicorn api:app --reload` to run the server locally
1. In a web browser, navigate to `localhost:8000/docs`, to see the auto-generated FastAPI docs

### Option 2: Python

Alternatively, you can use Python to use the library directly. We have provided some sample scripts of common tasks one might do:

```python
from gradescopeapi.classes.connection import login
from gradescopeapi.classes.courses import get_all_courses

# Login to Gradescope
session = login("email", "password")

# Fetch all courses for the user
courses = get_courses(session)
for course in courses["instructor"]:
    print(course)
for course in courses["student"]:
    print(course)

"""
Getting roster for a course
"""
course_id = "123456"
members = connection.account.get_course_users(course_id)
for member in members:
    print(member)

"""
Getting all assignments for course
"""
assignments = connection.account.get_assignments(course_id)
for assignment in assignments:
    print(assignment)
```

For more examples of features not covered here such as changing extensions, uploading files, etc., please refer to the [tests](tests/) directory.

## Testing

For information on how to run your own tests using `gradescopeapi` refer to [TESTING.md](docs/TESTING.md)

## Contributing Guidelines

Please refer to the [CONTRIBUTING.md](docs/CONTRIBUTING.md) file for more information on how to contribute to the project.

## Authors

- Susmitha Kusuma
- Berry Liu
- Margaret Jagger
- Calvin Tian
- Kevin Zheng
