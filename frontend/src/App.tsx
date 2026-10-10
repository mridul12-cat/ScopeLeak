import React, { useState, useEffect } from 'react';
import { api } from './api/client';
import {
  Project,
  Contract,
  ScopeItem,
  ClientRequest,
  WorkItem,
  Finding,
  ChangeOrder,
  FinancialImpact,
  AuditEvent,
  HealthStatus,
} from './types';
import { Sidebar, NavSection } from './components/Sidebar';
import { Header } from './components/Header';
import { EvidenceComparisonModal } from './components/EvidenceComparisonModal';

// Pages
import { OverviewPage } from './pages/OverviewPage';
import { ProjectsPage } from './pages/ProjectsPage';
import { ScopeBaselinePage } from './pages/ScopeBaselinePage';
import { RequestsEvidencePage } from './pages/RequestsEvidencePage';
import { WorkTrackingPage } from './pages/WorkTrackingPage';
import { FindingsReviewPage } from './pages/FindingsReviewPage';
import { FinancialImpactPage } from './pages/FinancialImpactPage';
import { ChangeOrdersPage } from './pages/ChangeOrdersPage';
import { AuditTrailPage } from './pages/AuditTrailPage';

export const App: React.FC = () => {
  const [currentSection, setCurrentSection] = useState<NavSection>('overview');
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [currentProject, setCurrentProject] = useState<Project | null>(null);

  // Active Project Data
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [scopeItems, setScopeItems] = useState<ScopeItem[]>([]);
  const [requests, setRequests] = useState<ClientRequest[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [workItems, setWorkItems] = useState<WorkItem[]>([]);
  const [impact, setImpact] = useState<FinancialImpact | null>(null);
  const [changeOrders, setChangeOrders] = useState<ChangeOrder[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);

  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [activeModalFinding, setActiveModalFinding] = useState<Finding | null>(null);
  const [isEvidenceModalOpen, setIsEvidenceModalOpen] = useState(false);

  // Initial load
  useEffect(() => {
    loadInitialData();
  }, []);

  // When active project changes, fetch its data
  useEffect(() => {
    if (currentProject) {
      loadProjectData(currentProject.id);
    }
  }, [currentProject?.id]);

  const loadInitialData = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const [h, projs] = await Promise.all([
        api.getHealth().catch(() => null),
        api.getProjects(),
      ]);
      setHealth(h);
      setProjects(projs);

      if (projs.length > 0) {
        // Prefer Northstar demo if exists, else first project
        const demoProj = projs.find((p) => p.name.includes('Northstar'));
        setCurrentProject(demoProj || projs[0]);
      } else {
        // Automatically seed demo project so hackathon reviewers see rich data immediately
        const demo = await api.seedDemoProject(false);
        setProjects([demo]);
        setCurrentProject(demo);
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to initialize app');
    } finally {
      setIsLoading(false);
    }
  };

  const loadProjectData = async (projectId: string) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const [c, s, r, f, w, imp, co, aud] = await Promise.all([
        api.getContracts(projectId).catch(() => []),
        api.getBaseline(projectId).catch(() => []),
        api.getRequests(projectId).catch(() => []),
        api.getFindings(projectId).catch(() => []),
        api.getWorkItems(projectId).catch(() => []),
        api.getFinancialImpact(projectId).catch(() => null),
        api.getChangeOrders(projectId).catch(() => []),
        api.getAuditTrail(projectId).catch(() => []),
      ]);
      setContracts(c);
      setScopeItems(s);
      setRequests(r);
      setFindings(f);
      setWorkItems(w);
      setImpact(imp);
      setChangeOrders(co);
      setAuditEvents(aud);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load project details');
    } finally {
      setIsLoading(false);
    }
  };

  // Actions
  const handleLoadDemo = async () => {
    setIsLoading(true);
    try {
      const demo = await api.seedDemoProject(true); // force reset to pristine state
      const projs = await api.getProjects();
      setProjects(projs);
      setCurrentProject(demo);
      await loadProjectData(demo.id);
      setCurrentSection('overview');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to seed demo project');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateProject = async (data: Partial<Project>) => {
    const created = await api.createProject(data);
    const updated = await api.getProjects();
    setProjects(updated);
    setCurrentProject(created);
    setCurrentSection('overview');
  };

  const handleDeleteProject = async (id: string) => {
    await api.deleteProject(id);
    const updated = await api.getProjects();
    setProjects(updated);
    if (currentProject?.id === id) {
      setCurrentProject(updated[0] || null);
    }
  };

  const handleUploadContract = async (file: File) => {
    if (!currentProject) return;
    await api.uploadContract(currentProject.id, file);
    await loadProjectData(currentProject.id);
  };

  const handleExtractBaseline = async (contractId?: string) => {
    if (!currentProject) return;
    await api.extractBaseline(currentProject.id, contractId);
    await loadProjectData(currentProject.id);
  };

  const handleConfirmBaseline = async () => {
    if (!currentProject) return;
    await api.confirmBaseline(currentProject.id);
    await loadProjectData(currentProject.id);
  };

  const handleAddScopeItem = async (item: Partial<ScopeItem>) => {
    if (!currentProject) return;
    await api.addScopeItem(currentProject.id, item);
    await loadProjectData(currentProject.id);
  };

  const handleUpdateScopeItem = async (id: string, item: Partial<ScopeItem>) => {
    if (!currentProject) return;
    await api.updateScopeItem(currentProject.id, id, item);
    await loadProjectData(currentProject.id);
  };

  const handleDeleteScopeItem = async (id: string) => {
    if (!currentProject) return;
    await api.deleteScopeItem(currentProject.id, id);
    await loadProjectData(currentProject.id);
  };

  const handleCreateRequest = async (text: string, sender?: string) => {
    if (!currentProject) return;
    await api.createRequest(currentProject.id, text, sender);
    await loadProjectData(currentProject.id);
  };

  const handleImportRequests = async (messages: { message_text: string; sender?: string }[]) => {
    if (!currentProject) return;
    await api.importRequests(currentProject.id, messages);
    await loadProjectData(currentProject.id);
  };

  const handleAnalyzeRequests = async () => {
    if (!currentProject) return;
    await api.analyzeRequests(currentProject.id);
    await loadProjectData(currentProject.id);
  };

  const handleUpdateFindingReview = async (findingId: string, status: string, notes: string, hours?: number) => {
    if (!currentProject) return;
    await api.updateFindingReview(findingId, {
      review_status: status,
      reviewer_notes: notes,
      estimated_extra_hours: hours,
    });
    await loadProjectData(currentProject.id);
  };

  const handleCreateWorkItem = async (item: Partial<WorkItem>) => {
    if (!currentProject) return;
    await api.createWorkItem(currentProject.id, item);
    await loadProjectData(currentProject.id);
  };

  const handleImportWorkItems = async (items: Partial<WorkItem>[]) => {
    if (!currentProject) return;
    await api.importWorkItems(currentProject.id, items);
    await loadProjectData(currentProject.id);
  };

  const handleUpdateWorkItem = async (id: string, item: Partial<WorkItem>) => {
    if (!currentProject) return;
    await api.updateWorkItem(currentProject.id, id, item);
    await loadProjectData(currentProject.id);
  };

  const handleDeleteWorkItem = async (id: string) => {
    if (!currentProject) return;
    await api.deleteWorkItem(currentProject.id, id);
    await loadProjectData(currentProject.id);
  };

  const handleCreateChangeOrder = async (data: { title: string; finding_ids?: string[]; tax_rate_percent?: number }) => {
    if (!currentProject) return;
    await api.createChangeOrder(currentProject.id, data);
    await loadProjectData(currentProject.id);
  };

  const handleUpdateChangeOrder = async (id: string, data: Partial<ChangeOrder>) => {
    if (!currentProject) return;
    await api.updateChangeOrder(id, data);
    await loadProjectData(currentProject.id);
  };

  const handleDownloadPdf = async (id: string, filename: string) => {
    await api.downloadChangeOrderPdf(id, filename);
  };

  const handleInspectFinding = (finding: Finding) => {
    setActiveModalFinding(finding);
    setIsEvidenceModalOpen(true);
  };

  // Section titles
  const sectionMeta: Record<NavSection, { title: string; subtitle: string }> = {
    overview: {
      title: 'Project Overview',
      subtitle: 'Active scope commitments, unapproved work value, and critical findings',
    },
    projects: {
      title: 'Projects Directory',
      subtitle: 'Manage client accounts, baseline rates, and workflow states',
    },
    contract_scope: {
      title: 'Contract & Scope Baseline',
      subtitle: 'Review and confirm original deliverables and explicit exclusions',
    },
    requests: {
      title: 'Requests & Evidence Log',
      subtitle: 'Preserve client messages and compare them with the confirmed baseline',
    },
    work: {
      title: 'Work Tracking & Timesheets',
      subtitle: 'Record estimated and actual hours with transparent billing rates',
    },
    findings: {
      title: 'Findings Review Hub',
      subtitle: 'Evaluate AI evidence interpretations and make authoritative decisions',
    },
    impact: {
      title: 'Financial Impact Breakdown',
      subtitle: 'Deterministic revenue-at-risk calculations and unapproved work exposure',
    },
    change_orders: {
      title: 'Change Orders & Exports',
      subtitle: 'Package reviewed findings into professional, printable PDF agreements',
    },
    audit: {
      title: 'Immutable Audit Trail',
      subtitle: 'Complete history of human decisions and system analysis transitions',
    },
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 font-sans">
      
      {/* Persistent Left Sidebar */}
      <Sidebar
        currentSection={currentSection}
        onSelectSection={setCurrentSection}
        projects={projects}
        currentProject={currentProject}
        onSelectProject={setCurrentProject}
        onOpenCreateProject={() => setCurrentSection('projects')}
        onLoadDemo={handleLoadDemo}
        health={health}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        
        {/* Top Header */}
        <Header
          title={sectionMeta[currentSection].title}
          subtitle={sectionMeta[currentSection].subtitle}
          currentProject={currentProject}
          onRefresh={() => currentProject && loadProjectData(currentProject.id)}
          isLoading={isLoading}
          onLoadDemo={handleLoadDemo}
          healthStatus={health}
        />

        {/* Global Error Banner */}
        {errorMsg && (
          <div className="bg-rose-50 border-b border-rose-200 px-8 py-2.5 flex items-center justify-between text-xs text-rose-800">
            <span>{errorMsg}</span>
            <button
              onClick={() => setErrorMsg(null)}
              className="text-rose-600 hover:text-rose-900 font-semibold ml-4"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-8">
          <div className="max-w-7xl mx-auto">
            {currentSection === 'overview' && (
              <OverviewPage
                project={currentProject}
                findings={findings}
                impact={impact}
                changeOrders={changeOrders}
                auditEvents={auditEvents}
                onNavigate={setCurrentSection}
                onInspectFinding={handleInspectFinding}
                onLoadDemo={handleLoadDemo}
              />
            )}

            {currentSection === 'projects' && (
              <ProjectsPage
                projects={projects}
                currentProject={currentProject}
                onSelectProject={setCurrentProject}
                onCreateProject={handleCreateProject}
                onDeleteProject={handleDeleteProject}
                onLoadDemo={handleLoadDemo}
              />
            )}

            {currentSection === 'contract_scope' && currentProject && (
              <ScopeBaselinePage
                project={currentProject}
                contracts={contracts}
                scopeItems={scopeItems}
                onUploadContract={handleUploadContract}
                onExtractBaseline={handleExtractBaseline}
                onConfirmBaseline={handleConfirmBaseline}
                onAddScopeItem={handleAddScopeItem}
                onUpdateScopeItem={handleUpdateScopeItem}
                onDeleteScopeItem={handleDeleteScopeItem}
              />
            )}

            {currentSection === 'requests' && currentProject && (
              <RequestsEvidencePage
                project={currentProject}
                requests={requests}
                findings={findings}
                scopeItems={scopeItems}
                onCreateRequest={handleCreateRequest}
                onImportRequests={handleImportRequests}
                onAnalyzeRequests={handleAnalyzeRequests}
                onInspectFinding={handleInspectFinding}
              />
            )}

            {currentSection === 'work' && currentProject && (
              <WorkTrackingPage
                project={currentProject}
                workItems={workItems}
                requests={requests}
                onCreateWorkItem={handleCreateWorkItem}
                onImportWorkItems={handleImportWorkItems}
                onUpdateWorkItem={handleUpdateWorkItem}
                onDeleteWorkItem={handleDeleteWorkItem}
              />
            )}

            {currentSection === 'findings' && currentProject && (
              <FindingsReviewPage
                project={currentProject}
                findings={findings}
                requests={requests}
                scopeItems={scopeItems}
                onUpdateReview={handleUpdateFindingReview}
                onInspectFinding={handleInspectFinding}
                onAnalyzeRequests={handleAnalyzeRequests}
              />
            )}

            {currentSection === 'impact' && currentProject && (
              <FinancialImpactPage
                project={currentProject}
                impact={impact}
              />
            )}

            {currentSection === 'change_orders' && currentProject && (
              <ChangeOrdersPage
                project={currentProject}
                changeOrders={changeOrders}
                findings={findings}
                onCreateChangeOrder={handleCreateChangeOrder}
                onUpdateChangeOrder={handleUpdateChangeOrder}
                onDownloadPdf={handleDownloadPdf}
              />
            )}

            {currentSection === 'audit' && currentProject && (
              <AuditTrailPage
                project={currentProject}
                auditEvents={auditEvents}
              />
            )}
          </div>
        </main>

      </div>

      {/* Side-by-Side Evidence Inspection Modal */}
      {isEvidenceModalOpen && activeModalFinding && (
        <EvidenceComparisonModal
          finding={activeModalFinding}
          request={requests.find((r) => r.id === activeModalFinding.request_id)}
          scopeItem={scopeItems.find((s) => s.id === activeModalFinding.scope_item_id)}
          isOpen={isEvidenceModalOpen}
          onClose={() => setIsEvidenceModalOpen(false)}
          onUpdateReview={handleUpdateFindingReview}
          currency={currentProject?.currency}
          defaultRate={currentProject?.default_hourly_rate}
        />
      )}

    </div>
  );
};
