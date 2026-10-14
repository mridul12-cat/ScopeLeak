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
          <h2 className="text-base font-bold text-white">Findings Review & Decision Hub</h2>
          <p className="text-xs text-zinc-400">
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
      <div className="bg-zinc-950 p-4 rounded-xl border border-zinc-800 flex flex-wrap items-center justify-between gap-4 shadow-sm">
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <div className="flex items-center space-x-2">
            <Filter className="w-3.5 h-3.5 text-zinc-400" />
            <span className="font-semibold text-zinc-300">Classification:</span>
            <select
              value={filterClassification}
              onChange={(e) => setFilterClassification(e.target.value)}
              className="text-xs rounded-lg border border-zinc-700 py-1.5 px-2 bg-zinc-900 text-white focus:border-blue-500"
            >
              <option value="all">All Classifications</option>
              <option value="likely_out_of_scope">Likely Out of Scope</option>
              <option value="likely_in_scope">Likely In Scope</option>
              <option value="ambiguous">Ambiguous</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <span className="font-semibold text-zinc-300">Review Status:</span>
            <select
              value={filterReviewStatus}
              onChange={(e) => setFilterReviewStatus(e.target.value)}
              className="text-xs rounded-lg border border-zinc-700 py-1.5 px-2 bg-zinc-900 text-white focus:border-blue-500"
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
          <Search className="w-3.5 h-3.5 text-zinc-400 absolute left-2.5 top-2.5" />
          <input
            type="text"
            placeholder="Search findings or text..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full text-xs rounded-lg border border-zinc-700 bg-zinc-900 text-white pl-8 pr-3 py-1.5 focus:border-blue-500 placeholder-zinc-500"
          />
        </div>
      </div>

      {/* Findings List */}
      <div className="space-y-4">
        {filteredFindings.length === 0 ? (
          <div className="p-12 text-center bg-zinc-950 rounded-xl border border-dashed border-zinc-800 text-xs text-zinc-400">
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
                className="p-5 bg-zinc-950 rounded-xl border border-zinc-800 shadow-sm transition-all hover:border-zinc-700 space-y-4"
              >
                {/* Header Row */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-zinc-800">
                  <div className="flex items-center space-x-2.5">
                    <StatusBadge status={finding.classification} />
                    <span className="text-zinc-600">•</span>
                    <span className="text-xs text-zinc-400">
                      Confidence: <strong className="text-zinc-200">{(finding.confidence * 100).toFixed(0)}%</strong>
                    </span>
                    {finding.estimated_extra_hours && (
                      <span className="text-xs font-bold text-rose-300 bg-rose-950/70 px-2 py-0.5 rounded-full border border-rose-800/60">
                        +{finding.estimated_extra_hours} hrs ({curr} {estVal.toLocaleString()})
                      </span>
                    )}
                    {finding.provider_source === 'gemini_live' ? (
                      <span className="text-[10px] font-semibold text-emerald-300 bg-emerald-950/70 px-2 py-0.5 rounded-full border border-emerald-800/60">
                        🤖 Gemini Live AI
                      </span>
                    ) : (
                      <span className="text-[10px] font-semibold text-zinc-300 bg-zinc-800 px-2 py-0.5 rounded-full border border-zinc-700">
                        ⚙️ Deterministic Fallback
                      </span>
                    )}
                  </div>

                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-zinc-400">Workflow Decision:</span>
                    <StatusBadge status={finding.review_status} />
                  </div>
                </div>

                {/* Evidence Comparison Preview */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  
                  {/* Left: Client Message */}
                  <div className="p-3 bg-zinc-900/90 rounded-lg border border-zinc-800 space-y-1">
                    <div className="flex items-center space-x-1.5 text-blue-400 font-bold text-[10px] uppercase tracking-wider">
                      <MessageSquare className="w-3.5 h-3.5" />
                      <span>Client Message ({req?.sender || 'Client'})</span>
                    </div>
                    <blockquote className="font-semibold text-white italic">
                      "{req?.message_text || 'Message text unavailable'}"
                    </blockquote>
                  </div>

                  {/* Right: Contract Quote */}
                  <div className="p-3 bg-zinc-900/90 rounded-lg border border-zinc-800 space-y-1">
                    <div className="flex items-center justify-between text-zinc-400 font-bold text-[10px] uppercase tracking-wider">
                      <span className="flex items-center space-x-1.5">
                        <FileText className="w-3.5 h-3.5" />
                        <span>Contract Evidence</span>
                      </span>
                      <span className="font-mono bg-black px-1.5 py-0.2 rounded border border-zinc-800 text-zinc-300">
                        {primaryEv?.ref || 'Clause Ref'}
                      </span>
                    </div>
                    <p className="font-mono text-[11px] text-zinc-300 italic">
                      "{primaryEv?.quote || 'No direct clause quote matching. Ambiguous terms.'}"
                    </p>
                  </div>

                </div>

                {/* AI Explanation & Reviewer Notes */}
                <div className="text-xs space-y-1">
                  <p className="text-zinc-300 font-medium leading-relaxed">
                    <strong className="text-white">Analysis:</strong> {finding.explanation}
                  </p>
                  {finding.reviewer_notes && (
                    <p className="text-zinc-400 italic">
                      <strong className="text-zinc-300 not-italic">Reviewer Notes:</strong> {finding.reviewer_notes}
                    </p>
                  )}
                </div>

                {/* Action Bar */}
                <div className="pt-3 border-t border-zinc-800 flex flex-wrap items-center justify-between gap-3">
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
                        className="inline-flex items-center px-3 py-1.5 text-xs font-semibold text-purple-300 bg-purple-950/50 hover:bg-purple-900/70 border border-purple-800/80 rounded-lg transition-colors"
                      >
                        <AlertTriangle className="w-3.5 h-3.5 mr-1" />
                        <span>Mark Uncertain</span>
                      </button>
                    )}

                    {finding.review_status !== 'dismissed' && (
                      <button
                        onClick={() => handleQuickDecision(finding.id, 'dismissed')}
                        className="inline-flex items-center px-3 py-1.5 text-xs font-semibold text-zinc-300 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg transition-colors"
                      >
                        <XCircle className="w-3.5 h-3.5 mr-1" />
                        <span>Dismiss Finding</span>
                      </button>
                    )}

                    {finding.review_status !== 'pending' && (
                      <button
                        onClick={() => handleQuickDecision(finding.id, 'pending')}
                        className="text-xs text-zinc-400 hover:text-zinc-200 underline px-2 py-1"
                      >
                        Reopen
                      </button>
                    )}
                  </div>

                  <button
                    onClick={() => onInspectFinding(finding)}
                    className="inline-flex items-center px-3 py-1.5 text-xs font-semibold text-blue-400 hover:text-blue-300 bg-blue-950/50 hover:bg-blue-900/70 rounded-lg border border-blue-800/80 transition-colors"
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
