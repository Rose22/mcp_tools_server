import utils
import os
import json
import datetime

memory_path = f"{utils.get_root_path()}/memory.json"

def register_mcp(mcp):
    def load_mem():
        if not os.path.exists(memory_path):
            with open(memory_path, "w") as f:
                f.write(json.dumps([]))

        try:
            with open(memory_path, "r") as f:
                data = json.load(f)
            return data
        except:
            return []

    def write_mem(mem):
        try:
            with open(memory_path, "w") as f:
                f.write(json.dumps(mem))
            return True
        except:
            return False

    @mcp.tool
    def get_memories(max_days_ago: int = 30):
        """
        Retrieves memories from your persistent memory storage. You ALWAYS need to use this tool when recalling something from the past. Do not rely on the current context window. Use even when user hasn't specified exactly what to recall. Assume information you don't have access to in the current context can be found within the memories.

        Information commonly stored within memories includes:
        - events from the past
        - personal preferences
        - information about user
        - information about you

        use max_days_ago to specify how many days into the past you want to remember.
        """

        mem = load_mem()
        mem_filtered = []
        for memory in mem:
            date_raw = datetime.datetime.strptime(memory.get("date"), "%c")
            date_past = date_raw - datetime.timedelta(days=max_days_ago)

            if date_raw >= date_past:
                mem_filtered.append(memory)

        return utils.result(mem_filtered)

    @mcp.tool
    def store_memory(content: str):
        """
        Stores a memory into your persistent memory storage. You ALWAYS need to use this tool when information must be remembered in future conversations with the user! Without using this tool, you will forget everything within the current context when user starts a new conversation.

        RULES:
        - Always refer to user as "user", never "you" or "i".
        - Summarize the memory before storing it. Keep it to one paragraph.
        - Prefer storing information given by user into memory whenever possible, including when user provides any new information about themselves.
        """
        mem = load_mem()

        mem.append({
            "id": len(mem)+1,
            "date": datetime.datetime.now().strftime("%c"),
            "content": content
        })

        return utils.result(write_mem(mem))

    @mcp.tool
    def delete_memory(id: int) -> dict:
        """Deletes a memory by id. To get the id, you first need to retrieve the memory using get_memories(). Use with caution!"""
        mem = load_mem()
        found_memory = False
        for index, memory in enumerate(mem):
            if memory.get("id") == id:
                del(mem[index])
                found_memory = True

        if not found_memory:
            return utils.result(None, "could not find memory with that ID. get all memories first, so you can get the memory's ID!")

        return utils.result(write_mem(mem))

    @mcp.tool
    def search_within_memories(query: str) -> dict:
        """Searches your persistent memory storage for a specific term. Use ONLY if user specifies the exact thing to recall."""
        mem = load_mem()
        found_memories = []
        for memory in mem:
            found_memory = False
            for word in memory.get("content"):
                if word in query:
                    found_memories.append(memory)
            if found_memory:
                continue

            if query.lower() in memory.get("date").lower():
                found_memories.append(memory)

        return utils.result(found_memories)
