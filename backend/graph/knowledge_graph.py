"""
Knowledge Graph
───────────────
Builds and manages an in-memory graph using NetworkX.

Nodes: every unique entity (skill, tool, org, role, topic)
Edges: typed relationships between entities

Node types:
  skill | tool | organization | role | topic | document

The graph is stored in memory and rebuilt from Qdrant
payloads on startup. It exposes D3.js-compatible output
for the frontend visualisation.
"""

import networkx as nx
from typing import Optional

# ── Singleton graph instance ───────────────────────────────────────────────
_graphs: dict[str, nx.DiGraph] = {}   # one graph per user_id


def get_graph(user_id: str) -> nx.DiGraph:
    """Get or create a directed graph for a user."""
    if user_id not in _graphs:
        _graphs[user_id] = nx.DiGraph()
    return _graphs[user_id]


def add_document_node(
    user_id    : str,
    doc_id     : str,
    source_file: str,
    source_type: str,
    date       : str,
    category   : str = "",
) -> None:
    """Add a document as a node in the graph."""
    graph = get_graph(user_id)
    graph.add_node(
        doc_id,
        label      = source_file.split("/")[-1],   # short name
        node_type  = "document",
        source_file= source_file,
        source_type= source_type,
        date       = date,
        category   = category,
    )


def add_entities_to_graph(
    user_id  : str,
    doc_id   : str,
    entities : dict,
) -> None:
    """
    Add extracted entities as nodes and connect them to their document.

    Args:
        user_id  : owner
        doc_id   : source document node (must already exist)
        entities : output from extract_entities()
    """
    graph = get_graph(user_id)

    # ── Add entity nodes ───────────────────────────────────────────────────
    type_map = {
        "skills"       : "skill",
        "tools"        : "tool",
        "organizations": "organization",
        "roles"        : "role",
        "topics"       : "topic",
    }

    for entity_type, node_type in type_map.items():
        for entity_name in entities.get(entity_type, []):
            node_id = f"{node_type}::{entity_name.lower()}"

            if not graph.has_node(node_id):
                graph.add_node(
                    node_id,
                    label    = entity_name,
                    node_type= node_type,
                )

            # Connect document → entity
            graph.add_edge(
                doc_id,
                node_id,
                relation="CONTAINS",
            )

    # ── Add explicit relations between entities ────────────────────────────
    for rel in entities.get("relations", []):
        from_id = _find_node_id(graph, rel["from"])
        to_id   = _find_node_id(graph, rel["to"])

        if from_id and to_id:
            graph.add_edge(
                from_id,
                to_id,
                relation=rel["type"],
            )


def _find_node_id(graph: nx.DiGraph, entity_name: str) -> Optional[str]:
    """Find a node by its label (case-insensitive)."""
    name_lower = entity_name.lower()
    for node_id, data in graph.nodes(data=True):
        if data.get("label", "").lower() == name_lower:
            return node_id
    return None


def get_graph_for_frontend(user_id: str) -> dict:
    """
    Export graph as D3.js-compatible JSON.

    Returns:
        {
          "nodes": [{"id": str, "label": str, "type": str}],
          "edges": [{"source": str, "target": str, "relation": str}]
        }
    """
    graph = get_graph(user_id)

    # Color map for node types
    color_map = {
        "document"    : "#3B82F6",   # blue
        "skill"       : "#10B981",   # green
        "tool"        : "#F59E0B",   # amber
        "organization": "#EF4444",   # red
        "role"        : "#8B5CF6",   # purple
        "topic"       : "#06B6D4",   # cyan
    }

    nodes = []
    for node_id, data in graph.nodes(data=True):
        node_type = data.get("node_type", "unknown")
        nodes.append({
            "id"   : node_id,
            "label": data.get("label", node_id),
            "type" : node_type,
            "color": color_map.get(node_type, "#94A3B8"),
            "date" : data.get("date", ""),
        })

    edges = []
    for source, target, data in graph.edges(data=True):
        edges.append({
            "source"  : source,
            "target"  : target,
            "relation": data.get("relation", "RELATED_TO"),
        })

    return {
        "nodes"     : nodes,
        "edges"     : edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }


def get_node_neighbours(user_id: str, node_id: str) -> dict:
    """
    Get all neighbours of a node — used when user clicks a node
    in the frontend to expand its connections.
    """
    graph = get_graph(user_id)

    if not graph.has_node(node_id):
        return {"error": f"Node '{node_id}' not found"}

    node_data = graph.nodes[node_id]

    successors   = [
        {"id": n, **graph.nodes[n]}
        for n in graph.successors(node_id)
    ]
    predecessors = [
        {"id": n, **graph.nodes[n]}
        for n in graph.predecessors(node_id)
    ]

    return {
        "node"        : {"id": node_id, **node_data},
        "successors"  : successors,
        "predecessors": predecessors,
        "total_connections": len(successors) + len(predecessors),
    }