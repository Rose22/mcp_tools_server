import utils
import importlib
# from mcp_tools import system, files, reader, networking, markdown_db, websearch

config = utils.load_config()

def register_mcp(mcp):
    """
    register the mcp tools from throughout the project into the MCP server
    """
    glob = globals()
    for module in config.get("enabled_modules"):
        try:
            print(f"loading module {module}..")
            globals()[module] = importlib.import_module(f"mcp_tools.{module}")
            glob.get(module).register_mcp(mcp)
        except Exception as e:
            print(f"could not load module {module}: {e}")
    print("modules loaded")
