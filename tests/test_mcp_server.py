# tests/test_mcp_server.py
"""Tests for the MCP server implementation."""
import pytest
from unittest.mock import patch, MagicMock, call
from datetime import datetime

from zettelkasten_mcp.server.mcp_server import ZettelkastenMcpServer
from zettelkasten_mcp.models.schema import LinkType, NoteType

class TestMcpServer:
    """Tests for the ZettelkastenMcpServer class."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Capture the tool decorator functions when registering
        self.registered_tools = {}
        
        # Create a mock for FastMCP
        self.mock_mcp = MagicMock()
        
        # Mock the tool decorator to capture registered functions BEFORE server creation
        def mock_tool_decorator(*args, **kwargs):
            def tool_wrapper(func):
                # Store the function with its name
                name = kwargs.get('name')
                self.registered_tools[name] = func
                return func
            return tool_wrapper
        self.mock_mcp.tool = mock_tool_decorator
        
        # Mock the ZettelService and SearchService
        self.mock_zettel_service = MagicMock()
        self.mock_search_service = MagicMock()
        
        # Create patchers for FastMCP, ZettelService, and SearchService
        self.mcp_patcher = patch('zettelkasten_mcp.server.mcp_server.FastMCP', return_value=self.mock_mcp)
        self.zettel_patcher = patch('zettelkasten_mcp.server.mcp_server.ZettelService', return_value=self.mock_zettel_service)
        self.search_patcher = patch('zettelkasten_mcp.server.mcp_server.SearchService', return_value=self.mock_search_service)
        
        # Start the patchers
        self.mcp_patcher.start()
        self.zettel_patcher.start()
        self.search_patcher.start()
        
        # Create a server instance AFTER setting up the mocks
        self.server = ZettelkastenMcpServer()

    def teardown_method(self):
        """Clean up after each test."""
        self.mcp_patcher.stop()
        self.zettel_patcher.stop()
        self.search_patcher.stop()

    def test_server_initialization(self):
        """Test server initialization."""
        # Check services are initialized
        assert self.mock_zettel_service.initialize.called
        assert self.mock_search_service.initialize.called
        
    def test_create_note_tool(self):
        """Test the zk_create_note tool."""
        # Check the tool is registered
        assert 'zk_create_note' in self.registered_tools
        # Set up return value for create_note
        mock_note = MagicMock()
        mock_note.id = "test123"
        self.mock_zettel_service.create_note.return_value = mock_note
        # Call the tool function directly
        create_note_func = self.registered_tools['zk_create_note']
        result = create_note_func(
            title="Test Note",
            content="Test content",
            note_type="permanent",
            tags="tag1, tag2"
        )
        # Verify result
        assert "successfully" in result
        assert mock_note.id in result
        # Verify service call
        self.mock_zettel_service.create_note.assert_called_with(
            title="Test Note",
            content="Test content",
            note_type=NoteType.PERMANENT,
            tags=["tag1", "tag2"]
        )

    def test_get_note_tool(self):
        """Test the zk_get_note tool."""
        # Check the tool is registered
        assert 'zk_get_note' in self.registered_tools
        
        # Set up mock note
        mock_note = MagicMock()
        mock_note.id = "test123"
        mock_note.title = "Test Note"
        mock_note.content = "Test content"
        mock_note.note_type = NoteType.PERMANENT
        mock_note.created_at.isoformat.return_value = "2023-01-01T12:00:00"
        mock_note.updated_at.isoformat.return_value = "2023-01-01T12:30:00"
        mock_tag1 = MagicMock()
        mock_tag1.name = "tag1"
        mock_tag2 = MagicMock()
        mock_tag2.name = "tag2"
        mock_note.tags = [mock_tag1, mock_tag2]
        mock_note.links = []
        
        # Set up return value for get_note
        self.mock_zettel_service.get_note.return_value = mock_note
        
        # Call the tool function directly
        get_note_func = self.registered_tools['zk_get_note']
        result = get_note_func(identifier="test123")
        
        # Verify result
        assert "# Test Note" in result
        assert "ID: test123" in result
        assert "Test content" in result
        
        # Verify service call
        self.mock_zettel_service.get_note.assert_called_with("test123")

    def test_create_link_tool(self):
        """Test the zk_create_link tool."""
        # Check the tool is registered
        assert 'zk_create_link' in self.registered_tools
        
        # Set up mock notes
        source_note = MagicMock()
        source_note.id = "source123"
        target_note = MagicMock()
        target_note.id = "target456"
        
        # Set up return value for create_link
        self.mock_zettel_service.create_link.return_value = (source_note, target_note)
        
        # Call the tool function directly
        create_link_func = self.registered_tools['zk_create_link']
        result = create_link_func(
            source_id="source123",
            target_id="target456",
            link_type="extends",
            description="Test link",
            bidirectional=True
        )
        
        # Verify result
        assert "Bidirectional link created" in result
        assert "source123" in result
        assert "target456" in result
        
        # Verify service call
        self.mock_zettel_service.create_link.assert_called_with(
            source_id="source123",
            target_id="target456",
            link_type=LinkType.EXTENDS,
            description="Test link",
            bidirectional=True
        )

    def test_search_notes_tool(self):
        """Test the zk_search_notes tool."""
        # Check the tool is registered
        assert 'zk_search_notes' in self.registered_tools
        
        # Set up mock notes
        mock_note1 = MagicMock()
        mock_note1.id = "note1"
        mock_note1.title = "Note 1"
        mock_note1.content = "This is note 1 content"
        mock_tag1 = MagicMock()
        mock_tag1.name = "tag1"
        mock_tag2 = MagicMock()
        mock_tag2.name = "tag2"
        mock_note1.tags = [mock_tag1, mock_tag2]
        mock_note1.created_at.strftime.return_value = "2023-01-01"
        
        mock_note2 = MagicMock()
        mock_note2.id = "note2"
        mock_note2.title = "Note 2"
        mock_note2.content = "This is note 2 content"
        # mock_note2.tags = [MagicMock(name="tag1")]
        mock_tag1 = MagicMock()
        mock_tag1.name = "tag1"
        mock_note2.tags = [mock_tag1]
        mock_note2.created_at.strftime.return_value = "2023-01-02"
        
        # Set up mock search results
        mock_result1 = MagicMock()
        mock_result1.note = mock_note1
        mock_result2 = MagicMock()
        mock_result2.note = mock_note2
        
        self.mock_search_service.search_combined.return_value = [mock_result1, mock_result2]
        
        # Call the tool function directly
        search_notes_func = self.registered_tools['zk_search_notes']
        result = search_notes_func(
            query="test query",
            tags="tag1, tag2",
            note_type="permanent",
            limit=10
        )
        
        # Verify result
        assert "Found 2 matching notes" in result
        assert "Note 1" in result
        assert "Note 2" in result
        
        # Verify service call
        self.mock_search_service.search_combined.assert_called_with(
            text="test query",
            tags=["tag1", "tag2"],
            note_type=NoteType.PERMANENT
        )

    def test_error_handling(self):
        """Test error handling in the server."""
        # Test ValueError handling
        value_error = ValueError("Invalid input")
        result = self.server.format_error_response(value_error)
        assert "Error: Invalid input" in result
        
        # Test IOError handling
        io_error = IOError("File not found")
        result = self.server.format_error_response(io_error)
        assert "Error: File not found" in result
        
        # Test general exception handling
        general_error = Exception("Something went wrong")
        result = self.server.format_error_response(general_error)
        assert "Error: Something went wrong" in result

    def test_find_broken_links_tool(self):
        """Test the zk_find_broken_links tool."""
        # Check the tool is registered
        assert 'zk_find_broken_links' in self.registered_tools
        
        # Create mock notes with broken links
        mock_note1 = MagicMock()
        mock_note1.id = "note1"
        mock_note1.title = "Note 1"
        
        mock_note2 = MagicMock()
        mock_note2.id = "note2"
        mock_note2.title = "Note 2"
        
        # Create a mix of valid and broken links
        mock_link1 = MagicMock()
        mock_link1.source_id = "note1"
        mock_link1.target_id = "existing_note"
        mock_link1.link_type = LinkType.REFERENCE
        mock_link1.description = "Valid link"
        
        mock_link2 = MagicMock()
        mock_link2.source_id = "note1"
        mock_link2.target_id = "broken_note"
        mock_link2.link_type = LinkType.EXTENDS
        mock_link2.description = "Broken link"
        
        mock_link3 = MagicMock()
        mock_link3.source_id = "note2"
        mock_link3.target_id = "another_broken"
        mock_link3.link_type = LinkType.RELATED
        mock_link3.description = None
        
        # Assign links to notes
        mock_note1.links = [mock_link1, mock_link2]
        mock_note2.links = [mock_link3]
        
        # Setup mock responses
        self.mock_zettel_service.get_all_notes.return_value = [mock_note1, mock_note2]
        
        # Setup get_note to return None for broken links
        def mock_get_note(note_id):
            if note_id == "existing_note":
                return MagicMock()
            return None
            
        self.mock_zettel_service.get_note.side_effect = mock_get_note
        
        # Call the tool function
        find_broken_links_func = self.registered_tools['zk_find_broken_links']
        result = find_broken_links_func()
        
        # Verify the result
        assert "Found 2 broken links" in result
        assert "Note 1" in result
        assert "Note 2" in result
        assert "broken_note" in result
        assert "another_broken" in result
        assert "Broken link" in result  # Description is included
        
        # Verify service was called correctly
        self.mock_zettel_service.get_all_notes.assert_called_once()
        assert self.mock_zettel_service.get_note.call_count == 3  # Called for each link
        
    def test_batch_get_notes_tool(self):
        """Test the zk_batch_get_notes tool."""
        # Check the tool is registered
        assert 'zk_batch_get_notes' in self.registered_tools
        
        # Create mock notes
        mock_note1 = MagicMock()
        mock_note1.id = "20230101120000"
        mock_note1.title = "First Note"
        mock_note1.note_type = NoteType.PERMANENT
        mock_note1.created_at = datetime(2023, 1, 1, 12, 0, 0)
        mock_note1.updated_at = datetime(2023, 1, 1, 12, 0, 0)
        mock_note1.tags = []
        mock_note1.content = "First note content"
        mock_note1.links = []
        
        mock_note2 = MagicMock()
        mock_note2.id = "20230102120000"
        mock_note2.title = "Second Note"
        mock_note2.note_type = NoteType.PERMANENT
        mock_note2.created_at = datetime(2023, 1, 2, 12, 0, 0)
        mock_note2.updated_at = datetime(2023, 1, 2, 12, 0, 0)
        mock_note2.tags = [MagicMock(name="tag1"), MagicMock(name="tag2")]
        mock_note2.content = "Second note content"
        mock_note2.links = []
        
        # Setup mock responses
        def mock_get_note(note_id):
            if note_id == "20230101120000":
                return mock_note1
            elif note_id == "20230102120000":
                return mock_note2
            return None
            
        def mock_get_note_by_title(title):
            if title == "Third Note":
                return MagicMock(id="20230103120000", 
                                title="Third Note",
                                note_type=NoteType.PERMANENT,
                                created_at=datetime(2023, 1, 3, 12, 0, 0),
                                updated_at=datetime(2023, 1, 3, 12, 0, 0),
                                tags=[],
                                content="Third note content",
                                links=[])
            return None
            
        self.mock_zettel_service.get_note.side_effect = mock_get_note
        self.mock_zettel_service.get_note_by_title.side_effect = mock_get_note_by_title
        
        # Call the tool function
        batch_get_notes_func = self.registered_tools['zk_batch_get_notes']
        result = batch_get_notes_func(["20230101120000", "20230102120000", "Third Note", "not_found"])
        
        # Verify the result
        assert "Retrieved 3 notes (1 not found)" in result
        assert "First Note" in result
        assert "Second Note" in result
        assert "Third Note" in result
        assert "not_found" in result
        assert "20230101120000" in result
        assert "20230102120000" in result
        assert "20230103120000" in result
        assert "tag1" in result
        assert "tag2" in result
        
        # Test with invalid input
        result_error = batch_get_notes_func("not_a_list")
        assert "Error: note_ids must be a list" in result_error
        
        # Test with too many IDs
        result_too_large = batch_get_notes_func(["id"] * 51)
        assert "Error: Batch size too large" in result_too_large
