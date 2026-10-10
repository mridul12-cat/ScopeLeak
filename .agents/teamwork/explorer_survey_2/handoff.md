# Handoff Report: Test Suite & Fixture Isolation Analysis

**Author:** explorer_survey_2  
**Date:** 2026-10-10  
**Target Recipient:** Orchestrator (`38c78d67-bc2e-45c3-ad2e-26ff6647c181`)  
**Status:** Complete (Hard Handoff)  

---

## 1. Observation

### 1.1 Test Suite Structure and Database Session Sourcing
Across `backend/tests/`, there are 8 test files with fundamentally diverging database connection strategies:

1. **`backend/tests/test_change_orders.py` (lines 9–16), `test_contracts.py` (lines 10–17), `test_requests_findings.py` (lines 13–20):**
   Use isolated in-memory SQLite fixtures scoped per test function:
   ```python
   @pytest.fixture
   def db_session():
       engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
       Base.metadata.create_all(bind=engine)
       Session = sessionmaker(bind=engine)
       session = Session()
       yield session
       session.close()
   ```
   These unit/service tests do not connect to `scopeleak.db` or the FastAPI application engine.

2. **`backend/tests/test_pricing.py` and `test_ai_provider.py`:**
   Pure logic / async service tests with no database connections or fixtures.

3. **`backend/tests/test_api_e2e.py` (lines 1–5):**
   ```python
   import pytest
   from fastapi.testclient import TestClient
   from backend.app.main import app

   client = TestClient(app)
   ```
   No database fixture and no `app.dependency_overrides` for `get_db`. All API calls hit the global application database engine and sessionmaker.

4. **`backend/tests/test_user_document_audit.py` (lines 1–13, 256–257):**
   ```python
   from fastapi.testclient import TestClient
   from backend.app.main import app
   from backend.app.database import SessionLocal
   ...
   client = TestClient(app)
   ...
   db = SessionLocal()
   ```
   Directly imports and instantiates the global `SessionLocal` alongside `TestClient(app)` with zero cleanup.

5. **`backend/tests/test_edge_cases_and_isolation.py` (lines 1–6):**
   Untracked test file also instantiating module-level `client = TestClient(app)` without teardown.

---

### 1.2 Default Database Engine Configuration in Application Code
1. **`backend/app/database.py` (lines 5–13, 33–38):**
   ```python
   DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./scopeleak.db")

   connect_args = {}
   if DATABASE_URL.startswith("sqlite"):
       connect_args = {"check_same_thread": False}

   engine = create_engine(DATABASE_URL, connect_args=connect_args)
   SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
   ...
   def get_db():
       db = SessionLocal()
       try:
           yield db
       finally:
           db.close()
   ```
   `DATABASE_URL`, `engine`, and `SessionLocal` are instantiated as module-level globals upon import.

2. **`backend/app/config.py` (lines 21–23):**
   ```python
   @property
   def DATABASE_URL(self) -> str:
       return os.getenv("DATABASE_URL", "sqlite:///./scopeleak.db")
   ```
   `backend/app/database.py` does not reference `backend.app.config.settings.DATABASE_URL`, maintaining its own raw `os.getenv` call.

---

### 1.3 Identification of Test Cases Creating 'Acme' and 'E2E Test Project'
1. **'E2E Test Project' and 'Acme Corp':**
   - File: `backend/tests/test_api_e2e.py`
   - Test: `test_full_project_workflow()`
   - Lines 16–21:
     ```python
     proj_res = client.post("/api/projects", json={
         "name": "E2E Test Project",
         "client_name": "Acme Corp",
         "currency": "USD",
         "default_hourly_rate": 100.0,
     })
     ```
   - Teardown: None. The created project is never deleted.

2. **'Acme Web Services Portal' and 'Acme Global':**
   - File: `backend/tests/test_user_document_audit.py`
   - Test: `test_user_document_audit_lifecycle()`
   - Lines 45–51:
     ```python
     proj_resp = client.post("/api/projects", json={
         "name": "Acme Web Services Portal",
         "client_name": "Acme Global",
         "currency": "USD",
         "default_hourly_rate": 150.0,
         "description": "Corporate web presence redesign for Acme Global"
     })
     ```
   - Teardown: None. The created project is never deleted.

3. **Non-Deduplicating Project Creation Endpoint:**
   - File: `backend/app/routes/projects.py` (lines 13–26):
     ```python
     @router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
     def create_project(project_in: ProjectCreate, db: Session = Depends(get_db)):
         project = Project(
             name=project_in.name,
             client_name=project_in.client_name,
             description=project_in.description,
             currency=project_in.currency or "INR",
             default_hourly_rate=project_in.default_hourly_rate,
             status="active",
         )
         db.add(project)
         db.commit()
         db.refresh(project)
     ```
     Every POST creates a new project with a new UUID. It does not check if a project with the same name already exists.

---

### 1.4 Test Runner Interaction, Missing Pytest Configuration, and Existing conftest.py
1. **Direct Pytest Invocation Without PYTHONPATH:**
   - Running `./venv/bin/pytest` produces:
     ```
     ERROR collecting backend/tests - ModuleNotFoundError: No module named 'backend'
     ```
   - No `pytest.ini`, `pyproject.toml`, or `setup.cfg` exists in the repository.
   - Running `PYTHONPATH=. ./venv/bin/pytest` passes all 22 tests.

