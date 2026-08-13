import axios from 'axios';

// Base API instance (proxied via Vite or direct in production)
const API_BASE = '';

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000, // 2 minutes for long AI analysis
});

// Set optional API key on all requests
export const setApiKey = (key) => {
  if (key) {
    api.defaults.headers.common['x-api-key'] = key;
  } else {
    delete api.defaults.headers.common['x-api-key'];
  }
};

// --- API Methods ---

export const getHealth = async () => {
  const res = await api.get('/health');
  return res.data;
};

export const getScenes = async () => {
  const res = await api.get('/scenes');
  return res.data;
};

export const getScene = async (sceneId) => {
  const res = await api.get(`/scenes/${sceneId}`);
  return res.data;
};

export const createScene = async (sceneData) => {
  const res = await api.post('/scenes', sceneData);
  return res.data;
};

export const uploadBatch = async (sceneId, fileList, onProgress) => {
  const formData = new FormData();
  for (let i = 0; i < fileList.length; i++) {
    formData.append('files', fileList[i]);
  }
  const res = await api.post(`/scenes/${sceneId}/upload-batch`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percent);
      }
    },
  });
  return res.data;
};

export const analyzeScene = async (sceneId) => {
  const res = await api.post(`/scenes/${sceneId}/analyze`);
  return res.data;
};

export const getEvidence = async (sceneId, requiresReview = null) => {
  const params = {};
  if (requiresReview !== null) {
    params.requires_review = requiresReview;
  }
  const res = await api.get(`/scenes/${sceneId}/evidence`, { params });
  return res.data;
};

export const reviewEvidence = async (evidenceId, notes = '') => {
  const res = await api.patch(`/evidence/${evidenceId}/review`, { notes });
  return res.data;
};

export const chatWithScene = async (sceneId, message, history = [], scope = 'scene') => {
  const res = await api.post(`/scenes/${sceneId}/chat`, { message, history, scope });
  return res.data;
};

export const reindexScene = async (sceneId) => {
  const res = await api.post(`/scenes/${sceneId}/reindex`);
  return res.data;
};

export const getFileUrl = (filePath) => {
  if (!filePath) return '';
  if (filePath.startsWith('http')) return filePath;
  // Format for /files/ endpoint
  return `/files/${filePath}`;
};
