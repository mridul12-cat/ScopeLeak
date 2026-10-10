# ScopeLeak — 5-Minute Hackathon Demo Script

## Target Audience & Premise
- **Target Customer:** Freelance software engineers, independent consultants, and boutique agency owners.
- **Pain Point:** Unpaid scope creep. A client casually asks on Slack: *"Can you just add Stripe checkout before we launch?"* The developer builds it, but at billing time, the client disputes the extra invoice because there was no signed change order.
- **ScopeLeak Solution:** Connects original contract clauses, incoming requests, and work records with verifiable evidence to generate formal Change Orders before work gets done.

---

## 5-Minute Walkthrough Flow

### 0:00 – 0:45: The Problem & 1-Click Demo Setup
1. Open ScopeLeak dashboard.
2. Click **"Load Demo Project"** in the top bar or sidebar.
3. Show **Northstar Website Redesign** for **Northstar Studio** (₹2,000/hr baseline rate).
4. Highlight the **Principle banner**: *"AI interprets evidence. Deterministic application logic validates references and calculates costs. Humans make the final decisions."*

### 0:45 – 1:30: The Contract Baseline Hub
1. Navigate to **Contract & Scope**.
2. Show the uploaded agreement: `Northstar_Redesign_Agreement_v1.pdf`.
3. Point out the extracted baseline items:
   - **Exclusion 4.1**: *"Payment gateway integration, merchant onboarding, and checkout workflows are strictly out of scope."*
   - **Exclusion 4.2**: Customer order history and user portals excluded.
   - **Clause 3.2**: Two rounds of design revisions included.
4. Explain why the **"Confirm Baseline"** gate is mandatory: AI extractions are never authoritative until the professional reviews them.

### 1:30 – 2:30: Client Request & Evidence-Grounded Findings
1. Navigate to **Requests & Evidence**.
2. Point out the 4 captured incoming requests:
   - *"Can you add Stripe checkout before launch?"*
   - *"Can we also add a customer order-history page?"*
   - *"Please fix the mobile navigation; it currently overlaps the page title."*
   - *"Can you make the existing contact form button blue?"*
3. Click **"Inspect Evidence"** on the Stripe request:
   - Show the side-by-side modal: client message on the left, verbatim **Exclusion 4.1** quote on the right.
   - Show that the AI didn't hallucinate: it cited the exact contract clause, section, and page number!
   - Show the Mobile Nav fix finding: classified as **Likely In Scope** under Clause 2.2 (responsive design obligations).
   - Show the Button Color finding: flagged as **Ambiguous** (covered if within 2 revision rounds; billable if exhausted).

### 2:30 – 3:30: Deterministic Financial Impact
1. Navigate to **Financial Impact**.
2. Show the top metric: **Potential Unapproved Exposure = ₹26,000 (13.0 hours)**.
   - Stripe Checkout: 8.0 hrs × ₹2,000 = ₹16,000
   - Order History: 5.0 hrs × ₹2,000 = ₹10,000
   - Button Color & Mobile Nav: correctly excluded from unapproved debt because they are covered under agreed revision terms and responsive deliverables.
3. Emphasize that **estimates are never labeled as guaranteed revenue or debt** until formally executed.

### 3:30 – 4:15: Human Review & Professional Change Order PDF Export
1. Navigate to **Change Orders**.
2. Select **Change Order #1: Stripe Checkout Integration** (v1).
3. Review line items, payment terms (50% deposit), and validity.
4. Click **"Export PDF"**:
   - The browser downloads `ChangeOrder_v1_Northstar_Website_Redesign.pdf`.
   - Open the generated PDF: beautiful ReportLab typography, line items table, and dual signature blocks for both freelancer and client authorized signatories.
5. Demonstrate lifecycle status transitions: `Draft` ➔ `Approved by Freelancer` ➔ `Sent to Client` ➔ `Accepted by Client`.

### 4:15 – 5:00: Architecture & Future Roadmap
1. Review the architecture:
   - Python FastAPI + SQLAlchemy + SQLite (Postgres-ready)
   - PyMuPDF + python-docx + ReportLab PDF generator
   - Google Gemini 2.5 Flash API with strict Pydantic schemas and deterministic grounding validation
   - React 18 + Vite + TypeScript + Tailwind CSS UI
2. Mention future roadmap:
   - Real-time Slack and Gmail webhooks
   - Electronic signature integration (DocuSign / HelloSign)
   - QuickBooks / Stripe automatic invoice creation on acceptance.
