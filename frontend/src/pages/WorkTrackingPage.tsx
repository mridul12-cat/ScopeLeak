import React, { useState } from 'react';
import { Project, WorkItem, ClientRequest } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import {
  Clock,
  Plus,
  Upload,
  Link as LinkIcon,
  CheckCircle2,
  AlertTriangle,
  Trash2,
  Search,
} from 'lucide-react';

interface Props {
  project: Project;
  workItems: WorkItem[];
  requests: ClientRequest[];
  onCreateWorkItem: (item: Partial<WorkItem>) => Promise<void>;
  onImportWorkItems: (items: Partial<WorkItem>[]) => Promise<void>;
  onUpdateWorkItem: (id: string, item: Partial<WorkItem>) => Promise<void>;
  onDeleteWorkItem: (id: string) => Promise<void>;
}

export const WorkTrackingPage: React.FC<Props> = ({
  project,
  workItems,
  requests,
  onCreateWorkItem,
  onImportWorkItems,
  onUpdateWorkItem,
  onDeleteWorkItem,
}) => {
  const [showAddModal, setShowAddModal] = useState(false);
  const [showCsvModal, setShowCsvModal] = useState(false);
  const [description, setDescription] = useState('');
  const [estimatedHours, setEstimatedHours] = useState('0');
  const [actualHours, setActualHours] = useState('');
  const [rate, setRate] = useState(project.default_hourly_rate.toString());
  const [workStatus, setWorkStatus] = useState('logged');
  const [approvalStatus, setApprovalStatus] = useState('unapproved');
  const [selectedRequestId, setSelectedRequestId] = useState('');
  const [sourceRef, setSourceRef] = useState('');
  const [csvText, setCsvText] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const curr = project.currency || 'INR';
  const requestById = new Map(requests.map((r) => [r.id, r]));

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) return;
    await onCreateWorkItem({
      description: description.trim(),
      estimated_hours: parseFloat(estimatedHours) || undefined,
      actual_hours: actualHours ? parseFloat(actualHours) : undefined,
      hourly_rate: parseFloat(rate) || project.default_hourly_rate,
      work_status: workStatus,
      approval_status: approvalStatus,
      request_id: selectedRequestId || undefined,
      source_reference: sourceRef.trim() || undefined,
      source_type: 'manual',
    });
    setDescription('');
    setEstimatedHours('0');
    setActualHours('');
    setSelectedRequestId('');
    setSourceRef('');
    setShowAddModal(false);
  };

  const handleCsvImport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!csvText.trim()) return;
    const lines = csvText.trim().split('\n');
    const items: Partial<WorkItem>[] = [];
    for (const line of lines) {
      if (!line.trim()) continue;
      const parts = line.split(',');
      if (parts.length >= 2) {
        items.push({
          description: parts[0].trim(),
          estimated_hours: parseFloat(parts[1]) || 0,
          actual_hours: parts[2] ? parseFloat(parts[2]) : undefined,
          hourly_rate: project.default_hourly_rate,
          approval_status: 'unapproved',
          source_type: 'csv_import',
        });
      }
    }
    if (items.length > 0) {
      await onImportWorkItems(items);
      setCsvText('');
      setShowCsvModal(false);
    }
  };

  const filteredItems = workItems.filter((w) =>
    w.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      
      {/* Top Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-white">Work & Timesheet Records</h2>
          <p className="text-xs text-zinc-400">
            Track planned vs actual work, link tasks to client requests, and identify unapproved scope
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowCsvModal(true)}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold text-zinc-200 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg shadow-sm transition-colors"
          >
            <Upload className="w-3.5 h-3.5 text-zinc-400" />
            <span>Import CSV</span>
          </button>

          <button
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Work Item</span>
          </button>
        </div>
      </div>

      {/* Work Table */}
      <div className="bg-zinc-950 rounded-xl border border-zinc-800 overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-zinc-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-zinc-900/40">
          <div className="flex items-center space-x-2">
            <h3 className="text-sm font-bold text-white">
              Work Items Logged ({filteredItems.length})
            </h3>
            <span className="text-xs text-zinc-400">• Clear distinction between estimates and actual logged time</span>
          </div>

          <div className="relative w-full sm:w-64">
            <Search className="w-3.5 h-3.5 text-zinc-400 absolute left-2.5 top-2.5" />
            <input
              type="text"
              placeholder="Search work items..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full text-xs rounded-lg border border-zinc-700 bg-zinc-900 text-white pl-8 pr-3 py-1.5 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 placeholder-zinc-500"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-zinc-900 border-b border-zinc-800 text-zinc-400 uppercase font-semibold text-[10px] tracking-wider">
                <th className="py-3 px-4">Task Description</th>
                <th className="py-3 px-4">Linked Request</th>
                <th className="py-3 px-4">Hours (Type)</th>
                <th className="py-3 px-4">Rate</th>
                <th className="py-3 px-4">Line Total</th>
                <th className="py-3 px-4">Approval Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/80">
              {filteredItems.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-zinc-500">
                    No work items found. Add tasks or import from timesheet CSV.
                  </td>
                </tr>
              ) : (
                filteredItems.map((item) => {
                  const linkedReq = item.request_id ? requestById.get(item.request_id) : null;
                  const effectiveHours = item.actual_hours !== undefined && item.actual_hours !== null && item.actual_hours > 0
                    ? item.actual_hours
                    : item.estimated_hours || 0;
                  const isLogged = item.actual_hours !== undefined && item.actual_hours !== null && item.actual_hours > 0;
                  const effectiveRate = item.hourly_rate ?? project.default_hourly_rate;
                  const lineTotal = effectiveHours * effectiveRate;

                  return (
                    <tr key={item.id} className="hover:bg-zinc-900/60 transition-colors">
                      <td className="py-3.5 px-4 align-top max-w-xs">
                        <p className="font-semibold text-white leading-snug">{item.description}</p>
                        {item.source_reference && (
                          <p className="text-[11px] text-zinc-400 font-mono mt-0.5">{item.source_reference}</p>
                        )}
                      </td>
                      <td className="py-3.5 px-4 align-top max-w-xs">
                        {linkedReq ? (
                          <div className="flex items-center space-x-1.5 text-blue-400 bg-blue-950/60 px-2 py-1 rounded border border-blue-800/60">
                            <LinkIcon className="w-3 h-3 flex-shrink-0" />
                            <span className="truncate italic">"{linkedReq.message_text}"</span>
                          </div>
                        ) : (
                          <span className="text-zinc-500 italic">Unlinked</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 align-top whitespace-nowrap">
                        <span className="font-bold text-white">{effectiveHours} hrs</span>
                        <span className={`ml-1.5 text-[10px] font-semibold px-1.5 py-0.2 rounded border ${
                          isLogged ? 'bg-emerald-950/70 text-emerald-300 border-emerald-800/60' : 'bg-zinc-800 text-zinc-300 border-zinc-700'
                        }`}>
                          {isLogged ? 'Actual Logged' : 'Estimated'}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 align-top whitespace-nowrap font-mono text-zinc-300">
                        {curr} {effectiveRate.toLocaleString()}
                      </td>
                      <td className="py-3.5 px-4 align-top whitespace-nowrap font-bold text-white">
                        {curr} {lineTotal.toLocaleString()}
                      </td>
                      <td className="py-3.5 px-4 align-top whitespace-nowrap">
                        <StatusBadge status={item.approval_status} />
                      </td>
                      <td className="py-3.5 px-4 align-top text-right whitespace-nowrap">
                        <button
                          onClick={() => onDeleteWorkItem(item.id)}
                          className="p-1 text-zinc-400 hover:text-rose-400"
                          title="Delete work item"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Add Work Item */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-zinc-950 rounded-2xl shadow-xl border border-zinc-800 max-w-lg w-full p-6 animate-in fade-in duration-150">
            <h3 className="text-base font-bold text-white mb-1">Add Work Item / Task</h3>
            <p className="text-xs text-zinc-400 mb-5">Record hours, rate, and link to client request if applicable.</p>

            <form onSubmit={handleAdd} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-zinc-300 mb-1">Task Description *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Stripe checkout API integration and webhook handler"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full text-xs rounded-lg border border-zinc-700 bg-zinc-900 text-white p-2.5 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 placeholder-zinc-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-300 mb-1">Link to Client Request</label>
                <select
                  value={selectedRequestId}
                  onChange={(e) => setSelectedRequestId(e.target.value)}
                  className="w-full text-xs rounded-lg border border-zinc-700 bg-zinc-900 text-white p-2.5 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">None (Unlinked task)</option>
                  {requests.map((r) => (
                    <option key={r.id} value={r.id}>
                      [{r.sender}] {r.message_text.slice(0, 50)}...
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-1">Estimated Hours</label>
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    value={estimatedHours}
                    onChange={(e) => setEstimatedHours(e.target.value)}
                    className="w-full text-xs rounded-lg border border-zinc-700 bg-zinc-900 text-white p-2.5"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-1">Actual Logged Hours</label>
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    placeholder="Leave empty if not logged yet"
                    value={actualHours}
                    onChange={(e) => setActualHours(e.target.value)}
                    className="w-full text-xs rounded-lg border border-zinc-700 bg-zinc-900 text-white p-2.5 placeholder-zinc-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-1">Hourly Rate ({curr})</label>
                  <input
                    type="number"
                    step="100"
                    value={rate}
                    onChange={(e) => setRate(e.target.value)}
                    className="w-full text-xs rounded-lg border border-zinc-700 bg-zinc-900 text-white p-2.5"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-1">Approval Status</label>
                  <select
                    value={approvalStatus}
                    onChange={(e) => setApprovalStatus(e.target.value)}
                    className="w-full text-xs rounded-lg border border-zinc-700 bg-zinc-900 text-white p-2.5"
                  >
                    <option value="unapproved">Unapproved Extra Work</option>
                    <option value="pending_review">Pending Review</option>
                    <option value="approved">Approved</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-300 mb-1">Source Reference / Git Commit</label>
                <input
                  type="text"
                  placeholder="e.g. Commit 7f83a21 or Timesheet Entry #41"
                  value={sourceRef}
                  onChange={(e) => setSourceRef(e.target.value)}
                  className="w-full text-xs rounded-lg border border-zinc-700 bg-zinc-900 text-white p-2.5 font-mono text-[11px] placeholder-zinc-500"
                />
              </div>

              <div className="flex items-center justify-end space-x-2 pt-3 border-t border-zinc-800">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3.5 py-2 text-xs font-medium text-zinc-400 hover:text-zinc-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm"
                >
                  Save Work Item
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: CSV Import */}
      {showCsvModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-zinc-950 rounded-2xl shadow-xl border border-zinc-800 max-w-lg w-full p-6 animate-in fade-in duration-150">
            <h3 className="text-base font-bold text-white mb-1">Import Timesheet Entries (CSV)</h3>
            <p className="text-xs text-zinc-400 mb-4">
              Format: <code className="bg-zinc-900 px-1 py-0.5 rounded border border-zinc-800 text-zinc-300">Task Description,Estimated Hours,Actual Hours</code>
            </p>

            <form onSubmit={handleCsvImport} className="space-y-4">
              <textarea
                rows={6}
                required
                placeholder="Stripe checkout API integration,8,0&#10;Fix mobile navigation viewport,1.5,1.5"
                value={csvText}
                onChange={(e) => setCsvText(e.target.value)}
                className="w-full text-xs font-mono rounded-lg border border-zinc-700 bg-zinc-900 text-white p-3 placeholder-zinc-500"
              />

              <div className="flex items-center justify-end space-x-2 pt-2 border-t border-zinc-800">
                <button
                  type="button"
                  onClick={() => setShowCsvModal(false)}
                  className="px-3.5 py-2 text-xs font-medium text-zinc-400 hover:text-zinc-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm"
                >
                  Import Entries
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
