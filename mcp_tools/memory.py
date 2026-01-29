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
        Retrieves memories from persistent storage. Call this proactively whenever you need context about:
        - Past conversations and events
        - User preferences and habits
        - Personal information about the user
        - Previous interactions or agreements

        **Important:** Do not assume information exists in your context window. Always retrieve memories when discussing anything from the past.

        Args:
            max_days_ago: Number of days to look back (default: 30 days)
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
        Saves important information to persistent memory for future conversations. **Always use this when:**
        - User shares personal information (preferences, background, goals)
        - Important facts about the user are established
        - Agreements, decisions, or preferences are made
        - Context that would be useful in future conversations

        **Guidelines:**
        - Write from neutral third-person perspective (refer to "user", not "you" or "I")
        - Keep summaries concise—one paragraph maximum
        - Focus on factual, actionable information
        - Include context that makes the memory standalone (don't assume future context)

        Args:
            content: A clear, summary statement of what to remember
        """
        mem = load_mem()

        # get highest id
        highest_id = 0
        for memory in mem:
            if memory.get("id") >= highest_id:
                highest_id = memory.get("id")
        highest_id += 1

        mem.append({
            "id": highest_id,
            "date": datetime.datetime.now().strftime("%c"),
            "content": content
        })

        return utils.result(write_mem(mem))

    @mcp.tool
    def edit_memory(id: int, content: str):
        """
        Updates an existing memory with new information. **Prerequisites:**
        - You must have retrieved the memory using `get_memories()` in the current conversation
        - The memory's ID must be visible in the current context
        - User is providing an update or correction to an existing memory

        **When to use:**
        - User clarifies or adds to existing stored information
        - Information previously stored needs updating
        - Correcting inaccurate or outdated memories

        **When NOT to use:**
        - If you cannot see the memory ID in the current context
        - If creating a new memory (use `store_memory` instead)

        Args:
            id: The memory ID (must be from `get_memories()` results)
            content: Updated content
        """
        mem = load_mem()
        for index, memory in enumerate(mem):
            if memory.get("id") == id:
                memory["content"] = content
                mem[index] = memory
                return utils.result(write_mem(mem))
        return utils.result(None, "could not find memory")

    @mcp.tool
    def delete_memory(id: int) -> dict:
        """
        Removes a memory from storage. **Use with caution!**

        **Prerequisites:**
        - The memory must be visible in current context (from `get_memories()` call)
        - User has explicitly requested deletion
        - You have confirmed the correct memory ID

        **Never delete without:**
        - Seeing the memory ID in current context
        - User's explicit confirmation (when appropriate)

        Args:
            id: The memory ID to delete
        """
        mem = load_mem()
        found_memory = False
        for index, memory in enumerate(mem):
            if found_memory:
                continue

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
            for word in memory.get("content").split():
                if found_memory:
                    continue

                if word.lower() in query.lower():
                    found_memories.append(memory)
                    found_memory = True

            if found_memory:
                continue

            if query.lower() in memory.get("date").lower():
                found_memories.append(memory)

        return utils.result(found_memories)
