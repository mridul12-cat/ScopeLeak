import React from 'react';
import { Project, HealthStatus } from '../types';
import { RefreshCw, Sparkles, Building, DollarSign } from 'lucide-react';

interface Props {
  title: string;
  subtitle?: string;
  currentProject: Project | null;
  onRefresh: () => void;
  isLoading: boolean;
  onLoadDemo: () => void;
  healthStatus?: HealthStatus | null;
}

export const Header: React.FC<Props> = ({
  title,
  subtitle,
  currentProject,
  onRefresh,
  isLoading,
  onLoadDemo,
  healthStatus,
}) => {
  return (
    <header className="h-16 bg-white border-b border-slate-200 px-8 flex items-center justify-between flex-shrink-0 z-10">
      <div>
        <h1 className="text-lg font-bold text-slate-900 tracking-tight">{title}</h1>
        {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
      </div>

      <div className="flex items-center space-x-4">
        {/* AI Engine Status Badge */}
        {healthStatus && (
          <div className="hidden lg:flex items-center">
            {healthStatus.gemini_configured ? (
              <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-semibold rounded-lg shadow-sm" title={`Active model: ${healthStatus.gemini_model}`}>
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>🤖 Gemini Live ({healthStatus.gemini_model})</span>
              </span>
            ) : (
              <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 bg-slate-100 border border-slate-200 text-slate-600 text-xs font-semibold rounded-lg shadow-sm" title="Zero hallucinated quotes — strictly grounded deterministic evidence">
                <span className="w-2 h-2 rounded-full bg-slate-400"></span>
                <span>⚙️ Deterministic Fallback</span>
              </span>
            )}
          </div>
        )}

        {currentProject && (
          <div className="hidden sm:flex items-center space-x-3 px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs">
            <div className="flex items-center text-slate-700 font-medium">
              <Building className="w-3.5 h-3.5 mr-1.5 text-slate-400" />
              <span>{currentProject.client_name}</span>
            </div>
            <span className="text-slate-300">|</span>
            <div className="flex items-center text-slate-700 font-medium">
              <DollarSign className="w-3.5 h-3.5 mr-0.5 text-slate-400" />
              <span>
                {currentProject.currency} {currentProject.default_hourly_rate.toLocaleString()}/hr
              </span>
            </div>
          </div>
        )}

        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
          title="Refresh view"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-blue-600' : ''}`} />
        </button>

        <button
          onClick={onLoadDemo}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-amber-50 hover:bg-amber-100 border border-amber-200/80 rounded-lg transition-colors shadow-sm"
          title="Reload the Northstar Website Redesign synthetic demo dataset"
        >
          <Sparkles className="w-3.5 h-3.5 text-amber-600" />
          <span>Load Demo Project</span>
        </button>
      </div>
    </header>
  );
};
