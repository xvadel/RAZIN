import React, { useState } from 'react';
import { useScene } from './context/SceneContext';
import { Navbar } from './components/Navbar';
import { IngestionZone } from './components/IngestionZone';
import { EvidenceGrid } from './components/EvidenceGrid';
import { ReviewQueue } from './components/ReviewQueue';
import { VisualGallery } from './components/VisualGallery';
import { ForensicReport } from './components/ForensicReport';
import { ChatPanel } from './components/ChatPanel';
import {
  Upload,
  Layers,
  AlertTriangle,
  Image as ImageIcon,
  FileText,
  MessageSquare,
  CheckCircle2,
  AlertCircle,
  Info,
} from 'lucide-react';

export function AppContent() {
  const { activeSceneId, evidence, toast } = useScene();
  const [activeTab, setActiveTab] = useState('catalog');

  const pendingReviewCount = evidence.filter((e) => e.requires_review).length;

  const tabs = [
    { id: 'ingestion', label: 'Ingestion & AI Run', icon: Upload },
    { id: 'catalog', label: `Evidence Catalog (${evidence.length})`, icon: Layers },
    {
      id: 'review',
      label: 'Review Queue',
      icon: AlertTriangle,
      badge: pendingReviewCount > 0 ? pendingReviewCount : null,
    },
    { id: 'chat', label: 'AI Forensic Chat', icon: MessageSquare },
    { id: 'visuals', label: 'Visual Gallery', icon: ImageIcon },
    { id: 'report', label: 'Forensic Report', icon: FileText },
  ];

  return (
    <div className="min-h-screen bg-background flex flex-col font-sans">
      <Navbar />

      {/* Main Content Area */}
      <main className="flex-1 mx-auto max-w-7xl w-full px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Toast Alert */}
        {toast && (
          <div
            className={`fixed bottom-6 right-6 z-50 flex items-center space-x-2 rounded-xl px-4 py-3 shadow-2xl text-xs font-semibold text-white border transition-all animate-bounce ${
              toast.type === 'error'
                ? 'bg-rose-900/90 border-rose-600'
                : toast.type === 'success'
                ? 'bg-emerald-900/90 border-emerald-600'
                : 'bg-cyan-900/90 border-cyan-600'
            }`}
          >
            {toast.type === 'error' ? (
              <AlertCircle className="h-4 w-4 text-rose-300" />
            ) : toast.type === 'success' ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-300" />
            ) : (
              <Info className="h-4 w-4 text-cyan-300" />
            )}
            <span>{toast.message}</span>
          </div>
        )}

        {!activeSceneId ? (
          <div className="glass-panel flex flex-col items-center justify-center rounded-2xl p-20 text-center border border-slate-800">
            <h2 className="text-xl font-bold text-white mb-2">No Active Scene Selected</h2>
            <p className="text-xs text-slate-400 max-w-md">
              Register a new crime scene in the top navbar or select an existing one to begin surveying evidence.
            </p>
          </div>
        ) : (
          <>
            {/* Tab Navigation */}
            <div className="flex border-b border-slate-800 space-x-2 overflow-x-auto pb-1">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center space-x-2 px-4 py-2.5 rounded-lg text-xs font-semibold font-mono tracking-wide transition relative shrink-0 ${
                      isActive
                        ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-surface-200'
                    }`}
                  >
                    <Icon className={`h-4 w-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                    <span>{tab.label}</span>
                    {tab.badge && (
                      <span className="rounded-full bg-amber-500 text-black px-1.5 py-0.2 text-[10px] font-bold">
                        {tab.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            {/* Tab Contents */}
            <div className="pt-2">
              {activeTab === 'ingestion' && <IngestionZone />}
              {activeTab === 'catalog' && <EvidenceGrid />}
              {activeTab === 'review' && <ReviewQueue />}
              {activeTab === 'chat' && <ChatPanel />}
              {activeTab === 'visuals' && <VisualGallery />}
              {activeTab === 'report' && <ForensicReport />}
            </div>
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-surface-300 py-4 text-center text-xs font-mono text-slate-500">
        RAZIN v0.1 — Autonomous Forensic Evidence Surveying Platform | Powered by YOLO26 &amp; ReAct Agent
      </footer>
    </div>
  );
}

export default function App() {
  return <AppContent />;
}
