import os
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def _set_test_env():
    # Ensure tests use a separate sqlite file and name
    os.environ["DATABASE_PUBLIC_URL"] = "sqlite:///./test.db"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    os.environ["APP_NAME"] = "boilerplate-fastapi-test"

@pytest.fixture()
def client():
    # Import AFTER env vars are set
    from main import app
    return TestClient(app)