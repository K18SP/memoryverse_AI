import React, { useState } from 'react';
import { USER_ID } from '../App';
import axios from 'axios';
import { MessageSquare, Star, ChevronRight, RotateCcw } from 'lucide-react';

const TYPES = [
  { value:'technical',  label:'Technical',  desc:'Deep dive into skills & tools' },
  { value:'behavioral', label:'Behavioral', desc:'STAR-format situational questions' },
  { value:'project',    label:'Project',    desc:'About your specific projects' },
];

const DIFFICULTIES = ['easy', 'medium', 'hard'];

export default function InterviewCoach() {
  const [qType,      setQType]      = useState('technical');
  const [difficulty, setDifficulty] = useState('medium');
  const [question,   setQuestion]   = useState(null);
  const [answer,     setAnswer]     = useState('');
  const [evaluation, setEvaluation] = useState(null);
  const [loading,    setLoading]    = useState(false);
  const [evalLoading,setEvalLoading]= useState(false);

  const getQuestion = async () => {
    setLoading(true);
    setQuestion(null);
    setAnswer('');
    setEvaluation(null);

    try {
      const form = new FormData();
      form.append('user_id',       USER_ID);
      form.append('question_type', qType);
      form.append('difficulty',    difficulty);

      const res = await axios.post('/api/v1/interview/question', form);
      setQuestion(res.data);
    } catch {
      setQuestion({ question: 'Failed to generate question. Try again.', error: true });
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = async () => {
    if (!answer.trim() || !question) return;
    setEvalLoading(true);

    try {
      const form = new FormData();
      form.append('user_id',  USER_ID);
      form.append('question', question.question);
      form.append('answer',   answer);

      const res = await axios.post('/api/v1/interview/evaluate', form);
      setEvaluation(res.data);
    } catch {
      setEvaluation({ error: 'Evaluation failed. Try again.' });
    } finally {
      setEvalLoading(false);
    }
  };

  const scoreColor = (s) => s >= 75 ? '#10B981' : s >= 50 ? '#F59E0B' : '#EF4444';

  return (
    <div style={{ maxWidth:'800px', margin:'0 auto' }}>
      <div style={{ marginBottom:'32px' }}>
        <h1 style={{ fontSize:'28px', fontWeight:700, marginBottom:'8px' }}>
          AI Interview Coach
        </h1>
        <p style={{ color:'#94A3B8' }}>
          Practice with questions based on your actual documents and get instant feedback.
        </p>
      </div>

      {/* ── Config ──────────────────────────────────────────────────── */}
      <div className="card" style={{ marginBottom:'24px' }}>
        <div style={{ marginBottom:'16px' }}>
          <label style={{ fontSize:'13px', color:'#94A3B8',
            display:'block', marginBottom:'8px' }}>
            Question Type
          </label>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)',
            gap:'8px' }}>
            {TYPES.map(t => (
              <button key={t.value} onClick={() => setQType(t.value)}
                style={{
                  padding:'12px', borderRadius:'8px', cursor:'pointer',
                  border:`1px solid ${qType===t.value ? '#3B82F6' : '#1E3A5F'}`,
                  background: qType===t.value ? '#1E3A5F' : 'transparent',
                  textAlign:'left', transition:'all 0.2s',
                }}>
                <div style={{ fontSize:'13px', fontWeight:500,
                  color: qType===t.value ? '#3B82F6' : '#E2E8F0',
                  marginBottom:'4px' }}>
                  {t.label}
                </div>
                <div style={{ fontSize:'11px', color:'#64748B' }}>
                  {t.desc}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div style={{ marginBottom:'16px' }}>
          <label style={{ fontSize:'13px', color:'#94A3B8',
            display:'block', marginBottom:'8px' }}>
            Difficulty
          </label>
          <div style={{ display:'flex', gap:'8px' }}>
            {DIFFICULTIES.map(d => (
              <button key={d} onClick={() => setDifficulty(d)}
                style={{
                  padding:'8px 20px', borderRadius:'20px',
                  border:`1px solid ${difficulty===d ? '#3B82F6' : '#1E3A5F'}`,
                  background: difficulty===d ? '#1E3A5F' : 'transparent',
                  color: difficulty===d ? '#3B82F6' : '#64748B',
                  cursor:'pointer', fontSize:'13px',
                  textTransform:'capitalize', transition:'all 0.2s',
                }}>
                {d}
              </button>
            ))}
          </div>
        </div>

        <button onClick={getQuestion} disabled={loading}
          className="btn-primary"
          style={{ width:'100%', padding:'12px',
            display:'flex', alignItems:'center',
            justifyContent:'center', gap:'8px' }}>
          <MessageSquare size={16}/>
          {loading ? 'Generating question...' : 'Generate Question'}
        </button>
      </div>

      {/* ── Question ────────────────────────────────────────────────── */}
      {question && (
        <div className="card" style={{ marginBottom:'16px',
          borderColor: '#3B82F6' }}>
          <div style={{ display:'flex', justifyContent:'space-between',
            alignItems:'flex-start', marginBottom:'12px' }}>
            <div style={{ display:'flex', gap:'8px' }}>
              <span className="badge badge-document">{question.type}</span>
              <span className="badge" style={{
                background:'#112240',
                color: difficulty==='hard' ? '#EF4444'
                     : difficulty==='medium' ? '#F59E0B' : '#10B981'
              }}>
                {question.difficulty}
              </span>
            </div>
            <button onClick={getQuestion}
              style={{ background:'transparent', border:'none',
                color:'#64748B', cursor:'pointer', padding:'4px' }}>
              <RotateCcw size={14}/>
            </button>
          </div>

          <p style={{ fontSize:'16px', fontWeight:500, lineHeight:'1.6',
            marginBottom:'12px' }}>
            {question.question}
          </p>

          {question.tips && (
            <p style={{ fontSize:'12px', color:'#F59E0B',
              background:'#451A0322', padding:'8px 12px',
              borderRadius:'6px' }}>
              💡 {question.tips}
            </p>
          )}
        </div>
      )}

      {/* ── Answer Input ─────────────────────────────────────────────── */}
      {question && !question.error && (
        <div className="card" style={{ marginBottom:'16px' }}>
          <label style={{ fontSize:'13px', color:'#94A3B8',
            display:'block', marginBottom:'8px' }}>
            Your Answer
          </label>
          <textarea
            value={answer}
            onChange={e => setAnswer(e.target.value)}
            placeholder="Type your answer here... Use STAR format: Situation, Task, Action, Result"
            rows={6}
            style={{
              width:'100%', padding:'12px',
              background:'#112240', border:'1px solid #1E3A5F',
              borderRadius:'8px', color:'#E2E8F0', fontSize:'14px',
              outline:'none', resize:'vertical', fontFamily:'inherit',
              lineHeight:'1.6', marginBottom:'12px',
            }}
          />
          <button onClick={submitAnswer}
            disabled={evalLoading || !answer.trim()}
            className="btn-primary"
            style={{ width:'100%', padding:'12px',
              display:'flex', alignItems:'center',
              justifyContent:'center', gap:'8px' }}>
            <ChevronRight size={16}/>
            {evalLoading ? 'Evaluating...' : 'Submit Answer for Feedback'}
          </button>
        </div>
      )}

      {/* ── Evaluation ──────────────────────────────────────────────── */}
      {evaluation && !evaluation.error && (
        <div style={{ display:'flex', flexDirection:'column', gap:'16px' }}>

          {/* Score */}
          <div className="card" style={{ textAlign:'center' }}>
            <div style={{ fontSize:'64px', fontWeight:700,
              color: scoreColor(evaluation.score), lineHeight:1 }}>
              {evaluation.score}
            </div>
            <div style={{ color:'#94A3B8', marginTop:'4px' }}>out of 100</div>
            {evaluation.overall && (
              <p style={{ color:'#94A3B8', marginTop:'16px', fontSize:'14px',
                lineHeight:'1.6' }}>
                {evaluation.overall}
              </p>
            )}
          </div>

          {/* STAR Breakdown */}
          {evaluation.star_breakdown && (
            <div className="card">
              <h3 style={{ fontSize:'14px', fontWeight:600,
                marginBottom:'16px', display:'flex',
                alignItems:'center', gap:'8px' }}>
                <Star size={16} color="#F59E0B"/> STAR Breakdown
              </h3>
              {Object.entries(evaluation.star_breakdown).map(([key, val]) => (
                <div key={key} style={{ marginBottom:'16px' }}>
                  <div style={{ display:'flex', justifyContent:'space-between',
                    marginBottom:'6px' }}>
                    <span style={{ fontSize:'13px', fontWeight:500,
                      color:'#E2E8F0', textTransform:'capitalize' }}>
                      {key}
                    </span>
                    <span style={{ fontSize:'13px',
                      color: scoreColor(val.score) }}>
                      {val.score}/100
                    </span>
                  </div>
                  <div style={{ height:'4px', background:'#1E3A5F',
                    borderRadius:'2px', marginBottom:'6px' }}>
                    <div style={{
                      height:'100%', borderRadius:'2px',
                      width:`${val.score}%`,
                      background: scoreColor(val.score),
                      transition:'width 0.8s ease',
                    }}/>
                  </div>
                  <p style={{ fontSize:'12px', color:'#64748B' }}>
                    {val.feedback}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Strengths & Improvements */}
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr',
            gap:'16px' }}>
            <div className="card">
              <h3 style={{ fontSize:'13px', color:'#10B981',
                marginBottom:'12px' }}>✓ Strengths</h3>
              {evaluation.strengths?.map((s, i) => (
                <div key={i} style={{ padding:'8px',
                  background:'#064E3B22', borderRadius:'6px',
                  marginBottom:'6px', fontSize:'13px', color:'#94A3B8',
                  lineHeight:'1.5' }}>
                  {s}
                </div>
              ))}
            </div>
            <div className="card">
              <h3 style={{ fontSize:'13px', color:'#F59E0B',
                marginBottom:'12px' }}>↑ Improve</h3>
              {evaluation.improvements?.map((s, i) => (
                <div key={i} style={{ padding:'8px',
                  background:'#451A0322', borderRadius:'6px',
                  marginBottom:'6px', fontSize:'13px', color:'#94A3B8',
                  lineHeight:'1.5' }}>
                  {s}
                </div>
              ))}
            </div>
          </div>

          {/* Ideal Answer */}
          {evaluation.ideal_answer && (
            <div className="card" style={{ borderColor:'#3B82F6' }}>
              <h3 style={{ fontSize:'13px', color:'#3B82F6',
                marginBottom:'12px' }}>
                💡 What a Great Answer Looks Like
              </h3>
              <p style={{ fontSize:'13px', color:'#94A3B8',
                lineHeight:'1.6' }}>
                {evaluation.ideal_answer}
              </p>
            </div>
          )}

          {/* Try another */}
          <button onClick={() => {
            setQuestion(null); setAnswer('');
            setEvaluation(null);
          }}
            className="btn-primary"
            style={{ padding:'12px', display:'flex',
              alignItems:'center', justifyContent:'center', gap:'8px' }}>
            <RotateCcw size={16}/> Try Another Question
          </button>
        </div>
      )}
    </div>
  );
}