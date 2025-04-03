# tests/test_models.py
"""Tests for the data models used in the Zettelkasten MCP server."""
import datetime
import pytest
from unittest.mock import patch
from pydantic import ValidationError
from zettelkasten_mcp.models.schema import Link, LinkType, Note, NoteType, Tag, generate_id

class TestNoteModel:
    """Tests for the Note model."""
    def test_note_creation(self):
        """Test creating a note with valid values."""
        note = Note(
            title="Test Note",
            content="This is a test note.",
            note_type=NoteType.PERMANENT,
            tags=[Tag(name="test"), Tag(name="example")]
        )
        assert note.id is not None
        assert note.title == "Test Note"
        assert note.content == "This is a test note."
        assert note.note_type == NoteType.PERMANENT
        assert len(note.tags) == 2
        assert note.links == []
        assert isinstance(note.created_at, datetime.datetime)
        assert isinstance(note.updated_at, datetime.datetime)

    def test_note_validation(self):
        """Test note validation for required fields."""
        # Empty title
        with pytest.raises(ValidationError):
            Note(title="", content="Content")
        # Title with only whitespace
        with pytest.raises(ValidationError):
            Note(title="   ", content="Content")
        # Without content - should fail
        with pytest.raises(ValidationError):
            Note(title="Title")

    def test_note_tag_operations(self):
        """Test adding and removing tags."""
        note = Note(
            title="Tag Test",
            content="Testing tag operations.",
            tags=[Tag(name="initial")]
        )
        assert len(note.tags) == 1
        # Add tag as string
        note.add_tag("test")
        assert len(note.tags) == 2
        assert any(tag.name == "test" for tag in note.tags)
        # Add tag as Tag object
        note.add_tag(Tag(name="another"))
        assert len(note.tags) == 3
        assert any(tag.name == "another" for tag in note.tags)
        # Add duplicate tag (should be ignored)
        note.add_tag("test")
        assert len(note.tags) == 3
        # Remove tag
        note.remove_tag("test")
        assert len(note.tags) == 2
        assert all(tag.name != "test" for tag in note.tags)
        # Remove tag that doesn't exist (should not error)
        note.remove_tag("nonexistent")
        assert len(note.tags) == 2

    def test_note_link_operations(self):
        """Test adding and removing links."""
        note = Note(
            title="Link Test",
            content="Testing link operations.",
            id="source123"
        )
        # Add link
        note.add_link("target456", LinkType.REFERENCE, "Test link")
        assert len(note.links) == 1
        assert note.links[0].source_id == "source123"
        assert note.links[0].target_id == "target456"
        assert note.links[0].link_type == LinkType.REFERENCE
        assert note.links[0].description == "Test link"
        # Add duplicate link (should be ignored)
        note.add_link("target456", LinkType.REFERENCE)
        assert len(note.links) == 1
        # Add link with different type
        note.add_link("target456", LinkType.EXTENDS)
        assert len(note.links) == 2
        # Remove specific link type
        note.remove_link("target456", LinkType.REFERENCE)
        assert len(note.links) == 1
        assert note.links[0].link_type == LinkType.EXTENDS
        # Remove all links to target
        note.remove_link("target456")
        assert len(note.links) == 0

    def test_note_to_markdown(self):
        """Test converting a note to markdown format."""
        note = Note(
            id="202501010000",
            title="Markdown Test",
            content="Testing markdown conversion.",
            note_type=NoteType.PERMANENT,
            tags=[Tag(name="test"), Tag(name="markdown")]
        )
        note.add_link("target123", LinkType.REFERENCE, "Reference link")
        markdown = note.to_markdown()
        # Check basic structure
        assert "# Markdown Test" in markdown
        assert "Testing markdown conversion." in markdown
        assert "test" in markdown
        assert "markdown" in markdown
        assert "Reference link" in markdown
        assert "target123" in markdown


class TestLinkModel:
    """Tests for the Link model."""
    def test_link_creation(self):
        """Test creating a link with valid values."""
        link = Link(
            source_id="source123",
            target_id="target456",
            link_type=LinkType.REFERENCE,
            description="Test description"
        )
        assert link.source_id == "source123"
        assert link.target_id == "target456"
        assert link.link_type == LinkType.REFERENCE
        assert link.description == "Test description"
        assert isinstance(link.created_at, datetime.datetime)

    def test_link_validation(self):
        """Test link validation for required fields."""
        # Missing source_id
        with pytest.raises(ValidationError):
            Link(target_id="target456")
        # Missing target_id
        with pytest.raises(ValidationError):
            Link(source_id="source123")
        # Invalid link_type
        with pytest.raises(ValidationError):
            Link(source_id="source123", target_id="target456", link_type="invalid")

    def test_link_immutability(self):
        """Test that Link objects are immutable."""
        link = Link(
            source_id="source123", 
            target_id="target456"
        )
        # Attempt to modify link should fail
        with pytest.raises(Exception):
            link.source_id = "newsource"


class TestTagModel:
    """Tests for the Tag model."""
    def test_tag_creation(self):
        """Test creating a tag with valid values."""
        tag = Tag(name="test")
        assert tag.name == "test"
        assert str(tag) == "test"

    def test_tag_immutability(self):
        """Test that Tag objects are immutable."""
        tag = Tag(name="test")
        # Attempt to modify tag should fail
        with pytest.raises(Exception):
            tag.name = "newname"


class TestHelperFunctions:
    """Tests for helper functions in the schema module."""
    
    @patch('zettelkasten_mcp.models.schema.datetime')
    def test_generate_id(self, mock_datetime):
        """Test the ID generation function with mocked datetime."""
        # Mock two different timestamp values with microseconds
        mock_first_time = datetime.datetime(2023, 1, 1, 12, 0, 0, microsecond=123000)
        mock_datetime.datetime.now.return_value = mock_first_time
        
        id1 = generate_id()
        
        # Change the mocked time
        mock_second_time = datetime.datetime(2023, 1, 1, 12, 0, 1, microsecond=456000)
        mock_datetime.datetime.now.return_value = mock_second_time
        
        id2 = generate_id()
        
        # Verify the IDs are formatted correctly with milliseconds (17 chars)
        assert id1 == "20230101120000123"  # Format is YYYYMMDDhhmmssmmm
        assert id2 == "20230101120001456"  # Second ID
        
        # Verify the IDs are unique
        assert id1 != id2
