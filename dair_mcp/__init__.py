"""dair_mcp — corpus-server MCP for the deep-ai-research project.

Exposes four tools to Claude Code subagents:
  - search(query, filters)     — hybrid (FTS5 + vector) RRF k=60 with authority
                                 boost and per-content-type recency decay
  - find_by_authority(...)     — engagements table, optionally time-filtered
  - recent(topic, hours)       — hard recency filter, optional vector narrowing
  - fetch_detail(source_id)    — full markdown content + frontmatter for an item
"""

__version__ = "0.1.0"
