import pytest


@pytest.fixture(scope="session", autouse=True)
def prepare_test_database():
    """UI unit tests do not require the application test database."""
    pass
