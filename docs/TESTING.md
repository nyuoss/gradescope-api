## Testing

Tests are performed using real Gradescope accounts to interact with the Gradescope server. As such, valid Gradescope accounts and courses are required to run the tests.

### Environment

Create an `.env` file in the root directory of the project with the following environment variables:

```
GRADESCOPE_CI_STUDENT_EMAIL
GRADESCOPE_CI_STUDENT_PASSWORD
GRADESCOPE_CI_INSTRUCTOR_EMAIL
GRADESCOPE_CI_INSTRUCTOR_PASSWORD
GRADESCOPE_CI_TA_EMAIL
GRADESCOPE_CI_TA_PASSWORD
```

For test cases to pass:

Student accounts are expected to be accounts that are **only** enrolled as students in courses. Similarly, instructor accounts are expected to **only** be instructors for courses. TA accounts are expected to be **both**. Tests can also be skipped by using the pytest decorator `@pytest.mark.skip(reason="...")`

### Running Tests Locally

Tests can be run locally using `pytest`. A PDM script is also provided to run the tests.

```bash
pytest tests
# or
pdm run test
```

### CI

Tests are run automatically using GitHub Actions.

### Running CI Locally

Install [act](https://github.com/nektos/act)

From the root of the repository, run the following command and pass in the `.env` file for Gradescope test account credentials:

```bash
act --secret-file .env
```
