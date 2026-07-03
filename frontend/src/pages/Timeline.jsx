import React, { useEffect, useState } from 'react';
import { clearDocuments, getTimeline } from '../api';
import { USER_ID } from '../App';
import {
  CalendarDays,
  ExternalLink,
  File,
  FileText,
  Github,
  Image,
  RefreshCw,
  Trash2,
} from 'lucide-react';

const TYPE_CONFIG = {
  github: { color: '#3B82F6', icon: Github, label: 'GitHub' },
  pdf: { color: '#EF4444', icon: FileText, label: 'PDF' },
  image: { color: '#F59E0B', icon: Image, label: 'Image' },
  docx: { color: '#10B981', icon: FileText, label: 'Document' },
  markdown: { color: '#8B5CF6', icon: File, label: 'Markdown' },
};

export default function Timeline() {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [clearing, setClearing] = useState(false);
  const [error, setError] = useState('');

  const loadTimeline = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await getTimeline(USER_ID);
      setDocs(res.data.documents || []);
    } catch {
      setError('Failed to load timeline. Make sure documents are ingested.');
    } finally {
      setLoading(false);
    }
  };

  const handleClear = async () => {
    const confirmed = window.confirm('Clear all indexed documents for this demo user?');
    if (!confirmed) return;

    setClearing(true);
    setError('');
    try {
      await clearDocuments(USER_ID);
      setDocs([]);
    } catch {
      setError('Failed to clear documents. Make sure the backend is running.');
    } finally {
      setClearing(false);
    }
  };

  useEffect(() => { loadTimeline(); }, []);

  if (loading) {
    return (
      <div className="card" style={{ maxWidth: '680px', margin: '80px auto', textAlign: 'center' }}>
        <CalendarDays size={34} color="#3B82F6" style={{ margin: '0 auto 12px' }} />
        <p style={{ color: '#94A3B8' }}>Loading your journey...</p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px', marginBottom: '32px' }}>
        <div>
          <div style={{ display: 'inline-flex', gap: '8px', alignItems: 'center', color: '#F59E0B', fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '10px' }}>
            <CalendarDays size={15} />
            Digital journey
          </div>
          <h1 style={{ fontSize: '32px', fontWeight: 800, marginBottom: '8px' }}>Your Journey</h1>
          <p style={{ color: '#94A3B8' }}>
            {docs.length} evidence item{docs.length === 1 ? '' : 's'} organized chronologically.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
          <button onClick={handleClear} disabled={clearing}
            style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              padding: '10px 16px', borderRadius: '8px',
              border: '1px solid #EF4444', background: '#450A0A22',
              color: '#FCA5A5', cursor: clearing ? 'not-allowed' : 'pointer',
            }}>
            <Trash2 size={14} /> {clearing ? 'Clearing...' : 'Clear Demo Data'}
          </button>
          <button onClick={loadTimeline} className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {error && <div className="card" style={{ borderColor: '#EF4444', color: '#EF4444', marginBottom: '24px' }}>{error}</div>}

      {docs.length === 0 && !error && (
        <div className="card" style={{ textAlign: 'center', padding: '56px' }}>
          <FileText size={42} color="#3B82F6" style={{ margin: '0 auto 16px' }} />
          <h3 style={{ fontSize: '18px', marginBottom: '8px' }}>No memories yet</h3>
          <p style={{ color: '#94A3B8', fontSize: '14px' }}>Upload certificates, resumes, reports, or GitHub links to build your timeline.</p>
        </div>
      )}

      <div style={{ position: 'relative' }}>
        {docs.length > 0 && (
          <div style={{
            position: 'absolute', left: '22px', top: '26px',
            width: '2px', height: 'calc(100% - 52px)',
            background: 'linear-gradient(to bottom, #3B82F6, #10B981, #1E3A5F)',
          }} />
        )}

        {docs.map((doc) => {
          const config = TYPE_CONFIG[doc.type] || TYPE_CONFIG.pdf;
          const Icon = config.icon;

          return (
            <div key={doc.id} style={{ display: 'flex', gap: '22px', marginBottom: '24px', position: 'relative' }}>
              <div style={{
                width: '44px', height: '44px', borderRadius: '50%',
                background: config.color + '22',
                border: `2px solid ${config.color}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0, zIndex: 1, boxShadow: `0 0 24px ${config.color}33`,
              }}>
                <Icon size={17} color={config.color} />
              </div>

              <div className="card interactive-card" style={{ flex: 1, padding: '18px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px', marginBottom: '10px' }}>
                  <div>
                    <span className={`badge badge-${doc.type}`}>{config.label}</span>
                    <h3 style={{ fontSize: '16px', fontWeight: 700, marginTop: '8px', color: '#E2E8F0' }}>{doc.label}</h3>
                  </div>
                  <span style={{ fontSize: '12px', color: '#94A3B8', fontFamily: 'JetBrains Mono, monospace', flexShrink: 0 }}>
                    {doc.date || 'No date'}
                  </span>
                </div>
                <p style={{ fontSize: '12px', color: '#64748B', wordBreak: 'break-all' }}>{doc.id}</p>
                {doc.original_file_url && (
                  <a href={doc.original_file_url} target="_blank" rel="noreferrer"
                    style={{ marginTop: '12px', display: 'inline-flex', alignItems: 'center', gap: '6px', color: '#3B82F6', fontSize: '12px', textDecoration: 'none' }}>
                    <ExternalLink size={13} /> View Original
                  </a>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
