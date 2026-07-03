import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { ingestFile, ingestGithub, buildGraph } from '../api';
import { USER_ID } from '../App';
import { Upload as UploadIcon, Github, Loader, Database, Network } from 'lucide-react';

const ACCEPTED = {
  'application/pdf'      : ['.pdf'],
  'image/png'            : ['.png'],
  'image/jpeg'           : ['.jpg', '.jpeg'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/markdown'        : ['.md'],
  'text/plain'           : ['.txt'],
};

export default function Upload() {
  const [logs,       setLogs]       = useState([]);
  const [githubUrl,  setGithubUrl]  = useState('');
  const [loading,    setLoading]    = useState(false);

  const addLog = (message, type = 'info') => {
    setLogs(prev => [...prev, { message, type, time: new Date().toLocaleTimeString() }]);
  };

  const processFile = async (file) => {
    setLoading(true);
    addLog(`Processing: ${file.name}`, 'info');

    try {
      addLog('Extracting text...', 'info');
      const res = await ingestFile(file, USER_ID);
      addLog(`Done: extracted ${res.data.char_count} characters`, 'success');
      addLog(`Done: created ${res.data.chunk_count} chunks`, 'success');
      addLog(`Done: generated embeddings and indexed ${res.data.upserted} vectors`, 'success');
      addLog(`Done: document stored as ${res.data.doc_id}`, 'success');

      // Auto-build graph after each upload
      addLog('Updating knowledge graph...', 'info');
      const graphRes = await buildGraph(USER_ID);
      addLog(`Done: graph updated with ${graphRes.data.graph_summary.nodes} nodes and ${graphRes.data.graph_summary.edges} edges`, 'success');

    } catch (e) {
      addLog(`Failed: ${e.response?.data?.detail || e.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const processGithub = async () => {
    if (!githubUrl.trim()) return;
    setLoading(true);
    addLog(`Fetching GitHub: ${githubUrl}`, 'info');

    try {
      addLog('Calling GitHub API...', 'info');
      const res = await ingestGithub(githubUrl, USER_ID);
      addLog(`Done: fetched ${res.data.char_count} characters`, 'success');
      addLog(`Done: created ${res.data.chunk_count} chunks`, 'success');
      addLog(`Done: indexed ${res.data.upserted} vectors`, 'success');

      addLog('Updating knowledge graph...', 'info');
      const graphRes = await buildGraph(USER_ID);
      addLog(`Done: graph now has ${graphRes.data.graph_summary.nodes} nodes`, 'success');
      setGithubUrl('');
    } catch (e) {
      addLog(`Failed: ${e.response?.data?.detail || e.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const onDrop = useCallback(acceptedFiles => {
    acceptedFiles.forEach(processFile);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: ACCEPTED, disabled: loading,
  });

  const logColor = { info:'#94A3B8', success:'#10B981', error:'#EF4444' };

  return (
    <div style={{ maxWidth:'860px', margin:'0 auto' }}>
      <div style={{ marginBottom:'28px' }}>
        <div style={{ display:'inline-flex', gap:'8px', alignItems:'center',
          color:'#3B82F6', fontSize:'12px', fontWeight:700,
          textTransform:'uppercase', letterSpacing:'0.8px', marginBottom:'10px' }}>
          <Database size={15} />
          Evidence ingestion
        </div>
        <h1 style={{ fontSize:'34px', fontWeight:800, marginBottom:'8px' }}>
          Upload Documents
        </h1>
        <p style={{ color:'#94A3B8', fontSize:'16px', lineHeight:1.6 }}>
          Add certificates, resumes, reports, and GitHub repositories. MemoryVerse extracts text, preserves originals, indexes vectors, and updates your graph.
        </p>
      </div>

      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:'12px', marginBottom:'24px' }}>
        {[
          ['Extract', 'PDF/OCR/text parsing', UploadIcon, '#3B82F6'],
          ['Embed', 'Semantic vector index', Database, '#10B981'],
          ['Connect', 'Knowledge graph update', Network, '#F59E0B'],
        ].map(([title, detail, Icon, color]) => (
          <div key={title} className="card interactive-card" style={{ padding:'16px' }}>
            <Icon size={18} color={color} style={{ marginBottom:'10px' }} />
            <div style={{ fontSize:'13px', fontWeight:700, marginBottom:'4px' }}>{title}</div>
            <div style={{ color:'#94A3B8', fontSize:'12px' }}>{detail}</div>
          </div>
        ))}
      </div>

      {/* ── Dropzone ────────────────────────────────────────────────── */}
      <div {...getRootProps()} className="interactive-card" style={{
        border: `2px dashed ${isDragActive ? '#3B82F6' : '#1E3A5F'}`,
        borderRadius: '12px', padding: '48px',
        textAlign: 'center', cursor: loading ? 'not-allowed' : 'pointer',
        background: isDragActive ? '#1E3A5F44' : '#112240',
        transition: 'all 0.2s', marginBottom: '24px',
      }}>
        <input {...getInputProps()} />
        <UploadIcon size={40} color={isDragActive ? '#3B82F6' : '#1E3A5F'}
          style={{ margin: '0 auto 16px' }} />
        <p style={{ color:'#E2E8F0', fontWeight:500, marginBottom:'8px' }}>
          {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
        </p>
        <p style={{ color:'#64748B', fontSize:'13px' }}>
          PDF, DOCX, PNG, JPG, MD, TXT - max 20MB each
        </p>
      </div>

      {/* ── GitHub URL ──────────────────────────────────────────────── */}
      <div className="card interactive-card" style={{ marginBottom:'24px' }}>
        <div style={{ display:'flex', alignItems:'center', gap:'8px',
          marginBottom:'16px' }}>
          <Github size={18} color="#94A3B8" />
          <span style={{ fontWeight:500 }}>Add GitHub Repository</span>
        </div>
        <div style={{ display:'flex', gap:'8px' }}>
          <input
            value={githubUrl}
            onChange={e => setGithubUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && processGithub()}
            placeholder="https://github.com/username/repo"
            style={{
              flex:1, padding:'10px 14px',
              background:'#112240', border:'1px solid #1E3A5F',
              borderRadius:'8px', color:'#E2E8F0', fontSize:'14px',
              outline:'none',
            }}
          />
          <button onClick={processGithub} disabled={loading || !githubUrl.trim()}
            className="btn-primary">
            {loading ? <Loader size={14}/> : 'Add'}
          </button>
        </div>
      </div>

      {/* ── Processing Log ──────────────────────────────────────────── */}
      {logs.length > 0 && (
        <div className="card">
          <h3 style={{ fontSize:'13px', color:'#94A3B8', marginBottom:'16px',
            textTransform:'uppercase', letterSpacing:'1px' }}>
            Processing Log
          </h3>
        <div style={{ fontFamily:'JetBrains Mono, monospace', fontSize:'12px' }}>
            {logs.map((log, i) => (
              <div key={i} style={{
                display:'flex', gap:'12px', padding:'4px 0',
                color: logColor[log.type],
              }}>
                <span style={{ color:'#475569', minWidth:'60px' }}>{log.time}</span>
                <span>{log.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
