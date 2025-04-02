# Zettelkasten MCP Server

A Model Context Protocol (MCP) server that implements the Zettelkasten knowledge management methodology, allowing you to create, link, and search atomic notes through Claude and other MCP-compatible clients.

## What is Zettelkasten?

The Zettelkasten method is a knowledge management system developed by German sociologist Niklas Luhmann, who used it to produce over 70 books and hundreds of articles. It consists of three core principles:

1. **Atomicity**: Each note contains exactly one idea, making it a discrete unit of knowledge
2. **Connectivity**: Notes are linked together to create a network of knowledge, with meaningful relationships between ideas
3. **Emergence**: As the network grows, new patterns and insights emerge that weren't obvious when the individual notes were created

What makes the Zettelkasten approach powerful is how it enables exploration in multiple ways. You can dive deeper into specific topics by following connections within a subject area ("vertical exploration"), or discover unexpected relationships between different fields by traversing links that cross domains ("horizontal exploration"). This structure invites serendipitous discoveries as you follow trails of thought from note to note, all while keeping each piece of information easily accessible through its unique identifier.

Luhmann called his system his "second brain" or "communication partner" - this digital implementation aims to provide similar benefits through modern technology.

## Features

- Create atomic notes with unique timestamp-based IDs
- Link notes bidirectionally to build a knowledge graph
- Tag notes for categorical organization
- Search notes by content, tags, or links
- Use markdown format for human readability and editing
- Integrate with Claude through MCP for AI-assisted knowledge management
- Dual storage architecture (see below)
- Synchronous operation model for simplified architecture

## Storage Architecture

This system uses a dual storage approach:

1. **Markdown Files**: All notes are stored as human-readable Markdown files with YAML frontmatter for metadata. These files are the **source of truth** and can be:
   - Edited directly in any text editor
   - Placed under version control (Git, etc.)
   - Backed up using standard file backup procedures
   - Shared or transferred like any other text files

2. **SQLite Database**: Functions as an indexing layer that:
   - Facilitates efficient querying and search operations
   - Enables Claude to quickly traverse the knowledge graph
   - Maintains relationship information for faster link traversal
   - Is automatically rebuilt from Markdown files when needed

If you edit Markdown files directly outside the system, you'll need to run the `zk_rebuild_index` tool to update the database. The database itself can be deleted at any time - it will be regenerated from your Markdown files.

## Installation

```bash
# Clone the repository
git clone https://github.com/entanglr/zettelkasten-mcp.git
cd zettelkasten-mcp

# Create a virtual environment with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv add "mcp[cli]"

# Install the package in development mode
uv pip install -e .
```

## Configuration

Create a `.env` file in the project root by copying the example:

```bash
cp .env.example .env
```

Then edit the file to configure your connection parameters.

## Usage

### Starting the Server

```bash
python -m zettelkasten_mcp.main
```

Or with explicit configuration:

```bash
python -m zettelkasten_mcp.main --notes-dir ./data/notes --database-path ./data/db/zettelkasten.db
```

### Connecting to Claude Desktop

Add the following configuration to your Claude Desktop:

```json
{
  "mcpServers": {
    "zettelkasten": {
      "command": "/absolute/path/to/zettelkasten-mcp/.venv/bin/python",
      "args": [
        "-m",
        "zettelkasten_mcp.main"
      ],
      "env": {
        "ZETTELKASTEN_NOTES_DIR": "/absolute/path/to/zettelkasten-mcp/data/notes",
        "ZETTELKASTEN_DATABASE_PATH": "/absolute/path/to/zettelkasten-mcp/data/db/zettelkasten.db",
        "ZETTELKASTEN_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Available MCP Tools

All tools have been prefixed with `zk_` for better organization:

| Tool | Description |
|---|---|
| `zk_create_note` | Create a new note with a title, content, and optional tags |
| `zk_get_note` | Retrieve a specific note by ID or title |
| `zk_update_note` | Update an existing note's content or metadata |
| `zk_delete_note` | Delete a note |
| `zk_create_link` | Create links between notes |
| `zk_remove_link` | Remove links between notes |
| `zk_search_notes` | Search for notes by content, tags, or links |
| `zk_get_linked_notes` | Find notes linked to a specific note |
| `zk_get_all_tags` | List all tags in the system |
| `zk_find_similar_notes` | Find notes similar to a given note |
| `zk_find_central_notes` | Find notes with the most connections |
| `zk_find_orphaned_notes` | Find notes with no connections |
| `zk_list_notes_by_date` | List notes by creation/update date |
| `zk_rebuild_index` | Rebuild the database index from Markdown files |

## Project Structure

```
zettelkasten-mcp/
├── src/
│   └── zettelkasten_mcp/
│       ├── models/       # Data models
│       ├── storage/      # Storage layer
│       ├── services/     # Business logic
│       └── server/       # MCP server implementation
├── data/
│   ├── notes/            # Note storage (Markdown files)
│   └── db/               # Database for indexing
├── tests/                # Test suite
├── .env.example          # Environment variable template
└── README.md
```

## Important Notice

**⚠️ USE AT YOUR OWN RISK**: This software is experimental and provided as-is without warranty of any kind. While efforts have been made to ensure data integrity, it may contain bugs that could potentially lead to data loss or corruption. Always back up your notes regularly and use caution when testing with important information.

## Credit Where Credit's Due

This MCP server was crafted with the assistance of Claude, who helped organize the atomic thoughts of this project into a coherent knowledge graph. Much like a good Zettelkasten system, Claude connected the dots between ideas that might otherwise have remained isolated. Unlike Luhmann's paper-based system, however, Claude didn't require 90,000 index cards to be effective.

## License

MIT License
