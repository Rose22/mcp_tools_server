import utils
import importlib

config = utils.load_config()

def register_mcp(mcp):
    """
    register the mcp tools from throughout the project into the MCP server
    """

    # dynamically load modules based on which ones are enabled
    for module in config.get("enabled_modules"):
        try:
            print(f"loading module {module}..")
            globals()[module] = importlib.import_module(f"mcp_tools.{module}")
            globals()[module] = globals()[module].register_mcp(mcp)
        except Exception as e:
            print(f"could not load module {module}: {e}")
    print("modules loaded")
