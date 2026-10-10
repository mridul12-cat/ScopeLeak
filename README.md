# ScopeLeak

> **Catch unpaid work before it becomes part of the project.**

ScopeLeak is an AI-powered scope-change evidence engine built specifically for freelance software developers, independent consultants, and boutique software agencies.

It connects:
1. **Original Contract Commitments:** What was agreed in the original signed contract baseline (deliverables, revision limits, and explicit exclusions).
2. **Subsequent Client Requests:** What the client later casually asked for via Slack, email, or tickets.
3. **Work & Timesheet Records:** What tasks or hours were actually planned or performed.
4. **Deterministic Financial Impact:** What the extra work costs based on explicit billable rates.
5. **Human Review & Change Orders:** Whether the change has been reviewed by the developer and formally accepted by the client.

---

## 1. Differentiator: Verifiable Evidence Engine

Scopecreep is the #1 reason freelancers lose revenue and agencies suffer margin collapse. Most tools either summarize static PDFs or give generic LLM warnings. 

ScopeLeak's differentiator is **verifiable grounding**:
- Every scope-change finding links the **exact client message** to the **exact verbatim contract quote, clause identifier, section reference, and page number**.
- **No Hallucinations:** AI outputs are validated against real project records; non-existent clauses are flagged as incomplete evidence.
- **The Core Invariant:**
  > **AI interprets the evidence. Deterministic application logic validates references, calculates costs, and controls workflow transitions. Humans make the final decisions.**

---

## 2. Features

- **Project Management:** Multi-project support, currency formatting (INR, USD, EUR, GBP), and baseline hourly rate configuration.
- **Contract Text Extraction:** PyMuPDF (PDF) and python-docx (DOCX) text extraction with page and section preservation.
- **Reviewed Scope Baseline:** Categorize deliverables, explicit exclusions, revision limits, milestones, and commercial terms. Unconfirmed until the freelancer verifies.
- **Client Requests Log & CSV Ingestion:** Ingest single messages or batch import CSV timesheets/chats with sender and timestamp preservation.
- **Evidence Comparison Panel:** Side-by-side inspection displaying the client's request right next to the supporting contract clause and confidence score.
- **Human Workflow Decisions:** Functional actions to *Approve Finding*, *Dismiss Finding*, *Mark Uncertain*, or *Reopen* with reviewer notes.
- **Deterministic Pricing Engine:** Calculates line totals (`hours × rate`), change order subtotals, and taxes without LLM hallucination.
- **Print-Ready PDF Change Orders:** One-click generation of professional Change Orders using ReportLab, complete with formal dual signature blocks.
- **Immutable Audit Trail:** Complete event history tracking before/after state diffs, distinguishing human decisions from AI inferences.
- **1-Click Synthetic Demo Project:** Instant pre-seeded **Northstar Studio** redesign scenario (₹2,000/hr, Stripe checkout, mobile nav fix, button color tweaks).

---

## 3. Architecture

ScopeLeak is built as a cohesive, high-performance full-stack application:

```
ScopeLeak/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application & SPA static serving
│   │   ├── config.py            # Environment configuration
│   │   ├── database.py          # SQLAlchemy SQLite / PostgreSQL engine
│   │   ├── models/              # Canonical data models (Project, Contract, ScopeItem, etc.)
│   │   ├── schemas/             # Pydantic v2 validation schemas
│   │   ├── services/            # Business logic
│   │   │   ├── ai_service.py    # Google Gemini REST provider & deterministic fallback
│   │   │   ├── pricing_service.py # Deterministic financial calculations
│   │   │   ├── contract_extractor.py # PyMuPDF & python-docx parsers
│   │   │   ├── pdf_export_service.py # ReportLab Change-Order PDF generator
│   │   │   └── seed_service.py  # Synthetic Northstar demo project seeder
│   │   └── routes/              # Modular REST routers
│   ├── tests/                   # 100% offline pytest suite (15 passing tests)
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── api/client.ts        # Typed API wrapper with binary PDF download
│   │   ├── components/          # Sidebar, Header, StatusBadge, MetricCard, EvidenceModal
│   │   ├── pages/               # 9 dedicated section pages
│   │   ├── types/index.ts       # Domain TypeScript definitions
│   │   └── App.tsx              # Modular application controller
│   ├── package.json
│   └── vite.config.ts
├── docs/                        # ARCHITECTURE.md, API.md, DEMO_SCRIPT.md, SECURITY.md, TEST_REPORT.md
├── render.yaml                  # Production Render blueprint
├── .env.example
└── README.md
```

---

## 4. AI vs Deterministic Responsibilities

| Capability | AI Responsibility | Deterministic System Responsibility |
| :--- | :--- | :--- |
| **Contract Ingestion** | Extract candidate deliverables and exclusions | Extract raw text via PyMuPDF; compute SHA-256 hash |
| **Scope Comparison** | Propose classification & draft rationale | Validate cited clause ID exists in project; check grounding |
| **Financial Exposure** | Propose estimated extra hours | Compute `hours × rate`, sum totals, deduplicate items |
| **Workflow State** | None | Enforce valid state transitions (Draft ➔ Sent ➔ Accepted) |
| **Final Authority** | None | Freelancer approves findings; client signs Change Order |

