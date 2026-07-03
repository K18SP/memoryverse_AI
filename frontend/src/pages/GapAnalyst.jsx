import React, { useState } from 'react';
import { USER_ID } from '../App';
import axios from 'axios';
import { Target, BookOpen, CheckCircle, XCircle } from 'lucide-react';

const ROLES = [
  'ML Engineer', 'Data Scientist', 'Data Analyst',
  'Backend Developer', 'Full Stack Developer', 'AI Research Engineer',
];

export default function GapAnalyst() {
  const [role,    setRole]    = useState('');
  const [jd,      setJd]      = useState('');
  const [result,  setResult]  = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');

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
    } catch (e) {
      setError('Analysis failed. Make sure documents are uploaded and graph is built.');
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
    <div style={{ maxWidth:'800px', margin:'0 auto' }}>
      <div style={{ marginBottom:'32px' }}>
        <h1 style={{ fontSize:'28px', fontWeight:700, marginBottom:'8px' }}>
          Skill Gap Analyst
        </h1>
        <p style={{ color:'#94A3B8' }}>
          Compare your skills against any job role and get a personalised learning plan.
        </p>
      </div>

      {/* ── Input ───────────────────────────────────────────────────── */}
      <div className="card" style={{ marginBottom:'24px' }}>
        <div style={{ marginBottom:'16px' }}>
          <label style={{ fontSize:'13px', color:'#94A3B8',
            display:'block', marginBottom:'8px' }}>
            Target Role
          </label>
          {/* Quick role buttons */}
          <div style={{ display:'flex', flexWrap:'wrap', gap:'8px',
            marginBottom:'12px' }}>
            {ROLES.map(r => (
              <button key={r} onClick={() => setRole(r)}
                style={{
                  padding:'6px 12px', borderRadius:'20px', fontSize:'12px',
                  border:`1px solid ${role === r ? '#3B82F6' : '#1E3A5F'}`,
                  background: role === r ? '#1E3A5F' : 'transparent',
                  color: role === r ? '#3B82F6' : '#64748B',
                  cursor:'pointer', transition:'all 0.2s',
                }}>
                {r}
              </button>
            ))}
          </div>
          <input
            value={role}
            onChange={e => setRole(e.target.value)}
            placeholder="Or type a custom role..."
            style={{
              width:'100%', padding:'10px 14px',
              background:'#112240', border:'1px solid #1E3A5F',
              borderRadius:'8px', color:'#E2E8F0', fontSize:'14px',
              outline:'none',
            }}
          />
        </div>

        <div style={{ marginBottom:'16px' }}>
          <label style={{ fontSize:'13px', color:'#94A3B8',
            display:'block', marginBottom:'8px' }}>
            Job Description (optional — paste for more accuracy)
          </label>
          <textarea
            value={jd}
            onChange={e => setJd(e.target.value)}
            placeholder="Paste job description here..."
            rows={4}
            style={{
              width:'100%', padding:'10px 14px',
              background:'#112240', border:'1px solid #1E3A5F',
              borderRadius:'8px', color:'#E2E8F0', fontSize:'14px',
              outline:'none', resize:'vertical', fontFamily:'inherit',
            }}
          />
        </div>

        <button onClick={runAnalysis}
          disabled={loading || !role.trim()}
          className="btn-primary"
          style={{ width:'100%', padding:'12px' }}>
          {loading ? '⟳ Analysing (30-60 seconds)...' : '⚡ Run Gap Analysis'}
        </button>
      </div>

      {error && (
        <div className="card" style={{ borderColor:'#EF4444',
          color:'#EF4444', marginBottom:'24px' }}>
          {error}
        </div>
      )}

      {/* ── Results ─────────────────────────────────────────────────── */}
      {result && !result.error && (
        <div style={{ display:'flex', flexDirection:'column', gap:'16px' }}>

          {/* Match Score */}
          <div className="card" style={{ textAlign:'center' }}>
            <div style={{
              fontSize:'64px', fontWeight:700,
              color: scoreColor(result.match_percentage),
              lineHeight:1,
            }}>
              {result.match_percentage}%
            </div>
            <div style={{ color:'#94A3B8', marginTop:'8px', fontSize:'15px' }}>
              Match for <strong style={{ color:'#E2E8F0' }}>{role}</strong>
            </div>
            {result.overall_readiness && (
              <p style={{ color:'#94A3B8', marginTop:'16px', fontSize:'14px',
                lineHeight:'1.6', maxWidth:'500px', margin:'16px auto 0' }}>
                {result.overall_readiness}
              </p>
            )}
          </div>

          {/* Skill Radar — simple bar chart version */}
          {result.radar_data?.length > 0 && (
            <div className="card">
              <h3 style={{ fontSize:'14px', fontWeight:600,
                marginBottom:'20px', display:'flex', alignItems:'center',
                gap:'8px' }}>
                <Target size={16} color="#3B82F6"/> Skill Radar
              </h3>
              {result.radar_data.map((item, i) => (
                <div key={i} style={{ marginBottom:'16px' }}>
                  <div style={{ display:'flex', justifyContent:'space-between',
                    marginBottom:'6px' }}>
                    <span style={{ fontSize:'13px', color:'#E2E8F0' }}>
                      {item.axis}
                    </span>
                    <span style={{ fontSize:'12px', color:'#64748B' }}>
                      {item.current}% / {item.required}%
                    </span>
                  </div>
                  {/* Required bar */}
                  <div style={{ height:'6px', background:'#1E3A5F',
                    borderRadius:'3px', position:'relative' }}>
                    <div style={{
                      height:'100%', borderRadius:'3px',
                      width:`${item.required}%`,
                      background:'#1E3A5F',
                      position:'absolute',
                    }}/>
                    {/* Current bar */}
                    <div style={{
                      height:'100%', borderRadius:'3px',
                      width:`${item.current}%`,
                      background: item.current >= item.required
                        ? '#10B981' : '#3B82F6',
                      position:'absolute',
                      transition:'width 1s ease',
                    }}/>
                  </div>
                </div>
              ))}
              <div style={{ display:'flex', gap:'16px', marginTop:'8px',
                fontSize:'11px', color:'#64748B' }}>
                <span>🔵 Your level</span>
                <span>⬛ Required level</span>
              </div>
            </div>
          )}

          {/* Skills breakdown */}
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr',
            gap:'16px' }}>
            <div className="card">
              <h3 style={{ fontSize:'13px', color:'#10B981',
                marginBottom:'12px', display:'flex', alignItems:'center',
                gap:'6px' }}>
                <CheckCircle size={14}/> Matching Skills
              </h3>
              {result.matching_skills?.map((s, i) => (
                <div key={i} style={{ padding:'6px 8px',
                  background:'#064E3B22', borderRadius:'6px',
                  marginBottom:'4px', fontSize:'13px', color:'#10B981' }}>
                  ✓ {s}
                </div>
              ))}
            </div>

            <div className="card">
              <h3 style={{ fontSize:'13px', color:'#EF4444',
                marginBottom:'12px', display:'flex', alignItems:'center',
                gap:'6px' }}>
                <XCircle size={14}/> Missing Skills
              </h3>
              {result.missing_skills?.map((s, i) => (
                <div key={i} style={{ padding:'6px 8px',
                  background:'#450A0A22', borderRadius:'6px',
                  marginBottom:'4px', fontSize:'13px', color:'#EF4444' }}>
                  ✗ {s}
                </div>
              ))}
            </div>
          </div>

          {/* Recommendations */}
          {result.recommendations?.length > 0 && (
            <div className="card">
              <h3 style={{ fontSize:'14px', fontWeight:600,
                marginBottom:'16px', display:'flex', alignItems:'center',
                gap:'8px' }}>
                <BookOpen size={16} color="#F59E0B"/> Learning Roadmap
              </h3>
              {result.recommendations.map((rec, i) => (
                <div key={i} style={{
                  padding:'16px', background:'#112240',
                  borderRadius:'8px', marginBottom:'12px',
                  borderLeft:'3px solid #F59E0B',
                }}>
                  <div style={{ display:'flex', justifyContent:'space-between',
                    alignItems:'center', marginBottom:'8px' }}>
                    <span style={{ fontWeight:600, color:'#E2E8F0',
                      fontSize:'14px' }}>
                      {rec.skill}
                    </span>
                    {rec.time_weeks && (
                      <span style={{ fontSize:'11px', color:'#F59E0B',
                        background:'#451A0333', padding:'2px 8px',
                        borderRadius:'10px' }}>
                        ~{rec.time_weeks} weeks
                      </span>
                    )}
                  </div>
                  <p style={{ fontSize:'13px', color:'#94A3B8',
                    marginBottom:'8px' }}>
                    {rec.reason}
                  </p>
                  {rec.resource && (
                    <p style={{ fontSize:'12px', color:'#F59E0B' }}>
                      📚 {rec.resource}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {result?.error && (
        <div className="card" style={{ borderColor:'#EF4444',
          color:'#EF4444' }}>
          {result.error}
        </div>
      )}
    </div>
  );
}