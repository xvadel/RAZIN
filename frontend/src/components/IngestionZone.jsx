import React, { useState, useRef } from 'react';
import { useScene } from '../context/SceneContext';
import { uploadBatch } from '../api/client';
import {
  UploadCloud,
  FileImage,
  Video,
  Play,
  CheckCircle2,
  Trash2,
  Cpu,
  Loader2,
  Sparkles,
  AlertCircle,
} from 'lucide-react';

export const IngestionZone = () => {
  const {
    activeSceneId,
    handleRunAnalysis,
    isAnalyzing,
    lastAnalysis,
    reloadSceneData,
    showToast,
  } = useScene();

  const [files, setFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      addFiles(Array.from(e.target.files));
    }
  };

  const addFiles = (newFiles) => {
    setFiles((prev) => [...prev, ...newFiles]);
  };

  const removeFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const clearFiles = () => {
    setFiles([]);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const uploadFiles = async () => {
    if (files.length === 0 || !activeSceneId) return;
    setIsUploading(true);
    setUploadProgress(0);

    try {
      await uploadBatch(activeSceneId, files, (percent) => {
        setUploadProgress(percent);
      });
      showToast(`Uploaded ${files.length} files to scene ${activeSceneId}`, 'success');
      clearFiles();
      await reloadSceneData();
    } catch (err) {
      showToast('Failed to upload files', 'error');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload Box */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`glass-panel relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-8 text-center transition-all ${
          isDragging
            ? 'border-cyan-400 bg-cyan-500/10'
            : 'border-slate-700/80 hover:border-slate-600'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/*,video/*"
          onChange={handleFileInput}
          className="hidden"
        />

        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-cyan-500/10 text-cyan-400 shadow-glow-cyan">
          <UploadCloud className="h-8 w-8" />
        </div>

        <h3 className="text-base font-semibold text-white">
          Drag & Drop Scene Photography or Video Clips
        </h3>
        <p className="mt-1 text-xs text-slate-400 max-w-md">
          Supports JPEG, PNG, MP4, MOV. Video clips will be automatically sampled at configurable FPS with duplicate filtering.
        </p>

        <div className="mt-5 flex items-center space-x-3">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="rounded-lg bg-surface-50 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-700 transition border border-slate-600"
          >
            Browse Local Files
          </button>

          {files.length > 0 && (
            <button
              type="button"
              disabled={isUploading}
              onClick={uploadFiles}
              className="flex items-center space-x-1.5 rounded-lg bg-cyan-600 px-5 py-2 text-xs font-semibold text-white shadow-lg hover:bg-cyan-500 transition disabled:opacity-50"
            >
              {isUploading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Uploading ({uploadProgress}%)...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="h-4 w-4" />
                  <span>Upload {files.length} Files</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Selected File Queue */}
      {files.length > 0 && (
        <div className="glass-panel rounded-xl p-4 border border-slate-800">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono font-bold text-slate-300">
              STAGED FOR UPLOAD ({files.length})
            </span>
            <button
              onClick={clearFiles}
              className="text-xs text-rose-400 hover:text-rose-300"
            >
              Clear All
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5 max-h-48 overflow-y-auto pr-1">
            {files.map((file, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between rounded-lg bg-surface-200 p-2 border border-slate-700/60 text-xs"
              >
                <div className="flex items-center space-x-2 truncate">
                  {file.type.startsWith('video') ? (
                    <Video className="h-4 w-4 text-purple-400 shrink-0" />
                  ) : (
                    <FileImage className="h-4 w-4 text-cyan-400 shrink-0" />
                  )}
                  <span className="truncate text-slate-200 font-mono">{file.name}</span>
                </div>
                <button
                  onClick={() => removeFile(idx)}
                  className="text-slate-400 hover:text-rose-400 p-1"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Trigger AI Detection & Agent Triage */}
      <div className="glass-panel relative overflow-hidden rounded-2xl p-6 border border-cyan-500/30 bg-gradient-to-r from-cyan-950/20 via-surface-100 to-purple-950/20 shadow-2xl">
        {isAnalyzing && <div className="scanner-beam" />}

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <Cpu className="h-5 w-5 text-cyan-400" />
              <h3 className="text-base font-bold text-white tracking-wide">
                Run YOLO26 + ReAct Agent Triage
              </h3>
            </div>
            <p className="text-xs text-slate-300 max-w-xl">
              Processes all unanalyzed imagery, extracts forensic crops, runs IoU overlap analysis, evaluates candidate evidence with LLM reasoning, and routes items to the human review queue.
            </p>
          </div>

          <button
            onClick={handleRunAnalysis}
            disabled={isAnalyzing || !activeSceneId}
            className="flex items-center justify-center space-x-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-6 py-3 text-sm font-bold text-white shadow-glow-cyan hover:from-cyan-400 hover:to-blue-500 transition disabled:opacity-50 min-w-[200px]"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin text-white" />
                <span className="font-mono">ANALYZING SCENE...</span>
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4 text-cyan-200" />
                <span>START SURVEY ANALYSIS</span>
              </>
            )}
          </button>
        </div>

        {/* Last Analysis Alert */}
        {lastAnalysis && (
          <div className="mt-4 rounded-xl bg-surface-200/80 p-3.5 border border-cyan-500/20 text-xs flex items-start space-x-2.5">
            <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
            <div className="space-y-1 text-slate-200">
              <div className="font-semibold text-emerald-300">
                Analysis Complete for Scene <span className="font-mono">{lastAnalysis.scene_id}</span>
              </div>
              <p className="text-slate-300">
                Processed {lastAnalysis.images_analyzed} images. Cataloged {lastAnalysis.evidence_found} items ({lastAnalysis.flagged_for_review} flagged for human review).
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
