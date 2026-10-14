import React, { useState } from 'react';
import { Project } from '../types';
import { FolderGit2, Plus, Sparkles, Building, Coins, Calendar, Trash2, ArrowRight } from 'lucide-react';

interface Props {
  projects: Project[];
  currentProject: Project | null;
  onSelectProject: (proj: Project) => void;
  onCreateProject: (data: Partial<Project>) => Promise<void>;
  onDeleteProject: (id: string) => Promise<void>;
  onLoadDemo: () => void;
}

export const ProjectsPage: React.FC<Props> = ({
  projects,
  currentProject,
  onSelectProject,
  onCreateProject,
  onDeleteProject,
  onLoadDemo,
}) => {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [name, setName] = useState('');
  const [clientName, setClientName] = useState('');
  const [currency, setCurrency] = useState('INR');
  const [rate, setRate] = useState('2000');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !clientName.trim()) return;
    setIsSubmitting(true);
    try {
      await onCreateProject({
        name: name.trim(),
        client_name: clientName.trim(),
        currency: currency.trim() || 'INR',
        default_hourly_rate: parseFloat(rate) || 2000.0,
        description: description.trim(),
      });
      setName('');
      setClientName('');
      setDescription('');
      setShowCreateModal(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      
      {/* Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-white">Projects Directory</h2>
          <p className="text-xs text-zinc-400">Manage client contracts, hourly rates, and scope baselines</p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={onLoadDemo}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold text-amber-300 bg-amber-950/60 hover:bg-amber-900/80 border border-amber-800/80 rounded-lg shadow-sm transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>Load Northstar Demo</span>
          </button>

          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Create Project</span>
          </button>
        </div>
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {projects.map((proj) => {
          const isSelected = currentProject?.id === proj.id;
          return (
            <div
              key={proj.id}
              className={`p-5 rounded-xl border bg-zinc-950 shadow-sm transition-all hover:border-zinc-700 flex flex-col justify-between ${
                isSelected ? 'border-blue-500 ring-2 ring-blue-500/20' : 'border-zinc-800'
              }`}
            >
              <div>
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <span className="text-[10px] font-bold text-blue-400 uppercase tracking-wider">
                      {proj.currency}
                    </span>
                    <h3 className="text-base font-bold text-white leading-snug">{proj.name}</h3>
                  </div>
                  {isSelected && (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-950/70 text-blue-300 border border-blue-800/60">
                      Active
                    </span>
                  )}
                </div>

                <div className="mt-4 space-y-2 text-xs text-zinc-400">
                  <div className="flex items-center">
                    <Building className="w-3.5 h-3.5 mr-2 text-zinc-500" />
                    <span>Client: <strong className="text-zinc-200">{proj.client_name}</strong></span>
                  </div>
                  <div className="flex items-center">
                    <Coins className="w-3.5 h-3.5 mr-2 text-zinc-500" />
                    <span>Rate: <strong className="text-zinc-200">{proj.currency} {proj.default_hourly_rate.toLocaleString()}/hr</strong></span>
                  </div>
                  <div className="flex items-center">
                    <Calendar className="w-3.5 h-3.5 mr-2 text-zinc-500" />
                    <span>Created: {new Date(proj.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                {proj.description && (
                  <p className="mt-3 text-xs text-zinc-400 line-clamp-2 italic">
                    "{proj.description}"
                  </p>
                )}
              </div>

              <div className="mt-6 pt-4 border-t border-zinc-800/80 flex items-center justify-between">
                <button
                  onClick={() => onSelectProject(proj)}
                  className={`inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                    isSelected
                      ? 'bg-blue-950/70 text-blue-300 border border-blue-800/60 hover:bg-blue-900/80'
                      : 'bg-zinc-800 text-white hover:bg-zinc-700'
                  }`}
                >
                  <span>{isSelected ? 'Currently Viewing' : 'Switch to Project'}</span>
                  <ArrowRight className="w-3 h-3" />
                </button>

                <button
                  onClick={() => {
                    if (confirm(`Delete project "${proj.name}"? This removes all associated records.`)) {
                      onDeleteProject(proj.id);
                    }
                  }}
                  className="p-1.5 text-zinc-400 hover:text-rose-400 rounded-md transition-colors"
                  title="Delete project"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal: Create Project */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-zinc-950 rounded-2xl shadow-xl border border-zinc-800 max-w-md w-full p-6 animate-in fade-in duration-150">
            <h3 className="text-base font-bold text-white mb-1">Create New Project</h3>
            <p className="text-xs text-zinc-400 mb-5">Define the project details and baseline hourly rate.</p>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-zinc-300 mb-1">Project Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Apex E-Commerce Platform"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full text-xs rounded-lg border border-zinc-700 bg-zinc-900 text-white p-2.5 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 placeholder-zinc-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-300 mb-1">Client Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Apex Brands Inc"
                  value={clientName}
                  onChange={(e) => setClientName(e.target.value)}
                  className="w-full text-xs rounded-lg border border-zinc-700 bg-zinc-900 text-white p-2.5 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 placeholder-zinc-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-1">Currency</label>
                  <select
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value)}
                    className="w-full text-xs rounded-lg border border-zinc-700 bg-zinc-900 text-white p-2.5 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="INR">INR (₹)</option>
                    <option value="USD">USD ($)</option>
                    <option value="EUR">EUR (€)</option>
                    <option value="GBP">GBP (£)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-1">Default Hourly Rate *</label>
                  <input
                    type="number"
                    step="100"
                    required
                    value={rate}
                    onChange={(e) => setRate(e.target.value)}
                    className="w-full text-xs rounded-lg border border-zinc-700 bg-zinc-900 text-white p-2.5 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-300 mb-1">Project Scope Summary</label>
                <textarea
                  rows={2}
                  placeholder="Summary of primary contract deliverables..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full text-xs rounded-lg border border-zinc-700 bg-zinc-900 text-white p-2.5 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 placeholder-zinc-500"
                />
              </div>

              <div className="flex items-center justify-end space-x-2 pt-3 border-t border-zinc-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3.5 py-2 text-xs font-medium text-zinc-400 hover:text-zinc-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm"
                >
                  {isSubmitting ? 'Creating...' : 'Create Project'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
