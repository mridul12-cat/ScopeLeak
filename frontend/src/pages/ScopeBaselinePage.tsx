import React, { useState } from 'react';
import { Project, Contract, ScopeItem } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import {
  Upload,
  FileText,
  CheckCircle,
  Plus,
  Trash2,
  Edit2,
  Sparkles,
  AlertCircle,
  FileCheck2,
} from 'lucide-react';

interface Props {
  project: Project;
  contracts: Contract[];
  scopeItems: ScopeItem[];
  onUploadContract: (file: File) => Promise<void>;
  onExtractBaseline: (contractId?: string) => Promise<void>;
  onConfirmBaseline: () => Promise<void>;
  onAddScopeItem: (item: Partial<ScopeItem>) => Promise<void>;
  onUpdateScopeItem: (id: string, item: Partial<ScopeItem>) => Promise<void>;
  onDeleteScopeItem: (id: string) => Promise<void>;
}

export const ScopeBaselinePage: React.FC<Props> = ({
  project,
  contracts,
  scopeItems,
  onUploadContract,
  onExtractBaseline,
  onConfirmBaseline,
  onAddScopeItem,
  onUpdateScopeItem,
  onDeleteScopeItem,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);

  // Manual Add Scope Item state
  const [showAddModal, setShowAddModal] = useState(false);
  const [itemType, setItemType] = useState<ScopeItem['item_type']>('deliverable');
  const [description, setDescription] = useState('');
  const [sourceClause, setSourceClause] = useState('');
  const [sourceQuote, setSourceQuote] = useState('');
  const [pageNumber, setPageNumber] = useState('1');
  const [sectionRef, setSectionRef] = useState('');

  const latestContract = contracts[0];
  const isBaselineConfirmed = scopeItems.length > 0 && scopeItems.every((s) => s.review_status === 'confirmed');

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;
    setIsUploading(true);
    try {
      await onUploadContract(selectedFile);
      setSelectedFile(null);
    } finally {
      setIsUploading(false);
    }
  };

  const handleExtract = async () => {
    if (!latestContract) return;
    setIsExtracting(true);
    try {
      await onExtractBaseline(latestContract.id);
    } finally {
      setIsExtracting(false);
    }
  };

  const handleConfirm = async () => {
    setIsConfirming(true);
    try {
      await onConfirmBaseline();
    } finally {
      setIsConfirming(false);
    }
  };

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) return;
    await onAddScopeItem({
      item_type: itemType,
      description: description.trim(),
      normalized_description: description.trim().slice(0, 60),
      source_clause_id: sourceClause.trim() || undefined,
      source_quote: sourceQuote.trim() || undefined,
      page_number: parseInt(pageNumber) || 1,
      section_reference: sectionRef.trim() || undefined,
      review_status: 'confirmed',
    });
    setDescription('');
    setSourceClause('');
    setSourceQuote('');
    setShowAddModal(false);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      
      {/* Principle Callout */}
      <div className={`p-4 rounded-xl border flex items-start space-x-3 ${
        isBaselineConfirmed
          ? 'bg-emerald-50/60 border-emerald-200 text-emerald-900'
          : 'bg-amber-50/70 border-amber-200 text-amber-900'
      }`}>
        <AlertCircle className={`w-5 h-5 flex-shrink-0 mt-0.5 ${isBaselineConfirmed ? 'text-emerald-600' : 'text-amber-600'}`} />
        <div className="text-xs space-y-1">
          <p className="font-bold">
            {isBaselineConfirmed ? 'Verified Scope Baseline Active' : 'Human Baseline Verification Required'}
          </p>
          <p className="leading-relaxed opacity-90">
            {isBaselineConfirmed
              ? 'The scope baseline has been explicitly reviewed and confirmed. All incoming client requests will be objectively evaluated against these exact clauses.'
              : 'AI extracts proposed scope clauses, deliverables, and exclusions from uploaded contracts. Review each item below and click "Confirm Baseline" to lock in the authoritative comparison benchmark.'}
          </p>
        </div>
      </div>

      {/* Contract Upload & Extraction Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-slate-100">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Contract Documents</h3>
            <p className="text-xs text-slate-500">Upload PDF, DOCX or text agreements to extract baseline commitments</p>
          </div>

          <form onSubmit={handleUpload} className="flex items-center space-x-2">
            <input
              type="file"
              accept=".pdf,.docx,.doc,.txt"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="text-xs file:mr-2 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-slate-100 file:text-slate-700 hover:file:bg-slate-200 text-slate-500 cursor-pointer"
            />
            <button
              type="submit"
              disabled={!selectedFile || isUploading}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm disabled:opacity-50 transition-colors"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>{isUploading ? 'Uploading...' : 'Upload Contract'}</span>
            </button>
          </form>
        </div>

        {/* Existing Contracts List */}
        <div className="mt-4">
          {contracts.length === 0 ? (
            <div className="text-center py-6 text-xs text-slate-400">
              No contracts uploaded yet. Upload a PDF or DOCX file to begin.
            </div>
          ) : (
            <div className="space-y-3">
              {contracts.map((c) => (
                <div key={c.id} className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                  <div className="flex items-center space-x-3">
                    <FileText className="w-5 h-5 text-blue-600 flex-shrink-0" />
                    <div>
                      <span className="font-bold text-slate-900">{c.filename}</span>
                      <div className="text-[11px] text-slate-500 flex items-center space-x-2 mt-0.5">
                        <span>Uploaded {new Date(c.uploaded_at).toLocaleDateString()}</span>
                        <span>•</span>
                        <span className="font-mono">{c.content_hash.slice(0, 10)}...</span>
                        <span>•</span>
                        <StatusBadge status={c.baseline_review_status} />
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={handleExtract}
                      disabled={isExtracting}
                      className="inline-flex items-center space-x-1 px-3 py-1.5 text-xs font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg transition-colors"
                    >
                      <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                      <span>{isExtracting ? 'Extracting Scope...' : 'Run Scope Extraction'}</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Scope Items Baseline Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50/50">
          <div>
            <h3 className="text-sm font-bold text-slate-900">
              Agreed Scope Baseline Items ({scopeItems.length})
            </h3>
            <p className="text-xs text-slate-500">Deliverables, explicit exclusions, revision limits, and commercial terms</p>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowAddModal(true)}
              className="inline-flex items-center space-x-1 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-100 border border-slate-300 rounded-lg shadow-sm transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Clause Item</span>
            </button>

            {!isBaselineConfirmed && scopeItems.length > 0 && (
              <button
                onClick={handleConfirm}
                disabled={isConfirming}
                className="inline-flex items-center space-x-1 px-3.5 py-1.5 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-sm transition-colors"
              >
                <CheckCircle className="w-3.5 h-3.5" />
                <span>{isConfirming ? 'Confirming...' : 'Confirm Baseline (All Items)'}</span>
              </button>
            )}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-100/70 border-b border-slate-200 text-slate-600 uppercase font-semibold text-[10px] tracking-wider">
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Scope Description & Verbatim Quote</th>
                <th className="py-3 px-4">Clause / Section</th>
                <th className="py-3 px-4">Review Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {scopeItems.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-400">
                    No scope items extracted or added yet. Run extraction from contract or add items manually.
                  </td>
                </tr>
              ) : (
                scopeItems.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3.5 px-4 align-top">
                      <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-bold uppercase ${
                        item.item_type === 'exclusion'
                          ? 'bg-rose-100 text-rose-800'
                          : item.item_type === 'revision_limit'
                          ? 'bg-amber-100 text-amber-800'
                          : item.item_type === 'commercial_term'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-emerald-100 text-emerald-800'
                      }`}>
                        {item.item_type.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 align-top max-w-md">
                      <p className="font-semibold text-slate-900 leading-snug">{item.description}</p>
                      {item.source_quote && (
                        <p className="mt-1 font-mono text-[11px] text-slate-500 italic bg-slate-50 p-2 rounded border border-slate-100">
                          "{item.source_quote}"
                        </p>
                      )}
                    </td>
                    <td className="py-3.5 px-4 align-top whitespace-nowrap">
                      <div className="font-mono text-xs font-semibold text-slate-700">
                        {item.source_clause_id || '-'}
                      </div>
                      <div className="text-[11px] text-slate-400">
                        {item.section_reference || 'General'} (p. {item.page_number || 1})
                      </div>
                    </td>
                    <td className="py-3.5 px-4 align-top whitespace-nowrap">
                      <StatusBadge status={item.review_status} />
                    </td>
                    <td className="py-3.5 px-4 align-top text-right whitespace-nowrap">
                      <div className="flex items-center justify-end space-x-1">
                        {item.review_status !== 'confirmed' && (
                          <button
                            onClick={() => onUpdateScopeItem(item.id, { review_status: 'confirmed' })}
                            className="p-1 text-emerald-600 hover:text-emerald-800"
                            title="Confirm item"
                          >
                            <CheckCircle className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={() => onDeleteScopeItem(item.id)}
                          className="p-1 text-slate-400 hover:text-rose-600"
                          title="Delete item"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Add Clause Item */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-lg w-full p-6 animate-in fade-in duration-150">
            <h3 className="text-base font-bold text-slate-900 mb-1">Add Baseline Scope Item</h3>
            <p className="text-xs text-slate-500 mb-5">Add a verifiable deliverable, exclusion, or revision condition.</p>

            <form onSubmit={handleAddItem} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Scope Item Type *</label>
                <select
                  value={itemType}
                  onChange={(e) => setItemType(e.target.value as any)}
                  className="w-full text-xs rounded-lg border border-slate-300 p-2.5 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 bg-white"
                >
                  <option value="deliverable">Included Deliverable</option>
                  <option value="exclusion">Explicit Exclusion</option>
                  <option value="revision_limit">Revision Limit</option>
                  <option value="milestone">Milestone</option>
                  <option value="commercial_term">Commercial / Billing Term</option>
                  <option value="ambiguous">Ambiguous / Unresolved Term</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Description *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Payment gateway integration strictly excluded."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full text-xs rounded-lg border border-slate-300 p-2.5 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Verbatim Contract Quote</label>
                <textarea
                  rows={2}
                  placeholder="Exact quote from contract document..."
                  value={sourceQuote}
                  onChange={(e) => setSourceQuote(e.target.value)}
                  className="w-full text-xs rounded-lg border border-slate-300 p-2.5 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 font-mono text-[11px]"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Clause ID</label>
                  <input
                    type="text"
                    placeholder="e.g. Clause 4.1"
                    value={sourceClause}
                    onChange={(e) => setSourceClause(e.target.value)}
                    className="w-full text-xs rounded-lg border border-slate-300 p-2.5"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Section Ref</label>
                  <input
                    type="text"
                    placeholder="e.g. Section 4"
                    value={sectionRef}
                    onChange={(e) => setSectionRef(e.target.value)}
                    className="w-full text-xs rounded-lg border border-slate-300 p-2.5"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Page #</label>
                  <input
                    type="number"
                    min="1"
                    value={pageNumber}
                    onChange={(e) => setPageNumber(e.target.value)}
                    className="w-full text-xs rounded-lg border border-slate-300 p-2.5"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3.5 py-2 text-xs font-medium text-slate-600 hover:text-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm"
                >
                  Add Scope Item
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
