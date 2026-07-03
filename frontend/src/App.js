import React from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import Dashboard    from './pages/Dashboard';
import Upload       from './pages/Upload';
import Timeline     from './pages/Timeline';
import Graph        from './pages/Graph';
import GapAnalyst   from './pages/GapAnalyst';
import InterviewCoach from './pages/InterviewCoach';
import { Brain, Upload as UploadIcon, Clock, Share2, Target, MessageSquare } from 'lucide-react';
import './index.css';

// ── Shared user ID for demo ────────────────────────────────────────────────
// In production this comes from auth; for hackathon demo use a fixed value
export const USER_ID = 'u_testgi_01';

const navStyle = ({ isActive }) => ({
  display       : 'flex',
  alignItems    : 'center',
  gap           : '8px',
  padding       : '10px 16px',
  borderRadius  : '8px',
  textDecoration: 'none',
  fontSize      : '14px',
  fontWeight    : '500',
  color         : isActive ? '#3B82F6' : '#94A3B8',
  background    : isActive ? '#1E3A5F' : 'transparent',
  transition    : 'all 0.2s',
});

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ display: 'flex', minHeight: '100vh' }}>

        {/* ── Sidebar ────────────────────────────────────────────────── */}
        <aside style={{
          width: '220px', background: '#112240',
          borderRight: '1px solid #1E3A5F',
          padding: '24px 16px', display: 'flex',
          flexDirection: 'column', gap: '8px',
          position: 'fixed', height: '100vh',
        }}>
          {/* Logo */}
          <div style={{ display:'flex', alignItems:'center', gap:'10px',
            padding:'0 8px 24px', borderBottom:'1px solid #1E3A5F', marginBottom:'8px' }}>
            <Brain size={24} color="#3B82F6" />
            <span style={{ fontWeight:700, fontSize:'16px', color:'#E2E8F0' }}>
              MemoryVerse
            </span>
          </div>

          <NavLink to="/"        style={navStyle}><Brain    size={16}/>Dashboard</NavLink>
          <NavLink to="/upload"  style={navStyle}><UploadIcon size={16}/>Upload</NavLink>
          <NavLink to="/timeline"style={navStyle}><Clock    size={16}/>Timeline</NavLink>
          <NavLink to="/graph"   style={navStyle}><Share2   size={16}/>Knowledge Graph</NavLink>
          <NavLink to="/gap"       style={navStyle}><Target       size={16}/>Gap Analyst</NavLink>
          <NavLink to="/interview" style={navStyle}><MessageSquare size={16}/>Interview Coach</NavLink>
        </aside>

        {/* ── Main content ───────────────────────────────────────────── */}
        <main style={{ marginLeft:'220px', flex:1, padding:'32px' }}>
          <Routes>
            <Route path="/"         element={<Dashboard />} />
            <Route path="/upload"   element={<Upload />} />
            <Route path="/timeline" element={<Timeline />} />
            <Route path="/graph"    element={<Graph />} />
            <Route path="/gap"       element={<GapAnalyst />} />
            <Route path="/interview" element={<InterviewCoach />} />
          </Routes>
        </main>

      </div>
    </BrowserRouter>
  );
}