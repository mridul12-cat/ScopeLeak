import React from 'react';

interface Props {
  title: string;
  value: string;
  subtitle?: string;
  icon?: React.ReactNode;
  badge?: string;
  variant?: 'default' | 'danger' | 'success' | 'warning';
}

export const MetricCard: React.FC<Props> = ({
  title,
  value,
  subtitle,
  icon,
  badge,
  variant = 'default',
}) => {
  let borderClass = 'border-slate-200';
  let badgeColor = 'bg-slate-100 text-slate-700';

  if (variant === 'danger') {
    borderClass = 'border-rose-200 bg-rose-50/20';
    badgeColor = 'bg-rose-100 text-rose-800';
  } else if (variant === 'success') {
    borderClass = 'border-emerald-200 bg-emerald-50/20';
    badgeColor = 'bg-emerald-100 text-emerald-800';
  } else if (variant === 'warning') {
    borderClass = 'border-amber-200 bg-amber-50/20';
    badgeColor = 'bg-amber-100 text-amber-800';
  }

  return (
    <div className={`p-5 bg-white rounded-xl border ${borderClass} shadow-sm transition-all hover:shadow-md`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{title}</span>
        {icon && <div className="text-slate-400">{icon}</div>}
      </div>
      <div className="flex items-baseline space-x-2">
        <span className="text-2xl font-bold tracking-tight text-slate-900">{value}</span>
        {badge && (
          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${badgeColor}`}>
            {badge}
          </span>
        )}
      </div>
      {subtitle && <p className="mt-1 text-xs text-slate-500">{subtitle}</p>}
    </div>
  );
};
