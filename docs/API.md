# ScopeLeak — API Reference Documentation

All endpoints return JSON responses and standard HTTP error codes (`400`, `404`, `500`). When deployed, OpenAPI Swagger documentation is also interactively available at `/docs`.

---

## 1. Projects

### `GET /api/projects`
List all active projects.

### `POST /api/projects`
Create a new project.
```json
{
  "name": "E-Commerce Replatforming",
  "client_name": "Acme Corp",
  "currency": "INR",
  "default_hourly_rate": 2000.0,
  "description": "Store redesign and migration"
}
```

### `GET /api/projects/{project_id}`
Retrieve project details by ID.

### `PATCH /api/projects/{project_id}`
Update project settings, rates, or workflow status.

### `POST /api/projects/demo/seed?force=true`
Seed or reset the Northstar Website Redesign synthetic demo project.

---

## 2. Contracts & Scope Baseline

### `POST /api/projects/{project_id}/contracts`
Upload a contract document (`multipart/form-data` with `file`). Supports PDF, DOCX, and plain text.

### `POST /api/projects/{project_id}/baseline/extract`
Run AI / deterministic scope extraction on the contract. Returns proposed scope items with verbatim quotes and clause IDs.

### `GET /api/projects/{project_id}/baseline`
List all scope baseline items for the project.

### `PATCH /api/projects/{project_id}/baseline`
Batch-update or confirm the reviewed baseline:
```json
{
  "items": [],
  "confirm_all": true
}
```

### `POST /api/projects/{project_id}/scope`
Add a single manual scope item.

---

## 3. Client Requests & Analysis

### `POST /api/projects/{project_id}/requests`
Log a single client message.
```json
{
  "message_text": "Can you add Stripe checkout before launch?",
  "sender": "Aarav Mehta (Product Lead)",
  "external_source": "slack"
}
```

### `POST /api/projects/{project_id}/requests/import`
Batch import multiple messages from CSV or JSON.

### `POST /api/projects/{project_id}/analyze`
Run evidence analysis comparing unanalyzed client messages against confirmed baseline items.
```json
{
  "request_ids": ["optional-id-list"],
  "force_reanalyze": false
}
```

### `GET /api/projects/{project_id}/findings`
List all findings with evidence references, citations, confidence scores, and review decisions.

### `PATCH /api/findings/{finding_id}`
Update human review decision on a finding:
```json
{
  "review_status": "approved", // approved | dismissed | uncertain | pending
  "reviewer_notes": "Confirmed scope change with client via Slack.",
  "estimated_extra_hours": 8.0
}
```

---

## 4. Work Tracking & Timesheets

### `POST /api/projects/{project_id}/work`
Add a manual work item or task.

### `POST /api/projects/{project_id}/work/import`
Import timesheet logs from CSV.

### `GET /api/projects/{project_id}/work`
List logged and planned work items.

---

## 5. Financial Impact

### `GET /api/projects/{project_id}/impact`
Returns deterministic financial impact metrics:
```json
{
  "project_id": "...",
  "currency": "INR",
  "potential_unapproved_hours": 13.0,
  "potential_unapproved_value": 26000.0,
  "draft_change_order_value": 16000.0,
  "approved_by_freelancer_value": 0.0,
  "accepted_by_client_value": 0.0,
  "estimated_revenue_at_risk": 26000.0,
  "items_with_missing_rates_count": 0,
  "breakdown": [...]
}
```

---

## 6. Change Orders & PDF Export

### `POST /api/projects/{project_id}/change-orders`
Create a new Change Order from selected findings:
```json
{
  "title": "Change Order #1: Stripe Checkout Integration",
  "finding_ids": ["finding-uuid"],
  "tax_rate_percent": 0.0,
  "assumptions": "Work commences upon receipt of initial deposit.",
  "validity_days": 14,
  "payment_terms": "50% upfront, 50% upon deployment"
}
```

### `GET /api/projects/{project_id}/change-orders`
List all Change Orders for the project.

### `PATCH /api/change-orders/{change_order_id}`
Update Change Order status or line items. Valid statuses: `draft`, `ready_for_review`, `approved_by_freelancer`, `sent`, `accepted_by_client`, `declined`.

### `GET /api/change-orders/{change_order_id}/export`
Download the generated, print-ready PDF binary (`application/pdf`).

---

## 7. Audit Trail & Health

### `GET /api/projects/{project_id}/audit`
List all immutable audit events for the project.

### `GET /health`
System status and Gemini provider configuration check.
