import React, { useState, useRef, useEffect } from 'react';
import { useScene } from '../context/SceneContext';
import { chatWithScene, getFileUrl } from '../api/client';
import {
  Send,
  Bot,
  User,
  Loader2,
  Globe,
  Target,
  ChevronDown,
  ChevronUp,
  Fingerprint,
  AlertTriangle,
} from 'lucide-react';

const SCOPE_OPTIONS = [
  { id: 'scene', label: 'This Scene', icon: Target, desc: 'Search evidence in the active scene only' },
  { id: 'all', label: 'All Scenes', icon: Globe, desc: 'Search evidence across all cases' },
];

function SourceCard({ source }) {
  const classColors = {
    bloodstain: 'border-red-500/40 bg-red-950/30 text-red-300',
    footprint: 'border-amber-500/40 bg-amber-950/30 text-amber-300',
    digital_device: 'border-cyan-500/40 bg-cyan-950/30 text-cyan-300',
  };
  const color = classColors[source.evidence_class] || 'border-slate-600 bg-slate-900 text-slate-300';

  return (
    <div className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-[11px] ${color}`}>
      {source.crop_image && (
        <img
          src={getFileUrl(source.crop_image)}
          alt="crop"
          className="h-8 w-8 rounded object-cover border border-slate-700"
        />
      )}
      <div className="flex-1 min-w-0">
        <span className="font-bold uppercase tracking-wider">{source.evidence_class?.replace('_', ' ')}</span>
        {source.confidence != null && (
          <span className="ml-2 opacity-70">{(source.confidence * 100).toFixed(0)}%</span>
        )}
      </div>
      <span className="font-mono text-[9px] opacity-40 truncate max-w-[80px]">
        {source.evidence_id?.slice(0, 8)}
      </span>
    </div>
  );
}

function MessageBubble({ msg }) {
  const [showSources, setShowSources] = useState(false);
  const isUser = msg.role === 'user';
  const hasSources = msg.sources && msg.sources.length > 0;

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex gap-3 max-w-[85%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div
          className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center ${
            isUser
              ? 'bg-cyan-600/20 border border-cyan-500/30'
              : 'bg-emerald-600/20 border border-emerald-500/30'
          }`}
        >
          {isUser ? (
            <User className="h-4 w-4 text-cyan-400" />
          ) : (
            <Bot className="h-4 w-4 text-emerald-400" />
          )}
        </div>

        {/* Content */}
        <div className="space-y-2">
          <div
            className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
              isUser
                ? 'bg-cyan-600/15 border border-cyan-500/20 text-cyan-50 rounded-tr-sm'
                : 'bg-slate-800/70 border border-slate-700/50 text-slate-200 rounded-tl-sm'
            }`}
          >
            {/* Render answer with basic formatting */}
            {msg.content.split('\n').map((line, i) => (
              <p key={i} className={line === '' ? 'h-2' : ''}>
                {line}
              </p>
            ))}
          </div>

          {/* Sources toggle */}
          {hasSources && (
            <div>
              <button
                onClick={() => setShowSources(!showSources)}
                className="flex items-center gap-1.5 text-[11px] text-slate-400 hover:text-slate-200 transition font-mono"
              >
                <Fingerprint className="h-3 w-3" />
                {msg.sources.length} evidence source{msg.sources.length !== 1 && 's'}
                {showSources ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
              </button>
              {showSources && (
                <div className="mt-1.5 space-y-1.5">
                  {msg.sources.map((src, i) => (
                    <SourceCard key={i} source={src} />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function ChatPanel() {
  const { activeSceneId } = useScene();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [scope, setScope] = useState('scene');
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || !activeSceneId || loading) return;

    const userMsg = { role: 'user', content: text, sources: [] };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      // Build history for the API (simple role/content pairs)
      const history = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const result = await chatWithScene(activeSceneId, text, history, scope);

      const aiMsg = {
        role: 'assistant',
        content: result.answer || 'No response received.',
        sources: result.sources || [],
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      const errorMsg = {
        role: 'assistant',
        content: `Error: ${err.response?.data?.detail || err.message || 'Failed to reach the server.'}`,
        sources: [],
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const suggestions = [
    'What evidence was found in this scene?',
    'Are there any items flagged for human review?',
    'Summarize the findings for this case.',
    'Which evidence has the highest confidence?',
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-280px)] min-h-[400px]">
      {/* Scope Toggle */}
      <div className="flex items-center gap-2 mb-4">
        {SCOPE_OPTIONS.map((opt) => {
          const Icon = opt.icon;
          const isActive = scope === opt.id;
          return (
            <button
              key={opt.id}
              onClick={() => setScope(opt.id)}
              title={opt.desc}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold font-mono transition border ${
                isActive
                  ? 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30'
                  : 'text-slate-400 border-slate-700/50 hover:text-slate-200 hover:bg-surface-200'
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {opt.label}
            </button>
          );
        })}
        <span className="ml-auto text-[10px] text-slate-500 font-mono">
          RAG + CLIP Visual Search
        </span>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto rounded-xl border border-slate-800 bg-surface-300/50 p-4 space-y-1">
        {messages.length === 0 && !loading && (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-6">
            <div className="rounded-full bg-emerald-600/10 border border-emerald-500/20 p-5">
              <Bot className="h-10 w-10 text-emerald-400" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white mb-1">RAZIN Forensic Assistant</h3>
              <p className="text-xs text-slate-400 max-w-sm">
                Ask questions about evidence detected in this scene. Answers are grounded in actual evidence data via RAG retrieval.
              </p>
            </div>
            {/* Suggestion chips */}
            <div className="flex flex-wrap justify-center gap-2 max-w-lg">
              {suggestions.map((s, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setInput(s);
                    inputRef.current?.focus();
                  }}
                  className="text-[11px] px-3 py-1.5 rounded-full border border-slate-700 text-slate-400 hover:text-cyan-300 hover:border-cyan-500/30 hover:bg-cyan-500/5 transition font-mono"
                >
                  {s}
                </button>
              ))}
            </div>
            {/* Warning */}
            <div className="flex items-center gap-2 text-[10px] text-amber-400/70 bg-amber-900/10 border border-amber-500/10 rounded-lg px-3 py-2">
              <AlertTriangle className="h-3.5 w-3.5 flex-shrink-0" />
              All AI responses are preliminary and must be verified by qualified investigators.
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} />
        ))}

        {/* Typing indicator */}
        {loading && (
          <div className="flex justify-start mb-4">
            <div className="flex gap-3">
              <div className="flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center bg-emerald-600/20 border border-emerald-500/30">
                <Bot className="h-4 w-4 text-emerald-400" />
              </div>
              <div className="rounded-2xl rounded-tl-sm bg-slate-800/70 border border-slate-700/50 px-4 py-3 flex items-center gap-2">
                <Loader2 className="h-4 w-4 text-emerald-400 animate-spin" />
                <span className="text-xs text-slate-400 font-mono">Analyzing evidence...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input Bar */}
      <div className="mt-3 flex gap-2">
        <div className="flex-1 relative">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about the evidence..."
            rows={1}
            disabled={loading}
            className="w-full resize-none rounded-xl border border-slate-700 bg-surface-200 px-4 py-3 pr-12 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 focus:border-cyan-500/40 transition disabled:opacity-50 font-mono"
          />
        </div>
        <button
          onClick={sendMessage}
          disabled={!input.trim() || loading}
          className="flex items-center justify-center h-12 w-12 rounded-xl bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-700 disabled:text-slate-500 text-white transition-all shadow-lg shadow-cyan-900/30 disabled:shadow-none"
        >
          {loading ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <Send className="h-5 w-5" />
          )}
        </button>
      </div>
    </div>
  );
}
