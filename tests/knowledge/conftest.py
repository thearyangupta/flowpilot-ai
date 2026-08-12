import pytest


@pytest.fixture(scope="session", autouse=True)
def prepare_test_database():
    pass