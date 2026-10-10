# ScopeLeak — System Architecture & Technical Design

## 1. Product Philosophy & Core Differentiator

**Tagline:** Catch unpaid work before it becomes part of the project.

Most existing AI tools either summarize whole contracts or attempt to flag vague "scope creep" without context. ScopeLeak's core differentiator is connecting:
1. **Agreed baseline commitments & exclusions** from original contracts.
2. **Subsequent incoming client requests** (from Slack, email, or tickets).
3. **Actually performed or estimated work records** (logged hours and rates).
4. **Deterministic financial impact calculations** (rates, hours, totals).
5. **Human review decisions and formal Change Orders**.

### The Central Principle
> **AI interprets the evidence. Deterministic application logic validates references, calculates costs, and controls workflow transitions. Humans make the final decisions.**

---

## 2. Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    React 18 + Vite Frontend                     │
│  • Persistent Sidebar      • Evidence Comparison Panel          │
│  • Contract Baseline Hub   • Financial Impact Breakdown         │
│  • Request Ingestion Log   • Change Order PDF Generator         │
└────────────────────────────────┬────────────────────────────────┘
                                 │ HTTP REST API / JSON
┌────────────────────────────────▼────────────────────────────────┐
│                   FastAPI Application Engine                    │
│  • Pydantic v2 Schema Validation                                │
│  • Project Isolation & Referential Integrity                    │
│  • Multi-format File Parsing (PDF fitz, DOCX, TXT)              │
│  • ReportLab Change-Order PDF Exporter                          │
└───────────────┬────────────────────────────────┬────────────────┘
                │                                │
┌───────────────▼──────────────┐ ┌───────────────▼────────────────┐
│   AI Evidence Engine         │ │ Deterministic Financial Engine │
│ • Google Gemini REST API     │ │ • line_total = hours × rate    │
│ • Pydantic Structured Schema │ │ • subtotal = sum(line_total)   │
│ • Cited ID Grounding Check   │ │ • taxes = subtotal × tax_rate  │
│ • Fallback Heuristic Matcher │ │ • Deduplicated exposure math   │
└──────────────────────────────┘ └────────────────────────────────┘
                │                                │
┌───────────────▼────────────────────────────────▼────────────────┐
│           SQLAlchemy Persistence Layer (SQLite / Postgres)      │
│  • Projects       • Contracts        • ScopeItems               │
│  • ClientRequests • WorkItems        • Findings                 │
│  • ReviewDecisions• ChangeOrders     • AuditEvents              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Data Integrity & Grounding Guarantees

1. **No Hallucinated References:** When Gemini returns an extraction or request analysis, ScopeLeak validates every cited `scope_item_id` and contract clause against real database records in the project. If a cited reference is non-existent, the engine marks the evidence incomplete and alerts the user.
2. **Deduplication:** Client requests and contracts compute SHA-256 hashes of normalized text. Duplicate messages do not inflate financial exposure.
3. **Non-destructive Baseline Review:** Extracted contracts remain in `pending_review` until the freelancer explicitly verifies and confirms the baseline.
4. **Separation of Estimations vs Recovered Revenue:** Potential exposure is clearly distinguished from approved and signed change orders.

---

## 4. Deployment Strategy

ScopeLeak supports a unified single-service deployment on **Render**:
- The backend serves the REST API under `/api/*`.
- When `frontend/dist` is built, FastAPI mounts static assets under `/assets` and delivers the Single-Page Application via an HTML fallback handler.
- Alternatively, frontend and backend can be hosted as separate microservices by providing `VITE_API_BASE_URL`.
