import React, { useState } from 'react';
import { searchDocuments } from '../api';
import { USER_ID } from '../App';
import {
  Clock,
  ExternalLink,
  FileText,
  Network,
  Search,
  ShieldCheck,
  Sparkles,
  Target,
  Zap,
} from 'lucide-react';

const SUGGESTIONS = [
  'Technical skills',
  'Show my certificates',
  'What projects have I built?',
  'About internships',
  'Give my profile summary',
  'What proves I know Python?',
];

const HIGHLIGHTS = [
  { label: 'Semantic Retrieval', detail: 'Vector + keyword search', icon: Search, color: '#3B82F6' },
  { label: 'Knowledge Graph', detail: 'Skills linked to evidence', icon: Network, color: '#10B981' },
  { label: 'Journey Timeline', detail: 'Growth over time', icon: Clock, color: '#F59E0B' },
  { label: 'Growth Coach', detail: 'Gap + interview prep', icon: Target, color: '#8B5CF6' },
];

export default function Dashboard() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async (q) => {
    const searchQuery = q || query;
    if (!searchQuery.trim()) return;

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const res = await searchDocuments(searchQuery, USER_ID);
      setResult(res.data);
      setQuery(searchQuery);
    } catch (e) {
      setError(e.response?.data?.detail || 'Search failed. Make sure the backend is running and documents are indexed.');
    } finally {
      setLoading(false);
    }
  };

  const scoreText = (value, digits = 3) => {
    const number = Number(value);
    return Number.isFinite(number) ? number.toFixed(digits) : '0.000';
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ marginBottom: '28px' }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          color: '#10B981',
          fontSize: '12px',
          fontWeight: 600,
          background: '#064E3B33',
          border: '1px solid #065F46',
          borderRadius: '999px',
          padding: '6px 10px',
          marginBottom: '14px',
        }}>
          <span className="pulse-dot" />
          Live AI memory system
        </div>

        <h1 style={{ fontSize: '34px', fontWeight: 800, marginBottom: '8px' }}>
          Your Digital Identity
        </h1>
        <p style={{ color: '#94A3B8', fontSize: '16px', maxWidth: '680px', lineHeight: 1.6 }}>
          Ask anything about your academic and professional journey. Every answer is grounded in uploaded evidence and linked back to the original file.
        </p>
      </div>

      {!result && !loading && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, minmax(0, 1fr))',
          gap: '12px',
          marginBottom: '24px',
        }}>
          {HIGHLIGHTS.map(item => {
            const Icon = item.icon;
            return (
              <div key={item.label} className="card interactive-card" style={{ padding: '16px', borderRadius: '10px' }}>
                <div style={{
                  width: '34px',
                  height: '34px',
                  borderRadius: '8px',
                  background: item.color + '22',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '12px',
                }}>
                  <Icon size={17} color={item.color} />
                </div>
                <div style={{ fontSize: '13px', fontWeight: 700, marginBottom: '4px' }}>
                  {item.label}
                </div>
                <div style={{ color: '#94A3B8', fontSize: '12px' }}>
                  {item.detail}
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div style={{ position: 'relative', marginBottom: '18px' }}>
        <Search
          size={18}
          color="#94A3B8"
          style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)' }}
        />
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSearch()}
          placeholder="Ask anything about your documents..."
          style={{
            width: '100%',
            padding: '16px 92px 16px 48px',
            background: '#1A2F4A',
            border: '1px solid #1E3A5F',
            borderRadius: '12px',
            color: '#E2E8F0',
            fontSize: '15px',
            outline: 'none',
            boxShadow: '0 14px 40px rgba(0,0,0,0.18)',
          }}
        />
        <button
          onClick={() => handleSearch()}
          disabled={loading}
          className="btn-primary"
          style={{ position: 'absolute', right: '8px', top: '50%', transform: 'translateY(-50%)', padding: '8px 16px' }}
        >
          {loading ? '...' : 'Ask'}
        </button>
      </div>

      {!result && !loading && (
        <div style={{ marginBottom: '28px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            color: '#94A3B8',
            fontSize: '12px',
            fontWeight: 600,
            marginBottom: '10px',
            textTransform: 'uppercase',
            letterSpacing: '0.8px',
          }}>
            <Sparkles size={14} color="#F59E0B" />
            Try these demo questions
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {SUGGESTIONS.map(s => (
              <button
                key={s}
                onClick={() => handleSearch(s)}
                className="prompt-button"
                style={{
                  padding: '8px 14px',
                  background: '#1A2F4A',
                  border: '1px solid #1E3A5F',
                  borderRadius: '20px',
                  color: '#94A3B8',
                  fontSize: '13px',
                  cursor: 'pointer',
                }}
              >
                <Zap size={12} style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {loading && (
        <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
          <Search size={28} color="#3B82F6" style={{ margin: '0 auto 12px' }} />
          <p style={{ color: '#94A3B8' }}>Searching your documents with AI...</p>
          <p style={{ color: '#64748B', fontSize: '12px', marginTop: '8px' }}>
            Retrieving semantic matches, checking keywords, and grounding the answer in sources.
          </p>
        </div>
      )}

      {error && (
        <div className="card" style={{ borderColor: '#EF4444', color: '#EF4444' }}>
          {error}
        </div>
      )}

      {result && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="card interactive-card" style={{ borderColor: '#2563EB' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <ShieldCheck size={16} color={result.confidence > 0.02 ? '#10B981' : '#F59E0B'} />
              <span style={{ fontSize: '12px', color: '#94A3B8' }}>
                Grounded confidence: {(Number(result.confidence || 0) * 1000).toFixed(1)}
              </span>
            </div>
            <p style={{ lineHeight: '1.75', fontSize: '15px', whiteSpace: 'pre-line' }}>
              {result.answer}
            </p>
            {result.answer_mode && (
              <p style={{ color: '#64748B', fontSize: '12px', marginTop: '12px' }}>
                Mode: {result.answer_mode === 'ai_enriched' ? 'AI enriched' : 'instant retrieval'}
              </p>
            )}
          </div>

          <div className="card">
            <h3 style={{
              fontSize: '13px',
              color: '#94A3B8',
              marginBottom: '16px',
              textTransform: 'uppercase',
              letterSpacing: '1px',
            }}>
              Sources Used
            </h3>

            {(result.sources || []).length === 0 && (
              <p style={{ color: '#64748B', fontSize: '13px' }}>
                No source chunks returned. Upload a document first, then search again.
              </p>
            )}

            {(result.sources || []).map((s, i) => (
              <div key={i} className="interactive-card" style={{
                padding: '12px',
                background: '#112240',
                borderRadius: '8px',
                marginBottom: '8px',
                borderLeft: '3px solid #3B82F6',
              }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  gap: '12px',
                  marginBottom: '6px',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    <FileText size={14} color="#3B82F6" />
                    <span style={{ fontSize: '13px', fontWeight: 500 }}>
                      {s.document.split('/').pop() || s.document}
                    </span>
                    <span className={`badge badge-${s.type}`}>{s.type}</span>
                    {s.original_file_url && (
                      <a
                        href={s.original_file_url}
                        target="_blank"
                        rel="noreferrer"
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          color: '#3B82F6',
                          fontSize: '12px',
                          textDecoration: 'none',
                        }}
                      >
                        <ExternalLink size={12} /> View Original
                      </a>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: '12px', fontSize: '11px', color: '#64748B', flexShrink: 0 }}>
                    <span>D: {scoreText(s.dense_score)}</span>
                    <span>B: {scoreText(s.bm25_score)}</span>
                    <span style={{ color: '#3B82F6' }}>F: {scoreText(s.fused_score, 4)}</span>
                  </div>
                </div>
                <p style={{
                  fontSize: '12px',
                  color: '#64748B',
                  fontFamily: 'JetBrains Mono, monospace',
                  lineHeight: 1.5,
                }}>
                  {s.preview}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
