import React from 'react';
import {
  LayoutDashboard,
  FolderGit2,
  FileCheck2,
  MessageSquareText,
  Clock,
  ShieldAlert,
  Coins,
  FileSpreadsheet,
  History,
  Sparkles,
  Layers,
  ChevronDown,
  PlusCircle,
} from 'lucide-react';
import { Project, HealthStatus } from '../types';

export type NavSection =
  | 'overview'
  | 'projects'
  | 'contract_scope'
  | 'requests'
  | 'work'
  | 'findings'
  | 'impact'
  | 'change_orders'
  | 'audit';

interface Props {
  currentSection: NavSection;
  onSelectSection: (section: NavSection) => void;
  projects: Project[];
  currentProject: Project | null;
  onSelectProject: (proj: Project) => void;
  onOpenCreateProject: () => void;
  onLoadDemo: () => void;
  health: HealthStatus | null;
}

export const Sidebar: React.FC<Props> = ({
  currentSection,
  onSelectSection,
  projects,
  currentProject,
  onSelectProject,
  onOpenCreateProject,
  onLoadDemo,
  health,
}) => {
  const navItems: { id: NavSection; label: string; icon: React.ReactNode; badge?: string }[] = [
    { id: 'overview', label: 'Overview', icon: <LayoutDashboard className="w-4 h-4" /> },
    { id: 'projects', label: 'Projects', icon: <FolderGit2 className="w-4 h-4" /> },
    { id: 'contract_scope', label: 'Contract & Scope', icon: <FileCheck2 className="w-4 h-4" /> },
    { id: 'requests', label: 'Requests & Evidence', icon: <MessageSquareText className="w-4 h-4" /> },
    { id: 'work', label: 'Work Tracking', icon: <Clock className="w-4 h-4" /> },
    { id: 'findings', label: 'Findings Review', icon: <ShieldAlert className="w-4 h-4" /> },
    { id: 'impact', label: 'Financial Impact', icon: <Coins className="w-4 h-4" /> },
    { id: 'change_orders', label: 'Change Orders', icon: <FileSpreadsheet className="w-4 h-4" /> },
    { id: 'audit', label: 'Audit Trail', icon: <History className="w-4 h-4" /> },
  ];

  return (
    <aside className="w-64 bg-black text-zinc-300 flex flex-col flex-shrink-0 border-r border-zinc-800 select-none">
      
      {/* Brand Header */}
      <div className="p-5 border-b border-zinc-800">
        <div className="flex items-center space-x-2.5">
          <div className="w-9 h-9 bg-blue-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white tracking-tight leading-none">ScopeLeak</h1>
            <p className="text-[10px] text-zinc-400 mt-1 font-medium">Evidence Engine</p>
          </div>
        </div>
      </div>

      {/* Project Switcher */}
      <div className="p-3 border-b border-zinc-800 bg-zinc-950/70">
        <label className="block text-[10px] font-semibold text-zinc-400 uppercase tracking-wider mb-1 px-1">
          Active Project
        </label>
        <div className="relative">
          <select
            value={currentProject?.id || ''}
            onChange={(e) => {
              const selected = projects.find((p) => p.id === e.target.value);
              if (selected) onSelectProject(selected);
            }}
            className="w-full bg-zinc-900 border border-zinc-800 text-white text-xs rounded-lg px-2.5 py-2 pr-7 appearance-none focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer font-medium truncate"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.currency})
              </option>
            ))}
            {projects.length === 0 && <option value="">No Projects</option>}
          </select>
          <ChevronDown className="w-3.5 h-3.5 text-zinc-400 absolute right-2.5 top-3 pointer-events-none" />
        </div>

        <div className="mt-2 flex items-center justify-between px-1">
          <button
            onClick={onOpenCreateProject}
            className="text-[11px] text-blue-400 hover:text-blue-300 font-medium inline-flex items-center space-x-1"
          >
            <PlusCircle className="w-3 h-3" />
            <span>New Project</span>
          </button>

          <button
            onClick={onLoadDemo}
            className="text-[11px] text-amber-400 hover:text-amber-300 font-medium inline-flex items-center space-x-1"
            title="Load Northstar Studio Redesign Synthetic Project"
          >
            <Sparkles className="w-3 h-3" />
            <span>Load Demo</span>
          </button>
        </div>
      </div>

      {/* Navigation List */}
      <nav className="flex-1 overflow-y-auto p-3 space-y-1">
        {navItems.map((item) => {
          const isActive = currentSection === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectSection(item.id)}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors text-left ${
                isActive
                  ? 'bg-blue-600 text-white shadow-sm font-semibold'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-800/70'
              }`}
            >
              <span className={isActive ? 'text-white' : 'text-zinc-400'}>{item.icon}</span>
              <span className="flex-1 truncate">{item.label}</span>
              {item.badge && (
                <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-zinc-800 text-zinc-300">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* AI & Engine Status Footer */}
      <div className="p-4 border-t border-zinc-800 bg-zinc-950/80 text-xs">
        <div className="flex items-center justify-between text-[11px] text-zinc-400 mb-1.5">
          <span>AI Engine</span>
          {health?.gemini_configured ? (
            <span className="inline-flex items-center text-emerald-400 text-[10px] font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1 animate-pulse"></span>
              Live Gemini API
            </span>
          ) : (
            <span className="inline-flex items-center text-amber-400 text-[10px] font-medium" title="Deterministic engine active; add GEMINI_API_KEY for live model inference">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mr-1"></span>
              Deterministic Mode
            </span>
          )}
        </div>
        <p className="text-[10px] text-zinc-500 leading-tight">
          Contract references verified deterministically.
        </p>
      </div>

    </aside>
  );
};
