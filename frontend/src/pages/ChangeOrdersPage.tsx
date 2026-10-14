import React, { useState } from 'react';
import { Project, ChangeOrder, Finding } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import {
  FileSpreadsheet,
  Plus,
  Download,
  Eye,
  CheckCircle2,
  Calendar,
  DollarSign,
  FileCheck,
  Send,
  XCircle,
} from 'lucide-react';

interface Props {
  project: Project;
  changeOrders: ChangeOrder[];
  findings: Finding[];
  onCreateChangeOrder: (data: { title: string; finding_ids?: string[]; tax_rate_percent?: number }) => Promise<void>;
  onUpdateChangeOrder: (id: string, data: Partial<ChangeOrder>) => Promise<void>;
  onDownloadPdf: (id: string, filename: string) => Promise<void>;
}

export const ChangeOrdersPage: React.FC<Props> = ({
  project,
  changeOrders,
  findings,
  onCreateChangeOrder,
  onUpdateChangeOrder,
  onDownloadPdf,
}) => {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedCo, setSelectedCo] = useState<ChangeOrder | null>(changeOrders[0] || null);
  const [title, setTitle] = useState('');
  const [taxRate, setTaxRate] = useState('0');
  const [selectedFindingIds, setSelectedFindingIds] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);

  const curr = project.currency || 'INR';

  // Findings available for drafting (e.g. out of scope or approved)
  const availableFindings = findings.filter(
    (f) => f.classification === 'likely_out_of_scope' || f.review_status === 'approved'
  );

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    setIsSubmitting(true);
    try {
      await onCreateChangeOrder({
        title: title.trim(),
        finding_ids: selectedFindingIds,
        tax_rate_percent: parseFloat(taxRate) || 0,
      });
      setTitle('');
      setSelectedFindingIds([]);
      setShowCreateModal(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleStatusChange = async (coId: string, status: ChangeOrder['status']) => {
    await onUpdateChangeOrder(coId, { status });
    if (selectedCo && selectedCo.id === coId) {
      setSelectedCo({ ...selectedCo, status });
    }
  };

  const handleDownload = async (co: ChangeOrder) => {
    setIsDownloading(true);
    try {
      await onDownloadPdf(co.id, `ChangeOrder_v${co.version}_${project.name.replace(/\s+/g, '_')}.pdf`);
    } finally {
      setIsDownloading(false);
    }
  };

  const toggleFindingSelection = (id: string) => {
    if (selectedFindingIds.includes(id)) {
      setSelectedFindingIds(selectedFindingIds.filter((item) => item !== id));
    } else {
      setSelectedFindingIds([...selectedFindingIds, id]);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      
      {/* Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900">Change Orders & Scoped Addendums</h2>
          <p className="text-xs text-slate-500">
            Generate formal, verifiable change orders from reviewed scope changes and export print-ready PDFs
          </p>
        </div>

        <button
          onClick={() => {
            setTitle(`Change Order: Additional Scope for ${project.name}`);
            setShowCreateModal(true);
          }}
          className="inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Draft New Change Order</span>
        </button>
      </div>

      {/* Main Two-Column Layout: List & Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Left Column: Change Orders Directory */}
        <div className="lg:col-span-1 space-y-3">
          <h3 className="text-xs font-bold text-zinc-300 uppercase tracking-wider px-1">
            Issued & Draft Documents ({changeOrders.length})
          </h3>

          {changeOrders.length === 0 ? (
            <div className="p-8 text-center bg-zinc-950 rounded-xl border border-dashed border-zinc-800 text-xs text-zinc-400">
              No change orders created yet. Draft one from your reviewed findings.
            </div>
          ) : (
            changeOrders.map((co) => {
              const isSelected = selectedCo?.id === co.id;
              return (
                <div
                  key={co.id}
                  onClick={() => setSelectedCo(co)}
                  className={`p-4 bg-zinc-950 rounded-xl border transition-all cursor-pointer shadow-sm hover:border-zinc-700 ${
                    isSelected ? 'border-blue-500 ring-2 ring-blue-500/20' : 'border-zinc-800'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">
                        Version {co.version}
                      </span>
                      <h4 className="text-sm font-bold text-white leading-snug">{co.title}</h4>
                    </div>
                    <StatusBadge status={co.status} />
                  </div>

                  <div className="mt-3 flex items-baseline justify-between text-xs">
                    <span className="font-bold text-white text-sm">
                      {co.currency} {co.total.toLocaleString()}
                    </span>
                    <span className="text-zinc-400 text-[11px]">
                      {new Date(co.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  <div className="mt-3 pt-3 border-t border-zinc-800/80 flex items-center justify-between text-xs text-zinc-400">
                    <span>{co.line_items?.length || 0} line items</span>
                    <span className="text-blue-400 font-semibold inline-flex items-center space-x-1">
                      <Eye className="w-3 h-3" />
                      <span>Preview</span>
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Right Column: Active Document Preview & Export Inspector */}
        <div className="lg:col-span-2">
          {selectedCo ? (
            <div className="bg-zinc-950 rounded-xl border border-zinc-800 shadow-sm overflow-hidden flex flex-col">
              
              {/* Document Toolbar */}
              <div className="px-6 py-4 border-b border-zinc-800 bg-zinc-900/60 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Document:</span>
                  <span className="font-mono text-xs font-bold bg-black px-2 py-0.5 rounded border border-zinc-800 text-zinc-200">
                    CO-{project.id.slice(0, 6).toUpperCase()}-v{selectedCo.version}
                  </span>
                  <StatusBadge status={selectedCo.status} />
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleDownload(selectedCo)}
                    disabled={isDownloading}
                    className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition-colors"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>{isDownloading ? 'Generating PDF...' : 'Export PDF'}</span>
                  </button>
                </div>
              </div>

              {/* Document Rendered Preview */}
              <div className="p-8 space-y-6 overflow-y-auto max-h-[70vh]">
                
                {/* Paper Header */}
                <div className="border-b-2 border-zinc-800 pb-4 flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-bold text-white uppercase tracking-tight">ScopeLeak Change Order</h3>
                    <p className="text-xs text-zinc-400 font-medium">Agreement Scope Amendment & Authorization</p>
                  </div>
                  <div className="text-right text-xs space-y-0.5">
                    <p className="font-semibold text-zinc-200">Version {selectedCo.version}</p>
                    <p className="text-zinc-400">Date: {new Date(selectedCo.created_at).toLocaleDateString()}</p>
                  </div>
                </div>

                {/* Metadata Table */}
                <div className="grid grid-cols-2 gap-4 text-xs bg-zinc-900/60 p-4 rounded-lg border border-zinc-800">
                  <div>
                    <span className="text-zinc-400 font-semibold">Project:</span>{' '}
                    <strong className="text-zinc-200">{project.name}</strong>
                  </div>
                  <div>
                    <span className="text-zinc-400 font-semibold">Client:</span>{' '}
                    <strong className="text-zinc-200">{project.client_name}</strong>
                  </div>
                  <div>
                    <span className="text-zinc-400 font-semibold">Validity:</span>{' '}
                    <span className="text-zinc-300">{selectedCo.validity_days || 14} days</span>
                  </div>
                  <div>
                    <span className="text-zinc-400 font-semibold">Payment Terms:</span>{' '}
                    <span className="text-zinc-300">{selectedCo.payment_terms || 'Standard terms'}</span>
                  </div>
                </div>

                {/* Line Items Table */}
                <div>
                  <h4 className="text-xs font-bold text-zinc-300 uppercase tracking-wider mb-2">Scope Modification Items</h4>
                  <table className="w-full text-left text-xs border border-zinc-800 rounded-lg overflow-hidden">
                    <thead className="bg-zinc-900 text-zinc-300 text-[10px] uppercase font-semibold">
                      <tr>
                        <th className="py-2.5 px-3">Item Description</th>
                        <th className="py-2.5 px-3 text-right">Hours</th>
                        <th className="py-2.5 px-3 text-right">Rate</th>
                        <th className="py-2.5 px-3 text-right">Line Total</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800/80">
                      {selectedCo.line_items?.map((item, idx) => (
                        <tr key={idx} className="hover:bg-zinc-900/40">
                          <td className="py-2.5 px-3">
                            <p className="font-semibold text-white">{item.title}</p>
                            {item.description && (
                              <p className="text-[11px] text-zinc-400">{item.description}</p>
                            )}
                          </td>
                          <td className="py-2.5 px-3 text-right font-medium text-zinc-300">{item.hours} hrs</td>
                          <td className="py-2.5 px-3 text-right font-mono text-zinc-300">
                            {selectedCo.currency} {item.rate.toLocaleString()}
                          </td>
                          <td className="py-2.5 px-3 text-right font-bold text-white">
                            {selectedCo.currency} {item.line_total.toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-zinc-900/60 border-t border-zinc-800 text-xs font-bold text-white">
                      <tr>
                        <td colSpan={3} className="py-2 px-3 text-right">Subtotal:</td>
                        <td className="py-2 px-3 text-right">{selectedCo.currency} {selectedCo.subtotal.toLocaleString()}</td>
                      </tr>
                      {selectedCo.taxes > 0 && (
                        <tr>
                          <td colSpan={3} className="py-2 px-3 text-right font-normal text-zinc-400">Taxes & Fees:</td>
                          <td className="py-2 px-3 text-right font-normal text-zinc-400">{selectedCo.currency} {selectedCo.taxes.toLocaleString()}</td>
                        </tr>
                      )}
                      <tr className="border-t-2 border-zinc-800 bg-blue-950/40 text-blue-400">
                        <td colSpan={3} className="py-2.5 px-3 text-right text-sm">TOTAL AMOUNT:</td>
                        <td className="py-2.5 px-3 text-right text-sm font-extrabold">{selectedCo.currency} {selectedCo.total.toLocaleString()}</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>

                {/* Terms and Exclusions */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs pt-2">
                  <div className="p-3 bg-zinc-900/60 rounded-lg border border-zinc-800">
                    <span className="font-bold text-zinc-300 block mb-1">Assumptions:</span>
                    <p className="text-zinc-400">{selectedCo.assumptions || 'Standard execution timeline.'}</p>
                  </div>
                  <div className="p-3 bg-zinc-900/60 rounded-lg border border-zinc-800">
                    <span className="font-bold text-zinc-300 block mb-1">Exclusions:</span>
                    <p className="text-zinc-400">{selectedCo.exclusions || 'Third party hosting and software subscription fees.'}</p>
                  </div>
                </div>

                {/* Workflow Progression Controls */}
                <div className="p-4 bg-zinc-900/60 rounded-xl border border-zinc-800 space-y-3">
                  <span className="text-xs font-bold text-zinc-300 uppercase tracking-wider block">
                    Workflow & Approval Lifecycle
                  </span>

                  <div className="flex flex-wrap items-center gap-2">
                    {selectedCo.status === 'draft' && (
                      <button
                        onClick={() => handleStatusChange(selectedCo.id, 'ready_for_review')}
                        className="px-3 py-1.5 text-xs font-semibold text-zinc-200 bg-zinc-800 border border-zinc-700 rounded-lg hover:bg-zinc-700"
                      >
                        Mark Ready For Review
                      </button>
                    )}

                    {(selectedCo.status === 'draft' || selectedCo.status === 'ready_for_review') && (
                      <button
                        onClick={() => handleStatusChange(selectedCo.id, 'approved_by_freelancer')}
                        className="px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700"
                      >
                        Approve (Freelancer)
                      </button>
                    )}

                    {selectedCo.status === 'approved_by_freelancer' && (
                      <button
                        onClick={() => handleStatusChange(selectedCo.id, 'sent')}
                        className="px-3 py-1.5 text-xs font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 inline-flex items-center space-x-1"
                      >
                        <Send className="w-3 h-3" />
                        <span>Mark as Sent to Client</span>
                      </button>
                    )}

                    {selectedCo.status === 'sent' && (
                      <button
                        onClick={() => handleStatusChange(selectedCo.id, 'accepted_by_client')}
                        className="px-3 py-1.5 text-xs font-semibold text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 inline-flex items-center space-x-1"
                      >
                        <CheckCircle2 className="w-3 h-3" />
                        <span>Record Client Acceptance</span>
                      </button>
                    )}

                    {selectedCo.status !== 'declined' && selectedCo.status !== 'accepted_by_client' && (
                      <button
                        onClick={() => handleStatusChange(selectedCo.id, 'declined')}
                        className="px-3 py-1.5 text-xs font-medium text-zinc-400 hover:text-rose-400"
                      >
                        Mark Declined
                      </button>
                    )}
                  </div>
                </div>

              </div>

            </div>
          ) : (
            <div className="p-12 text-center bg-zinc-950 rounded-xl border border-zinc-800 text-xs text-zinc-400">
              Select a change order from the left to preview and export.
            </div>
          )}
        </div>

      </div>

      {/* Modal: Draft Change Order */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-zinc-950 rounded-2xl shadow-xl border border-zinc-800 max-w-xl w-full p-6 animate-in fade-in duration-150">
            <h3 className="text-base font-bold text-white mb-1">Draft New Change Order</h3>
            <p className="text-xs text-zinc-400 mb-5">
              Select reviewed findings to package into a professional change order.
            </p>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-zinc-300 mb-1">Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Change Order #1: Stripe Checkout Integration"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full text-xs rounded-lg border border-zinc-700 bg-zinc-900 text-white p-2.5 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 font-semibold placeholder-zinc-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-300 mb-1">
                  Select Scope Findings to Include ({selectedFindingIds.length} selected)
                </label>
                <div className="max-h-48 overflow-y-auto space-y-2 border border-zinc-800 rounded-lg p-2.5 bg-zinc-900/60">
                  {availableFindings.length === 0 ? (
                    <div className="text-xs text-zinc-400 py-4 text-center">
                      No reviewed scope findings found. Approve findings first in the Findings Review tab.
                    </div>
                  ) : (
                    availableFindings.map((f) => (
                      <label
                        key={f.id}
                        className="flex items-start space-x-2.5 p-2 rounded bg-zinc-900 border border-zinc-800 hover:bg-zinc-800/60 cursor-pointer text-xs"
                      >
                        <input
                          type="checkbox"
                          checked={selectedFindingIds.includes(f.id)}
                          onChange={() => toggleFindingSelection(f.id)}
                          className="mt-0.5 rounded text-blue-600 focus:ring-blue-500"
                        />
                        <div className="space-y-0.5 flex-1">
                          <p className="font-semibold text-white">{f.explanation.slice(0, 80)}...</p>
                          <div className="flex items-center space-x-2 text-[11px] text-zinc-400">
                            <span className="font-bold text-rose-400">+{f.estimated_extra_hours || 0} hrs</span>
                            <span>•</span>
                            <StatusBadge status={f.review_status} />
                          </div>
                        </div>
                      </label>
                    ))
                  )}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-300 mb-1">Tax Rate (%)</label>
                <input
                  type="number"
                  step="1"
                  min="0"
                  value={taxRate}
                  onChange={(e) => setTaxRate(e.target.value)}
                  className="w-full text-xs rounded-lg border border-zinc-700 bg-zinc-900 text-white p-2.5"
                />
              </div>

              <div className="flex items-center justify-end space-x-2 pt-3 border-t border-zinc-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3.5 py-2 text-xs font-medium text-zinc-400 hover:text-zinc-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !title.trim()}
                  className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm disabled:opacity-50"
                >
                  {isSubmitting ? 'Creating...' : 'Create Draft'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
