import React, { useState } from 'react';
import { searchDocuments } from '../api';
import { USER_ID } from '../App';
import { Search, Zap, FileText} from 'lucide-react';

const SUGGESTIONS = [
  'What programming skills do I have?',
  'What projects have I worked on?',
  'What machine learning techniques do I know?',
  'What tools and technologies have I used?',
];

export default function Dashboard() {
  const [query,      setQuery]      = useState('');
  const [result,     setResult]     = useState(null);
  const [loading,    setLoading]    = useState(false);
  const [error,      setError]      = useState('');

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
      setError('Search failed. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>

      {/* ── Header ──────────────────────────────────────────────────── */}
      <div style={{ marginBottom: '40px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '8px' }}>
          Your Digital Identity
        </h1>
        <p style={{ color: '#94A3B8', fontSize: '15px' }}>
          Ask anything about your academic and professional journey.
        </p>
      </div>

      {/* ── Search Bar ──────────────────────────────────────────────── */}
      <div style={{ position: 'relative', marginBottom: '24px' }}>
        <Search size={18} color="#94A3B8"
          style={{ position:'absolute', left:'16px', top:'50%',
            transform:'translateY(-50%)' }} />
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSearch()}
          placeholder="Ask anything about your documents..."
          style={{
            width: '100%', padding: '16px 16px 16px 48px',
            background: '#1A2F4A', border: '1px solid #1E3A5F',
            borderRadius: '12px', color: '#E2E8F0', fontSize: '15px',
            outline: 'none',
          }}
        />
        <button onClick={() => handleSearch()} disabled={loading}
          className="btn-primary"
          style={{ position:'absolute', right:'8px', top:'50%',
            transform:'translateY(-50%)', padding:'8px 16px' }}>
          {loading ? '...' : 'Ask'}
        </button>
      </div>

      {/* ── Suggested Prompts ───────────────────────────────────────── */}
      {!result && !loading && (
        <div style={{ display:'flex', flexWrap:'wrap', gap:'8px', marginBottom:'32px' }}>
          {SUGGESTIONS.map(s => (
            <button key={s} onClick={() => handleSearch(s)}
              style={{
                padding: '8px 14px', background: '#1A2F4A',
                border: '1px solid #1E3A5F', borderRadius: '20px',
                color: '#94A3B8', fontSize: '13px', cursor: 'pointer',
                transition: 'all 0.2s',
              }}
              onMouseOver={e => e.target.style.borderColor = '#3B82F6'}
              onMouseOut={e  => e.target.style.borderColor = '#1E3A5F'}
            >
              <Zap size={12} style={{ marginRight:'4px', verticalAlign:'middle' }}/>
              {s}
            </button>
          ))}
        </div>
      )}

      {/* ── Loading ─────────────────────────────────────────────────── */}
      {loading && (
        <div className="card" style={{ textAlign:'center', padding:'40px' }}>
          <div style={{ color:'#3B82F6', marginBottom:'12px', fontSize:'24px' }}>⟳</div>
          <p style={{ color:'#94A3B8' }}>Searching your documents with AI...</p>
          <p style={{ color:'#64748B', fontSize:'12px', marginTop:'8px' }}>
            First query may take 20-30 seconds while Mistral loads
          </p>
        </div>
      )}

      {/* ── Error ───────────────────────────────────────────────────── */}
      {error && (
        <div className="card" style={{ borderColor:'#EF4444', color:'#EF4444' }}>
          {error}
        </div>
      )}

      {/* ── Results ─────────────────────────────────────────────────── */}
      {result && (
        <div style={{ display:'flex', flexDirection:'column', gap:'16px' }}>

          {/* Answer */}
          <div className="card">
            <div style={{ display:'flex', alignItems:'center', gap:'8px',
              marginBottom:'16px' }}>
              <div style={{ width:'8px', height:'8px', borderRadius:'50%',
                background: result.confidence > 0.02 ? '#10B981' : '#F59E0B' }}/>
              <span style={{ fontSize:'12px', color:'#94A3B8' }}>
                Confidence: {(result.confidence * 1000).toFixed(1)}
              </span>
            </div>
            <p style={{ lineHeight:'1.7', fontSize:'15px' }}>{result.answer}</p>
          </div>

          {/* Sources */}
          <div className="card">
            <h3 style={{ fontSize:'13px', color:'#94A3B8',
              marginBottom:'16px', textTransform:'uppercase',
              letterSpacing:'1px' }}>
              Sources Used
            </h3>
            {result.sources.map((s, i) => (
              <div key={i} style={{
                padding: '12px', background: '#112240',
                borderRadius: '8px', marginBottom: '8px',
                borderLeft: '3px solid #3B82F6',
              }}>
                <div style={{ display:'flex', justifyContent:'space-between',
                  alignItems:'center', marginBottom:'6px' }}>
                  <div style={{ display:'flex', alignItems:'center', gap:'8px' }}>
                    <FileText size={14} color="#3B82F6" />
                    <span style={{ fontSize:'13px', fontWeight:500 }}>
                      {s.document.split('/').pop() || s.document}
                    </span>
                    <span className={`badge badge-${s.type}`}>{s.type}</span>
                  </div>
                  <div style={{ display:'flex', gap:'12px', fontSize:'11px',
                    color:'#64748B' }}>
                    <span>D: {s.dense_score.toFixed(3)}</span>
                    <span>B: {s.bm25_score.toFixed(3)}</span>
                    <span style={{ color:'#3B82F6' }}>
                      F: {s.fused_score.toFixed(4)}
                    </span>
                  </div>
                </div>
                <p style={{ fontSize:'12px', color:'#64748B',
                  fontFamily:'JetBrains Mono, monospace' }}>
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