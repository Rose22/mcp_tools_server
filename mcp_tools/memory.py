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

    # Track which memory IDs were retrieved in this conversation
    retrieved_memory_ids = set()

    @mcp.tool
    def get_memories(max_days_ago: int = 30):
        """
        Retrieves memories from persistent storage. Call this proactively whenever you need context about:
        - Past conversations and events
        - User preferences and habits
        - Personal information about the user
        - Previous interactions or agreements

        **Important:** Do not assume information exists in your context window. Always retrieve memories when discussing anything from the past.
        """
        mem = load_mem()
        mem_filtered = []
        for memory in mem:
            date_raw = datetime.datetime.strptime(memory.get("date"), "%c")
            date_past = date_raw - datetime.timedelta(days=max_days_ago)

            if date_raw >= date_past:
                mem_filtered.append(memory)
                # Track that this memory was retrieved
                retrieved_memory_ids.add(memory.get("id"))

        return utils.result(mem_filtered)

    @mcp.tool
    def search_within_memories(query: str) -> dict:
        """Searches memories for specific keywords. Returns matching memories with their IDs."""
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
                    # Track that this memory was retrieved
                    retrieved_memory_ids.add(memory.get("id"))

            if found_memory:
                continue

            if query.lower() in memory.get("date").lower():
                found_memories.append(memory)
                retrieved_memory_ids.add(memory.get("id"))

        return utils.result(found_memories)

    @mcp.tool
    def store_memory(content: str):
        """
        Saves important information to persistent memory for future conversations.

        Use when:
        - User shares personal information (preferences, background, goals)
        - Important facts are established
        - Agreements or preferences are made
        - Information needed in future conversations

        Write from neutral perspective. Keep to one paragraph. Use "user", not "you" or "I".
        """
        mem = load_mem()

        highest_id = max([memory.get("id", 0) for memory in mem], default=0)
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
        Edits an existing memory. ONLY works if you just retrieved this memory ID using get_memories() or search_within_memories() in this conversation.

        The memory ID must be visible in your recent tool results.
        """
        # ENFORCE: Memory must have been retrieved first
        if id not in retrieved_memory_ids:
            return utils.result(
                None, 
                f"ERROR: Cannot edit memory {id}. You must call get_memories() or search_within_memories() first to retrieve the memory you want to edit. This prevents accidental edits to memories you haven't reviewed."
            )

        mem = load_mem()
        for index, memory in enumerate(mem):
            if memory.get("id") == id:
                memory["content"] = content
                mem[index] = memory
                return utils.result(write_mem(mem))
        
        return utils.result(None, "Memory not found in storage.")

    @mcp.tool
    def delete_memory(id: int) -> dict:
        """
        Deletes a memory from storage. ONLY works if you just retrieved this memory ID using get_memories() or search_within_memories() in this conversation.

        The memory ID must be visible in your recent tool results. Use with caution!
        """
        # ENFORCE: Memory must have been retrieved first
        if id not in retrieved_memory_ids:
            return utils.result(
                None,
                f"ERROR: Cannot delete memory {id}. You must call get_memories() or search_within_memories() first to retrieve the memory you want to delete. This is a safety measure to prevent accidental deletions."
            )

        mem = load_mem()
        for index, memory in enumerate(mem):
            if memory.get("id") == id:
                del(mem[index])
                return utils.result(write_mem(mem))

        return utils.result(None, "Memory not found in storage.")
