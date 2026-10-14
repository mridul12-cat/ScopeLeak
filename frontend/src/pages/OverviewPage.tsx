import React from 'react';
import { Project, Finding, FinancialImpact, ChangeOrder, AuditEvent } from '../types';
import { MetricCard } from '../components/MetricCard';
import { StatusBadge } from '../components/StatusBadge';
import {
  ShieldAlert,
  Coins,
  FileSpreadsheet,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  History,
} from 'lucide-react';
import { NavSection } from '../components/Sidebar';

interface Props {
  project: Project | null;
  findings: Finding[];
  impact: FinancialImpact | null;
  changeOrders: ChangeOrder[];
  auditEvents: AuditEvent[];
  onNavigate: (section: NavSection) => void;
  onInspectFinding: (f: Finding) => void;
  onLoadDemo: () => void;
}

export const OverviewPage: React.FC<Props> = ({
  project,
  findings,
  impact,
  changeOrders,
  auditEvents,
  onNavigate,
  onInspectFinding,
  onLoadDemo,
}) => {
  if (!project) {
    return (
      <div className="p-8 text-center bg-white rounded-xl border border-slate-200">
        <h2 className="text-lg font-bold text-slate-900 mb-2">Welcome to ScopeLeak</h2>
        <p className="text-sm text-slate-500 mb-6">
          Catch unpaid work before it becomes part of the project.
        </p>
        <button
          onClick={onLoadDemo}
          className="inline-flex items-center space-x-2 px-5 py-2.5 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 shadow-md"
        >
          <Sparkles className="w-4 h-4" />
          <span>Load Northstar Demo Project</span>
        </button>
      </div>
    );
  }

  const curr = project.currency || 'INR';
  const pendingFindings = findings.filter((f) => f.review_status === 'pending');
  const outOfScopeFindings = findings.filter((f) => f.classification === 'likely_out_of_scope');

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      
      {/* Top Banner / Callout */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 text-white rounded-2xl p-6 sm:p-8 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-full bg-blue-500/20 text-blue-300 text-xs font-semibold mb-3">
            <span>Project: {project.name}</span>
            <span>•</span>
            <span>Client: {project.client_name}</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
            Catch unpaid work with contract-grounded evidence.
          </h2>
          <p className="mt-2 text-xs sm:text-sm text-slate-300 max-w-2xl leading-relaxed">
            AI interprets client messages against the confirmed contract baseline. You maintain full deterministic control over rates, hours, and change-order creation.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto">
          <button
            onClick={() => onNavigate('findings')}
            className="inline-flex items-center justify-center px-4 py-2.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-xl shadow-sm transition-all"
          >
            <span>Review Scope Findings ({findings.length})</span>
            <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
          </button>
          <button
            onClick={() => onNavigate('change_orders')}
            className="inline-flex items-center justify-center px-4 py-2.5 text-xs font-semibold text-slate-200 bg-slate-800/80 hover:bg-slate-700 border border-slate-700 rounded-xl transition-all"
          >
            <span>Change Orders</span>
          </button>
        </div>
      </div>

      {/* Primary Financial & Scope Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard
          title="Potential Unapproved Work"
          value={`${curr} ${(impact?.potential_unapproved_value || 0).toLocaleString()}`}
          subtitle={`${impact?.potential_unapproved_hours || 0} estimated or logged hours`}
          badge="Estimate"
          variant="danger"
          icon={<AlertTriangle className="w-4 h-4 text-rose-500" />}
        />

        <MetricCard
          title="Change Orders in Draft"
          value={`${curr} ${(impact?.draft_change_order_value || 0).toLocaleString()}`}
          subtitle={`${changeOrders.filter(c => c.status === 'draft' || c.status === 'ready_for_review').length} drafts created`}
          badge="Internal Draft"
          variant="warning"
          icon={<FileSpreadsheet className="w-4 h-4 text-amber-500" />}
        />

        <MetricCard
          title="Client Accepted Value"
          value={`${curr} ${(impact?.accepted_by_client_value || 0).toLocaleString()}`}
          subtitle="Confirmed signed addendums"
          badge="Secured"
          variant="success"
          icon={<CheckCircle2 className="w-4 h-4 text-emerald-500" />}
        />

        <MetricCard
          title="Pending Scope Findings"
          value={`${pendingFindings.length} / ${findings.length}`}
          subtitle={`${outOfScopeFindings.length} flagged out-of-scope`}
          badge={pendingFindings.length > 0 ? "Action Needed" : "All Reviewed"}
          variant={pendingFindings.length > 0 ? "warning" : "default"}
          icon={<ShieldAlert className="w-4 h-4 text-blue-500" />}
        />
      </div>

      {/* Two Column Grid: Critical Scope Findings vs Recent Audit Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Left 2 Cols: Critical Findings requiring review */}
        <div className="lg:col-span-2 bg-zinc-950 rounded-xl border border-zinc-800 overflow-hidden shadow-sm">
          <div className="px-6 py-4 border-b border-zinc-800 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white">Key Scope Findings</h3>
              <p className="text-xs text-zinc-400">Incoming requests interpreted against original contract commitments</p>
            </div>
            <button
              onClick={() => onNavigate('findings')}
              className="text-xs font-semibold text-blue-400 hover:text-blue-300 inline-flex items-center space-x-1"
            >
              <span>View All</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="divide-y divide-zinc-800/80">
            {findings.length === 0 ? (
              <div className="p-8 text-center text-xs text-zinc-500">
                No scope findings generated yet. Upload a contract and analyze requests.
              </div>
            ) : (
              findings.slice(0, 4).map((f) => {
                const primaryEv = f.evidence_references?.[0];
                return (
                  <div key={f.id} className="p-5 hover:bg-zinc-900/40 transition-colors flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                    <div className="space-y-1.5 flex-1">
                      <div className="flex items-center space-x-2">
                        <StatusBadge status={f.classification} />
                        <span className="text-xs font-mono text-zinc-300 bg-black px-1.5 py-0.5 rounded border border-zinc-800">
                          {primaryEv?.ref || 'Clause Ref'}
                        </span>
                        {f.estimated_extra_hours && (
                          <span className="text-xs font-semibold text-rose-300 bg-rose-950/70 px-2 py-0.5 rounded-full border border-rose-800/60">
                            +{f.estimated_extra_hours} hrs ({curr} {((f.estimated_value || (f.estimated_extra_hours * project.default_hourly_rate))).toLocaleString()})
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-zinc-300 font-medium leading-relaxed">
                        {f.explanation}
                      </p>
                    </div>

                    <div className="flex items-center space-x-2 flex-shrink-0">
                      <button
                        onClick={() => onInspectFinding(f)}
                        className="px-3 py-1.5 text-xs font-semibold text-zinc-200 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg transition-colors"
                      >
                        Inspect Evidence
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right 1 Col: Audit Trail Highlights */}
        <div className="bg-zinc-950 rounded-xl border border-zinc-800 overflow-hidden shadow-sm flex flex-col">
          <div className="px-6 py-4 border-b border-zinc-800 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white">Audit Trail</h3>
              <p className="text-xs text-zinc-400">Human & system actions</p>
            </div>
            <button
              onClick={() => onNavigate('audit')}
              className="text-xs font-semibold text-blue-400 hover:text-blue-300"
            >
              Full Log
            </button>
          </div>

          <div className="p-4 flex-1 space-y-3 overflow-y-auto max-h-[360px]">
            {auditEvents.length === 0 ? (
              <p className="text-xs text-zinc-500 text-center py-6">No audit activity logged yet.</p>
            ) : (
              auditEvents.slice(0, 5).map((ev) => (
                <div key={ev.id} className="text-xs border-l-2 border-zinc-700 pl-3 py-1 space-y-0.5">
                  <div className="flex items-center justify-between text-zinc-500 text-[10px]">
                    <span className="font-semibold text-zinc-300 capitalize">{ev.actor}</span>
                    <span>{new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                  <p className="text-zinc-300 font-medium line-clamp-2">{ev.description || ev.event_type}</p>
                </div>
              ))
            )}
          </div>
        </div>

      </div>

    </div>
  );
};
