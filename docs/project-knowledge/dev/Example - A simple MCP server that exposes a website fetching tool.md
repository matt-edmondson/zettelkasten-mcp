================================================================
Start of Project Knowledge File
================================================================

Purpose:
--------
This file is designed to be consumed by AI systems for analysis, review,
or other automated processes. It solely serves the purpose of background
information and should NOT under any circumstances leak into the user's
interaction with the AI when actually USING the Zettelkasten MCP tools to
process, explore or synthesize user-supplied information.

Content:
--------

# Example: A simple MCP server that exposes a website fetching tool.

## Usage

Start the server using either stdio (default) or SSE transport:

```bash
# Using stdio transport (default)
uv run mcp-simple-tool

# Using SSE transport on custom port
uv run mcp-simple-tool --transport sse --port 8000
```

The server exposes a tool named "fetch" that accepts one required argument:

- `url`: The URL of the website to fetch

## Example

Using the MCP client, you can use the tool like this using the STDIO transport:

```python
import asyncio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def main():
    async with stdio_client(
        StdioServerParameters(command="uv", args=["run", "mcp-simple-tool"])
    ) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print(tools)

            # Call the fetch tool
            result = await session.call_tool("fetch", {"url": "https://example.com"})
            print(result)


asyncio.run(main())

```

================================================================
End of Project Knowledge File
================================================================
