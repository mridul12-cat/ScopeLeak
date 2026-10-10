import React from 'react';
import { Project, FinancialImpact } from '../types';
import { MetricCard } from '../components/MetricCard';
import { StatusBadge } from '../components/StatusBadge';
import {
  Coins,
  AlertTriangle,
  CheckCircle2,
  FileSpreadsheet,
  ShieldCheck,
  Info,
} from 'lucide-react';

interface Props {
  project: Project;
  impact: FinancialImpact | null;
}

export const FinancialImpactPage: React.FC<Props> = ({ project, impact }) => {
  const curr = project.currency || 'INR';

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      
      {/* Principle Notice */}
      <div className="p-4 bg-slate-900 text-slate-200 rounded-xl border border-slate-800 text-xs flex items-start space-x-3 shadow-sm">
        <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-bold text-white">Transparent Financial Governance</p>
          <p className="text-slate-300 leading-relaxed">
            All amounts are computed deterministically using billable hours multiplied by agreed hourly rates.
            Estimated amounts are clearly distinguished from legally executed change orders.
            Values are never misrepresented as guaranteed revenue or recoverable debt until approved and signed.
          </p>
        </div>
      </div>

      {/* Primary Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard
          title="Potential Unapproved Exposure"
          value={`${curr} ${(impact?.potential_unapproved_value || 0).toLocaleString()}`}
          subtitle={`${impact?.potential_unapproved_hours || 0} total hours`}
          badge="Estimate at Risk"
          variant="danger"
          icon={<AlertTriangle className="w-4 h-4 text-rose-500" />}
        />

        <MetricCard
          title="Draft Change Orders"
          value={`${curr} ${(impact?.draft_change_order_value || 0).toLocaleString()}`}
          subtitle="Awaiting submission"
          badge="In Progress"
          variant="warning"
          icon={<FileSpreadsheet className="w-4 h-4 text-amber-500" />}
        />

        <MetricCard
          title="Freelancer Approved"
          value={`${curr} ${(impact?.approved_by_freelancer_value || 0).toLocaleString()}`}
          subtitle="Sent to client"
          badge="Pending Signature"
          variant="default"
          icon={<Coins className="w-4 h-4 text-blue-500" />}
        />

        <MetricCard
          title="Client Accepted Total"
          value={`${curr} ${(impact?.accepted_by_client_value || 0).toLocaleString()}`}
          subtitle="Legally locked addendums"
          badge="Secured"
          variant="success"
          icon={<CheckCircle2 className="w-4 h-4 text-emerald-500" />}
        />
      </div>

      {/* Rate notice if missing rates */}
      {impact && impact.items_with_missing_rates_count > 0 && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800 flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
          <span>
            Notice: {impact.items_with_missing_rates_count} item(s) have unspecified custom rates; defaulted to project baseline ({curr} {project.default_hourly_rate}/hr).
          </span>
        </div>
      )}

      {/* Detailed Per-Item Financial Breakdown */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/50">
          <h3 className="text-sm font-bold text-slate-900">
            Deduplicated Financial Item Breakdown ({impact?.breakdown?.length || 0})
          </h3>
          <p className="text-xs text-slate-500">
            Item-by-item calculation of billable hours, rates, and approval status
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-100/70 border-b border-slate-200 text-slate-600 uppercase font-semibold text-[10px] tracking-wider">
                <th className="py-3 px-4">Item / Scope Description</th>
                <th className="py-3 px-4">Hours (Type)</th>
                <th className="py-3 px-4">Hourly Rate</th>
                <th className="py-3 px-4">Line Total</th>
                <th className="py-3 px-4">Scope Classification</th>
                <th className="py-3 px-4">Approval State</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {!impact?.breakdown || impact.breakdown.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400">
                    No financial line items recorded. Add work items or analyze client requests.
                  </td>
                </tr>
              ) : (
                impact.breakdown.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3.5 px-4 font-semibold text-slate-900 max-w-sm">
                      {item.description}
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <span className="font-bold text-slate-900">{item.hours} hrs</span>{' '}
                      <span className="text-[10px] font-semibold text-slate-500 uppercase">
                        ({item.hours_type})
                      </span>
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap font-mono text-slate-700">
                      {curr} {item.hourly_rate.toLocaleString()}
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap font-bold text-slate-900">
                      {curr} {item.line_total.toLocaleString()}
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      {item.finding_classification ? (
                        <StatusBadge status={item.finding_classification} />
                      ) : (
                        <span className="text-slate-400 italic">Direct Task</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <StatusBadge status={item.approval_status} />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
            {impact?.breakdown && impact.breakdown.length > 0 && (
              <tfoot>
                <tr className="bg-slate-50 border-t-2 border-slate-200 font-bold text-slate-900">
                  <td className="py-3 px-4">Total Potential Exposure</td>
                  <td className="py-3 px-4">{impact.potential_unapproved_hours} hrs</td>
                  <td className="py-3 px-4">-</td>
                  <td className="py-3 px-4 text-rose-700 font-bold">
                    {curr} {impact.potential_unapproved_value.toLocaleString()}
                  </td>
                  <td colSpan={2} className="py-3 px-4 text-right text-xs text-slate-500 font-normal">
                    * Subject to human approval and executed addendum
                  </td>
                </tr>
              </tfoot>
            )}
          </table>
        </div>
      </div>

    </div>
  );
};
