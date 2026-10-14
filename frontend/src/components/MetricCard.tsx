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
  let borderClass = 'border-zinc-800';
  let badgeColor = 'bg-zinc-800 text-zinc-300 border border-zinc-700';

  if (variant === 'danger') {
    borderClass = 'border-rose-900/50 bg-rose-950/20';
    badgeColor = 'bg-rose-950/70 text-rose-300 border border-rose-800/60';
  } else if (variant === 'success') {
    borderClass = 'border-emerald-900/50 bg-emerald-950/20';
    badgeColor = 'bg-emerald-950/70 text-emerald-300 border border-emerald-800/60';
  } else if (variant === 'warning') {
    borderClass = 'border-amber-900/50 bg-amber-950/20';
    badgeColor = 'bg-amber-950/70 text-amber-300 border border-amber-800/60';
  }

  return (
    <div className={`p-5 bg-zinc-950 rounded-xl border ${borderClass} shadow-sm transition-all hover:border-zinc-700`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">{title}</span>
        {icon && <div className="text-zinc-400">{icon}</div>}
      </div>
      <div className="flex items-baseline space-x-2">
        <span className="text-2xl font-bold tracking-tight text-white">{value}</span>
        {badge && (
          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${badgeColor}`}>
            {badge}
          </span>
        )}
      </div>
      {subtitle && <p className="mt-1 text-xs text-zinc-400">{subtitle}</p>}
    </div>
  );
};
