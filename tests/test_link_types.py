"""Tests for link type functionality in the Zettelkasten MCP server."""
import pytest
from zettelkasten_mcp.models.schema import LinkType, Note, NoteType, Tag

def test_link_type_creation_and_retrieval(note_repository):
    """Test creating and retrieving links with different semantic types."""
    # Create test notes
    source_note = note_repository.create(Note(
        title="Source Note",
        content="This is the source note.",
        note_type=NoteType.PERMANENT
    ))
    target_note = note_repository.create(Note(
        title="Target Note",
        content="This is the target note.",
        note_type=NoteType.PERMANENT
    ))
    
    # Test all link types
    link_types = [
        (LinkType.EXTENDS, LinkType.EXTENDED_BY),
        (LinkType.REFINES, LinkType.REFINED_BY),
        (LinkType.CONTRADICTS, LinkType.CONTRADICTED_BY),
        (LinkType.QUESTIONS, LinkType.QUESTIONED_BY),
        (LinkType.SUPPORTS, LinkType.SUPPORTED_BY),
        (LinkType.REFERENCE, LinkType.REFERENCE),
        (LinkType.RELATED, LinkType.RELATED)
    ]
    
    for forward_type, reverse_type in link_types:
        # Add link with specific type
        source_note.add_link(
            target_id=target_note.id,
            link_type=forward_type,
            description=f"Testing {forward_type.value} link"
        )
        note_repository.update(source_note)
        
        # Test outgoing link retrieval
        outgoing_notes = note_repository.find_linked_notes(source_note.id, "outgoing")
        assert len(outgoing_notes) == 1
        outgoing_note = outgoing_notes[0]
        outgoing_link = next(
            link for link in outgoing_note.links 
            if link.source_id == source_note.id
        )
        assert outgoing_link.link_type == forward_type
        assert outgoing_link.description == f"Testing {forward_type.value} link"
        
        # Clear links for next test
        source_note.links = []
        note_repository.update(source_note)

def test_bidirectional_link_types(note_repository):
    """Test bidirectional links with proper semantic inverse relationships."""
    # Create test notes
    note1 = note_repository.create(Note(
        title="Note One",
        content="First note for bidirectional linking.",
        note_type=NoteType.PERMANENT
    ))
    note2 = note_repository.create(Note(
        title="Note Two",
        content="Second note for bidirectional linking.",
        note_type=NoteType.PERMANENT
    ))
    
    # Test each semantic link type pair
    test_cases = [
        (LinkType.EXTENDS, LinkType.EXTENDED_BY),
        (LinkType.REFINES, LinkType.REFINED_BY),
        (LinkType.CONTRADICTS, LinkType.CONTRADICTED_BY),
        (LinkType.QUESTIONS, LinkType.QUESTIONED_BY),
        (LinkType.SUPPORTS, LinkType.SUPPORTED_BY)
    ]
    
    for forward_type, expected_reverse_type in test_cases:
        # Create bidirectional link
        note1.add_link(
            target_id=note2.id,
            link_type=forward_type,
            description=f"Forward {forward_type.value} link"
        )
        note2.add_link(
            target_id=note1.id,
            link_type=expected_reverse_type,
            description=f"Reverse {expected_reverse_type.value} link"
        )
        note_repository.update(note1)
        note_repository.update(note2)
        
        # Check forward direction
        forward_notes = note_repository.find_linked_notes(note1.id, "outgoing")
        assert len(forward_notes) == 1
        forward_link = next(
            link for link in forward_notes[0].links 
            if link.source_id == note1.id
        )
        assert forward_link.link_type == forward_type
        
        # Check reverse direction
        reverse_notes = note_repository.find_linked_notes(note2.id, "outgoing")
        assert len(reverse_notes) == 1
        reverse_link = next(
            link for link in reverse_notes[0].links 
            if link.source_id == note2.id
        )
        assert reverse_link.link_type == expected_reverse_type
        
        # Clear links for next test
        note1.links = []
        note2.links = []
        note_repository.update(note1)
        note_repository.update(note2)

def test_link_type_persistence(note_repository):
    """Test that link types persist correctly through save and reload."""
    # Create test notes
    source = note_repository.create(Note(
        title="Source Note",
        content="Testing link type persistence.",
        note_type=NoteType.PERMANENT
    ))
    target = note_repository.create(Note(
        title="Target Note",
        content="Target for link type persistence test.",
        note_type=NoteType.PERMANENT
    ))
    
    # Create links with different types
    test_links = [
        (LinkType.EXTENDS, "Extension relationship"),
        (LinkType.REFINES, "Refinement relationship"),
        (LinkType.SUPPORTS, "Supporting evidence")
    ]
    
    for link_type, description in test_links:
        # Add link
        source.add_link(
            target_id=target.id,
            link_type=link_type,
            description=description
        )
    
    # Save to repository
    note_repository.update(source)
    
    # Retrieve and verify each direction
    for direction in ["outgoing", "incoming", "both"]:
        linked_notes = note_repository.find_linked_notes(source.id, direction)
        if direction in ["outgoing", "both"]:
            assert len(linked_notes) == 1
            retrieved_note = linked_notes[0]
            # Verify each link type and description was preserved
            for link_type, description in test_links:
                matching_links = [
                    link for link in retrieved_note.links
                    if link.source_id == source.id
                    and link.link_type == link_type
                    and link.description == description
                ]
                assert len(matching_links) == 1

def test_link_type_updates(note_repository):
    """Test updating link types between notes."""
    # Create test notes
    note1 = note_repository.create(Note(
        title="First Note",
        content="Testing link type updates.",
        note_type=NoteType.PERMANENT
    ))
    note2 = note_repository.create(Note(
        title="Second Note",
        content="Target for link type update test.",
        note_type=NoteType.PERMANENT
    ))
    
    # Initial link
    note1.add_link(
        target_id=note2.id,
        link_type=LinkType.REFERENCE,
        description="Initial reference link"
    )
    note_repository.update(note1)
    
    # Verify initial link
    linked_notes = note_repository.find_linked_notes(note1.id, "outgoing")
    assert len(linked_notes) == 1
    initial_link = next(
        link for link in linked_notes[0].links
        if link.source_id == note1.id
    )
    assert initial_link.link_type == LinkType.REFERENCE
    
    # Update to a different link type
    note1.links = []  # Clear existing links
    note1.add_link(
        target_id=note2.id,
        link_type=LinkType.EXTENDS,
        description="Updated to extends relationship"
    )
    note_repository.update(note1)
    
    # Verify updated link type
    updated_notes = note_repository.find_linked_notes(note1.id, "outgoing")
    assert len(updated_notes) == 1
    updated_link = next(
        link for link in updated_notes[0].links
        if link.source_id == note1.id
    )
    assert updated_link.link_type == LinkType.EXTENDS
    assert updated_link.description == "Updated to extends relationship" 