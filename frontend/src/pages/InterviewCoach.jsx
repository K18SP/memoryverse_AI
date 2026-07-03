import React, { useState } from 'react';
import axios from 'axios';
import {
  ChevronRight,
  MessageSquare,
  RotateCcw,
  Sparkles,
  Star,
  Target,
} from 'lucide-react';
import { USER_ID } from '../App';

const TYPES = [
  { value: 'technical', label: 'Technical', desc: 'Deep dive into skills and tools' },
  { value: 'behavioral', label: 'Behavioral', desc: 'STAR-format situational answers' },
  { value: 'project', label: 'Project', desc: 'Explain decisions and tradeoffs' },
];

const DIFFICULTIES = ['easy', 'medium', 'hard'];

export default function InterviewCoach() {
  const [qType, setQType] = useState('technical');
  const [difficulty, setDifficulty] = useState('medium');
  const [question, setQuestion] = useState(null);
  const [answer, setAnswer] = useState('');
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [evalLoading, setEvalLoading] = useState(false);

  const getQuestion = async () => {
    setLoading(true);
    setQuestion(null);
    setAnswer('');
    setEvaluation(null);

    try {
      const form = new FormData();
      form.append('user_id', USER_ID);
      form.append('question_type', qType);
      form.append('difficulty', difficulty);
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
      form.append('user_id', USER_ID);
      form.append('question', question.question);
      form.append('answer', answer);
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
    <div style={{ maxWidth: '940px', margin: '0 auto' }}>
      <div style={{ marginBottom: '28px' }}>
        <div style={{ display: 'inline-flex', gap: '8px', alignItems: 'center', color: '#06B6D4', fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '10px' }}>
          <MessageSquare size={15} />
          Personal interview simulator
        </div>
        <h1 style={{ fontSize: '34px', fontWeight: 800, marginBottom: '8px' }}>AI Interview Coach</h1>
        <p style={{ color: '#94A3B8', fontSize: '16px', lineHeight: 1.6 }}>
          Practice with questions grounded in your uploaded evidence, then get structured STAR feedback.
        </p>
      </div>

      <div className="card interactive-card" style={{ marginBottom: '24px' }}>
        <label style={{ fontSize: '13px', color: '#94A3B8', display: 'block', marginBottom: '10px' }}>
          Question Type
        </label>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', marginBottom: '18px' }}>
          {TYPES.map(t => (
            <button
              key={t.value}
              onClick={() => setQType(t.value)}
              className="interactive-card"
              style={{
                padding: '14px',
                borderRadius: '8px',
                cursor: 'pointer',
                border: `1px solid ${qType === t.value ? '#3B82F6' : '#1E3A5F'}`,
                background: qType === t.value ? '#1E3A5F' : '#112240',
                textAlign: 'left',
              }}
            >
              <div style={{ fontSize: '13px', fontWeight: 700, color: qType === t.value ? '#3B82F6' : '#E2E8F0', marginBottom: '5px' }}>
                {t.label}
              </div>
              <div style={{ fontSize: '11px', color: '#94A3B8', lineHeight: 1.4 }}>{t.desc}</div>
            </button>
          ))}
        </div>

        <label style={{ fontSize: '13px', color: '#94A3B8', display: 'block', marginBottom: '10px' }}>
          Difficulty
        </label>
        <div style={{ display: 'flex', gap: '8px', marginBottom: '18px' }}>
          {DIFFICULTIES.map(d => (
            <button
              key={d}
              onClick={() => setDifficulty(d)}
              className="prompt-button"
              style={{
                padding: '8px 20px',
                borderRadius: '20px',
                border: `1px solid ${difficulty === d ? '#3B82F6' : '#1E3A5F'}`,
                background: difficulty === d ? '#1E3A5F' : 'transparent',
                color: difficulty === d ? '#3B82F6' : '#94A3B8',
                cursor: 'pointer',
                fontSize: '13px',
                textTransform: 'capitalize',
              }}
            >
              {d}
            </button>
          ))}
        </div>

        <button onClick={getQuestion} disabled={loading} className="btn-primary" style={{ width: '100%', padding: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
          <Sparkles size={16} /> {loading ? 'Generating question...' : 'Generate Question'}
        </button>
      </div>

      {question && (
        <div className="card interactive-card" style={{ marginBottom: '16px', borderColor: '#3B82F6' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'flex-start', marginBottom: '14px' }}>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <span className="badge badge-document">{question.type}</span>
              <span className="badge" style={{ background: '#112240', color: difficulty === 'hard' ? '#EF4444' : difficulty === 'medium' ? '#F59E0B' : '#10B981' }}>
                {question.difficulty}
              </span>
            </div>
            <button onClick={getQuestion} style={{ background: 'transparent', border: 'none', color: '#94A3B8', cursor: 'pointer', padding: '4px' }}>
              <RotateCcw size={15} />
            </button>
          </div>

          <p style={{ fontSize: '17px', fontWeight: 600, lineHeight: 1.65, marginBottom: '12px' }}>{question.question}</p>
          {question.what_interviewer_wants && (
            <p style={{ fontSize: '13px', color: '#94A3B8', lineHeight: 1.55, marginBottom: '10px' }}>
              <strong style={{ color: '#E2E8F0' }}>What they want:</strong> {question.what_interviewer_wants}
            </p>
          )}
          {question.tips && (
            <p style={{ fontSize: '12px', color: '#F59E0B', background: '#451A0322', padding: '9px 12px', borderRadius: '6px' }}>
              Tip: {question.tips}
            </p>
          )}
          {question.mode && <p style={{ fontSize: '11px', color: '#64748B', marginTop: '8px' }}>Mode: {question.mode === 'ai_enriched' ? 'AI enriched' : 'instant profile-based'}</p>}
        </div>
      )}

      {question && !question.error && (
        <div className="card" style={{ marginBottom: '16px' }}>
          <label style={{ fontSize: '13px', color: '#94A3B8', display: 'block', marginBottom: '8px' }}>
            Your Answer
          </label>
          <textarea
            value={answer}
            onChange={e => setAnswer(e.target.value)}
            placeholder="Use STAR: Situation, Task, Action, Result..."
            rows={6}
            style={{ width: '100%', padding: '12px', background: '#112240', border: '1px solid #1E3A5F', borderRadius: '8px', color: '#E2E8F0', fontSize: '14px', outline: 'none', resize: 'vertical', fontFamily: 'inherit', lineHeight: 1.6, marginBottom: '12px' }}
          />
          <button onClick={submitAnswer} disabled={evalLoading || !answer.trim()} className="btn-primary" style={{ width: '100%', padding: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
            <ChevronRight size={16} /> {evalLoading ? 'Evaluating...' : 'Submit Answer for Feedback'}
          </button>
        </div>
      )}

      {evaluation && !evaluation.error && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="card interactive-card" style={{ textAlign: 'center', borderColor: scoreColor(evaluation.score) }}>
            <div style={{ fontSize: '68px', fontWeight: 800, color: scoreColor(evaluation.score), lineHeight: 1 }}>{evaluation.score}</div>
            <div style={{ color: '#94A3B8', marginTop: '4px' }}>out of 100</div>
            {evaluation.overall && <p style={{ color: '#94A3B8', marginTop: '16px', fontSize: '14px', lineHeight: 1.6 }}>{evaluation.overall}</p>}
            {evaluation.mode && <p style={{ color: '#64748B', marginTop: '8px', fontSize: '12px' }}>Mode: {evaluation.mode === 'ai_enriched' ? 'AI enriched' : 'instant profile-based'}</p>}
          </div>

          {evaluation.star_breakdown && (
            <div className="card">
              <h3 style={{ fontSize: '15px', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Star size={17} color="#F59E0B" /> STAR Breakdown
              </h3>
              {Object.entries(evaluation.star_breakdown).map(([key, val]) => (
                <div key={key} style={{ marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '13px', fontWeight: 600, color: '#E2E8F0', textTransform: 'capitalize' }}>{key}</span>
                    <span style={{ fontSize: '13px', color: scoreColor(val.score) }}>{val.score}/100</span>
                  </div>
                  <div style={{ height: '6px', background: '#112240', borderRadius: '999px', marginBottom: '6px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${val.score}%`, background: scoreColor(val.score), borderRadius: '999px', transition: 'width 0.8s ease' }} />
                  </div>
                  <p style={{ fontSize: '12px', color: '#94A3B8' }}>{val.feedback}</p>
                </div>
              ))}
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <FeedbackCard title="Strengths" color="#10B981" items={evaluation.strengths} />
            <FeedbackCard title="Improve" color="#F59E0B" items={evaluation.improvements} />
          </div>

          {evaluation.ideal_answer && (
            <div className="card" style={{ borderColor: '#3B82F6' }}>
              <h3 style={{ fontSize: '13px', color: '#3B82F6', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Target size={15} /> What a Great Answer Looks Like
              </h3>
              <p style={{ fontSize: '13px', color: '#94A3B8', lineHeight: 1.6 }}>{evaluation.ideal_answer}</p>
            </div>
          )}

          <button onClick={() => { setQuestion(null); setAnswer(''); setEvaluation(null); }} className="btn-primary" style={{ padding: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
            <RotateCcw size={16} /> Try Another Question
          </button>
        </div>
      )}
    </div>
  );
}

function FeedbackCard({ title, color, items = [] }) {
  return (
    <div className="card">
      <h3 style={{ fontSize: '13px', color, marginBottom: '12px' }}>{title}</h3>
      {items?.map((item, i) => (
        <div key={i} style={{ padding: '9px', background: color + '18', borderRadius: '6px', marginBottom: '6px', fontSize: '13px', color: '#94A3B8', lineHeight: 1.5 }}>
          {item}
        </div>
      ))}
    </div>
  );
}
