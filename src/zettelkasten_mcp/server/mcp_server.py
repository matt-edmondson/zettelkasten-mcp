"""MCP server implementation for the Zettelkasten."""
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import exc as sqlalchemy_exc
from mcp.server.fastmcp import FastMCP
from zettelkasten_mcp.config import config
from zettelkasten_mcp.models.schema import LinkType, NoteType
from zettelkasten_mcp.services.search_service import SearchService
from zettelkasten_mcp.services.zettel_service import ZettelService

logger = logging.getLogger(__name__)

class ZettelkastenMcpServer:
    """MCP server for Zettelkasten."""
    def __init__(self):
        """Initialize the MCP server."""
        self.mcp = FastMCP(
            config.server_name,
            version=config.server_version
        )
        # Services
        self.zettel_service = ZettelService()
        self.search_service = SearchService(self.zettel_service)
        # Initialize services
        self.initialize()
        # Register tools
        self._register_tools()
        self._register_resources()
        self._register_prompts()

    def initialize(self) -> None:
        """Initialize services."""
        self.zettel_service.initialize()
        self.search_service.initialize()
        logger.info("Zettelkasten MCP server initialized")

    def format_error_response(self, error: Exception) -> str:
        """Format an error response in a consistent way.
        
        Args:
            error: The exception that occurred
            
        Returns:
            Formatted error message with appropriate level of detail
        """
        # Generate a unique error ID for traceability in logs
        error_id = str(uuid.uuid4())[:8]
        
        if isinstance(error, ValueError):
            # Domain validation errors - typically safe to show to users
            logger.error(f"Validation error [{error_id}]: {str(error)}")
            return f"Error: {str(error)}"
        elif isinstance(error, (IOError, OSError)):
            # File system errors - don't expose paths or detailed error messages
            logger.error(f"File system error [{error_id}]: {str(error)}", exc_info=True)
            # return f"Unable to access the requested resource. Error ID: {error_id}"
            return f"Error: {str(error)}"
        else:
            # Unexpected errors - log with full stack trace but return generic message
            logger.error(f"Unexpected error [{error_id}]: {str(error)}", exc_info=True)
            # return f"An unexpected error occurred. Error ID: {error_id}"
            return f"Error: {str(error)}"

    def _register_tools(self) -> None:
        """Register MCP tools."""
        # Create a new note
        @self.mcp.tool(name="zk_create_note")
        def zk_create_note(
            title: str, 
            content: str, 
            note_type: str = "permanent",
            tags: Optional[str] = None
        ) -> str:
            """Create a new Zettelkasten note.
            Args:
                title: The title of the note
                content: The main content of the note
                note_type: Type of note (fleeting, literature, permanent, structure, hub)
                tags: Comma-separated list of tags (optional)
            """
            try:
                # Convert note_type string to enum
                try:
                    note_type_enum = NoteType(note_type.lower())
                except ValueError:
                    return f"Invalid note type: {note_type}. Valid types are: {', '.join(t.value for t in NoteType)}"
                
                # Convert tags string to list
                tag_list = []
                if tags:
                    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
                
                # Create the note
                note = self.zettel_service.create_note(
                    title=title,
                    content=content,
                    note_type=note_type_enum,
                    tags=tag_list,
                )
                return f"Note created successfully with ID: {note.id}"
            except Exception as e:
                return self.format_error_response(e)

        # Get a note by ID or title
        @self.mcp.tool(name="zk_get_note")
        def zk_get_note(identifier: str) -> str:
            """Retrieve a note by ID or title.
            Args:
                identifier: The ID or title of the note
            """
            try:
                identifier = str(identifier)
                # Try to get by ID first
                note = self.zettel_service.get_note(identifier)
                # If not found, try by title
                if not note:
                    note = self.zettel_service.get_note_by_title(identifier)
                if not note:
                    return f"Note not found: {identifier}"
                
                # Format the note
                result = f"# {note.title}\n"
                result += f"ID: {note.id}\n"
                result += f"Type: {note.note_type.value}\n"
                result += f"Created: {note.created_at.isoformat()}\n"
                result += f"Updated: {note.updated_at.isoformat()}\n"
                if note.tags:
                    result += f"Tags: {', '.join(tag.name for tag in note.tags)}\n"
                result += f"\n{note.content}\n"
                if note.links:
                    result += "\n## Links\n"
                    for link in note.links:
                        desc = f" - {link.description}" if link.description else ""
                        result += f"- {link.link_type.value}: {link.target_id}{desc}\n"
                return result
            except Exception as e:
                return self.format_error_response(e)

        # Update a note
        @self.mcp.tool(name="zk_update_note")
        def zk_update_note(
            note_id: str,
            title: Optional[str] = None,
            content: Optional[str] = None,
            note_type: Optional[str] = None,
            tags: Optional[str] = None
        ) -> str:
            """Update an existing note.
            Args:
                note_id: The ID of the note to update
                title: New title (optional)
                content: New content (optional)
                note_type: New note type (optional)
                tags: New comma-separated list of tags (optional)
            """
            try:
                # Get the note
                note = self.zettel_service.get_note(str(note_id))
                if not note:
                    return f"Note not found: {note_id}"
                
                # Convert note_type string to enum if provided
                note_type_enum = None
                if note_type:
                    try:
                        note_type_enum = NoteType(note_type.lower())
                    except ValueError:
                        return f"Invalid note type: {note_type}. Valid types are: {', '.join(t.value for t in NoteType)}"
                
                # Convert tags string to list if provided
                tag_list = None
                if tags is not None:  # Allow empty string to clear tags
                    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
                
                # Update the note
                updated_note = self.zettel_service.update_note(
                    note_id=note_id,
                    title=title,
                    content=content,
                    note_type=note_type_enum,
                    tags=tag_list
                )
                return f"Note updated successfully: {updated_note.id}"
            except Exception as e:
                return self.format_error_response(e)

        # Delete a note
        @self.mcp.tool(name="zk_delete_note")
        def zk_delete_note(note_id: str) -> str:
            """Delete a note.
            Args:
                note_id: The ID of the note to delete
            """
            try:
                # Check if note exists
                note = self.zettel_service.get_note(note_id)
                if not note:
                    return f"Note not found: {note_id}"
                
                # Delete the note
                self.zettel_service.delete_note(str(note_id))
                return f"Note deleted successfully: {note_id}"
            except Exception as e:
                return self.format_error_response(e)

        # Add a link between notes
        @self.mcp.tool(name="zk_create_link")
        def zk_create_link(
            source_id: str,
            target_id: str,
            link_type: str = "reference",
            description: Optional[str] = None,
            bidirectional: bool = False
        ) -> str:
            """Create a link between two notes.
            Args:
                source_id: ID of the source note
                target_id: ID of the target note
                link_type: Type of link (reference, extends, refines, contradicts, questions, supports, related)
                description: Optional description of the link
                bidirectional: Whether to create a link in both directions
            """
            try:
                # Convert link_type string to enum
                try:
                    source_id_str = str(source_id)
                    target_id_str = str(target_id)
                    link_type_enum = LinkType(link_type.lower())
                except ValueError:
                    return f"Invalid link type: {link_type}. Valid types are: {', '.join(t.value for t in LinkType)}"
                
                # Create the link
                source_note, target_note = self.zettel_service.create_link(
                    source_id=source_id,
                    target_id=target_id,
                    link_type=link_type_enum,
                    description=description,
                    bidirectional=bidirectional
                )
                if bidirectional:
                    return f"Bidirectional link created between {source_id} and {target_id}"
                else:
                    return f"Link created from {source_id} to {target_id}"
            except (Exception, sqlalchemy_exc.IntegrityError) as e:
                if "UNIQUE constraint failed" in str(e):
                    return f"A link of this type already exists between these notes. Try a different link type."
                return self.format_error_response(e)

        # Remove a link between notes
        @self.mcp.tool(name="zk_remove_link")
        def zk_remove_link(
            source_id: str,
            target_id: str,
            bidirectional: bool = False
        ) -> str:
            """Remove a link between two notes.
            Args:
                source_id: ID of the source note
                target_id: ID of the target note
                bidirectional: Whether to remove the link in both directions
            """
            try:
                # Remove the link
                source_note, target_note = self.zettel_service.remove_link(
                    source_id=str(source_id),
                    target_id=str(target_id),
                    bidirectional=bidirectional
                )
                if bidirectional:
                    return f"Bidirectional link removed between {source_id} and {target_id}"
                else:
                    return f"Link removed from {source_id} to {target_id}"
            except Exception as e:
                return self.format_error_response(e)

        # Search for notes
        @self.mcp.tool(name="zk_search_notes")
        def zk_search_notes(
            query: Optional[str] = None,
            tags: Optional[str] = None,
            note_type: Optional[str] = None,
            limit: int = 10
        ) -> str:
            """Search for notes by text, tags, or type.
            Args:
                query: Text to search for in titles and content
                tags: Comma-separated list of tags to filter by
                note_type: Type of note to filter by
                limit: Maximum number of results to return
            """
            try:
                # Convert tags string to list if provided
                tag_list = None
                if tags:
                    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
                
                # Convert note_type string to enum if provided
                note_type_enum = None
                if note_type:
                    try:
                        note_type_enum = NoteType(note_type.lower())
                    except ValueError:
                        return f"Invalid note type: {note_type}. Valid types are: {', '.join(t.value for t in NoteType)}"
                
                # Perform search
                results = self.search_service.search_combined(
                    text=query,
                    tags=tag_list,
                    note_type=note_type_enum
                )
                
                # Limit results
                results = results[:limit]
                if not results:
                    return "No matching notes found."
                
                # Format results
                output = f"Found {len(results)} matching notes:\n\n"
                for i, result in enumerate(results, 1):
                    note = result.note
                    output += f"{i}. {note.title} (ID: {note.id})\n"
                    if note.tags:
                        output += f"   Tags: {', '.join(tag.name for tag in note.tags)}\n"
                    output += f"   Created: {note.created_at.strftime('%Y-%m-%d')}\n"
                    # Add a snippet of content (first 150 chars)
                    content_preview = note.content[:150].replace("\n", " ")
                    if len(note.content) > 150:
                        content_preview += "..."
                    output += f"   Preview: {content_preview}\n\n"
                return output
            except Exception as e:
                return self.format_error_response(e)

        # Get linked notes
        @self.mcp.tool(name="zk_get_linked_notes")
        def zk_get_linked_notes(
            note_id: str,
            direction: str = "both"
        ) -> str:
            """Get notes linked to/from a note.
            Args:
                note_id: ID of the note
                direction: Direction of links (outgoing, incoming, both)
            """
            try:
                if direction not in ["outgoing", "incoming", "both"]:
                    return f"Invalid direction: {direction}. Use 'outgoing', 'incoming', or 'both'."
                
                # Get linked notes
                linked_notes = self.zettel_service.get_linked_notes(str(note_id), direction)
                if not linked_notes:
                    return f"No {direction} links found for note {note_id}."
                
                # Format results
                output = f"Found {len(linked_notes)} {direction} linked notes for {note_id}:\n\n"
                for i, note in enumerate(linked_notes, 1):
                    output += f"{i}. {note.title} (ID: {note.id})\n"
                    if note.tags:
                        output += f"   Tags: {', '.join(tag.name for tag in note.tags)}\n"
                    # Try to determine link type
                    if direction in ["outgoing", "both"]:
                        # Check source note's outgoing links
                        source_note = self.zettel_service.get_note(str(note_id))
                        if source_note:
                            for link in source_note.links:
                                if link.target_id == note.id:
                                    output += f"   Link type: {link.link_type.value}\n"
                                    if link.description:
                                        output += f"   Description: {link.description}\n"
                                    break
                    if direction in ["incoming", "both"]:
                        # Check target note's outgoing links
                        for link in note.links:
                            if link.target_id == str(note_id):
                                output += f"   Incoming link type: {link.link_type.value}\n"
                                if link.description:
                                    output += f"   Description: {link.description}\n"
                                break
                    output += "\n"
                return output
            except Exception as e:
                return self.format_error_response(e)

        # Get all tags
        @self.mcp.tool(name="zk_get_all_tags")
        def zk_get_all_tags() -> str:
            """Get all tags in the Zettelkasten."""
            try:
                tags = self.zettel_service.get_all_tags()
                if not tags:
                    return "No tags found in the Zettelkasten."
                
                # Format results
                output = f"Found {len(tags)} tags:\n\n"
                # Sort alphabetically
                tags.sort(key=lambda t: t.name.lower())
                for i, tag in enumerate(tags, 1):
                    output += f"{i}. {tag.name}\n"
                return output
            except Exception as e:
                return self.format_error_response(e)

        # Find similar notes
        @self.mcp.tool(name="zk_find_similar_notes")
        def zk_find_similar_notes(
            note_id: str,
            threshold: float = 0.3,
            limit: int = 5
        ) -> str:
            """Find notes similar to a given note.
            Args:
                note_id: ID of the reference note
                threshold: Similarity threshold (0.0-1.0)
                limit: Maximum number of results to return
            """
            try:
                # Get similar notes
                similar_notes = self.zettel_service.find_similar_notes(str(note_id), threshold)
                # Limit results
                similar_notes = similar_notes[:limit]
                if not similar_notes:
                    return f"No similar notes found for {note_id} with threshold {threshold}."
                
                # Format results
                output = f"Found {len(similar_notes)} similar notes for {note_id}:\n\n"
                for i, (note, similarity) in enumerate(similar_notes, 1):
                    output += f"{i}. {note.title} (ID: {note.id})\n"
                    output += f"   Similarity: {similarity:.2f}\n"
                    if note.tags:
                        output += f"   Tags: {', '.join(tag.name for tag in note.tags)}\n"
                    # Add a snippet of content (first 100 chars)
                    content_preview = note.content[:100].replace("\n", " ")
                    if len(note.content) > 100:
                        content_preview += "..."
                    output += f"   Preview: {content_preview}\n\n"
                return output
            except Exception as e:
                return self.format_error_response(e)

        # Find central notes
        @self.mcp.tool(name="zk_find_central_notes")
        def zk_find_central_notes(limit: int = 10) -> str:
            """Find notes with the most connections (incoming + outgoing links).
            Notes are ranked by their total number of connections, determining
            their centrality in the knowledge network. Due to database constraints,
            only one link of each type is counted between any pair of notes.

            Args:
                limit: Maximum number of results to return (default: 10)
            """
            try:
                # Get central notes
                central_notes = self.search_service.find_central_notes(limit)
                if not central_notes:
                    return "No notes found with connections."
                
                # Format results
                output = "Central notes in the Zettelkasten (most connected):\n\n"
                for i, (note, connection_count) in enumerate(central_notes, 1):
                    output += f"{i}. {note.title} (ID: {note.id})\n"
                    output += f"   Connections: {connection_count}\n"
                    if note.tags:
                        output += f"   Tags: {', '.join(tag.name for tag in note.tags)}\n"
                    # Add a snippet of content (first 100 chars)
                    content_preview = note.content[:100].replace("\n", " ")
                    if len(note.content) > 100:
                        content_preview += "..."
                    output += f"   Preview: {content_preview}\n\n"
                return output
            except Exception as e:
                return self.format_error_response(e)

        # Find orphaned notes
        @self.mcp.tool(name="zk_find_orphaned_notes")
        def zk_find_orphaned_notes() -> str:
            """Find notes with no connections to other notes."""
            try:
                # Get orphaned notes
                orphans = self.search_service.find_orphaned_notes()
                if not orphans:
                    return "No orphaned notes found."
                
                # Format results
                output = f"Found {len(orphans)} orphaned notes:\n\n"
                for i, note in enumerate(orphans, 1):
                    output += f"{i}. {note.title} (ID: {note.id})\n"
                    if note.tags:
                        output += f"   Tags: {', '.join(tag.name for tag in note.tags)}\n"
                    # Add a snippet of content (first 100 chars)
                    content_preview = note.content[:100].replace("\n", " ")
                    if len(note.content) > 100:
                        content_preview += "..."
                    output += f"   Preview: {content_preview}\n\n"
                return output
            except Exception as e:
                return self.format_error_response(e)

        # List notes by date range
        @self.mcp.tool(name="zk_list_notes_by_date")
        def zk_list_notes_by_date(
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            use_updated: bool = False,
            limit: int = 10
        ) -> str:
            """List notes created or updated within a date range.
            Args:
                start_date: Start date in ISO format (YYYY-MM-DD)
                end_date: End date in ISO format (YYYY-MM-DD)
                use_updated: Whether to use updated_at instead of created_at
                limit: Maximum number of results to return
            """
            try:
                # Parse dates
                start_datetime = None
                if start_date:
                    start_datetime = datetime.fromisoformat(f"{start_date}T00:00:00")
                end_datetime = None
                if end_date:
                    end_datetime = datetime.fromisoformat(f"{end_date}T23:59:59")
                
                # Get notes
                notes = self.search_service.find_notes_by_date_range(
                    start_date=start_datetime,
                    end_date=end_datetime,
                    use_updated=use_updated
                )
                
                # Limit results
                notes = notes[:limit]
                if not notes:
                    date_type = "updated" if use_updated else "created"
                    date_range = ""
                    if start_date and end_date:
                        date_range = f" between {start_date} and {end_date}"
                    elif start_date:
                        date_range = f" after {start_date}"
                    elif end_date:
                        date_range = f" before {end_date}"
                    return f"No notes found {date_type}{date_range}."
                
                # Format results
                date_type = "updated" if use_updated else "created"
                output = f"Notes {date_type}"
                if start_date or end_date:
                    if start_date and end_date:
                        output += f" between {start_date} and {end_date}"
                    elif start_date:
                        output += f" after {start_date}"
                    elif end_date:
                        output += f" before {end_date}"
                output += f" (showing {len(notes)} results):\n\n"
                for i, note in enumerate(notes, 1):
                    date = note.updated_at if use_updated else note.created_at
                    output += f"{i}. {note.title} (ID: {note.id})\n"
                    output += f"   {date_type.capitalize()}: {date.strftime('%Y-%m-%d %H:%M')}\n"
                    if note.tags:
                        output += f"   Tags: {', '.join(tag.name for tag in note.tags)}\n"
                    # Add a snippet of content (first 100 chars)
                    content_preview = note.content[:100].replace("\n", " ")
                    if len(note.content) > 100:
                        content_preview += "..."
                    output += f"   Preview: {content_preview}\n\n"
                return output
            except ValueError as e:
                # Special handling for date parsing errors
                logger.error(f"Date parsing error: {str(e)}")
                return f"Error parsing date: {str(e)}"
            except Exception as e:
                return self.format_error_response(e)

        # Rebuild the index
        @self.mcp.tool(name="zk_rebuild_index")
        def zk_rebuild_index() -> str:
            """Rebuild the database index from files."""
            try:
                # Get count before rebuild
                note_count_before = len(self.zettel_service.get_all_notes())
                
                # Perform the rebuild
                self.zettel_service.rebuild_index()
                
                # Get count after rebuild
                note_count_after = len(self.zettel_service.get_all_notes())
                
                # Return a detailed success message
                return (
                    f"Database index rebuilt successfully.\n"
                    f"Notes processed: {note_count_after}\n"
                    f"Change in note count: {note_count_after - note_count_before}"
                )
            except Exception as e:
                # Provide a detailed error message
                logger.error(f"Failed to rebuild index: {e}", exc_info=True)
                return self.format_error_response(e)
        
        # Batch create notes
        @self.mcp.tool(name="zk_batch_create_notes")
        def zk_batch_create_notes(notes: List[Dict[str, Any]]) -> str:
            """Create multiple notes in a batch operation.
            Args:
                notes: List of note objects, each with:
                    - title: Note title (required)
                    - content: Note content (required) 
                    - note_type: Type of note (optional, default: "permanent")
                    - tags: Comma-separated list of tags (optional)
            
            Example:
                [
                    {"title": "Note 1", "content": "Content 1", "note_type": "permanent", "tags": "tag1,tag2"},
                    {"title": "Note 2", "content": "Content 2"}
                ]
            """
            try:
                # Prepare note data for the service layer
                notes_data = []
                for note in notes:
                    # Extract required fields
                    title = note.get("title")
                    content = note.get("content")
                    
                    # Extract optional fields
                    note_type_str = note.get("note_type", "permanent")
                    tags_str = note.get("tags", "")
                    
                    # Convert note_type string to enum
                    try:
                        note_type_enum = NoteType(note_type_str.lower())
                    except ValueError:
                        note_type_enum = NoteType.PERMANENT  # Use default, service will validate
                    
                    # Convert tags string to list
                    tag_list = []
                    if tags_str:
                        tag_list = [t.strip() for t in tags_str.split(",") if t.strip()]
                    
                    # Add to batch
                    notes_data.append({
                        "title": title,
                        "content": content,
                        "note_type": note_type_enum,
                        "tags": tag_list
                    })
                
                # Delegate to service layer
                batch_result = self.zettel_service.batch_create_notes(notes_data)
                
                # Format response
                result = f"Batch note creation completed: {batch_result.success_count}/{batch_result.total_count} successful\n\n"
                
                for i, op_result in enumerate(batch_result.results, 1):
                    if op_result.success:
                        note = op_result.result
                        result += f"{i}. Created: '{note.title}' (ID: {note.id})\n"
                    else:
                        result += f"{i}. Failed: {op_result.error}\n"
                
                return result
            except Exception as e:
                return self.format_error_response(e)

        # Batch update notes
        @self.mcp.tool(name="zk_batch_update_notes")
        def zk_batch_update_notes(updates: List[Dict[str, Any]]) -> str:
            """Update multiple notes in a batch operation.
            Args:
                updates: List of note update objects, each with:
                    - note_id: ID of the note to update (required)
                    - title: New title (optional)
                    - content: New content (optional)
                    - note_type: New note type (optional)
                    - tags: New comma-separated list of tags (optional)
                    
            Example:
                [
                    {"note_id": "20230101120000", "title": "Updated Title"},
                    {"note_id": "20230102120000", "content": "Updated content", "tags": "new_tag,another_tag"}
                ]
            """
            try:
                # Prepare update data for the service layer
                updates_data = []
                
                for update in updates:
                    # Extract fields
                    note_id = update.get("note_id")
                    title = update.get("title")
                    content = update.get("content")
                    note_type_str = update.get("note_type")
                    tags_str = update.get("tags")
                    
                    # Convert note_type if provided
                    note_type_enum = None
                    if note_type_str:
                        try:
                            note_type_enum = NoteType(note_type_str.lower())
                        except ValueError:
                            # Service will handle validation
                            pass
                    
                    # Convert tags if provided
                    tag_list = None
                    if tags_str is not None:  # Allow empty string to clear tags
                        tag_list = [t.strip() for t in tags_str.split(",") if t.strip()]
                    
                    # Add to batch
                    updates_data.append({
                        "note_id": note_id,
                        "title": title,
                        "content": content,
                        "note_type": note_type_enum,
                        "tags": tag_list
                    })
                
                # Delegate to service layer
                batch_result = self.zettel_service.batch_update_notes(updates_data)
                
                # Format response
                result = f"Batch note update completed: {batch_result.success_count}/{batch_result.total_count} successful\n\n"
                
                for i, op_result in enumerate(batch_result.results, 1):
                    if op_result.success:
                        note = op_result.result
                        result += f"{i}. Updated: ID {note.id} - '{note.title}'\n"
                    else:
                        item_id = op_result.item_id
                        result += f"{i}. Failed: ID {item_id} - {op_result.error}\n"
                
                return result
            except Exception as e:
                return self.format_error_response(e)

        # Batch delete notes
        @self.mcp.tool(name="zk_batch_delete_notes")
        def zk_batch_delete_notes(ids: List[str]) -> str:
            """Delete multiple notes in a batch operation.
            Args:
                ids: List of note IDs to delete
                
            Example:
                ["20230101120000", "20230102120000"]
            """
            try:
                # Delegate to service layer
                batch_result = self.zettel_service.batch_delete_notes(ids)
                
                # Format response
                result = f"Batch note deletion completed: {batch_result.success_count}/{batch_result.total_count} successful\n\n"
                
                for i, op_result in enumerate(batch_result.results, 1):
                    if op_result.success:
                        item_id = op_result.item_id
                        result += f"{i}. Deleted: ID {item_id}\n"
                    else:
                        item_id = op_result.item_id
                        result += f"{i}. Failed: ID {item_id} - {op_result.error}\n"
                
                return result
            except Exception as e:
                return self.format_error_response(e)

        # Batch create links
        @self.mcp.tool(name="zk_batch_create_links")
        def zk_batch_create_links(links: List[Dict[str, Any]]) -> str:
            """Create multiple links between notes in a batch operation.
            Args:
                links: List of link objects, each with:
                    - source_id: ID of source note (required)
                    - target_id: ID of target note (required)
                    - link_type: Type of link (optional, default: "reference")
                    - description: Link description (optional)
                    - bidirectional: Whether to create a reciprocal link (optional, default: false)
                    
            Example:
                [
                    {"source_id": "20230101120000", "target_id": "20230102120000"},
                    {"source_id": "20230103120000", "target_id": "20230104120000", "link_type": "refines", "description": "Refines the concept", "bidirectional": true}
                ]
            """
            try:
                # Prepare link data for the service layer
                link_operations = []
                
                for link in links:
                    # Extract required fields
                    source_id = link.get("source_id")
                    target_id = link.get("target_id")
                    
                    # Extract optional fields
                    link_type_str = link.get("link_type", "reference")
                    description = link.get("description")
                    bidirectional = link.get("bidirectional", False)
                    
                    # Convert link_type string to enum
                    try:
                        link_type_enum = LinkType(link_type_str.lower())
                    except ValueError:
                        link_type_enum = LinkType.REFERENCE  # Default value, service will validate
                    
                    # Add to batch
                    link_operations.append({
                        "source_id": source_id,
                        "target_id": target_id,
                        "link_type": link_type_enum,
                        "description": description,
                        "bidirectional": bidirectional
                    })
                
                # Delegate to service layer
                batch_result = self.zettel_service.batch_create_links(link_operations)
                
                # Format response
                result = f"Batch link creation completed: {batch_result.success_count}/{batch_result.total_count} successful\n\n"
                
                for i, op_result in enumerate(batch_result.results, 1):
                    if op_result.success:
                        source_note, target_note = op_result.result
                        link_type = link_operations[i-1].get("link_type").value
                        is_bidirectional = link_operations[i-1].get("bidirectional", False)
                        
                        link_desc = link_type + (" (bidirectional)" if is_bidirectional else "")
                        result += f"{i}. Created: {source_note.title} -> {target_note.title} [{link_desc}]\n"
                    else:
                        # Get the failed operation
                        if i-1 < len(link_operations):
                            source_id = link_operations[i-1].get("source_id", "unknown")
                            target_id = link_operations[i-1].get("target_id", "unknown")
                            result += f"{i}. Failed: {source_id} -> {target_id} - {op_result.error}\n"
                        else:
                            result += f"{i}. Failed: Unknown operation - {op_result.error}\n"
                
                return result
            except Exception as e:
                return self.format_error_response(e)
                
        # Batch search by text
        @self.mcp.tool(name="zk_batch_search_by_text")
        def zk_batch_search_by_text(queries: List[str], include_content: bool = True, 
                                   include_title: bool = True, limit: int = 5) -> str:
            """Perform multiple text searches in a batch operation.
            Args:
                queries: List of search query strings
                include_content: Whether to search in content (default: true)
                include_title: Whether to search in titles (default: true)
                limit: Maximum number of results per query (default: 5)
                
            Example:
                ["search term 1", "search term 2"]
            """
            try:
                if not isinstance(queries, list):
                    return "Error: Input must contain an array of search queries"
                
                # Delegate to service layer
                batch_result = self.search_service.batch_search_by_text(
                    queries=queries,
                    include_content=include_content,
                    include_title=include_title,
                    limit=limit
                )
                
                # Format response
                output = f"Batch search completed for {batch_result.total_count} queries - {batch_result.success_count} successful\n\n"
                
                for i, op_result in enumerate(batch_result.results, 1):
                    if op_result.success:
                        query = op_result.item_id
                        search_results = op_result.result
                        
                        output += f"{i}. Query: \"{query}\"\n"
                        output += f"   Found: {len(search_results)} results\n"
                        
                        # List the results for this query
                        if search_results:
                            for j, result in enumerate(search_results, 1):
                                note = result.note
                                output += f"   {j}. {note.title} (ID: {note.id})\n"
                                if note.tags:
                                    output += f"      Tags: {', '.join(tag.name for tag in note.tags)}\n"
                                
                                # Show the score and matched terms
                                output += f"      Score: {result.score:.2f}\n"
                                if result.matched_terms:
                                    output += f"      Matched terms: {', '.join(result.matched_terms)}\n"
                                
                                # Add context snippet if available
                                if result.matched_context:
                                    output += f"      Context: \"{result.matched_context}\"\n"
                        else:
                            output += "   No matches found\n"
                    else:
                        query = op_result.item_id
                        output += f"{i}. Query: \"{query}\" - Failed: {op_result.error}\n"
                    
                    output += "\n"
                
                return output
            except Exception as e:
                return self.format_error_response(e)

    def _register_resources(self) -> None:
        """Register MCP resources."""
        # Currently, we don't define resources for the Zettelkasten server
        pass

    def _register_prompts(self) -> None:
        """Register MCP prompts."""
        # Currently, we don't define prompts for the Zettelkasten server
        pass

    def run(self) -> None:
        """Run the MCP server."""
        self.mcp.run()
