"""Data models for the Zettelkasten MCP server."""
import sys
import datetime
from datetime import datetime as dt
import random
import inspect
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, Set, TypeVar, Union, TypedDict
from pydantic import BaseModel, Field, field_validator

# Module-level variables to track ID generation state
_last_datetime_component = ""
_id_counter = 0

def generate_id() -> str:
    """Generate an ISO 8601 compliant timestamp-based ID with nanosecond precision.
    
    Returns:
        A string in format "YYYYMMDDTHHMMSSsssssssss" where:
        - YYYYMMDD is the date
        - T is the ISO 8601 date/time separator
        - HHMMSS is the time (hours, minutes, seconds)
        - sssssssss is the 9-digit nanosecond component
        
    The format follows ISO 8601 basic format with extended precision,
    allowing up to 1 billion unique IDs per second.
    """
    # Get nanoseconds since epoch
    ns_timestamp = time.time_ns()
    
    # Convert to seconds and nanosecond fraction
    seconds = ns_timestamp // 1_000_000_000
    nanoseconds = ns_timestamp % 1_000_000_000
    
    # Convert seconds to datetime
    timestamp = dt.fromtimestamp(seconds)
    
    # Format as ISO 8601 basic format (YYYYMMDDThhmmss) with nanoseconds
    # Use basic format (without separators except T) for filesystem compatibility
    date_time = timestamp.strftime('%Y%m%dT%H%M%S')
    
    # Return the ISO 8601 timestamp with nanosecond precision
    return f"{date_time}{nanoseconds:09d}"

class LinkType(str, Enum):
    """Types of links between notes."""
    REFERENCE = "reference"        # Simple reference to another note
    EXTENDS = "extends"            # Current note extends another note
    EXTENDED_BY = "extended_by"    # Current note is extended by another note
    REFINES = "refines"            # Current note refines another note
    REFINED_BY = "refined_by"      # Current note is refined by another note
    CONTRADICTS = "contradicts"    # Current note contradicts another note
    CONTRADICTED_BY = "contradicted_by"  # Current note is contradicted by another note
    QUESTIONS = "questions"        # Current note questions another note
    QUESTIONED_BY = "questioned_by"  # Current note is questioned by another note
    SUPPORTS = "supports"          # Current note supports another note
    SUPPORTED_BY = "supported_by"  # Current note is supported by another note
    RELATED = "related"            # Notes are related in some way

class Link(BaseModel):
    """A link between two notes."""
    source_id: str = Field(..., description="ID of the source note")
    target_id: str = Field(..., description="ID of the target note")
    link_type: LinkType = Field(default=LinkType.REFERENCE, description="Type of link")
    description: Optional[str] = Field(default=None, description="Optional description of the link")
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description="When the link was created"
    )
    
    model_config = {
        "validate_assignment": True,
        "extra": "forbid",
        "frozen": True  # Links are immutable
    }

class NoteType(str, Enum):
    """Types of notes in a Zettelkasten."""
    FLEETING = "fleeting"    # Quick, temporary notes
    LITERATURE = "literature"  # Notes from reading material
    PERMANENT = "permanent"  # Permanent, well-formulated notes
    STRUCTURE = "structure"  # Structure/index notes that organize other notes
    HUB = "hub"              # Hub notes that serve as entry points

class Tag(BaseModel):
    """A tag for categorizing notes."""
    name: str = Field(..., description="Tag name")
    
    model_config = {
        "validate_assignment": True,
        "frozen": True
    }
    
    def __str__(self) -> str:
        """Return string representation of tag."""
        return self.name

