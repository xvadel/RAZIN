import React, { useState } from 'react';
import { useScene } from '../context/SceneContext';
import { getFileUrl } from '../api/client';
import {
  X,
  ShieldAlert,
  CheckCircle2,
  Clock,
  FileImage,
  Maximize2,
  Tag,
  Crosshair,
} from 'lucide-react';

export const EvidenceModal = ({ item, onClose }) => {
  const { handleReviewEvidence } = useScene();
  const [notes, setNotes] = useState(item?.notes || '');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!item) return null;

  const onConfirm = async () => {
    setIsSubmitting(true);
    await handleReviewEvidence(item.evidence_id, notes || 'Verified by forensic investigator');
    setIsSubmitting(false);
    onClose();
  };

  const badgeColor = {
    bloodstain: 'bg-red-500/20 text-red-400 border-red-500/30',
    footprint: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    digital_device: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
  }[item.evidence_class] || 'bg-slate-500/20 text-slate-400 border-slate-500/30';

  const cropUrl = item.crop_image ? getFileUrl(item.crop_image) : null;
  const sourceUrl = item.source_image ? getFileUrl(item.source_image) : null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 overflow-y-auto">
      <div className="glass-panel w-full max-w-3xl rounded-2xl p-6 shadow-2xl border border-slate-700 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <span className={`rounded-lg px-2.5 py-1 text-xs font-mono font-bold uppercase border ${badgeColor}`}>
              {item.evidence_class}
            </span>
            <span className="font-mono text-xs text-slate-400">
              ID: <span className="text-slate-200">{item.evidence_id}</span>
            </span>
          </div>

          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-surface-200 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 my-6 overflow-y-auto pr-1">
          {/* Visuals */}
          <div className="space-y-3">
            <div className="relative rounded-xl overflow-hidden bg-surface-200 border border-slate-700/80 aspect-video flex items-center justify-center">
              {cropUrl ? (
                <img
                  src={cropUrl}
                  alt="Forensic Crop"
                  className="h-full w-full object-contain"
                />
              ) : sourceUrl ? (
                <img
                  src={sourceUrl}
                  alt="Source"
                  className="h-full w-full object-contain"
                />
              ) : (
                <div className="flex flex-col items-center text-slate-500">
                  <FileImage className="h-8 w-8 mb-1" />
                  <span className="text-xs">No image preview</span>
                </div>
              )}
              <span className="absolute bottom-2 left-2 rounded bg-black/70 px-2 py-0.5 text-[10px] font-mono text-slate-300">
                FORENSIC CROP
              </span>
            </div>

            {/* Bounding Box Coordinates */}
            <div className="rounded-lg bg-surface-200 p-3 text-xs font-mono text-slate-300 border border-slate-800 space-y-1">
              <div className="flex items-center space-x-1.5 text-slate-400">
                <Crosshair className="h-3.5 w-3.5 text-cyan-400" />
                <span className="font-bold">BOUNDING BOX (PIXELS)</span>
              </div>
              <div className="grid grid-cols-2 gap-x-4 text-[11px] text-slate-400">
                <span>X-Min: <b className="text-white">{item.bbox?.x_min}</b></span>
                <span>Y-Min: <b className="text-white">{item.bbox?.y_min}</b></span>
                <span>X-Max: <b className="text-white">{item.bbox?.x_max}</b></span>
                <span>Y-Max: <b className="text-white">{item.bbox?.y_max}</b></span>
              </div>
            </div>
          </div>

          {/* Details & Action */}
          <div className="space-y-4 text-xs">
            {/* Confidence Gauge */}
            <div className="rounded-xl bg-surface-200 p-4 border border-slate-800 space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-slate-400 font-mono">AI CONFIDENCE SCORE</span>
                <span className="font-mono font-bold text-sm text-cyan-400">
                  {(item.confidence * 100).toFixed(1)}%
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    item.confidence >= 0.5 ? 'bg-cyan-500' : 'bg-amber-500'
                  }`}
                  style={{ width: `${item.confidence * 100}%` }}
                />
              </div>
            </div>

            {/* Status & Review Reason */}
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                {item.requires_review ? (
                  <span className="flex items-center space-x-1 rounded bg-amber-500/20 px-2.5 py-1 text-xs font-semibold text-amber-300 border border-amber-500/30">
                    <ShieldAlert className="h-3.5 w-3.5" />
                    <span>Requires Human Verification</span>
                  </span>
                ) : item.reviewed ? (
                  <span className="flex items-center space-x-1 rounded bg-emerald-500/20 px-2.5 py-1 text-xs font-semibold text-emerald-300 border border-emerald-500/30">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    <span>Human Confirmed</span>
                  </span>
                ) : (
                  <span className="rounded bg-slate-500/20 px-2.5 py-1 text-xs text-slate-400 border border-slate-700">
                    AI Auto-Triage (Unverified)
                  </span>
                )}
              </div>

              {item.notes && (
                <div className="rounded-lg bg-surface-200 p-3 border border-slate-800 text-slate-300">
                  <span className="block font-bold text-slate-400 mb-1">Triage Reason / Notes:</span>
                  <p className="leading-relaxed">{item.notes}</p>
                </div>
              )}
            </div>

            {/* Investigator Review Action */}
            <div className="space-y-2 pt-2 border-t border-slate-800">
              <label className="block font-mono text-slate-400">
                INVESTIGATOR CASE NOTE:
              </label>
              <textarea
                rows={2}
                placeholder="e.g. Confirmed blood spatter pattern on east wall."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full rounded-lg bg-surface-200 px-3 py-2 text-xs text-white border border-slate-700 focus:border-cyan-500 focus:outline-none"
              />
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-4 border-t border-slate-800">
          <div className="flex items-center space-x-1.5 text-xs text-slate-400 font-mono">
            <Clock className="h-3.5 w-3.5" />
            <span>{new Date(item.timestamp).toLocaleString()}</span>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={onClose}
              className="rounded-lg px-4 py-2 text-xs text-slate-400 hover:bg-surface-200"
            >
              Close
            </button>
            <button
              disabled={isSubmitting}
              onClick={onConfirm}
              className="flex items-center space-x-1.5 rounded-lg bg-emerald-600 px-5 py-2 text-xs font-semibold text-white shadow-lg hover:bg-emerald-500 transition disabled:opacity-50"
            >
              <CheckCircle2 className="h-4 w-4" />
              <span>{item.reviewed ? 'Update Verification' : 'Confirm Evidence'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
