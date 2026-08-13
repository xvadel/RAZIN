import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  getHealth,
  getScenes,
  getScene,
  createScene,
  getEvidence,
  analyzeScene,
  reviewEvidence,
  setApiKey,
} from '../api/client';

const SceneContext = createContext(null);

export const SceneProvider = ({ children }) => {
  const [scenes, setScenes] = useState([]);
  const [activeSceneId, setActiveSceneId] = useState('');
  const [activeScene, setActiveScene] = useState(null);
  const [evidence, setEvidence] = useState([]);
  const [backendOnline, setBackendOnline] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [lastAnalysis, setLastAnalysis] = useState(null);
  const [apiKeyVal, setApiKeyVal] = useState('');
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'info') => {
    setToast({ message, type, id: Date.now() });
    setTimeout(() => setToast(null), 4000);
  };

  // Check health and load scenes
  const checkHealthAndLoad = useCallback(async () => {
    try {
      await getHealth();
      setBackendOnline(true);
      const sceneList = await getScenes();
      setScenes(sceneList);
      if (sceneList.length > 0 && !activeSceneId) {
        setActiveSceneId(sceneList[0].scene_id);
      }
    } catch {
      setBackendOnline(false);
    }
  }, [activeSceneId]);

  useEffect(() => {
    checkHealthAndLoad();
    const interval = setInterval(checkHealthAndLoad, 15000);
    return () => clearInterval(interval);
  }, [checkHealthAndLoad]);

  // Load details & evidence when activeSceneId changes
  const loadSceneData = useCallback(async (sId) => {
    if (!sId) return;
    setIsLoading(true);
    try {
      const [sceneData, evData] = await Promise.all([
        getScene(sId),
        getEvidence(sId),
      ]);
      setActiveScene(sceneData);
      setEvidence(evData);
    } catch {
      showToast(`Failed to load data for scene ${sId}`, 'error');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeSceneId) {
      loadSceneData(activeSceneId);
    }
  }, [activeSceneId, loadSceneData]);

  // Update API Key
  const updateApiKey = (key) => {
    setApiKeyVal(key);
    setApiKey(key);
    showToast('API key updated', 'success');
  };

  // Create new scene
  const handleCreateScene = async (sceneId, caseRef) => {
    try {
      const newScene = await createScene({
        scene_id: sceneId,
        case_reference: caseRef || null,
      });
      setScenes((prev) => [newScene, ...prev]);
      setActiveSceneId(newScene.scene_id);
      showToast(`Scene ${sceneId} created successfully!`, 'success');
      return true;
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to create scene', 'error');
      return false;
    }
  };

  // Trigger AI Analysis
  const handleRunAnalysis = async () => {
    if (!activeSceneId) return;
    setIsAnalyzing(true);
    try {
      const result = await analyzeScene(activeSceneId);
      setLastAnalysis(result);
      showToast(
        `Analysis complete! Found ${result.evidence_found} evidence items (${result.flagged_for_review} flagged).`,
        'success'
      );
      await loadSceneData(activeSceneId);
    } catch (err) {
      showToast(err.response?.data?.detail || 'Scene analysis failed', 'error');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Mark evidence as reviewed
  const handleReviewEvidence = async (evidenceId, notes) => {
    try {
      await reviewEvidence(evidenceId, notes);
      setEvidence((prev) =>
        prev.map((item) =>
          item.evidence_id === evidenceId
            ? { ...item, requires_review: false, reviewed: true, notes: notes || item.notes }
            : item
        )
      );
      showToast('Evidence confirmed and verified!', 'success');
    } catch {
      showToast('Failed to update evidence status', 'error');
    }
  };

  return (
    <SceneContext.Provider
      value={{
        scenes,
        activeSceneId,
        setActiveSceneId,
        activeScene,
        evidence,
        backendOnline,
        isLoading,
        isAnalyzing,
        lastAnalysis,
        apiKeyVal,
        updateApiKey,
        handleCreateScene,
        handleRunAnalysis,
        handleReviewEvidence,
        reloadSceneData: () => loadSceneData(activeSceneId),
        toast,
        showToast,
      }}
    >
      {children}
    </SceneContext.Provider>
  );
};

export const useScene = () => {
  const context = useContext(SceneContext);
  if (!context) throw new Error('useScene must be used within a SceneProvider');
  return context;
};
