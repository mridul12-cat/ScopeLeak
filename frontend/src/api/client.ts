import {
  Project,
  Contract,
  ScopeItem,
  ClientRequest,
  WorkItem,
  Finding,
  ChangeOrder,
  FinancialImpact,
  AuditEvent,
  HealthStatus,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!res.ok) {
    let errorDetail = 'API Request failed';
    try {
      const err = await res.json();
      errorDetail = err.detail || errorDetail;
    } catch (_) {
      errorDetail = `HTTP ${res.status}: ${res.statusText}`;
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  // Health
  getHealth: (): Promise<HealthStatus> => fetchJson('/health'),

  // Projects
  getProjects: (): Promise<Project[]> => fetchJson('/api/projects'),
  getProject: (id: string): Promise<Project> => fetchJson(`/api/projects/${id}`),
  createProject: (data: Partial<Project>): Promise<Project> =>
    fetchJson('/api/projects', { method: 'POST', body: JSON.stringify(data) }),
  updateProject: (id: string, data: Partial<Project>): Promise<Project> =>
    fetchJson(`/api/projects/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteProject: (id: string): Promise<void> =>
    fetchJson(`/api/projects/${id}`, { method: 'DELETE' }),
  seedDemoProject: (force: boolean = false): Promise<Project> =>
    fetchJson(`/api/projects/demo/seed?force=${force}`, { method: 'POST' }),

  // Contracts & Scope Baseline
  getContracts: (projectId: string): Promise<Contract[]> =>
    fetchJson(`/api/projects/${projectId}/contracts`),
  uploadContract: async (projectId: string, file: File): Promise<Contract> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/api/projects/${projectId}/contracts`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },
  extractBaseline: (projectId: string, contractId?: string): Promise<ScopeItem[]> =>
    fetchJson(`/api/projects/${projectId}/baseline/extract`, {
      method: 'POST',
      body: JSON.stringify({ contract_id: contractId, force_reextract: false }),
    }),
  getBaseline: (projectId: string): Promise<ScopeItem[]> =>
    fetchJson(`/api/projects/${projectId}/baseline`),
  confirmBaseline: (projectId: string): Promise<ScopeItem[]> =>
    fetchJson(`/api/projects/${projectId}/baseline`, {
      method: 'PATCH',
      body: JSON.stringify({ items: [], confirm_all: true }),
    }),
  addScopeItem: (projectId: string, item: Partial<ScopeItem>): Promise<ScopeItem> =>
    fetchJson(`/api/projects/${projectId}/scope`, {
      method: 'POST',
      body: JSON.stringify(item),
    }),
  updateScopeItem: (projectId: string, itemId: string, item: Partial<ScopeItem>): Promise<ScopeItem> =>
    fetchJson(`/api/projects/${projectId}/scope/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify(item),
    }),
  deleteScopeItem: (projectId: string, itemId: string): Promise<void> =>
    fetchJson(`/api/projects/${projectId}/scope/${itemId}`, { method: 'DELETE' }),

  // Client Requests
  getRequests: (projectId: string): Promise<ClientRequest[]> =>
    fetchJson(`/api/projects/${projectId}/requests`),
  createRequest: (projectId: string, text: string, sender?: string): Promise<ClientRequest> =>
    fetchJson(`/api/projects/${projectId}/requests`, {
      method: 'POST',
      body: JSON.stringify({ message_text: text, sender: sender || 'Client', external_source: 'manual' }),
    }),
  importRequests: (projectId: string, messages: { message_text: string; sender?: string }[]): Promise<ClientRequest[]> =>
    fetchJson(`/api/projects/${projectId}/requests/import`, {
      method: 'POST',
      body: JSON.stringify({ messages }),
    }),

  // Findings & Analysis
  analyzeRequests: (projectId: string, requestIds?: string[]): Promise<Finding[]> =>
    fetchJson(`/api/projects/${projectId}/analyze`, {
      method: 'POST',
      body: JSON.stringify({ request_ids: requestIds, force_reanalyze: true }),
    }),
  getFindings: (projectId: string): Promise<Finding[]> =>
    fetchJson(`/api/projects/${projectId}/findings`),
  updateFindingReview: (findingId: string, data: { review_status?: string; reviewer_notes?: string; estimated_extra_hours?: number }): Promise<Finding> =>
    fetchJson(`/api/findings/${findingId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  // Work Tracking
  getWorkItems: (projectId: string): Promise<WorkItem[]> =>
    fetchJson(`/api/projects/${projectId}/work`),
  createWorkItem: (projectId: string, item: Partial<WorkItem>): Promise<WorkItem> =>
    fetchJson(`/api/projects/${projectId}/work`, {
      method: 'POST',
      body: JSON.stringify(item),
    }),
  importWorkItems: (projectId: string, items: Partial<WorkItem>[]): Promise<WorkItem[]> =>
    fetchJson(`/api/projects/${projectId}/work/import`, {
      method: 'POST',
      body: JSON.stringify({ items }),
    }),
  updateWorkItem: (projectId: string, itemId: string, item: Partial<WorkItem>): Promise<WorkItem> =>
    fetchJson(`/api/projects/${projectId}/work/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify(item),
    }),
  deleteWorkItem: (projectId: string, itemId: string): Promise<void> =>
    fetchJson(`/api/projects/${projectId}/work/${itemId}`, { method: 'DELETE' }),

  // Financial Impact
  getFinancialImpact: (projectId: string): Promise<FinancialImpact> =>
    fetchJson(`/api/projects/${projectId}/impact`),

  // Change Orders
  getChangeOrders: (projectId: string): Promise<ChangeOrder[]> =>
    fetchJson(`/api/projects/${projectId}/change-orders`),
  createChangeOrder: (projectId: string, data: { title: string; finding_ids?: string[]; tax_rate_percent?: number }): Promise<ChangeOrder> =>
    fetchJson(`/api/projects/${projectId}/change-orders`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  updateChangeOrder: (changeOrderId: string, data: Partial<ChangeOrder>): Promise<ChangeOrder> =>
    fetchJson(`/api/change-orders/${changeOrderId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  downloadChangeOrderPdf: async (changeOrderId: string, filename: string): Promise<void> => {
    const res = await fetch(`${API_BASE}/api/change-orders/${changeOrderId}/export`);
    if (!res.ok) throw new Error('PDF export failed');
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || 'ChangeOrder.pdf';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  },

  // Audit Trail
  getAuditTrail: (projectId: string): Promise<AuditEvent[]> =>
    fetchJson(`/api/projects/${projectId}/audit`),
};
