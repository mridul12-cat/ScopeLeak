# Original User Request

## 2026-10-10T09:14:14Z

Test invocation to verify teamwork preview subagent existence
## 2026-10-10T10:22:34Z

Inspect the database scopeleak.db and tests/fixtures to determine why duplicate 'Acme' and 'E2E Test Project' records appear in the project list. Analyze test isolation and propose a solution where tests use an isolated database (e.g., in-memory SQLite or test_scopeleak.db via pytest fixture/override) so tests never modify the development/demo scopeleak.db. Also inspect seed_demo_project idempotency.
