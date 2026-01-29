import utils

def register_mcp(mcp):
    @mcp.tool()
    def shell_exec(cmd: str) -> dict:
        """executes cmd in a shell. use with caution!"""
        return utils.sh_exec(cmd)