class Note(BaseModel):
    """A Zettelkasten note."""
    id: str = Field(default_factory=generate_id, description="Unique ID of the note")
    title: str = Field(..., description="Title of the note")
    content: str = Field(..., description="Content of the note")
    note_type: NoteType = Field(default=NoteType.PERMANENT, description="Type of note")
    tags: List[Tag] = Field(default_factory=list, description="Tags for categorization")
    links: List[Link] = Field(default_factory=list, description="Links to other notes")
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description="When the note was created"
    )
    updated_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description="When the note was last updated"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Additional metadata for the note"
    )
    
    model_config = {
        "validate_assignment": True,
        "extra": "forbid"
    }
    
    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate that the title is not empty."""
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v
    
    def add_tag(self, tag: Union[str, Tag]) -> None:
        """Add a tag to the note."""
        if isinstance(tag, str):
            tag = Tag(name=tag)
        # Check if tag already exists
        tag_names = {t.name for t in self.tags}
        if tag.name not in tag_names:
            self.tags.append(tag)
            self.updated_at = datetime.datetime.now()
    
    def remove_tag(self, tag: Union[str, Tag]) -> None:
        """Remove a tag from the note."""
        tag_name = tag.name if isinstance(tag, Tag) else tag
        self.tags = [t for t in self.tags if t.name != tag_name]
        self.updated_at = datetime.datetime.now()
    
    def add_link(self, target_id: str, link_type: LinkType = LinkType.REFERENCE, 
                description: Optional[str] = None) -> None:
        """Add a link to another note."""
        # Check if link already exists
        for link in self.links:
            if link.target_id == target_id and link.link_type == link_type:
                return  # Link already exists
        link = Link(
            source_id=self.id,
            target_id=target_id,
            link_type=link_type,
            description=description
        )
        self.links.append(link)
        self.updated_at = datetime.datetime.now()
    
    def remove_link(self, target_id: str, link_type: Optional[LinkType] = None) -> None:
        """Remove a link to another note."""
        if link_type:
            self.links = [
                link for link in self.links 
                if not (link.target_id == target_id and link.link_type == link_type)
            ]
        else:
            self.links = [link for link in self.links if link.target_id != target_id]
        self.updated_at = datetime.datetime.now()
    
    def get_linked_note_ids(self) -> Set[str]:
        """Get all note IDs that this note links to."""
        return {link.target_id for link in self.links}
    
    def to_markdown(self) -> str:
        """Convert the note to a markdown formatted string."""
        from zettelkasten_mcp.config import config
        # Format tags
        tags_str = ", ".join([tag.name for tag in self.tags])
        # Format links
        links_str = ""
        if self.links:
            links_str = "\n".join([
                f"- [{link.link_type}] [[{link.target_id}]] {link.description or ''}"
                for link in self.links
            ])
        # Apply template
        return config.default_note_template.format(
            title=self.title,
            content=self.content,
            created_at=self.created_at.isoformat(),
            tags=tags_str,
            links=links_str
        )

T = TypeVar('T')
I = TypeVar('I')

class BatchOperationResult(BaseModel, Generic[T, I]):
    """Results of a batch operation."""
    success: bool
    item_id: I 
    result: Optional[T] = None
    error: Optional[str] = None

class BatchResult(BaseModel, Generic[T, I]):
    """Result of a batch operation with summary statistics."""
    total_count: int
    success_count: int 
    failure_count: int
    results: List[BatchOperationResult[T, I]]

# TypedDict definitions for batch operations
class NoteData(TypedDict, total=False):
    """Schema for note creation data."""
    title: str  # required
    content: str  # required
    note_type: str
    tags: str
    metadata: Dict[str, str]

class NoteUpdateData(TypedDict, total=False):
    """Schema for note update data."""
    note_id: str  # required
    title: Optional[str]
    content: Optional[str]
    note_type: Optional[str]
    tags: Optional[str]
    metadata: Optional[Dict[str, str]]

class LinkData(TypedDict, total=False):
    """Schema for link creation data."""
    source_id: str  # required
    target_id: str  # required
    link_type: str
    description: Optional[str]
    bidirectional: bool
    bidirectional_type: Optional[str]

class TagOperationData(TypedDict, total=False):
    """Schema for tag operations."""
    note_id: str  # required
    tags: str  # required