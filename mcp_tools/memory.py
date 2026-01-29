import utils

def register_mcp(mcp):
    @mcp.tool
    def get_memories():
        """retrieves your memories. ALWAYS call this at the start of a conversation!"""
        return utils.result(True)

    @mcp.tool
    def store_memory(title: str, description: str):
        """stores a memory. ALWAYS call this when you need to remember something later!"""
        return utils.result(True)
