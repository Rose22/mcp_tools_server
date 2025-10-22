#!/usr/bin/python

import fastmcp
import mcp_tools

if __name__ == "__main__":
    print("starting server..")
    mcp = fastmcp.FastMCP("tools")

    # register all the tools from throughout the project into the MCP server
    mcp_tools.register_mcp(mcp)

    try:
        #mcp.run(transport="streamable-http", port=12435)
        #mcp.run(transport="sse", port=12435)
        #mcp.run(transport="http", port=12435)
        mcp.run()
    except Exception as e:
        print(f"err: {e}")