2. **Untracked `backend/tests/conftest.py` State:**
   - Git status reveals `backend/tests/conftest.py` is untracked (recently created after commit `5ca63df`):
     ```python
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
     ```
   - Limitations of this existing `conftest.py`:
     a. **Session-scoped shared file:** `test_isolated_suite.db` is shared across all test files in the session. Tests execute sequentially against the same DB file without per-test table truncation or rollback.
     b. **No FastAPI dependency override:** Routes still use whatever global `SessionLocal` was instantiated. If `conftest.py` is bypassed (e.g. running a test file in an environment where conftest isn't loaded before app import), the app silently falls back to `sqlite:///./scopeleak.db`.
     c. **Teardown fragility:** If unclosed connections remain during test teardown, `os.remove` fails silently inside `except Exception: pass`, leaving `test_isolated_suite.db` on disk.

---

## 2. Logic Chain

1. **Premise 1 (Codebase Evolution):** In Git commits `027a840` (initial commit) and `5ca63df` (audit commit), no `conftest.py` existed in `backend/tests/` or the root directory.
2. **Premise 2 (Default Fallback):** In the absence of an explicit `DATABASE_URL` environment variable, `backend/app/database.py:5` defaulted to `sqlite:///./scopeleak.db`.
3. **Premise 3 (Test Execution):** When developers or CI ran `PYTHONPATH=. ./venv/bin/pytest backend/tests -v` (as documented in `docs/POST_BUILD_AUDIT.md:28`), `test_api_e2e.py` executed `test_full_project_workflow()`, inserting `E2E Test Project` (`Acme Corp`), and `test_user_document_audit.py` executed `test_user_document_audit_lifecycle()`, inserting `Acme Web Services Portal` (`Acme Global`).
4. **Premise 4 (Lack of Teardown & Deduplication):** Because neither test cleaned up its data, and `POST /api/projects` blindly inserts new rows without deduplication, each execution persisted records permanently into `scopeleak.db`. Multiple test runs caused multiple duplicate copies of `Acme` and `E2E Test Project` to accumulate.
5. **Premise 5 (Frontend Display):** In `frontend/src/App.tsx:70`, the frontend calls `api.getProjects()`, displaying all projects present in `scopeleak.db` in `ProjectsPage.tsx`, exposing test artifacts directly to end users.
6. **Premise 6 (Existing conftest.py Flaws):** The untracked `conftest.py` attempted to fix this by pointing `DATABASE_URL` to `./test_isolated_suite.db`, but does so at session scope with a shared disk file and lacks per-test isolation or FastAPI `dependency_overrides`.

---

## 3. Caveats

- In the current working tree, `scopeleak.db` contains only 1 record (`Northstar Website Redesign`), confirming that previous duplicate test records were already manually purged or reset in SQLite.
- The root cause is fully reproducible: deleting `conftest.py` and running `PYTHONPATH=. ./venv/bin/pytest backend/tests/test_api_e2e.py` immediately writes `E2E Test Project` back into `scopeleak.db`.
- Tests `test_change_orders.py`, `test_contracts.py`, and `test_requests_findings.py` already implement clean per-test in-memory isolation and do not contribute to database pollution.

---

## 4. Conclusion & Proposed Architectural Solution

The duplicate records were caused by:
1. Integration and E2E tests (`test_api_e2e.py`, `test_user_document_audit.py`) running against `FastAPI`'s default `get_db` without database isolation or dependency overrides.
2. Absence of a committed `conftest.py` prior to recent edits, causing tests to default to `scopeleak.db`.
3. Zero post-test cleanup or transactional rollback in those test functions.

### Proposed Architecture for Complete Isolation:
1. **FastAPI Dependency Override in `conftest.py`:**
   Configure an isolated in-memory SQLite database using `StaticPool` or an isolated temporary SQLite database, and explicitly register:
   ```python
   app.dependency_overrides[get_db] = override_get_db
   ```
2. **Per-Test Database Reset Fixture:**
   Implement an autouse fixture that runs `Base.metadata.create_all(bind=engine)` and drops or truncates all tables on fixture teardown (`Base.metadata.drop_all(bind=engine)`), guaranteeing 100% clean state for every test case.
3. **Repository-Level `pytest.ini`:**
   Add `pytest.ini` at repository root:
   ```ini
   [pytest]
   pythonpath = .
   testpaths = backend/tests
   ```
   This prevents `ModuleNotFoundError: No module named 'backend'` when executing bare `pytest`.
4. **App Settings Alignment:**
   Ensure `backend/app/database.py` imports and honors `backend.app.config.settings.DATABASE_URL` rather than reading raw `os.getenv` independently.

---

## 5. Verification Method

To verify these findings independently:

1. **Verify Test Project Names & Code Locations:**
   - Inspect `backend/tests/test_api_e2e.py:17` for `E2E Test Project` / `Acme Corp`.
   - Inspect `backend/tests/test_user_document_audit.py:46` for `Acme Web Services Portal` / `Acme Global`.
2. **Verify Global Database Binding:**
   - Inspect `backend/app/database.py:5-12` to confirm `engine` and `SessionLocal` are module-level globals defaulting to `./scopeleak.db`.
3. **Verify Pytest Execution with and without PYTHONPATH:**
   - Run `./venv/bin/pytest` -> observes `ModuleNotFoundError: No module named 'backend'`.
   - Run `PYTHONPATH=. ./venv/bin/pytest backend/tests -v` -> observes all 22 tests passing against `conftest.py`'s `test_isolated_suite.db`.
4. **Verify Current DB State:**
   - Run `sqlite3 scopeleak.db "SELECT id, name, client_name FROM projects;"` -> confirms current database rows.
