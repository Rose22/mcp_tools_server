import os
import utils

DATA_PATH = utils.get_data_path()
NOTES_PATH = f"{DATA_PATH}/notes"

def filter_note_path(name, category):
    name = utils.strip_filename(name).replace(".md", "")
    category = utils.strip_filename(category)

    if not os.path.exists(f"{NOTES_PATH}/{category}"):
        raise Exception("invalid category")

    if not os.path.exists(f"{NOTES_PATH}/{category}/{name}.md"):
        raise Exception("note does not exist")

    return (name, category)

def register_mcp(mcp):
    if not os.path.exists(NOTES_PATH):
        os.mkdir(NOTES_PATH)

    @mcp.tool()
    def create_note(name: str, category: str, body: str) -> str:
        """
        creates a note and adds it to the note storage.
        please use markdown format!
        """

        utils.console_log(f"creating note {name}")

        # strip the path names of any shenanigans
        name = utils.strip_filename(name)
        category = utils.strip_filename(category)

        if not os.path.exists(f"{NOTES_PATH}/{category}"):
            os.mkdir(f"{NOTES_PATH}/{category}")

        note_filename = f"{NOTES_PATH}/{category}/{name}.md"

        if os.path.exists(note_filename):
            return "note already exists! you should read it and then use edit_note() instead."

        with open(note_filename, 'w') as f:
            f.write(body)
            f.write("\n")

        return "success"

    @mcp.tool()
    def read_note(name: str, category: str) -> str: 
        """
        reads a note that's already in storage
        """

        utils.console_log(f"reading note {name}")

        name, category = filter_note_path(name, category)
        return open(f"{NOTES_PATH}/{category}/{name}.md", 'r').read()

    @mcp.tool()
    def edit_note(name: str, category: str, body: str) -> str:
        """
        edits an existing note.
        please use markdown format!
        """

        utils.console_log(f"editing note {name}")

        name, category = filter_note_path(name, category)

        with open(f"{NOTES_PATH}/{category}/{name}.md", 'w') as f:
            f.write(body)
            f.write("\n")
        
        return "success"

    @mcp.tool()
    def delete_note(name: str, category: str) -> str:
        """delete a note"""

        utils.console_log(f"deleting note {name}")

        name, category = filter_note_path(name, category)
        os.remove(f"{NOTES_PATH}/{category}/{name}.md")
        return "success"

    @mcp.tool()
    def search_notes(query: str) -> list:
        """searches within the name and contents of all stored notes for your given query"""

        utils.console_log(f"searching notes for {query}")

        results = []
        for category in os.listdir(NOTES_PATH):
            for note_filename in os.listdir(f"{NOTES_PATH}/{category}"):
                note_name = os.path.splitext(note_filename)[0]
                note_body = open(f"{NOTES_PATH}/{category}/{note_filename}").read()

                if query in note_name or query in note_body:
                    results.append({"category": category, "name": note_name, "content": note_body})

        return results


