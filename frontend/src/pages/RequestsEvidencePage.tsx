import React, { useState } from 'react';
import { Project, ClientRequest, Finding, ScopeItem } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import {
  MessageSquare,
  Sparkles,
  Plus,
  Upload,
  Calendar,
  User,
  ArrowRight,
  ShieldAlert,
  Search,
} from 'lucide-react';

interface Props {
  project: Project;
  requests: ClientRequest[];
  findings: Finding[];
  scopeItems: ScopeItem[];
  onCreateRequest: (text: string, sender?: string) => Promise<void>;
  onImportRequests: (messages: { message_text: string; sender?: string }[]) => Promise<void>;
  onAnalyzeRequests: () => Promise<void>;
  onInspectFinding: (f: Finding) => void;
}

export const RequestsEvidencePage: React.FC<Props> = ({
  project,
  requests,
  findings,
  scopeItems,
  onCreateRequest,
  onImportRequests,
  onAnalyzeRequests,
  onInspectFinding,
}) => {
  const [singleMessage, setSingleMessage] = useState('');
  const [senderName, setSenderName] = useState('Client');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [csvText, setCsvText] = useState('');
  const [showCsvModal, setShowCsvModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const findingByRequestId = new Map(findings.map((f) => [f.request_id, f]));

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!singleMessage.trim()) return;
    setIsSubmitting(true);
    try {
      await onCreateRequest(singleMessage.trim(), senderName.trim() || 'Client');
      setSingleMessage('');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    try {
      await onAnalyzeRequests();
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleCsvImport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!csvText.trim()) return;
    const lines = csvText.trim().split('\n');
    const messages: { message_text: string; sender?: string }[] = [];
    for (const line of lines) {
      if (!line.trim()) continue;
      const parts = line.split(',');
      if (parts.length >= 2) {
        messages.push({ sender: parts[0].trim(), message_text: parts.slice(1).join(',').trim() });
      } else {
        messages.push({ message_text: parts[0].trim(), sender: 'Client' });
      }
    }
    if (messages.length > 0) {
      await onImportRequests(messages);
      setCsvText('');
      setShowCsvModal(false);
    }
  };

  const filteredRequests = requests.filter((r) =>
    r.message_text.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (r.sender && r.sender.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      
      {/* Top Banner & Primary Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900">Client Requests & Evidence Log</h2>
          <p className="text-xs text-slate-500">
            Log incoming requests from Slack, email, or tickets to interpret against the agreed contract baseline
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowCsvModal(true)}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 rounded-lg shadow-sm transition-colors"
          >
            <Upload className="w-3.5 h-3.5 text-slate-500" />
            <span>Import CSV</span>
          </button>

          <button
            onClick={handleAnalyze}
            disabled={isAnalyzing || requests.length === 0}
            className="inline-flex items-center space-x-1.5 px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm disabled:opacity-50 transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{isAnalyzing ? 'Analyzing Scope...' : 'Analyze All Requests'}</span>
          </button>
        </div>
      </div>

      {/* Quick Ingestion Form */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
        <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">
          Log New Incoming Client Message
        </h3>
        <form onSubmit={handleCreate} className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <div className="sm:col-span-1">
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">Sender</label>
              <input
                type="text"
                placeholder="e.g. Aarav Mehta (Product Lead)"
                value={senderName}
                onChange={(e) => setSenderName(e.target.value)}
                className="w-full text-xs rounded-lg border border-slate-300 p-2 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
            </div>
            <div className="sm:col-span-3">
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">Original Message Text *</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  required
                  placeholder='e.g. "Can we also add customer order-history before launching?"'
                  value={singleMessage}
                  onChange={(e) => setSingleMessage(e.target.value)}
                  className="flex-1 text-xs rounded-lg border border-slate-300 p-2 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 font-medium"
                />
                <button
                  type="submit"
                  disabled={isSubmitting || !singleMessage.trim()}
                  className="px-4 py-2 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg shadow-sm whitespace-nowrap disabled:opacity-50 transition-colors"
                >
                  {isSubmitting ? 'Logging...' : 'Log Request'}
                </button>
              </div>
            </div>
          </div>
        </form>
      </div>

      {/* Requests Listing with Evidence Connection */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50/50">
          <div className="flex items-center space-x-2">
            <h3 className="text-sm font-bold text-slate-900">
              Captured Messages ({filteredRequests.length})
            </h3>
            <span className="text-xs text-slate-400">• Preserves verbatim text & sender timestamp</span>
          </div>

          <div className="relative w-full sm:w-64">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
            <input
              type="text"
              placeholder="Search message text..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full text-xs rounded-lg border border-slate-300 pl-8 pr-3 py-1.5 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="divide-y divide-slate-100">
          {filteredRequests.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-400">
              No matching client requests found. Log a message or import from CSV above.
            </div>
          ) : (
            filteredRequests.map((req) => {
              const finding = findingByRequestId.get(req.id);
              const primaryEv = finding?.evidence_references?.[0];

              return (
                <div key={req.id} className="p-5 hover:bg-slate-50/60 transition-colors">
                  <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                    
                    {/* Message details */}
                    <div className="space-y-2 flex-1">
                      <div className="flex items-center space-x-2 text-xs text-slate-500">
                        <span className="font-semibold text-slate-800">{req.sender || 'Client'}</span>
                        <span>•</span>
                        <span className="capitalize">{req.external_source}</span>
                        {req.message_timestamp && (
                          <>
                            <span>•</span>
                            <span>{new Date(req.message_timestamp).toLocaleDateString()}</span>
                          </>
                        )}
                      </div>

                      <blockquote className="text-sm font-semibold text-slate-900 italic">
                        "{req.message_text}"
                      </blockquote>

                      {/* AI finding connection */}
                      {finding ? (
                        <div className="mt-2.5 p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs space-y-1.5">
                          <div className="flex items-center space-x-2">
                            <StatusBadge status={finding.classification} />
                            <span className="text-[11px] font-mono text-slate-600 bg-white px-2 py-0.5 rounded border border-slate-200">
                              {primaryEv?.ref || 'Clause Ref'}
                            </span>
                            <span className="text-[11px] text-slate-500">
                              Confidence: {(finding.confidence * 100).toFixed(0)}%
                            </span>
                          </div>
                          <p className="text-slate-700 font-medium leading-relaxed">
                            {finding.explanation}
                          </p>
                        </div>
                      ) : (
                        <div className="text-xs text-slate-400 italic">
                          Not analyzed yet. Click "Analyze All Requests" above.
                        </div>
                      )}
                    </div>

                    {/* Action buttons */}
                    <div className="flex items-center space-x-2 flex-shrink-0">
                      {finding && (
                        <button
                          onClick={() => onInspectFinding(finding)}
                          className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg transition-colors"
                        >
                          <ShieldAlert className="w-3.5 h-3.5 text-blue-600" />
                          <span>Inspect Evidence</span>
                        </button>
                      )}
                    </div>

                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Modal: CSV Import */}
      {showCsvModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-lg w-full p-6 animate-in fade-in duration-150">
            <h3 className="text-base font-bold text-slate-900 mb-1">Batch Import Client Messages (CSV)</h3>
            <p className="text-xs text-slate-500 mb-4">
              Paste lines in <code className="bg-slate-100 px-1 py-0.5 rounded">Sender,Message Text</code> format or one message per line.
            </p>

            <form onSubmit={handleCsvImport} className="space-y-4">
              <textarea
                rows={6}
                required
                placeholder="Aarav Mehta,Can you add Stripe checkout before launch?&#10;Priya Sharma,Can we also add a customer order-history page?"
                value={csvText}
                onChange={(e) => setCsvText(e.target.value)}
                className="w-full text-xs font-mono rounded-lg border border-slate-300 p-3 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />

              <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowCsvModal(false)}
                  className="px-3.5 py-2 text-xs font-medium text-slate-600 hover:text-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm"
                >
                  Import Messages
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
