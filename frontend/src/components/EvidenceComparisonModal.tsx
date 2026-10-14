import React, { useState } from 'react';
import { Finding, ClientRequest, ScopeItem } from '../types';
import { StatusBadge } from './StatusBadge';
import { X, CheckCircle2, AlertTriangle, XCircle, FileText, MessageSquare, Clock, ArrowRight } from 'lucide-react';

interface Props {
  finding: Finding | null;
  request?: ClientRequest;
  scopeItem?: ScopeItem;
  isOpen: boolean;
  onClose: () => void;
  onUpdateReview: (findingId: string, status: string, notes: string, hours?: number) => Promise<void>;
  currency?: string;
  defaultRate?: number;
}

export const EvidenceComparisonModal: React.FC<Props> = ({
  finding,
  request,
  scopeItem,
  isOpen,
  onClose,
  onUpdateReview,
  currency = 'INR',
  defaultRate = 2000,
}) => {
  if (!isOpen || !finding) return null;

  const [notes, setNotes] = useState(finding.reviewer_notes || '');
  const [hours, setHours] = useState<number>(finding.estimated_extra_hours || 0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleDecision = async (status: string) => {
    setIsSubmitting(true);
    try {
      await onUpdateReview(finding.id, status, notes, hours);
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  const primaryEvidence = finding.evidence_references?.[0];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-zinc-950 rounded-2xl shadow-2xl border border-zinc-800 max-w-4xl w-full max-h-[92vh] flex flex-col overflow-hidden animate-in fade-in duration-150">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800 bg-zinc-900/60">
          <div className="flex items-center space-x-3">
            <h2 className="text-lg font-bold text-white">Verifiable Scope Evidence Inspection</h2>
            <StatusBadge status={finding.classification} />
            {finding.provider_source === 'gemini_live' ? (
              <span className="text-[11px] font-semibold text-emerald-300 bg-emerald-950/70 px-2.5 py-0.5 rounded-full border border-emerald-800/60">
                🤖 Gemini Live AI
              </span>
            ) : (
              <span className="text-[11px] font-semibold text-zinc-300 bg-zinc-800 px-2.5 py-0.5 rounded-full border border-zinc-700">
                ⚙️ Deterministic Fallback
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-white p-1.5 rounded-lg hover:bg-zinc-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6">

          {/* Side by side evidence comparison grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Left: What the Client Requested */}
            <div className="p-5 bg-zinc-900/90 rounded-xl border border-zinc-800 flex flex-col justify-between">
              <div>
                <div className="flex items-center space-x-2 text-xs font-bold text-blue-400 uppercase tracking-wider mb-2">
                  <MessageSquare className="w-4 h-4" />
                  <span>1. Incoming Client Request</span>
                </div>
                <blockquote className="text-sm font-medium text-white bg-black/80 p-3.5 rounded-lg border border-zinc-800 shadow-sm italic">
                  "{request?.message_text || 'Message details loading...'}"
                </blockquote>
              </div>
              <div className="mt-4 pt-3 border-t border-zinc-800 text-xs text-zinc-400 space-y-1">
                <div><span className="font-semibold text-zinc-300">Sender:</span> {request?.sender || 'Client'}</div>
                <div><span className="font-semibold text-zinc-300">Source:</span> <span className="capitalize">{request?.external_source || 'Direct Message'}</span></div>
                {request?.message_timestamp && (
                  <div><span className="font-semibold text-zinc-300">Received:</span> {new Date(request.message_timestamp).toLocaleString()}</div>
                )}
              </div>
            </div>

            {/* Right: What the Contract Says */}
            <div className="p-5 bg-zinc-900/90 rounded-xl border border-zinc-800 flex flex-col justify-between">
              <div>
                <div className="flex items-center space-x-2 text-xs font-bold text-zinc-300 uppercase tracking-wider mb-2">
                  <FileText className="w-4 h-4 text-zinc-400" />
                  <span>2. Contract Baseline Scope Commitment</span>
                </div>

                {primaryEvidence?.quote || scopeItem?.source_quote ? (
                  <blockquote className="text-sm text-zinc-200 bg-black/80 p-3.5 rounded-lg border border-zinc-800 shadow-sm font-mono text-xs leading-relaxed">
                    "{primaryEvidence?.quote || scopeItem?.source_quote}"
                  </blockquote>
                ) : (
                  <div className="p-3 bg-amber-950/40 rounded-lg border border-amber-800/60 text-amber-300 text-xs flex items-center space-x-2">
                    <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                    <span>No verbatim clause match found in uploaded baseline. Evidence incomplete.</span>
                  </div>
                )}
              </div>

              <div className="mt-4 pt-3 border-t border-zinc-800 text-xs text-zinc-400 space-y-1">
                <div>
                  <span className="font-semibold text-zinc-300">Clause Reference:</span>{' '}
                  <span className="font-mono bg-black px-1.5 py-0.5 rounded text-[11px] text-zinc-200 border border-zinc-800">
                    {primaryEvidence?.ref && primaryEvidence.ref !== 'Unspecified'
                      ? primaryEvidence.ref
                      : scopeItem?.source_clause_id
                      ? scopeItem.source_clause_id
                      : primaryEvidence?.section
                      ? primaryEvidence.section
                      : scopeItem?.section_reference
                      ? scopeItem.section_reference
                      : 'Section Reference Pending'}
                  </span>
                </div>
                <div>
                  <span className="font-semibold text-zinc-300">Section:</span>{' '}
                  {primaryEvidence?.section || scopeItem?.section_reference || 'General Terms'}
                </div>
                <div>
                  <span className="font-semibold text-zinc-300">Location:</span>{' '}
                  Page {primaryEvidence?.page || scopeItem?.page_number || 1}
                </div>
              </div>
            </div>

          </div>

          {/* AI Evidence Engine Analysis & Rationale */}
          <div className="p-4 bg-zinc-900 border border-zinc-800 text-white rounded-xl shadow-inner">
            <div className="flex items-center justify-between text-xs font-medium text-zinc-400 mb-2">
              <span className="flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></span>
                <span>AI Interpretation & Rationale</span>
              </span>
              <span>Confidence: {(finding.confidence * 100).toFixed(0)}%</span>
            </div>
            <p className="text-sm text-zinc-200 leading-relaxed">
              {finding.explanation}
            </p>
            {primaryEvidence?.is_missing_or_incomplete && (
              <div className="mt-3 p-2.5 bg-amber-950/40 border border-amber-700/50 rounded-lg text-amber-200 text-xs flex items-start space-x-2">
                <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <div className="space-y-0.5">
                  <span className="font-semibold block">Notice: Ambiguity detected in baseline records.</span>
                  <span className="text-[11px] text-amber-300/90 block">
                    {primaryEvidence?.notes || 'Human confirmation required before issuing change orders.'}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Financial Calculation & Human Review Decision Panel */}
          <div className="p-5 bg-zinc-900/60 rounded-xl border border-zinc-800 space-y-4">
            <h4 className="text-xs font-bold text-zinc-300 uppercase tracking-wider">
              Human Review & Financial Calibration
            </h4>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-zinc-300 mb-1">
                  Estimated Extra Hours
                </label>
                <div className="relative rounded-md shadow-sm">
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    value={hours}
                    onChange={(e) => setHours(parseFloat(e.target.value) || 0)}
                    className="block w-full rounded-lg border-zinc-700 py-2 pl-3 pr-10 text-sm focus:border-blue-500 focus:ring-blue-500 border bg-zinc-900 text-white"
                  />
                  <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
                    <span className="text-xs text-zinc-400">hrs</span>
                  </div>
                </div>
                <p className="mt-1 text-[11px] text-zinc-400">
                  Calculated Value: {currency} {(hours * (typeof defaultRate === 'number' && defaultRate > 0 ? defaultRate : 2000)).toLocaleString()} (@ {currency} {typeof defaultRate === 'number' && defaultRate > 0 ? defaultRate : 2000}/hr)
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-300 mb-1">
                  Reviewer Notes / Client Communications
                </label>
                <input
                  type="text"
                  placeholder="e.g. Client agreed in email; waiting on deposit..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="block w-full rounded-lg border-zinc-700 py-2 px-3 text-sm focus:border-blue-500 focus:ring-blue-500 border bg-zinc-900 text-white placeholder-zinc-500"
                />
              </div>
            </div>

            {/* Explanatory banner */}
            <div className="text-[11px] text-zinc-400 italic bg-black/80 p-2.5 rounded-lg border border-zinc-800">
              * Note: Approving a finding accepts this scope analysis for internal workflow tracking and change-order drafting. It does not legally bind the client until a signed change order is executed.
            </div>

            {/* Decision Actions */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  disabled={isSubmitting}
                  onClick={() => handleDecision('approved')}
                  className="inline-flex items-center px-4 py-2 text-xs font-semibold text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 shadow-sm transition-colors"
                >
                  <CheckCircle2 className="w-4 h-4 mr-1.5" />
                  Approve Finding (Scope Change)
                </button>
                <button
                  type="button"
                  disabled={isSubmitting}
                  onClick={() => handleDecision('uncertain')}
                  className="inline-flex items-center px-3.5 py-2 text-xs font-semibold text-purple-300 bg-purple-950/50 border border-purple-800/80 rounded-lg hover:bg-purple-900/70 transition-colors"
                >
                  <AlertTriangle className="w-4 h-4 mr-1.5" />
                  Mark Uncertain
                </button>
                <button
                  type="button"
                  disabled={isSubmitting}
                  onClick={() => handleDecision('dismissed')}
                  className="inline-flex items-center px-3.5 py-2 text-xs font-semibold text-zinc-300 bg-zinc-800 border border-zinc-700 rounded-lg hover:bg-zinc-700 transition-colors"
                >
                  <XCircle className="w-4 h-4 mr-1.5" />
                  Dismiss Finding
                </button>
              </div>

              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-xs font-medium text-zinc-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
            </div>

          </div>

        </div>

      </div>
    </div>
  );
};
