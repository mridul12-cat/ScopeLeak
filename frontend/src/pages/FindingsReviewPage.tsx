import React, { useState } from 'react';
import { Project, Finding, ClientRequest, ScopeItem } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import {
  ShieldAlert,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  FileText,
  MessageSquare,
  Clock,
  Sparkles,
} from 'lucide-react';

interface Props {
  project: Project;
  findings: Finding[];
  requests: ClientRequest[];
  scopeItems: ScopeItem[];
  onUpdateReview: (findingId: string, status: string, notes: string, hours?: number) => Promise<void>;
  onInspectFinding: (f: Finding) => void;
  onAnalyzeRequests: () => Promise<void>;
}

export const FindingsReviewPage: React.FC<Props> = ({
  project,
  findings,
  requests,
  scopeItems,
  onUpdateReview,
  onInspectFinding,
  onAnalyzeRequests,
}) => {
  const [filterClassification, setFilterClassification] = useState<string>('all');
  const [filterReviewStatus, setFilterReviewStatus] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const curr = project.currency || 'INR';
  const requestById = new Map(requests.map((r) => [r.id, r]));
  const scopeById = new Map(scopeItems.map((s) => [s.id, s]));

  const handleQuickDecision = async (findingId: string, status: string) => {
    const finding = findings.find((f) => f.id === findingId);
    await onUpdateReview(
      findingId,
      status,
      finding?.reviewer_notes || `Review updated to ${status}`,
      finding?.estimated_extra_hours
    );
  };

  const handleReanalyze = async () => {
    setIsAnalyzing(true);
    try {
      await onAnalyzeRequests();
    } finally {
      setIsAnalyzing(false);
    }
  };

  const filteredFindings = findings.filter((f) => {
    if (filterClassification !== 'all' && f.classification !== filterClassification) return false;
    if (filterReviewStatus !== 'all' && f.review_status !== filterReviewStatus) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchExpl = f.explanation.toLowerCase().includes(q);
      const req = requestById.get(f.request_id);
      const matchReq = req ? req.message_text.toLowerCase().includes(q) : false;
      if (!matchExpl && !matchReq) return false;
    }
    return true;
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      
      {/* Top Banner & Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900">Findings Review & Decision Hub</h2>
          <p className="text-xs text-slate-500">
            Compare incoming client requests with contract commitments; make authoritative decisions
          </p>
        </div>

        <button
          onClick={handleReanalyze}
          disabled={isAnalyzing}
          className="inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm disabled:opacity-50 transition-colors"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>{isAnalyzing ? 'Re-analyzing...' : 'Re-run Analysis'}</span>
        </button>
      </div>

      {/* Filter Controls Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 flex flex-wrap items-center justify-between gap-4 shadow-sm">
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <div className="flex items-center space-x-2">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <span className="font-semibold text-slate-600">Classification:</span>
            <select
              value={filterClassification}
              onChange={(e) => setFilterClassification(e.target.value)}
              className="text-xs rounded-lg border border-slate-300 py-1.5 px-2 bg-white focus:border-blue-500"
            >
              <option value="all">All Classifications</option>
              <option value="likely_out_of_scope">Likely Out of Scope</option>
              <option value="likely_in_scope">Likely In Scope</option>
              <option value="ambiguous">Ambiguous</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <span className="font-semibold text-slate-600">Review Status:</span>
            <select
              value={filterReviewStatus}
              onChange={(e) => setFilterReviewStatus(e.target.value)}
              className="text-xs rounded-lg border border-slate-300 py-1.5 px-2 bg-white focus:border-blue-500"
            >
              <option value="all">All Statuses</option>
              <option value="pending">Pending Review</option>
              <option value="approved">Approved</option>
              <option value="uncertain">Marked Uncertain</option>
              <option value="dismissed">Dismissed</option>
            </select>
          </div>
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
          <input
            type="text"
            placeholder="Search findings or text..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 pl-8 pr-3 py-1.5 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Findings List */}
      <div className="space-y-4">
        {filteredFindings.length === 0 ? (
          <div className="p-12 text-center bg-white rounded-xl border border-dashed border-slate-300 text-xs text-slate-500">
            No matching scope findings found. Try clearing your filters or running analysis on incoming requests.
          </div>
        ) : (
          filteredFindings.map((finding) => {
            const req = requestById.get(finding.request_id);
            const primaryEv = finding.evidence_references?.[0];
            const estVal = finding.estimated_value ?? ((finding.estimated_extra_hours || 0) * project.default_hourly_rate);

            return (
              <div
                key={finding.id}
                className="p-5 bg-white rounded-xl border border-slate-200 shadow-sm transition-all hover:shadow-md space-y-4"
              >
                {/* Header Row */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                  <div className="flex items-center space-x-2.5">
                    <StatusBadge status={finding.classification} />
                    <span className="text-slate-300">•</span>
                    <span className="text-xs text-slate-500">
                      Confidence: <strong>{(finding.confidence * 100).toFixed(0)}%</strong>
                    </span>
                    {finding.estimated_extra_hours && (
                      <span className="text-xs font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200">
                        +{finding.estimated_extra_hours} hrs ({curr} {estVal.toLocaleString()})
                      </span>
                    )}
                  </div>

                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-slate-500">Workflow Decision:</span>
                    <StatusBadge status={finding.review_status} />
                  </div>
                </div>

                {/* Evidence Comparison Preview */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  
                  {/* Left: Client Message */}
                  <div className="p-3 bg-blue-50/40 rounded-lg border border-blue-100/70 space-y-1">
                    <div className="flex items-center space-x-1.5 text-blue-700 font-bold text-[10px] uppercase tracking-wider">
                      <MessageSquare className="w-3.5 h-3.5" />
                      <span>Client Message ({req?.sender || 'Client'})</span>
                    </div>
                    <blockquote className="font-semibold text-slate-900 italic">
                      "{req?.message_text || 'Message text unavailable'}"
                    </blockquote>
                  </div>

                  {/* Right: Contract Quote */}
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
                    <div className="flex items-center justify-between text-slate-600 font-bold text-[10px] uppercase tracking-wider">
                      <span className="flex items-center space-x-1.5">
                        <FileText className="w-3.5 h-3.5" />
                        <span>Contract Evidence</span>
                      </span>
                      <span className="font-mono bg-white px-1.5 py-0.2 rounded border border-slate-200 text-slate-800">
                        {primaryEv?.ref || 'Clause Ref'}
                      </span>
                    </div>
                    <p className="font-mono text-[11px] text-slate-700 italic">
                      "{primaryEv?.quote || 'No direct clause quote matching. Ambiguous terms.'}"
                    </p>
                  </div>

                </div>

                {/* AI Explanation & Reviewer Notes */}
                <div className="text-xs space-y-1">
                  <p className="text-slate-800 font-medium leading-relaxed">
                    <strong className="text-slate-900">Analysis:</strong> {finding.explanation}
                  </p>
                  {finding.reviewer_notes && (
                    <p className="text-slate-500 italic">
                      <strong className="text-slate-700 not-italic">Reviewer Notes:</strong> {finding.reviewer_notes}
                    </p>
                  )}
                </div>

                {/* Action Bar */}
                <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center space-x-2">
                    {finding.review_status !== 'approved' && (
                      <button
                        onClick={() => handleQuickDecision(finding.id, 'approved')}
                        className="inline-flex items-center px-3 py-1.5 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-sm transition-colors"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                        <span>Approve Finding</span>
                      </button>
                    )}

                    {finding.review_status !== 'uncertain' && (
                      <button
                        onClick={() => handleQuickDecision(finding.id, 'uncertain')}
                        className="inline-flex items-center px-3 py-1.5 text-xs font-semibold text-purple-700 bg-purple-50 hover:bg-purple-100 border border-purple-200 rounded-lg transition-colors"
                      >
                        <AlertTriangle className="w-3.5 h-3.5 mr-1" />
                        <span>Mark Uncertain</span>
                      </button>
                    )}

                    {finding.review_status !== 'dismissed' && (
                      <button
                        onClick={() => handleQuickDecision(finding.id, 'dismissed')}
                        className="inline-flex items-center px-3 py-1.5 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-200 rounded-lg transition-colors"
                      >
                        <XCircle className="w-3.5 h-3.5 mr-1" />
                        <span>Dismiss Finding</span>
                      </button>
                    )}

                    {finding.review_status !== 'pending' && (
                      <button
                        onClick={() => handleQuickDecision(finding.id, 'pending')}
                        className="text-xs text-slate-500 hover:text-slate-700 underline px-2 py-1"
                      >
                        Reopen
                      </button>
                    )}
                  </div>

                  <button
                    onClick={() => onInspectFinding(finding)}
                    className="inline-flex items-center px-3 py-1.5 text-xs font-semibold text-blue-600 hover:text-blue-800 bg-blue-50/50 hover:bg-blue-100/60 rounded-lg border border-blue-200 transition-colors"
                  >
                    <span>Full Evidence Inspector & Hour Calibration</span>
                  </button>
                </div>

              </div>
            );
          })
        )}
      </div>

    </div>
  );
};
