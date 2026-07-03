import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { getGraph, getNodeDetails, buildGraph } from '../api';
import { USER_ID } from '../App';
import { RefreshCw, } from 'lucide-react';

export default function Graph() {
  const svgRef             = useRef(null);
  const [graphData,    setGraphData]    = useState(null);
  const [selected,     setSelected]     = useState(null);
  const [loading,      setLoading]      = useState(true);
  const [building,     setBuilding]     = useState(false);

  const loadGraph = async () => {
    setLoading(true);
    try {
      const res = await getGraph(USER_ID);
      setGraphData(res.data);
    } catch {
      setGraphData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleBuild = async () => {
    setBuilding(true);
    try {
      await buildGraph(USER_ID);
      await loadGraph();
    } finally {
      setBuilding(false);
    }
  };

  const handleNodeClick = async (nodeId) => {
    try {
      const res = await getNodeDetails(USER_ID, nodeId);
      setSelected(res.data);
    } catch {}
  };

  useEffect(() => { loadGraph(); }, []);

  // ── D3 rendering ────────────────────────────────────────────────────────
  useEffect(() => {
    if (!graphData || !svgRef.current) return;

    const width  = svgRef.current.clientWidth  || 800;
    const height = svgRef.current.clientHeight || 500;

    // Clear previous render
    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current);

    // Zoom support
    const g   = svg.append('g');
    svg.call(d3.zoom().scaleExtent([0.3, 3])
      .on('zoom', e => g.attr('transform', e.transform)));

    // Arrow marker
    svg.append('defs').append('marker')
      .attr('id', 'arrow').attr('viewBox', '0 -5 10 10')
      .attr('refX', 20).attr('refY', 0)
      .attr('markerWidth', 6).attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path').attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#1E3A5F');

    const nodes = graphData.nodes.map(d => ({ ...d }));
    const edges = graphData.edges.map(d => ({ ...d }));

    // Force simulation
    const sim = d3.forceSimulation(nodes)
      .force('link',   d3.forceLink(edges)
        .id(d => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide(30));

    // Edges
    const link = g.append('g').selectAll('line')
      .data(edges).join('line')
      .attr('stroke', '#1E3A5F')
      .attr('stroke-width', 1.5)
      .attr('marker-end', 'url(#arrow)');

    // Edge labels
    const edgeLabel = g.append('g').selectAll('text')
      .data(edges).join('text')
      .text(d => d.relation)
      .attr('font-size', '8px')
      .attr('fill', '#475569')
      .attr('text-anchor', 'middle');

    // Nodes
    const node = g.append('g').selectAll('g')
      .data(nodes).join('g')
      .attr('cursor', 'pointer')
      .on('click', (_, d) => handleNodeClick(d.id))
      .call(d3.drag()
        .on('start', (e, d) => {
          if (!e.active) sim.alphaTarget(0.3).restart();
          d.fx = d.x; d.fy = d.y;
        })
        .on('drag', (e, d) => { d.fx = e.x; d.fy = e.y; })
        .on('end',  (e, d) => {
          if (!e.active) sim.alphaTarget(0);
          d.fx = null; d.fy = null;
        })
      );

    // Node circles
    node.append('circle')
      .attr('r', d => d.type === 'document' ? 18 : 12)
      .attr('fill', d => d.color + '33')
      .attr('stroke', d => d.color)
      .attr('stroke-width', 2);

    // Node labels
    node.append('text')
      .text(d => d.label.length > 12 ? d.label.slice(0, 12) + '…' : d.label)
      .attr('text-anchor', 'middle')
      .attr('dy', '30px')
      .attr('font-size', '10px')
      .attr('fill', '#94A3B8');

    // Simulation tick
    sim.on('tick', () => {
      link
        .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
      edgeLabel
        .attr('x', d => (d.source.x + d.target.x) / 2)
        .attr('y', d => (d.source.y + d.target.y) / 2);
      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });

  }, [graphData]);

  return (
    <div style={{ height:'calc(100vh - 64px)', display:'flex',
      flexDirection:'column' }}>

      {/* ── Header ────────────────────────────────────────────────── */}
      <div style={{ display:'flex', justifyContent:'space-between',
        alignItems:'center', marginBottom:'24px' }}>
        <div>
          <h1 style={{ fontSize:'28px', fontWeight:700 }}>Knowledge Graph</h1>
          {graphData && (
            <p style={{ color:'#94A3B8', fontSize:'14px', marginTop:'4px' }}>
              {graphData.node_count} nodes · {graphData.edge_count} edges
            </p>
          )}
        </div>
        <div style={{ display:'flex', gap:'8px' }}>
          <button onClick={loadGraph} className="btn-primary"
            style={{ display:'flex', alignItems:'center', gap:'6px',
              background:'#1A2F4A', border:'1px solid #1E3A5F' }}>
            <RefreshCw size={14}/> Refresh
          </button>
          <button onClick={handleBuild} disabled={building}
            className="btn-primary"
            style={{ display:'flex', alignItems:'center', gap:'6px' }}>
            {building ? '⟳ Building...' : '⚡ Rebuild Graph'}
          </button>
        </div>
      </div>

      <div style={{ display:'flex', gap:'16px', flex:1 }}>

        {/* ── SVG Graph ───────────────────────────────────────────── */}
        <div style={{ flex:1, background:'#112240',
          borderRadius:'12px', border:'1px solid #1E3A5F',
          overflow:'hidden', position:'relative' }}>
          {loading ? (
            <div style={{ display:'flex', alignItems:'center',
              justifyContent:'center', height:'100%', color:'#94A3B8' }}>
              Loading graph...
            </div>
          ) : !graphData || graphData.node_count === 0 ? (
            <div style={{ display:'flex', alignItems:'center',
              justifyContent:'center', height:'100%',
              flexDirection:'column', gap:'16px' }}>
              <p style={{ color:'#94A3B8' }}>No graph data yet.</p>
              <button onClick={handleBuild} className="btn-primary">
                Build Knowledge Graph
              </button>
            </div>
          ) : (
            <svg ref={svgRef} width="100%" height="100%" />
          )}
        </div>

        {/* ── Node Detail Panel ───────────────────────────────────── */}
        {selected && (
          <div className="card" style={{ width:'260px', flexShrink:0,
            overflowY:'auto' }}>
            <h3 style={{ fontWeight:600, marginBottom:'4px' }}>
              {selected.node?.label}
            </h3>
            <span className={`badge badge-${selected.node?.node_type}`}>
              {selected.node?.node_type}
            </span>

            {selected.successors?.length > 0 && (
              <div style={{ marginTop:'16px' }}>
                <p style={{ fontSize:'11px', color:'#64748B',
                  textTransform:'uppercase', letterSpacing:'1px',
                  marginBottom:'8px' }}>
                  Connected To
                </p>
                {selected.successors.map((n, i) => (
                  <div key={i} style={{ padding:'6px 8px',
                    background:'#112240', borderRadius:'6px',
                    marginBottom:'4px', fontSize:'12px', color:'#94A3B8' }}>
                    {n.label || n.id}
                  </div>
                ))}
              </div>
            )}

            {selected.predecessors?.length > 0 && (
              <div style={{ marginTop:'12px' }}>
                <p style={{ fontSize:'11px', color:'#64748B',
                  textTransform:'uppercase', letterSpacing:'1px',
                  marginBottom:'8px' }}>
                  Connected From
                </p>
                {selected.predecessors.map((n, i) => (
                  <div key={i} style={{ padding:'6px 8px',
                    background:'#112240', borderRadius:'6px',
                    marginBottom:'4px', fontSize:'12px', color:'#94A3B8' }}>
                    {n.label || n.id}
                  </div>
                ))}
              </div>
            )}

            <button onClick={() => setSelected(null)}
              style={{ marginTop:'16px', width:'100%', padding:'8px',
                background:'transparent', border:'1px solid #1E3A5F',
                borderRadius:'6px', color:'#94A3B8', cursor:'pointer',
                fontSize:'12px' }}>
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
}