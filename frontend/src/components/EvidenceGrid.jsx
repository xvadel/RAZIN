import React, { useState } from 'react';
import { useScene } from '../context/SceneContext';
import { getFileUrl } from '../api/client';
import { EvidenceModal } from './EvidenceModal';
import {
  Search,
  Filter,
  CheckCircle2,
  AlertTriangle,
  FileImage,
  Eye,
  Shield,
  Layers,
} from 'lucide-react';

export const EvidenceGrid = () => {
  const { evidence, activeSceneId } = useScene();
  const [selectedItem, setSelectedItem] = useState(null);
  const [classFilter, setClassFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Filter evidence
  const filtered = evidence.filter((item) => {
    if (classFilter !== 'all' && item.evidence_class !== classFilter) return false;
    if (statusFilter === 'review' && !item.requires_review) return false;
    if (statusFilter === 'confirmed' && !item.reviewed) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchClass = item.evidence_class.toLowerCase().includes(q);
      const matchNotes = (item.notes || '').toLowerCase().includes(q);
      const matchId = item.evidence_id.toLowerCase().includes(q);
      if (!matchClass && !matchNotes && !matchId) return false;
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Controls / Filter Bar */}
      <div className="glass-panel flex flex-col md:flex-row md:items-center justify-between gap-4 rounded-xl p-4 border border-slate-800">
        {/* Class Filter Buttons */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs font-mono">
          <button
            onClick={() => setClassFilter('all')}
            className={`rounded-lg px-3 py-1.5 transition ${
              classFilter === 'all'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold'
                : 'text-slate-400 hover:bg-surface-200'
            }`}
          >
            ALL ({evidence.length})
          </button>
          <button
            onClick={() => setClassFilter('bloodstain')}
            className={`rounded-lg px-3 py-1.5 transition ${
              classFilter === 'bloodstain'
                ? 'bg-red-500/20 text-red-300 border border-red-500/40 font-bold'
                : 'text-slate-400 hover:bg-surface-200'
            }`}
          >
            BLOODSTAINS ({evidence.filter((e) => e.evidence_class === 'bloodstain').length})
          </button>
          <button
            onClick={() => setClassFilter('footprint')}
            className={`rounded-lg px-3 py-1.5 transition ${
              classFilter === 'footprint'
                ? 'bg-orange-500/20 text-orange-300 border border-orange-500/40 font-bold'
                : 'text-slate-400 hover:bg-surface-200'
            }`}
          >
            FOOTPRINTS ({evidence.filter((e) => e.evidence_class === 'footprint').length})
          </button>
          <button
            onClick={() => setClassFilter('digital_device')}
            className={`rounded-lg px-3 py-1.5 transition ${
              classFilter === 'digital_device'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold'
                : 'text-slate-400 hover:bg-surface-200'
            }`}
          >
            DIGITAL DEVICES ({evidence.filter((e) => e.evidence_class === 'digital_device').length})
          </button>
        </div>

        {/* Status Dropdown & Search */}
        <div className="flex items-center space-x-3 text-xs">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg bg-surface-200 px-3 py-1.5 font-mono text-slate-300 border border-slate-700 focus:outline-none focus:border-cyan-500"
          >
            <option value="all">Status: All</option>
            <option value="review">⚠️ Needs Human Review</option>
            <option value="confirmed">✅ Confirmed</option>
          </select>

          <div className="relative">
            <Search className="absolute left-2.5 top-2 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search evidence..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="rounded-lg bg-surface-200 pl-8 pr-3 py-1.5 text-slate-200 border border-slate-700 focus:outline-none focus:border-cyan-500 w-44"
            />
          </div>
        </div>
      </div>

      {/* Evidence Cards Grid */}
      {filtered.length === 0 ? (
        <div className="glass-panel flex flex-col items-center justify-center rounded-2xl p-12 text-center border border-slate-800 text-slate-400">
          <Layers className="h-10 w-10 text-slate-600 mb-2" />
          <p className="text-sm font-semibold text-slate-300">No evidence items matching the current filter</p>
          <p className="text-xs text-slate-500 mt-1">Try resetting the filter or uploading imagery in the Ingestion tab.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filtered.map((item) => {
            const cropUrl = item.crop_image ? getFileUrl(item.crop_image) : null;
            const badgeBg = {
              bloodstain: 'bg-red-500/20 text-red-400 border-red-500/30',
              footprint: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
              digital_device: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
            }[item.evidence_class] || 'bg-slate-500/20 text-slate-400 border-slate-700';

            return (
              <div
                key={item.evidence_id}
                onClick={() => setSelectedItem(item)}
                className="glass-panel glass-panel-hover group relative flex flex-col justify-between rounded-xl overflow-hidden cursor-pointer border border-slate-800 p-3.5 space-y-3"
              >
                {/* Image Thumbnail */}
                <div className="relative aspect-video rounded-lg overflow-hidden bg-surface-200 border border-slate-700/60 flex items-center justify-center">
                  {cropUrl ? (
                    <img
                      src={cropUrl}
                      alt={item.evidence_class}
                      className="h-full w-full object-contain group-hover:scale-105 transition duration-300"
                    />
                  ) : (
                    <FileImage className="h-8 w-8 text-slate-600" />
                  )}

                  {/* Status Badges Overlay */}
                  <div className="absolute top-2 left-2 flex items-center space-x-1">
                    <span className={`rounded px-2 py-0.5 text-[10px] font-mono font-bold uppercase border ${badgeBg}`}>
                      {item.evidence_class}
                    </span>
                  </div>

                  <div className="absolute top-2 right-2">
                    {item.requires_review && (
                      <span className="flex items-center space-x-1 rounded bg-amber-500/90 text-black px-1.5 py-0.5 text-[10px] font-bold shadow">
                        <AlertTriangle className="h-3 w-3" />
                        <span>REVIEW</span>
                      </span>
                    )}
                    {item.reviewed && (
                      <span className="flex items-center space-x-1 rounded bg-emerald-500/90 text-white px-1.5 py-0.5 text-[10px] font-bold shadow">
                        <CheckCircle2 className="h-3 w-3" />
                        <span>VERIFIED</span>
                      </span>
                    )}
                  </div>
                </div>

                {/* Card Info */}
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between items-center font-mono">
                    <span className="text-[11px] text-slate-400">Confidence</span>
                    <span className="font-bold text-cyan-300">{(item.confidence * 100).toFixed(1)}%</span>
                  </div>

                  <div className="h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        item.confidence >= 0.5 ? 'bg-cyan-500' : 'bg-amber-500'
                      }`}
                      style={{ width: `${item.confidence * 100}%` }}
                    />
                  </div>

                  {item.notes && (
                    <p className="text-[11px] text-slate-400 truncate italic">
                      {item.notes}
                    </p>
                  )}
                </div>

                {/* Footer */}
                <div className="pt-2 border-t border-slate-800 flex justify-between items-center text-[10px] font-mono text-slate-500">
                  <span className="truncate max-w-[150px]">{item.evidence_id.slice(0, 13)}...</span>
                  <div className="flex items-center space-x-1 text-cyan-400 group-hover:text-cyan-300">
                    <Eye className="h-3.5 w-3.5" />
                    <span>Inspect</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Detail Modal */}
      {selectedItem && (
        <EvidenceModal
          item={selectedItem}
          onClose={() => setSelectedItem(null)}
        />
      )}
    </div>
  );
};
