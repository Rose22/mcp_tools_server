import utils
import os
import msgpack
import datetime
import re

memory_path = f"{utils.get_root_path()}/memory.mp"
cached_mem = None

def register_mcp(mcp):
    def load_mem():
        global cached_mem

        if cached_mem:
            return cached_mem

        if not os.path.exists(memory_path):
            with open(memory_path, "wb") as f:
                f.write(msgpack.dumps([]))

        try:
            with open(memory_path, "rb") as f:
                data = msgpack.load(f)
            cached_mem = data.copy()

            return data
        except:
            return []

    def write_mem(mem):
        try:
            with open(memory_path, "wb") as f:
                f.write(msgpack.dumps(mem))
            return True
        except:
            return False

    def _filter_memory_content(content):
        # replace common phrases in memory content

        replacement_map = {
            "today": "on this day",
            "yesterday": "the day before this day",
            "now": "at the time",
            "tomorrow": "the day after this day",
            "last week": "a week before this day",
            "next week": "a week after this day"
        }
        
        for orig, replacement in replacement_map.items():
            # case insensitive replace
            content = re.sub(orig, replacement, content, flags=re.IGNORECASE)

        return content

    @mcp.tool
    def get_memories(from_days_ago: int = 30, to_days_ago: int = 0):
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

        RETRIEVAL LOGIC:
        1. ALL persistent memories are ALWAYS included (regardless of how far back you recall)
        2. Non-persistent memories are filtered by date range

        Args:
            from_days_ago (int, optional): Number of days to remember from, relative to today
                if None, defaults to 30 days ago.
            to_days_ago (int, optional): Number of days to remember up to, relative to today
                if None, defaults to today.

        Examples:
            - get_memories(30, 0) → Last 30 days
            - get_memories(30, 1) → Last 30 days up until yesterday
            - get_memories(30, 7) → Last 30 days up until 7 days before today
            - get_memories(1, 1) → Only yesterday
            - get_memories(365, 0) → A whole year up until today
            - get_memories(730, 365) → Last year (730 days = 2 years ago, 365 days = 1 year ago)
            - get_memories(7, 7) → Exactly 7 days ago, without any other days included
        """
        mem = load_mem()
        mem_filtered = []

        max_date_in_past = datetime.datetime.now() - datetime.timedelta(days=from_days_ago)
        min_date_in_past = datetime.datetime.now() - datetime.timedelta(days=to_days_ago)
        
        for memory in mem:
            if memory.get("persistent", False):
                # include persistent memories if no date range was set
                if from_days_ago == 30 and not to_days_ago:
                    mem_filtered.append(memory)
                continue

            # filter non-persistent memories by date
            memory_date = datetime.datetime.fromisoformat(memory.get("date"))
            if max_date_in_past <= memory_date <= min_date_in_past:
                mem_filtered.append(memory)
        
        return utils.result(mem_filtered)

    @mcp.tool
    def store_memory(content: str, persistent: bool = False):
        """
        Stores a memory for future use. You MUST use this to retain information across conversations.

        CRITICAL STORAGE RULES:
        1. ALWAYS use when user provides new personal information
        2. ALWAYS use for important conversation outcomes
        3. ALWAYS use for user preferences/changes
        4. ALWAYS summarize in 1-2 concise paragraphs
        5. ALWAYS refer to user as "user", never "you" or "i"

        IMPORTANT: Use edit_memory instead if modifying existing visible memories.
        A memory is "visible" ONLY if returned by get_memories() in current context.

        PERSISTENT MEMORIES:
        • persistent=False (default): Memory is date-based and will only appear in get_memories()
          when its date falls within the requested date range.
        • persistent=True: Memory is ALWAYS included in get_memories() results, regardless of date range.
          Use this for evergreen information that should never be forgotten.

        When to use persistent=True:
        • User's core identity details (name, occupation, family)
        • Permanent preferences (allergies, dietary restrictions)
        • Long-term goals or life circumstances
        • System configuration that never changes

        When to use persistent=False:
        • Recent events or conversations
        • Temporary preferences or moods
        • Time-sensitive information
        • Context that might become outdated

        Examples:
        - store_memory("User's name is Rose and she has blue eyes", persistent=True)
        - store_memory("User mentioned feeling tired today and wants to reschedule", persistent=False)
        """
        mem = load_mem()
        content = _filter_memory_content(content)

        # Generate new ID
        highest_id = max([m.get("id", 0) for m in mem], default=0) + 1

        new_mem = {
            "id": highest_id,
            "date": datetime.datetime.now().isoformat(),
            "content": content
        }

        if persistent:
            new_mem["persistent"] = True

        mem.append(new_mem)

        success = write_mem(mem)
        return utils.result({"id": highest_id, "success": success})

    @mcp.tool
    def edit_memory(id: int, content: str, persistent: bool = None):
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

        Do not modify persistent flag unless explicitely requested.
        """
        mem = load_mem()
        content = _filter_memory_content(content)
        
        # Check if memory exists
        for index, memory in enumerate(mem):
            if memory.get("id") == id:
                memory["content"] = content
                mem[index] = memory
                if persistent != None:
                    mem["persistent"] = persistent

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
