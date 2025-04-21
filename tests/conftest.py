"""Common test fixtures for the Zettelkasten MCP server."""
import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from zettelkasten_mcp.config import ZettelkastenConfig, config
from zettelkasten_mcp.models.db_models import Base
from zettelkasten_mcp.services.zettel_service import ZettelService
from zettelkasten_mcp.storage.note_repository import NoteRepository
from zettelkasten_mcp.services.search_service import SearchService
from zettelkasten_mcp.server.mcp_server import ZettelkastenMcpServer

@pytest.fixture
def test_config():
    """Fixture for test configuration."""
    # Save original config values
    original_notes_dir = config.notes_dir
    original_database_path = config.database_path
    
    # Create temporary directories for test
    with tempfile.TemporaryDirectory() as temp_dir:
        notes_dir = os.path.join(temp_dir, "notes")
        os.makedirs(notes_dir, exist_ok=True)
        
        # Update config for test
        config.notes_dir = notes_dir
        config.database_path = os.path.join(temp_dir, "test_zettelkasten.db")
        
        yield config
        
        # Clean up resources
        try:
            if os.path.exists(config.database_path):
                os.unlink(config.database_path)
        except PermissionError:
            pass  # Handle case where file is still in use
            
        # Restore original config
        config.notes_dir = original_notes_dir
        config.database_path = original_database_path

@pytest.fixture
def note_repository(test_config):
    """Fixture for note repository."""
    repo = NoteRepository(notes_dir=test_config.notes_dir)
    yield repo
    repo.close()

@pytest.fixture
def zettel_service(note_repository):
    """Fixture for zettel service."""
    service = ZettelService(repository=note_repository)
    yield service
    service.cleanup()

@pytest.fixture
def search_service(zettel_service):
    """Fixture for search service."""
    service = SearchService(zettel_service=zettel_service)
    service.initialize()
    yield service
    service.cleanup()

@pytest.fixture
def mcp_server(zettel_service, search_service):
    """Fixture for MCP server."""
    server = ZettelkastenMcpServer(zettel_service=zettel_service, search_service=search_service)
    yield server
    server.cleanup()

@pytest.fixture(scope="function")
def db_session(test_config: ZettelkastenConfig) -> Generator[Session, None, None]:
    """Create a test database session.
    
    Args:
        test_config: Test configuration fixture.
        
    Yields:
        Database session for testing.
    """
    engine = create_engine(test_config.get_db_url())
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
        Base.metadata.drop_all(engine)
