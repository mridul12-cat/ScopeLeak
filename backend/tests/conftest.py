import os
import pytest

# Ensure tests use an isolated test database, NEVER touching the production/demo scopeleak.db
TEST_DB_PATH = os.path.abspath("./test_isolated_suite.db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["ENVIRONMENT"] = "testing"

from backend.app.database import engine, Base, init_db

@pytest.fixture(scope="session", autouse=True)
def setup_isolated_test_database():
    """Session fixture providing an isolated SQLite database for all automated tests."""
    init_db()
    yield
    # Dispose connection pool before removing file
    engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass
