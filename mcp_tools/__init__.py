from mcp_tools import system, files, reader, networking, notes

def register_mcp(mcp):
    """
    register the mcp tools from throughout the project into the MCP server
    """
    system.register_mcp(mcp)
    files.register_mcp(mcp)
    reader.register_mcp(mcp)
    networking.register_mcp(mcp)
    notes.register_mcp(mcp)
