import React from 'react';

interface Props {
  status: string;
  type?: 'classification' | 'review' | 'order' | 'generic';
}

export const StatusBadge: React.FC<Props> = ({ status, type = 'generic' }) => {
  let colorClasses = 'bg-slate-100 text-slate-700 border-slate-200';
  let label = status.replace(/_/g, ' ');

  // Classification styling
  if (status === 'likely_out_of_scope') {
    colorClasses = 'bg-rose-50 text-rose-700 border-rose-200 font-semibold';
    label = 'Likely Out of Scope';
  } else if (status === 'likely_in_scope') {
    colorClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200 font-semibold';
    label = 'Likely In Scope';
  } else if (status === 'ambiguous') {
    colorClasses = 'bg-amber-50 text-amber-700 border-amber-200 font-semibold';
    label = 'Ambiguous / Unresolved';
  }
  // Review Status
  else if (status === 'approved' || status === 'accepted_by_client') {
    colorClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200';
    label = status === 'accepted_by_client' ? 'Client Accepted' : 'Approved (Freelancer)';
  } else if (status === 'pending' || status === 'draft' || status === 'ready_for_review') {
    colorClasses = 'bg-amber-50 text-amber-700 border-amber-200';
    label = status === 'ready_for_review' ? 'Ready For Review' : status === 'draft' ? 'Draft' : 'Pending Review';
  } else if (status === 'dismissed' || status === 'declined' || status === 'rejected') {
    colorClasses = 'bg-slate-100 text-slate-600 border-slate-200';
    label = status === 'declined' ? 'Declined' : status === 'dismissed' ? 'Dismissed' : 'Rejected';
  } else if (status === 'uncertain') {
    colorClasses = 'bg-purple-50 text-purple-700 border-purple-200';
    label = 'Marked Uncertain';
  } else if (status === 'confirmed') {
    colorClasses = 'bg-blue-50 text-blue-700 border-blue-200';
    label = 'Baseline Confirmed';
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border capitalize ${colorClasses}`}>
      <span className="w-1.5 h-1.5 mr-1.5 rounded-full bg-current opacity-70"></span>
      {label}
    </span>
  );
};
