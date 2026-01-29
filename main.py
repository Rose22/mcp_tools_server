#!/usr/bin/python

import os
import yaml
import fastmcp

import mcp_tools
import utils

config = utils.load_config()

if __name__ == "__main__":
    print("starting server..")
    mcp = fastmcp.FastMCP("tools")

    # register all the tools from throughout the project into the MCP server
    mcp_tools.register_mcp(mcp)

    try:
        if config.get("transport_type") == "stdio":
            mcp.run()
        else:
            mcp.run(transport=config.get("transport_type"), port=config.get("network_port"))
    except Exception as e:
        print(f"err: {e}")
