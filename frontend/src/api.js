/**
 * API client — all backend calls go through here.
 * Base URL points to FastAPI running on port 8000.
 */

import axios from 'axios';

const API = axios.create({
  baseURL: '/api/v1',
  timeout: 300000,   // 2 min — Mistral can be slow on first query
});

// ── Ingestion ──────────────────────────────────────────────────────────────
export const ingestFile = (file, userId, date = '') => {
  const form = new FormData();
  form.append('file', file);
  form.append('user_id', userId);
  if (date) form.append('date', date);
  return API.post('/ingest', form);
};

export const ingestGithub = (url, userId) => {
  const form = new FormData();
  form.append('github_url', url);
  form.append('user_id', userId);
  return API.post('/ingest', form);
};

// ── Search ─────────────────────────────────────────────────────────────────
export const searchDocuments = (query, userId, topK = 5) => {
  const form = new FormData();
  form.append('query', query);
  form.append('user_id', userId);
  form.append('top_k', topK);
  return API.post('/search', form);
};

// ── Knowledge Graph ────────────────────────────────────────────────────────
export const buildGraph    = (userId) => API.post(`/graph/${userId}/build`);
export const getGraph      = (userId) => API.get(`/graph/${userId}`);
export const getNodeDetails= (userId, nodeId) =>
  API.get(`/graph/${userId}/node/${encodeURIComponent(nodeId)}`);
export const clearDocuments = (userId) => API.delete(`/documents/${userId}`);

// ── Timeline ───────────────────────────────────────────────────────────────
export const getTimeline = async (userId) => {
  // Fetch graph data and filter to document nodes only
  // sorted chronologically for the timeline view
  const res = await getGraph(userId);
  const seen = new Set();
  const docs = res.data.nodes
    .filter(n => n.type === 'document')
    .filter(n => {
      const key = `${n.label || n.id}-${n.date || ''}`.toLowerCase();
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .sort((a, b) => (a.date > b.date ? 1 : -1));
  return { data: { documents: docs } };
};
