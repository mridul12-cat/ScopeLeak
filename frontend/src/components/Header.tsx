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
    <header className="h-16 bg-black border-b border-zinc-800 px-8 flex items-center justify-between flex-shrink-0 z-10 text-white">
      <div>
        <h1 className="text-lg font-bold text-white tracking-tight">{title}</h1>
        {subtitle && <p className="text-xs text-zinc-400">{subtitle}</p>}
      </div>

      <div className="flex items-center space-x-4">
        {/* AI Engine Status Badge */}
        {healthStatus && (
          <div className="hidden lg:flex items-center">
            {healthStatus.gemini_configured ? (
              <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 bg-emerald-950/60 border border-emerald-800/80 text-emerald-400 text-xs font-semibold rounded-lg shadow-sm" title={`Active model: ${healthStatus.gemini_model}`}>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>🤖 Gemini Live ({healthStatus.gemini_model})</span>
              </span>
            ) : (
              <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 bg-zinc-900 border border-zinc-800 text-zinc-300 text-xs font-semibold rounded-lg shadow-sm" title="Zero hallucinated quotes — strictly grounded deterministic evidence">
                <span className="w-2 h-2 rounded-full bg-zinc-500"></span>
                <span>⚙️ Deterministic Fallback</span>
              </span>
            )}
          </div>
        )}

        {currentProject && (
          <div className="hidden sm:flex items-center space-x-3 px-3 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-xs">
            <div className="flex items-center text-zinc-200 font-medium">
              <Building className="w-3.5 h-3.5 mr-1.5 text-zinc-400" />
              <span>{currentProject.client_name}</span>
            </div>
            <span className="text-zinc-600">|</span>
            <div className="flex items-center text-zinc-200 font-medium">
              <DollarSign className="w-3.5 h-3.5 mr-0.5 text-zinc-400" />
              <span>
                {currentProject.currency} {currentProject.default_hourly_rate.toLocaleString()}/hr
              </span>
            </div>
          </div>
        )}

        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="p-2 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors"
          title="Refresh view"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-blue-400' : ''}`} />
        </button>

        <button
          onClick={onLoadDemo}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-amber-300 bg-amber-950/50 hover:bg-amber-900/60 border border-amber-800/80 rounded-lg transition-colors shadow-sm"
          title="Reload the Northstar Website Redesign synthetic demo dataset"
        >
          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
          <span>Load Demo Project</span>
        </button>
      </div>
    </header>
  );
};
