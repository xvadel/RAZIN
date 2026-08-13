import React, { useState } from 'react';
import { useScene } from '../context/SceneContext';
import { getFileUrl } from '../api/client';
import {
  AlertTriangle,
  CheckCircle2,
  ShieldCheck,
  FileImage,
  Sparkles,
  Send,
} from 'lucide-react';

export const ReviewQueue = () => {
  const { evidence, handleReviewEvidence } = useScene();
  const [noteInputs, setNoteInputs] = useState({});
  const [submittingId, setSubmittingId] = useState(null);

  const reviewItems = evidence.filter((e) => e.requires_review);

  const handleNoteChange = (id, text) => {
    setNoteInputs((prev) => ({ ...prev, [id]: text }));
  };

  const onConfirm = async (item) => {
    setSubmittingId(item.evidence_id);
    const note = noteInputs[item.evidence_id] || 'Verified and confirmed by investigator';
    await handleReviewEvidence(item.evidence_id, note);
    setSubmittingId(null);
  };

  if (reviewItems.length === 0) {
    return (
      <div className="glass-panel flex flex-col items-center justify-center rounded-2xl p-16 text-center border border-slate-800">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-400 mb-4 shadow-lg">
          <ShieldCheck className="h-8 w-8" />
        </div>
        <h3 className="text-lg font-bold text-white">All Clear! No Pending Reviews</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-sm">
          All candidate evidence detections for this scene have either passed confidence validation or have already been confirmed.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="glass-panel rounded-xl p-4 border border-amber-500/30 bg-amber-950/10 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-500/20 text-amber-400">
            <AlertTriangle className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-amber-300">
              Human-in-the-Loop Triage Queue
            </h3>
            <p className="text-xs text-slate-400">
              {reviewItems.length} candidate items require human confirmation before joining the confirmed case inventory.
            </p>
          </div>
        </div>
      </div>

      {/* Review Queue Items */}
      <div className="space-y-4">
        {reviewItems.map((item) => {
          const cropUrl = item.crop_image ? getFileUrl(item.crop_image) : null;
          const isSubmitting = submittingId === item.evidence_id;

          const badgeColor = {
            bloodstain: 'bg-red-500/20 text-red-400 border-red-500/30',
            footprint: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
            digital_device: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
          }[item.evidence_class] || 'bg-slate-500/20 text-slate-400 border-slate-700';

          return (
            <div
              key={item.evidence_id}
              className="glass-panel rounded-xl p-5 border border-slate-800 flex flex-col lg:flex-row gap-6 items-start justify-between"
            >
              {/* Thumbnail & Class */}
              <div className="flex items-start space-x-4">
                <div className="relative h-24 w-32 shrink-0 rounded-lg overflow-hidden bg-surface-200 border border-slate-700 flex items-center justify-center">
                  {cropUrl ? (
                    <img
                      src={cropUrl}
                      alt={item.evidence_class}
                      className="h-full w-full object-contain"
                    />
                  ) : (
                    <FileImage className="h-8 w-8 text-slate-600" />
                  )}
                  <span className="absolute bottom-1 left-1 rounded bg-black/70 px-1.5 py-0.5 text-[9px] font-mono text-slate-300">
                    CROP
                  </span>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <span className={`rounded-md px-2.5 py-1 text-xs font-mono font-bold uppercase border ${badgeColor}`}>
                      {item.evidence_class}
                    </span>
                    <span className="font-mono text-xs text-slate-400">
                      Score: <b className="text-amber-400">{(item.confidence * 100).toFixed(1)}%</b>
                    </span>
                  </div>

                  <div className="space-y-1">
                    <span className="block text-[11px] font-mono font-bold text-amber-400/90">
                      FLAG REASON / AGENT NOTES:
                    </span>
                    <p className="text-xs text-slate-300 max-w-lg bg-surface-200 p-2 rounded-lg border border-slate-800 leading-relaxed">
                      {item.notes || 'Confidence below threshold (0.50)'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Investigator Action Box */}
              <div className="w-full lg:w-96 flex flex-col space-y-2.5 shrink-0 pt-2 lg:pt-0 border-t lg:border-t-0 border-slate-800">
                <label className="text-[11px] font-mono text-slate-400">
                  INVESTIGATOR VERIFICATION NOTE:
                </label>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    placeholder="e.g. Confirmed footprint pattern"
                    value={noteInputs[item.evidence_id] || ''}
                    onChange={(e) => handleNoteChange(item.evidence_id, e.target.value)}
                    className="flex-1 rounded-lg bg-surface-200 px-3 py-1.5 text-xs text-white border border-slate-700 focus:outline-none focus:border-cyan-500"
                  />
                  <button
                    disabled={isSubmitting}
                    onClick={() => onConfirm(item)}
                    className="flex items-center space-x-1 rounded-lg bg-emerald-600 px-4 py-1.5 text-xs font-semibold text-white shadow hover:bg-emerald-500 transition disabled:opacity-50"
                  >
                    <CheckCircle2 className="h-4 w-4" />
                    <span>Confirm</span>
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
