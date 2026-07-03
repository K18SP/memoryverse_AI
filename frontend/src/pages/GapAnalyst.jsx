import React, { useState } from 'react';
import axios from 'axios';
import {
  BookOpen,
  CheckCircle,
  ExternalLink,
  Target,
  TrendingUp,
  XCircle,
  Zap,
} from 'lucide-react';
import { USER_ID } from '../App';

const ROLES = [
  'ML Engineer',
  'Data Scientist',
  'Data Analyst',
  'Backend Developer',
  'Full Stack Developer',
  'AI Research Engineer',
];

export default function GapAnalyst() {
  const [role, setRole] = useState('');
  const [jd, setJd] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const runAnalysis = async () => {
    if (!role.trim()) return;
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const form = new FormData();
      form.append('user_id', USER_ID);
      form.append('target_role', role);
      form.append('job_description', jd);
      const res = await axios.post('/api/v1/gap-analysis', form);
      setResult(res.data);
    } catch {
      setError('Analysis failed. Upload documents and rebuild the graph first.');
    } finally {
      setLoading(false);
    }
  };

  const scoreColor = (pct) => {
    if (pct >= 75) return '#10B981';
    if (pct >= 50) return '#F59E0B';
    return '#EF4444';
  };

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto' }}>
      <div style={{ marginBottom: '28px' }}>
        <div style={{ display: 'inline-flex', gap: '8px', alignItems: 'center', color: '#8B5CF6', fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '10px' }}>
          <TrendingUp size={15} />
          Growth compass
        </div>
        <h1 style={{ fontSize: '34px', fontWeight: 800, marginBottom: '8px' }}>Skill Gap Analyst</h1>
        <p style={{ color: '#94A3B8', fontSize: '16px', lineHeight: 1.6 }}>
          Compare your evidence-backed skills against a target role and get a focused learning roadmap.
        </p>
      </div>

      <div className="card interactive-card" style={{ marginBottom: '24px' }}>
        <label style={{ fontSize: '13px', color: '#94A3B8', display: 'block', marginBottom: '10px' }}>
          Target Role
        </label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '14px' }}>
          {ROLES.map(r => (
            <button
              key={r}
              onClick={() => setRole(r)}
              className="prompt-button"
              style={{
                padding: '7px 13px',
                borderRadius: '20px',
                fontSize: '12px',
                border: `1px solid ${role === r ? '#3B82F6' : '#1E3A5F'}`,
                background: role === r ? '#1E3A5F' : 'transparent',
                color: role === r ? '#3B82F6' : '#94A3B8',
                cursor: 'pointer',
              }}
            >
              {r}
            </button>
          ))}
        </div>

        <input
          value={role}
          onChange={e => setRole(e.target.value)}
          placeholder="Or type a custom role..."
          style={{ width: '100%', padding: '12px 14px', background: '#112240', border: '1px solid #1E3A5F', borderRadius: '8px', color: '#E2E8F0', fontSize: '14px', outline: 'none', marginBottom: '16px' }}
        />

        <label style={{ fontSize: '13px', color: '#94A3B8', display: 'block', marginBottom: '8px' }}>
          Job Description
        </label>
        <textarea
          value={jd}
          onChange={e => setJd(e.target.value)}
          placeholder="Optional: paste a job description for sharper recommendations..."
          rows={4}
          style={{ width: '100%', padding: '12px 14px', background: '#112240', border: '1px solid #1E3A5F', borderRadius: '8px', color: '#E2E8F0', fontSize: '14px', outline: 'none', resize: 'vertical', fontFamily: 'inherit', marginBottom: '16px' }}
        />

        <button onClick={runAnalysis} disabled={loading || !role.trim()} className="btn-primary" style={{ width: '100%', padding: '12px', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}>
          <Zap size={16} /> {loading ? 'Analysing profile...' : 'Run Gap Analysis'}
        </button>
      </div>

      {error && <div className="card" style={{ borderColor: '#EF4444', color: '#EF4444', marginBottom: '24px' }}>{error}</div>}

      {result && !result.error && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="card interactive-card" style={{ textAlign: 'center', borderColor: scoreColor(result.match_percentage) }}>
            <div style={{ fontSize: '68px', fontWeight: 800, color: scoreColor(result.match_percentage), lineHeight: 1 }}>
              {result.match_percentage}%
            </div>
            <div style={{ color: '#94A3B8', marginTop: '8px', fontSize: '15px' }}>
              Match for <strong style={{ color: '#E2E8F0' }}>{role}</strong>
            </div>
            {result.analysis_mode && (
              <div style={{ color: '#64748B', marginTop: '8px', fontSize: '12px' }}>
                Mode: {result.analysis_mode === 'llm_enriched' ? 'AI enriched' : 'instant skill-map'}
              </div>
            )}
            {result.overall_readiness && (
              <p style={{ color: '#94A3B8', marginTop: '16px', fontSize: '14px', lineHeight: 1.6, maxWidth: '560px', marginLeft: 'auto', marginRight: 'auto' }}>
                {result.overall_readiness}
              </p>
            )}
          </div>

          {result.radar_data?.length > 0 && (
            <div className="card">
              <h3 style={{ fontSize: '15px', fontWeight: 700, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Target size={17} color="#3B82F6" /> Skill Radar
              </h3>
              {result.radar_data.map((item, i) => (
                <div key={i} style={{ marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '13px', color: '#E2E8F0' }}>{item.axis}</span>
                    <span style={{ fontSize: '12px', color: '#94A3B8' }}>{item.current}% / {item.required}%</span>
                  </div>
                  <div style={{ height: '8px', background: '#112240', borderRadius: '999px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${item.current}%`, background: item.current >= item.required ? '#10B981' : '#3B82F6', borderRadius: '999px', transition: 'width 0.8s ease' }} />
                  </div>
                </div>
              ))}
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <SkillList title="Matching Skills" icon={CheckCircle} color="#10B981" items={result.matching_skills} />
            <SkillList title="Missing Skills" icon={XCircle} color="#EF4444" items={result.missing_skills} />
          </div>

          {result.recommendations?.length > 0 && (
            <div className="card">
              <h3 style={{ fontSize: '15px', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <BookOpen size={17} color="#F59E0B" /> Learning Roadmap
              </h3>
              {result.recommendations.map((rec, i) => (
                <div key={i} className="interactive-card" style={{ padding: '16px', background: '#112240', borderRadius: '8px', marginBottom: '12px', borderLeft: '3px solid #F59E0B' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontWeight: 700, color: '#E2E8F0', fontSize: '14px' }}>{rec.skill}</span>
                    {rec.time_weeks && <span style={{ fontSize: '11px', color: '#F59E0B', background: '#451A0333', padding: '3px 9px', borderRadius: '10px' }}>~{rec.time_weeks} weeks</span>}
                  </div>
                  <p style={{ fontSize: '13px', color: '#94A3B8', marginBottom: '10px', lineHeight: 1.5 }}>{rec.reason}</p>
                  {rec.resource && (
                    rec.resource_url ? (
                      <a href={rec.resource_url} target="_blank" rel="noreferrer" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#F59E0B', textDecoration: 'none' }}>
                        <ExternalLink size={13} /> {rec.resource}
                      </a>
                    ) : <span style={{ fontSize: '12px', color: '#F59E0B' }}>{rec.resource}</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {result?.error && <div className="card" style={{ borderColor: '#EF4444', color: '#EF4444' }}>{result.error}</div>}
    </div>
  );
}

function SkillList({ title, icon: Icon, color, items = [] }) {
  return (
    <div className="card">
      <h3 style={{ fontSize: '13px', color, marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
        <Icon size={14} /> {title}
      </h3>
      {items.length === 0 ? (
        <p style={{ color: '#64748B', fontSize: '13px' }}>No items found.</p>
      ) : items.map((item, i) => (
        <div key={i} style={{ padding: '7px 9px', background: color + '18', borderRadius: '6px', marginBottom: '6px', fontSize: '13px', color }}>
          {item}
        </div>
      ))}
    </div>
  );
}
