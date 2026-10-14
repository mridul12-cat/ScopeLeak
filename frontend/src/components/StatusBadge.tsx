import React from 'react';

interface Props {
  status: string;
  type?: 'classification' | 'review' | 'order' | 'generic';
}

export const StatusBadge: React.FC<Props> = ({ status, type = 'generic' }) => {
  let colorClasses = 'bg-zinc-800 text-zinc-300 border-zinc-700';
  let label = status.replace(/_/g, ' ');

  // Classification styling
  if (status === 'likely_out_of_scope') {
    colorClasses = 'bg-rose-950/70 text-rose-300 border-rose-800/60 font-semibold';
    label = 'Likely Out of Scope';
  } else if (status === 'likely_in_scope') {
    colorClasses = 'bg-emerald-950/70 text-emerald-300 border-emerald-800/60 font-semibold';
    label = 'Likely In Scope';
  } else if (status === 'ambiguous') {
    colorClasses = 'bg-amber-950/70 text-amber-300 border-amber-800/60 font-semibold';
    label = 'Ambiguous / Unresolved';
  }
  // Review Status
  else if (status === 'approved' || status === 'accepted_by_client') {
    colorClasses = 'bg-emerald-950/70 text-emerald-300 border-emerald-800/60';
    label = status === 'accepted_by_client' ? 'Client Accepted' : 'Approved (Freelancer)';
  } else if (status === 'pending' || status === 'draft' || status === 'ready_for_review') {
    colorClasses = 'bg-amber-950/70 text-amber-300 border-amber-800/60';
    label = status === 'ready_for_review' ? 'Ready For Review' : status === 'draft' ? 'Draft' : 'Pending Review';
  } else if (status === 'dismissed' || status === 'declined' || status === 'rejected') {
    colorClasses = 'bg-zinc-800 text-zinc-400 border-zinc-700';
    label = status === 'declined' ? 'Declined' : status === 'dismissed' ? 'Dismissed' : 'Rejected';
  } else if (status === 'uncertain') {
    colorClasses = 'bg-purple-950/70 text-purple-300 border-purple-800/60';
    label = 'Marked Uncertain';
  } else if (status === 'confirmed') {
    colorClasses = 'bg-blue-950/70 text-blue-300 border-blue-800/60';
    label = 'Baseline Confirmed';
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border capitalize ${colorClasses}`}>
      <span className="w-1.5 h-1.5 mr-1.5 rounded-full bg-current opacity-70"></span>
      {label}
    </span>
  );
};
