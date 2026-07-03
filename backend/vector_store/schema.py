"""
Qdrant Document Schema
───────────────────────
Defines the payload structure stored alongside every vector.
Import DocChunk anywhere you need to build or validate a payload.
"""

from pydantic import BaseModel, Field
from typing import Optional
import uuid


class DocChunk(BaseModel):
    """
    One chunk of a document stored as a Qdrant point.

    Each uploaded document produces N chunks.
    All chunks from the same document share doc_id.
    Each chunk has its own unique chunk_id (used as Qdrant point ID).
    """

    # Identity
    chunk_id   : str = Field(default_factory=lambda: str(uuid.uuid4()))
    doc_id     : str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id    : str

    # Content
    text        : str
    chunk_index : int
    token_count : int

    # Source metadata
    source_type : str    # pdf | image | docx | markdown | github
    source_file : str    # filename or URL
    date        : str    # YYYY-MM-DD
    original_file_url: Optional[str] = None

    # AI-assigned fields (populated in Block 2 & 3)
    category    : Optional[str] = None
    entities    : list[str]     = []
    skills      : list[str]     = []
    trust_score : int           = 0

    def to_payload(self) -> dict:
        """Convert to flat dict for Qdrant payload storage."""
        return {
            "chunk_id"   : self.chunk_id,
            "doc_id"     : self.doc_id,
            "user_id"    : self.user_id,
            "text"       : self.text,
            "chunk_index": self.chunk_index,
            "token_count": self.token_count,
            "source_type": self.source_type,
            "source_file": self.source_file,
            "date"       : self.date,
            "original_file_url": self.original_file_url,
            "category"   : self.category,
            "entities"   : self.entities,
            "skills"     : self.skills,
            "trust_score": self.trust_score,
        }
