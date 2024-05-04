# Example showing how to import different components of the package and use them in the main function
"""
from sylveon._classes._account import *

def main():
    acc = Account()
    acc.connection.login("email", "password")

    print(acc.get_courses())
    print(acc.get_assignment_submissions("course_id", "assignment_id"))
    print(acc.get_assignments("course_id"))
    print(acc.get_assignment_submission("student_email", "course_id", "assignment_id"))

    if __name__ == "__main__":
    main()
"""

def main():
    pass


if __name__ == "__main__":
    main()