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
                f.write(json.dumps(mem, indent=2))
            return True
        except:
            return False

    @mcp.tool
    def get_memories(start_date: str = None, end_date: str = None):
        """
        Retrieves memories from persistent memory storage. This is your ONLY source of past information - DO NOT assume you know anything from previous conversations unless you call this first.

        CRITICAL RULES:
        1. You MUST call this before ANY memory-related operations (edit, delete, search)
        2. Only memories returned by this call are "currently visible" and available for editing/deleting
        3. Call this at conversation start to see what you should remember

        Information stored includes:
        - Past events and conversations
        - User preferences and personal details
        - Important facts about the user
        - Your own configuration/state information

        Args:
            start_date (str, optional): Start date in "YYYY-MM-DD" format.
                If None, defaults to 30 days ago.
            end_date (str, optional): End date in "YYYY-MM-DD" format.
                If None, defaults to today.

        Examples:
            - get_memories("2024-01-01", "2024-12-31") → Only 2024 memories
            - get_memories("2024-06-01", None) → June 1, 2024 to today
            - get_memories(None, None) → Last 30 days
        """
        # Parse or default dates
        if end_date is None:
            end_date_obj = datetime.datetime.now()
        else:
            end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        
        if start_date is None:
            start_date_obj = end_date_obj - timedelta(days=30)
        else:
            start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        
        mem = load_mem()
        mem_filtered = []
        
        for memory in mem:
            memory_date = datetime.datetime.strptime(
                memory.get("last_modified", memory.get("date", "")), "%c"
            )
            if start_date_obj <= memory_date <= end_date_obj:
                mem_filtered.append(memory)
        
        return utils.result(mem_filtered)

    @mcp.tool
    def store_memory(content: str):
        """
        Stores a memory for future use. You MUST use this to retain information across conversations.

        STORAGE RULES:
        1. ALWAYS use when user provides new personal information
        2. ALWAYS use for important conversation outcomes
        3. ALWAYS use for user preferences/changes
        4. ALWAYS summarize in 1-2 concise paragraphs
        5. ALWAYS refer to user as "user", never "you" or "i"
        6. NEVER store temporary or trivial information
        
        IMPORTANT: Use edit_memory instead if modifying existing visible memories. 
        A memory is "visible" ONLY if returned by get_memories() in current context.
        """
        mem = load_mem()

        # Generate new ID
        highest_id = max([m.get("id", 0) for m in mem], default=0) + 1

        mem.append({
            "id": highest_id,
            "date": datetime.datetime.now().strftime("%c"),
            "content": content
        })

        success = write_mem(mem)
        return utils.result({"id": highest_id, "success": success})

    @mcp.tool
    def edit_memory(id: int, content: str):
        """
        MODIFIES AN EXISTING MEMORY. EXTREME RESTRICTIONS APPLY:
        
        YOU MAY ONLY EDIT MEMORIES THAT ARE CURRENTLY VISIBLE
        
        VISIBILITY REQUIREMENTS:
        1. You MUST have called get_memories() in this conversation
        2. The target memory MUST be in the returned results
        3. You MUST have the exact ID from get_memories() results
        
        REJECT EDITING IF:
        - You haven't called get_memories() recently
        - The ID isn't in get_memories() results
        - User mentions a memory but hasn't shown you the ID
        - You're guessing about which memory to edit
        
        PROPER USAGE:
        1. Call get_memories() to see available memories
        2. Verify target memory appears in results
        3. Extract exact ID from those results
        4. Only then call edit_memory()
        """
        mem = load_mem()
        
        # Check if memory exists
        for index, memory in enumerate(mem):
            if memory.get("id") == id:
                memory["content"] = content
                memory["last_modified"] = datetime.datetime.now().strftime("%c")
                mem[index] = memory
                success = write_mem(mem)
                return utils.result({"success": success, "id": id})
        
        return utils.result(
            {"success": False, "error": f"Memory ID {id} not found. You must call get_memories() first to see available memories and their IDs."}
        )

    @mcp.tool
    def delete_memory(id: int) -> dict:
        """
        PERMANENTLY DELETES A MEMORY. HIGHEST RESTRICTIONS APPLY
        
        YOU MAY ONLY DELETE MEMORIES THAT ARE CURRENTLY VISIBLE
        
        VISIBILITY REQUIREMENTS:
        1. You MUST have called get_memories() in this conversation
        2. The target memory MUST be in the returned results
        3. You MUST have the exact ID from get_memories() results
        4. User MUST explicitly request deletion of this specific ID
        
        REJECT DELETION IF:
        - You haven't called get_memories() recently
        - The ID isn't in get_memories() results
        - User asks to delete "that memory about X" without showing you the ID
        - You're making assumptions about which memory to delete
        
        PROPER USAGE:
        1. Call get_memories() to see available memories
        2. Verify target memory appears in results
        3. Extract exact ID from those results
        4. Confirm user wants THIS SPECIFIC ID deleted
        5. Only then call delete_memory()
        """
        mem = load_mem()
        
        # Check if memory exists
        for index, memory in enumerate(mem):
            if memory.get("id") == id:
                del mem[index]
                success = write_mem(mem)
                return utils.result({"success": success, "deleted_id": id})
        
        return utils.result(
            {"success": False, "error": f"Memory ID {id} not found. You must call get_memories() first to see available memories and their IDs."}
        )

    @mcp.tool
    def search_within_memories(query: str) -> dict:
        """
        Searches memory contents for specific terms. Returns matching memories with their IDs.
        
        USE WHEN:
        - User asks for something specific (e.g., "find memories about vacation")
        - You need to locate memories containing certain keywords
        - You want to filter memories by content
        
        NOTE: Results from this search become "visible" for editing/deleting.
        """
        mem = load_mem()
        found_memories = []
        query_lower = query.lower()
        
        for memory in mem:
            content = memory.get("content", "").lower()
            date_str = memory.get("date", "").lower()
            
            if (query_lower in content) or (query_lower in date_str):
                found_memories.append(memory)
        
        return utils.result(found_memories)
