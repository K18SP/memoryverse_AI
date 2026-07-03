import React, { useEffect, useState } from 'react';
import { getTimeline } from '../api';
import { USER_ID } from '../App';
import { FileText, Github, Image, File, RefreshCw } from 'lucide-react';

const TYPE_CONFIG = {
  github  : { color:'#3B82F6', icon: Github,   label:'GitHub' },
  pdf     : { color:'#EF4444', icon: FileText,  label:'PDF' },
  image   : { color:'#F59E0B', icon: Image,     label:'Image' },
  docx    : { color:'#10B981', icon: FileText,  label:'Document' },
  markdown: { color:'#8B5CF6', icon: File,      label:'Markdown' },
};

export default function Timeline() {
  const [docs,    setDocs]    = useState([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState('');

  const loadTimeline = async () => {
    setLoading(true);
    try {
      const res = await getTimeline(USER_ID);
      setDocs(res.data.documents || []);
    } catch {
      setError('Failed to load timeline. Make sure documents are ingested.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadTimeline(); }, []);

  if (loading) return (
    <div style={{ textAlign:'center', paddingTop:'80px', color:'#94A3B8' }}>
      Loading timeline...
    </div>
  );

  return (
    <div style={{ maxWidth:'700px', margin:'0 auto' }}>
      <div style={{ display:'flex', justifyContent:'space-between',
        alignItems:'center', marginBottom:'40px' }}>
        <div>
          <h1 style={{ fontSize:'28px', fontWeight:700, marginBottom:'8px' }}>
            Your Journey
          </h1>
          <p style={{ color:'#94A3B8' }}>
            {docs.length} documents in your knowledge base
          </p>
        </div>
        <button onClick={loadTimeline} className="btn-primary"
          style={{ display:'flex', alignItems:'center', gap:'6px' }}>
          <RefreshCw size={14}/> Refresh
        </button>
      </div>

      {error && (
        <div className="card" style={{ borderColor:'#EF4444', color:'#EF4444',
          marginBottom:'24px' }}>
          {error}
        </div>
      )}

      {docs.length === 0 && !error && (
        <div className="card" style={{ textAlign:'center', padding:'48px' }}>
          <FileText size={40} color="#1E3A5F"
            style={{ margin:'0 auto 16px' }} />
          <p style={{ color:'#94A3B8' }}>No documents yet.</p>
          <p style={{ color:'#64748B', fontSize:'13px', marginTop:'8px' }}>
            Upload documents to see your timeline.
          </p>
        </div>
      )}

      {/* ── Timeline ────────────────────────────────────────────────── */}
      <div style={{ position:'relative' }}>
        {/* Vertical line */}
        {docs.length > 0 && (
          <div style={{
            position:'absolute', left:'19px', top:'24px',
            width:'2px', height:'calc(100% - 48px)',
            background:'linear-gradient(to bottom, #3B82F6, #1E3A5F)',
          }}/>
        )}

        {docs.map((doc, i) => {
          const config = TYPE_CONFIG[doc.type] || TYPE_CONFIG['pdf'];
          const Icon   = config.icon;

          return (
            <div key={doc.id} style={{
              display:'flex', gap:'24px', marginBottom:'32px',
              position:'relative',
            }}>
              {/* Circle on timeline */}
              <div style={{
                width:'40px', height:'40px', borderRadius:'50%',
                background: config.color + '22',
                border: `2px solid ${config.color}`,
                display:'flex', alignItems:'center', justifyContent:'center',
                flexShrink:0, zIndex:1,
              }}>
                <Icon size={16} color={config.color} />
              </div>

              {/* Card */}
              <div className="card" style={{ flex:1, padding:'16px' }}>
                <div style={{ display:'flex', justifyContent:'space-between',
                  alignItems:'flex-start', marginBottom:'8px' }}>
                  <div>
                    <span className={`badge badge-${doc.type}`}>
                      {config.label}
                    </span>
                    <h3 style={{ fontSize:'14px', fontWeight:600,
                      marginTop:'8px', color:'#E2E8F0' }}>
                      {doc.label}
                    </h3>
                  </div>
                  <span style={{ fontSize:'12px', color:'#64748B',
                    fontFamily:'JetBrains Mono, monospace' }}>
                    {doc.date || 'No date'}
                  </span>
                </div>
                <p style={{ fontSize:'12px', color:'#64748B',
                  wordBreak:'break-all' }}>
                  {doc.id}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}