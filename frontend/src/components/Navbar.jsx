import React, { useState } from 'react';
import { useScene } from '../context/SceneContext';
import {
  FolderPlus,
  ShieldCheck,
  Radio,
  Key,
  Layers,
  AlertTriangle,
  FileText,
  Activity,
  X,
} from 'lucide-react';

export const Navbar = () => {
  const {
    scenes,
    activeSceneId,
    setActiveSceneId,
    activeScene,
    evidence,
    backendOnline,
    handleCreateScene,
    apiKeyVal,
    updateApiKey,
  } = useScene();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isKeyModalOpen, setIsKeyModalOpen] = useState(false);
  const [newSceneId, setNewSceneId] = useState('');
  const [newCaseRef, setNewCaseRef] = useState('');
  const [tempApiKey, setTempApiKey] = useState(apiKeyVal);

  const pendingReviewCount = evidence.filter((e) => e.requires_review).length;
  const confirmedCount = evidence.filter((e) => e.reviewed).length;

  const onRegisterScene = async (e) => {
    e.preventDefault();
    if (!newSceneId.trim()) return;
    const ok = await handleCreateScene(newSceneId.trim(), newCaseRef.trim());
    if (ok) {
      setNewSceneId('');
      setNewCaseRef('');
      setIsModalOpen(false);
    }
  };

  const onSaveKey = (e) => {
    e.preventDefault();
    updateApiKey(tempApiKey.trim());
    setIsKeyModalOpen(false);
  };

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b border-slate-800/80 bg-surface-100/90 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          {/* Brand */}
          <div className="flex items-center space-x-3">
            <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 shadow-glow-cyan">
              <ShieldCheck className="h-6 w-6 text-white" />
              <span className="absolute -bottom-0.5 -right-0.5 flex h-3 w-3">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex h-3 w-3 rounded-full bg-cyan-500"></span>
              </span>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-mono text-lg font-bold tracking-wider text-white">RAZIN</span>
                <span className="rounded bg-cyan-500/10 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-cyan-400 border border-cyan-500/20">
                  v0.1 MVP
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-sans hidden sm:block">
                Autonomous Forensic Evidence Surveying
              </p>
            </div>
          </div>

          {/* Center: Scene Selector */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2 rounded-lg bg-surface-200/80 p-1.5 border border-slate-700/50">
              <label className="pl-2 font-mono text-xs text-slate-400">SCENE:</label>
              <select
                value={activeSceneId}
                onChange={(e) => setActiveSceneId(e.target.value)}
                className="bg-surface-100 px-3 py-1 font-mono text-sm text-cyan-300 rounded border border-slate-700 focus:border-cyan-500 focus:outline-none"
              >
                {scenes.length === 0 && <option value="">No scenes</option>}
                {scenes.map((s) => (
                  <option key={s.scene_id} value={s.scene_id}>
                    {s.scene_id} {s.case_reference ? `(${s.case_reference})` : ''}
                  </option>
                ))}
              </select>

              <button
                onClick={() => setIsModalOpen(true)}
                className="flex items-center space-x-1 rounded bg-cyan-600/20 px-2.5 py-1 text-xs font-medium text-cyan-300 border border-cyan-500/30 hover:bg-cyan-600/30 transition"
              >
                <FolderPlus className="h-3.5 w-3.5" />
                <span className="hidden md:inline">New Scene</span>
              </button>
            </div>
          </div>

          {/* Right Metrics & Health */}
          <div className="flex items-center space-x-4">
            {/* Quick Metrics */}
            <div className="hidden lg:flex items-center space-x-3 text-xs font-mono">
              <div className="flex items-center space-x-1.5 rounded-md bg-surface-200 px-2.5 py-1 border border-slate-800">
                <Layers className="h-3.5 w-3.5 text-slate-400" />
                <span className="text-slate-400">Media:</span>
                <span className="font-bold text-white">{activeScene?.media_count || 0}</span>
              </div>

              <div className="flex items-center space-x-1.5 rounded-md bg-surface-200 px-2.5 py-1 border border-slate-800">
                <Activity className="h-3.5 w-3.5 text-cyan-400" />
                <span className="text-slate-400">Evidence:</span>
                <span className="font-bold text-cyan-300">{evidence.length}</span>
              </div>

              {pendingReviewCount > 0 && (
                <div className="flex items-center space-x-1.5 rounded-md bg-amber-500/10 px-2.5 py-1 border border-amber-500/30 text-amber-300 animate-pulse">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  <span>Review: {pendingReviewCount}</span>
                </div>
              )}
            </div>

            {/* API Key Modal Button */}
            <button
              onClick={() => setIsKeyModalOpen(true)}
              className="rounded-lg p-2 text-slate-400 hover:bg-surface-200 hover:text-white transition"
              title="API Key Settings"
            >
              <Key className="h-4 w-4" />
            </button>

            {/* Backend Status indicator */}
            <div className="flex items-center space-x-1.5 font-mono text-xs">
              <Radio
                className={`h-4 w-4 ${
                  backendOnline ? 'text-emerald-400 animate-pulse' : 'text-rose-500'
                }`}
              />
              <span className={`hidden sm:inline ${backendOnline ? 'text-emerald-400' : 'text-rose-500'}`}>
                {backendOnline ? 'API READY' : 'OFFLINE'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* New Scene Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="glass-panel w-full max-w-md rounded-xl p-6 shadow-2xl border border-slate-700">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white flex items-center space-x-2">
                <FolderPlus className="h-5 w-5 text-cyan-400" />
                <span>Register Crime Scene</span>
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={onRegisterScene} className="space-y-4">
              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1">
                  SCENE ID <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. SCENE-2026-08A"
                  value={newSceneId}
                  onChange={(e) => setNewSceneId(e.target.value)}
                  className="w-full rounded-lg bg-surface-200 px-3 py-2 text-sm text-white border border-slate-700 focus:border-cyan-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1">
                  CASE REFERENCE (OPTIONAL)
                </label>
                <input
                  type="text"
                  placeholder="e.g. CASE-CR-8891"
                  value={newCaseRef}
                  onChange={(e) => setNewCaseRef(e.target.value)}
                  className="w-full rounded-lg bg-surface-200 px-3 py-2 text-sm text-white border border-slate-700 focus:border-cyan-500 focus:outline-none"
                />
              </div>
              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="rounded-lg px-4 py-2 text-sm text-slate-400 hover:bg-surface-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-cyan-600 px-5 py-2 text-sm font-semibold text-white shadow-lg hover:bg-cyan-500 transition"
                >
                  Create Scene
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* API Key Modal */}
      {isKeyModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="glass-panel w-full max-w-md rounded-xl p-6 shadow-2xl border border-slate-700">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white flex items-center space-x-2">
                <Key className="h-5 w-5 text-amber-400" />
                <span>Backend API Key</span>
              </h3>
              <button
                onClick={() => setIsKeyModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={onSaveKey} className="space-y-4">
              <p className="text-xs text-slate-400">
                If your FastAPI backend has an API key enabled via <code className="text-cyan-300">API_KEY</code>, enter it below.
              </p>
              <div>
                <input
                  type="password"
                  placeholder="Enter X-API-Key (leave blank if disabled)"
                  value={tempApiKey}
                  onChange={(e) => setTempApiKey(e.target.value)}
                  className="w-full rounded-lg bg-surface-200 px-3 py-2 text-sm text-white border border-slate-700 focus:border-cyan-500 focus:outline-none"
                />
              </div>
              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsKeyModalOpen(false)}
                  className="rounded-lg px-4 py-2 text-sm text-slate-400 hover:bg-surface-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-amber-600 px-5 py-2 text-sm font-semibold text-white shadow-lg hover:bg-amber-500 transition"
                >
                  Save Key
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
};
