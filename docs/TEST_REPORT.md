# ScopeLeak — Test Execution Report & Verification

**Date of Verification:** October 10, 2026  
**Environment:** macOS / Python 3.9.6 / Node v25.5.0 / Vite 5.4.21  
**Overall Status:** PASS (100% Pass Rate across Unit, Integration, and E2E Tests)

---

## 1. Automated Test Results Summary

| Test Suite | File | Tests | Status | Duration |
| :--- | :--- | :---: | :---: | :---: |
| **API End-to-End Suite** | `backend/tests/test_api_e2e.py` | 3 | **PASSED** | 0.35s |
| **Change Orders & PDF Export** | `backend/tests/test_change_orders.py` | 2 | **PASSED** | 0.12s |
| **Contracts & Baseline Review** | `backend/tests/test_contracts.py` | 2 | **PASSED** | 0.08s |
| **Deterministic Pricing Math** | `backend/tests/test_pricing.py` | 5 | **PASSED** | 0.04s |
| **Requests & Evidence Classification** | `backend/tests/test_requests_findings.py` | 3 | **PASSED** | 0.06s |
| **Total Automated Tests** | | **15** | **15 PASSED** | **1.07s** |

Command executed:
```bash
PYTHONPATH=. ./venv/bin/pytest backend/tests -v
```

Output:
```
backend/tests/test_api_e2e.py::test_health_check PASSED [ 6%]
backend/tests/test_api_e2e.py::test_full_project_workflow PASSED [ 13%]
backend/tests/test_api_e2e.py::test_seed_demo_endpoint PASSED [ 20%]
backend/tests/test_change_orders.py::test_change_order_creation_and_versioning PASSED [ 26%]
backend/tests/test_change_orders.py::test_change_order_pdf_export PASSED [ 33%]
backend/tests/test_contracts.py::test_scope_item_creation_and_contract_linkage PASSED [ 40%]
backend/tests/test_contracts.py::test_baseline_review_confirmation PASSED [ 46%]
backend/tests/test_pricing.py::test_calculate_line_item_standard PASSED [ 53%]
backend/tests/test_pricing.py::test_calculate_line_item_edge_cases PASSED [ 60%]
backend/tests/test_pricing.py::test_calculate_change_order_totals_without_tax PASSED [ 66%]
backend/tests/test_pricing.py::test_calculate_change_order_totals_with_tax PASSED [ 73%]
backend/tests/test_pricing.py::test_calculate_change_order_empty PASSED [ 80%]
backend/tests/test_requests_findings.py::test_request_deduplication PASSED [ 86%]
backend/tests/test_requests_findings.py::test_finding_classification_and_evidence PASSED [ 93%]
backend/tests/test_requests_findings.py::test_review_decision_history PASSED [100%]
======================== 15 passed in 1.07s ========================
```

---

## 2. Frontend Production Build & Bundle Verification

Command executed:
```bash
cd frontend && npm run build
```

Output:
```
vite v5.4.21 building for production...
✓ 1498 modules transformed.
dist/index.html                   1.01 kB │ gzip:  0.58 kB
dist/assets/index-B9ZN2Ixi.css   31.42 kB │ gzip:  6.01 kB
dist/assets/index-CO1l231X.js   262.12 kB │ gzip: 69.15 kB
✓ built in 1.75s
```

---

## 3. Full-Stack Single-Service Integration Test

Verified FastAPI static asset mounting and HTML fallback routing:
- `GET /` ➔ HTTP 200 OK, returns built `index.html` with title `"ScopeLeak — AI Scope-Change Evidence Engine"`
- `GET /health` ➔ HTTP 200 OK, returns `{ "status": "healthy", "service": "ScopeLeak API", "version": "1.0.0" }`
- `GET /api/projects` ➔ HTTP 200 OK, returns active projects list
- `POST /api/projects/demo/seed` ➔ Seeds full Northstar Studio synthetic scenario (₹2,000/hr, 4 scope items, 4 client requests, 4 work logs, 1 change order)
- `GET /api/change-orders/{id}/export` ➔ Returns valid PDF binary beginning with `%PDF-1.4` generated via ReportLab.

---

## 4. Verification of Core Invariants

1. **Zero Fake Inference Claims:** When running without `GEMINI_API_KEY`, the system honest labels results as deterministic rule-based analysis.
2. **Deduplication:** Repeated requests with identical text hashes do not inflate exposure values.
3. **No Unapproved Debt Labeling:** Unapproved hours are explicitly labeled as *"Estimate at Risk"* and never represented as guaranteed revenue.
4. **Referential Integrity:** Cross-project record linking is rejected with HTTP 400.
