export interface Project {
  id: string;
  name: string;
  client_name: string;
  description?: string;
  currency: string;
  default_hourly_rate: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Contract {
  id: string;
  project_id: string;
  filename: string;
  content_hash: string;
  extracted_text?: string;
  processing_status: string;
  baseline_review_status: string;
  uploaded_at: string;
}

export interface ScopeItem {
  id: string;
  project_id: string;
  contract_id?: string;
  item_type: 'deliverable' | 'exclusion' | 'revision_limit' | 'milestone' | 'commercial_term' | 'ambiguous';
  description: string;
  normalized_description?: string;
  source_clause_id?: string;
  source_quote?: string;
  page_number?: number;
  section_reference?: string;
  review_status: 'pending' | 'confirmed' | 'modified' | 'rejected';
  created_at: string;
  updated_at: string;
}

export interface ClientRequest {
  id: string;
  project_id: string;
  external_source: string;
  sender?: string;
  message_text: string;
  message_timestamp?: string;
  content_hash: string;
  imported_at: string;
}

export interface WorkItem {
  id: string;
  project_id: string;
  source_type: string;
  external_id?: string;
  description: string;
  estimated_hours?: number;
  actual_hours?: number;
  hourly_rate?: number;
  work_status: string;
  approval_status: string;
  source_reference?: string;
  request_id?: string;
  created_at: string;
  updated_at: string;
}

export interface EvidenceReference {
  type: string;
  quote?: string;
  ref?: string;
  section?: string;
  page?: number;
  confidence?: number;
  notes?: string;
  is_missing_or_incomplete?: boolean;
}

export interface ReviewDecision {
  id: string;
  finding_id: string;
  actor: string;
  decision: string;
  notes?: string;
  timestamp: string;
}

export interface Finding {
  id: string;
  project_id: string;
  request_id: string;
  scope_item_id?: string;
  classification: 'likely_in_scope' | 'likely_out_of_scope' | 'ambiguous';
  explanation: string;
  confidence: number;
  evidence_references: EvidenceReference[];
  linked_work_item_ids: string[];
  estimated_extra_hours?: number;
  estimated_value?: number;
  review_status: 'pending' | 'approved' | 'dismissed' | 'uncertain';
  reviewer_notes?: string;
  created_at: string;
  updated_at: string;
  decisions?: ReviewDecision[];
}

export interface ChangeOrderLineItem {
  title: string;
  description?: string;
  hours: number;
  rate: number;
  line_total: number;
  source_finding_id?: string;
  source_work_item_id?: string;
  is_estimated?: boolean;
}

export interface ChangeOrder {
  id: string;
  project_id: string;
  version: number;
  title: string;
  status: 'draft' | 'ready_for_review' | 'approved_by_freelancer' | 'sent' | 'accepted_by_client' | 'declined';
  currency: string;
  line_items: ChangeOrderLineItem[];
  subtotal: number;
  taxes: number;
  total: number;
  assumptions?: string;
  exclusions?: string;
  validity_days?: number;
  payment_terms?: string;
  created_at: string;
  updated_at: string;
}

export interface WorkItemBreakdown {
  id: string;
  description: string;
  hours: number;
  hours_type: string;
  hourly_rate: number;
  line_total: number;
  approval_status: string;
  work_status: string;
  linked_request_id?: string;
  finding_classification?: string;
}

export interface FinancialImpact {
  project_id: string;
  currency: string;
  potential_unapproved_hours: number;
  potential_unapproved_value: number;
  draft_change_order_value: number;
  approved_by_freelancer_value: number;
  accepted_by_client_value: number;
  estimated_revenue_at_risk: number;
  items_with_missing_rates_count: number;
  breakdown: WorkItemBreakdown[];
}

export interface AuditEvent {
  id: string;
  project_id: string;
  actor: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  description?: string;
  before_state?: Record<string, any>;
  after_state?: Record<string, any>;
  timestamp: string;
}

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  gemini_configured: boolean;
  gemini_model: string;
  environment: string;
}
