from mcp_tools import system, files, reader, networking, markdown_db, websearch

def register_mcp(mcp):
    """
    register the mcp tools from throughout the project into the MCP server
    """
    system.register_mcp(mcp)
    files.register_mcp(mcp)
    reader.register_mcp(mcp)
    networking.register_mcp(mcp)
    markdown_db.register_mcp(mcp)
    websearch.register_mcp(mcp)