---

## 5. Local Setup & Quickstart

### Prerequisites
- Python 3.9+
- Node.js 18+ and npm

### Step 1: Clone and Set Up Virtual Environment
```bash
git clone https://github.com/your-username/scopeleak.git
cd scopeleak

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt
```

### Step 2: Configure Environment
```bash
cp .env.example .env
```
*(Optional: Add `GEMINI_API_KEY=your_key` in `.env` for live model inference. If omitted, the deterministic fallback engine powers all extractions and evidence lookups offline.)*

### Step 3: Install and Build Frontend
```bash
cd frontend
npm install
npm run build
cd ..
```

### Step 4: Run Application
Start the backend server (FastAPI automatically serves the built frontend SPA at `http://localhost:8000`):
```bash
python backend/run.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser!

*(For hot-reloading frontend development, run `cd frontend && npm run dev` and open `http://localhost:5173`.)*

---

## 6. Synthetic Demo Project (Northstar Studio)

ScopeLeak includes a built-in 1-click synthetic demo project:
- **Project:** Northstar Website Redesign (Northstar Studio)
- **Baseline Rate:** ₹2,000 / hour
- **Agreed Scope:** Five-page marketing site, 2 rounds of design revisions, responsive layout, contact form.
- **Explicit Exclusions:** Payment gateway integration (Exclusion 4.1), customer account/order history portals (Exclusion 4.2).
- **Synthetic Incoming Requests:**
  1. *"Can you add Stripe checkout before launch?"* ➔ Flagged as **Likely Out of Scope** (8 hrs = ₹16,000).
  2. *"Can we also add a customer order-history page?"* ➔ Flagged as **Likely Out of Scope** (5 hrs = ₹10,000).
  3. *"Please fix the mobile navigation overlap."* ➔ Flagged as **Likely In Scope** (Clause 2.2 responsive design).
  4. *"Can you make the existing contact form button blue?"* ➔ Flagged as **Ambiguous** (covered if within 2 revision rounds).
- **Financial Metric:** Clearly displays **₹26,000 (13.0 hrs)** potential exposure as an **Estimate at Risk**, separated from approved change orders.

To load or reset the demo, click **"Load Demo Project"** in the top navigation bar at any time.

---

## 7. Testing & Verification

Run the automated test suite:
```bash
PYTHONPATH=. ./venv/bin/pytest backend/tests -v
```

Observed Test Results:
```
backend/tests/test_api_e2e.py::test_health_check PASSED
backend/tests/test_api_e2e.py::test_full_project_workflow PASSED
backend/tests/test_api_e2e.py::test_seed_demo_endpoint PASSED
backend/tests/test_change_orders.py::test_change_order_creation_and_versioning PASSED
backend/tests/test_change_orders.py::test_change_order_pdf_export PASSED
backend/tests/test_contracts.py::test_scope_item_creation_and_contract_linkage PASSED
backend/tests/test_contracts.py::test_baseline_review_confirmation PASSED
backend/tests/test_pricing.py::test_calculate_line_item_standard PASSED
backend/tests/test_pricing.py::test_calculate_line_item_edge_cases PASSED
backend/tests/test_pricing.py::test_calculate_change_order_totals_without_tax PASSED
backend/tests/test_pricing.py::test_calculate_change_order_totals_with_tax PASSED
backend/tests/test_pricing.py::test_calculate_change_order_empty PASSED
backend/tests/test_requests_findings.py::test_request_deduplication PASSED
backend/tests/test_requests_findings.py::test_finding_classification_and_evidence PASSED
backend/tests/test_requests_findings.py::test_review_decision_history PASSED
======================== 15 passed in 1.07s ========================
```

---

## 8. Render Deployment Instructions

ScopeLeak includes a turnkey `render.yaml` blueprint for one-click deployment:

1. Push your repository to GitHub.
2. Log in to [Render](https://render.com) and click **New > Blueprint**.
3. Select your repository. Render automatically reads `render.yaml`.
4. Add your optional `GEMINI_API_KEY` under Environment Variables.
5. Click **Apply**. Render installs dependencies, builds the Vite frontend bundle, and launches the FastAPI service on port 10000.

---

## 9. Known Limitations & Future Work

- **Multi-user Authentication:** In this MVP, projects are isolated by `project_id`. Production enterprise rollout will add OAuth / SSO user tenancy.
- **Direct Integration Webhooks:** Future releases will include native Slack bot apps and Gmail add-ons for automatic ingestion of incoming scope requests.
- **E-Signature Execution:** Future integration with DocuSign or HelloSign API to collect legally binding client signatures directly from the Change Order preview.

---

## 10. Documentation Index

- [System Architecture](file:///docs/ARCHITECTURE.md) (`docs/ARCHITECTURE.md`)
- [API Reference](file:///docs/API.md) (`docs/API.md`)
- [5-Minute Demo Script](file:///docs/DEMO_SCRIPT.md) (`docs/DEMO_SCRIPT.md`)
- [Security & Data Handling](file:///docs/SECURITY.md) (`docs/SECURITY.md`)
- [Test Report](file:///docs/TEST_REPORT.md) (`docs/TEST_REPORT.md`)
