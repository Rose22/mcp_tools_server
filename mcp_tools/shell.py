import utils

def register_mcp(mcp):
    @mcp.tool()
    def shell_exec(cmd: str) -> dict:
        return utils.sh_exec(cmd)
