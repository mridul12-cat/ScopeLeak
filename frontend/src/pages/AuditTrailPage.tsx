import React, { useState } from 'react';
import { Project, AuditEvent } from '../types';
import { History, User, Bot, Clock, Search, Filter } from 'lucide-react';

interface Props {
  project: Project;
  auditEvents: AuditEvent[];
}

export const AuditTrailPage: React.FC<Props> = ({ project, auditEvents }) => {
  const [filterActor, setFilterActor] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredEvents = auditEvents.filter((ev) => {
    if (filterActor !== 'all' && ev.actor.toLowerCase() !== filterActor.toLowerCase()) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchDesc = (ev.description || '').toLowerCase().includes(q);
      const matchType = ev.event_type.toLowerCase().includes(q);
      if (!matchDesc && !matchType) return false;
    }
    return true;
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900">Immutable Audit Trail</h2>
          <p className="text-xs text-slate-500">
            Verifiable log distinguishing system inferences from human decisions and before/after states
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 flex flex-wrap items-center justify-between gap-4 shadow-sm">
        <div className="flex items-center space-x-3 text-xs">
          <span className="font-semibold text-slate-600">Actor Filter:</span>
          <select
            value={filterActor}
            onChange={(e) => setFilterActor(e.target.value)}
            className="text-xs rounded-lg border border-slate-300 py-1.5 px-2 bg-white focus:border-blue-500"
          >
            <option value="all">All Actors</option>
            <option value="system">System / AI Inferences</option>
            <option value="user">User / Human Decisions</option>
            <option value="Lead Developer">Lead Developer</option>
          </select>
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
          <input
            type="text"
            placeholder="Search audit trail..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full text-xs rounded-lg border border-slate-300 pl-8 pr-3 py-1.5 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Timeline List */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="divide-y divide-slate-100">
          {filteredEvents.length === 0 ? (
            <div className="p-12 text-center text-xs text-slate-400">
              No audit events found matching the search criteria.
            </div>
          ) : (
            filteredEvents.map((ev) => {
              const isSystem = ev.actor.toLowerCase() === 'system' || ev.actor.toLowerCase() === 'gemini_ai';

              return (
                <div key={ev.id} className="p-5 hover:bg-slate-50/60 transition-colors">
                  <div className="flex items-start justify-between gap-4">
                    
                    <div className="flex items-start space-x-3">
                      <div className={`p-2 rounded-lg mt-0.5 ${
                        isSystem ? 'bg-slate-100 text-slate-600' : 'bg-blue-50 text-blue-600'
                      }`}>
                        {isSystem ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
                      </div>

                      <div className="space-y-1">
                        <div className="flex items-center space-x-2 text-xs">
                          <span className="font-bold text-slate-900">{ev.actor}</span>
                          <span className="text-slate-300">•</span>
                          <span className="font-mono text-[11px] text-slate-500 bg-slate-100 px-1.5 py-0.2 rounded">
                            {ev.event_type}
                          </span>
                          <span className="text-slate-300">•</span>
                          <span className="text-slate-400 text-[11px]">
                            {ev.entity_type} ({ev.entity_id.slice(0, 8)})
                          </span>
                        </div>

                        <p className="text-xs text-slate-800 font-medium leading-relaxed">
                          {ev.description || ev.event_type}
                        </p>

                        {/* Before / After State Diff */}
                        {(ev.before_state || ev.after_state) && (
                          <div className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] font-mono bg-slate-50 p-2.5 rounded border border-slate-200">
                            {ev.before_state && (
                              <div>
                                <span className="font-bold text-rose-600 block mb-0.5">Before:</span>
                                <pre className="text-slate-600 whitespace-pre-wrap">{JSON.stringify(ev.before_state, null, 1)}</pre>
                              </div>
                            )}
                            {ev.after_state && (
                              <div>
                                <span className="font-bold text-emerald-600 block mb-0.5">After:</span>
                                <pre className="text-slate-600 whitespace-pre-wrap">{JSON.stringify(ev.after_state, null, 1)}</pre>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="text-right text-[11px] text-slate-400 whitespace-nowrap">
                      {new Date(ev.timestamp).toLocaleString([], {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </div>

                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

    </div>
  );
};
