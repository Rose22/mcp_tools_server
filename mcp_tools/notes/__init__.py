import os
import utils

DATA_PATH = utils.get_data_path()

def filter_data_path(type_name_plural: str, category: str, name: str):
    name = utils.strip_filename(name).replace(".md", "")
    category = utils.strip_filename(category)

    if type_name_plural == "trash":
        raise Exception("trash is not a data type!")

    if not os.path.exists(os.path.join(DATA_PATH, type_name_plural, category)):
        raise Exception("invalid category")

    if not os.path.exists(os.path.join(DATA_PATH, type_name_plural, category, name+".md")):
        raise Exception("note does not exist")

    return (name, category)

def register_mcp(mcp):
    # this is a simple flat-file markdown database system
    # that's flexible and can easily be extended with additional types of data

    def add_data_entry(type_name_plural: str, category: str, name: str, content: str):
        """creates an entry in the data folder. designed to be flexible and usable for things like notes, bookmarks, tasks, and so on!"""
        # not callable by the LLM, this is an internal function used by all the other types of data entry functions.

        utils.console_log(f"creating {name} of type {type_name_plural} in {category}")

        data_type_path = os.path.join(DATA_PATH, type_name_plural)

        # strip the path names of any shenanigans
        name = utils.strip_filename(name)
        category = utils.strip_filename(category)

        if not os.path.exists(data_type_path):
            os.mkdir(data_type_path)

        if not os.path.exists(os.path.join(data_type_path, category)):
            os.mkdir(os.path.join(data_type_path, category))

        note_path = os.path.join(data_type_path, category, name+".md")

        if os.path.exists(note_path):
            return f"{name} already exists! you should read it and then edit it instead."

        with open(note_path, 'w') as f:
            f.write(content)
            f.write("\n")

        return "success"

    def get_data_categories(type_name_plural: str):
        """gets all categories (folders) within a data type"""
        return [category for category in os.listdir(os.path.join(DATA_PATH, type_name_plural)) if os.path.isdir(os.path.join(DATA_PATH, type_name_plural, category))]

    def get_data_entries(type_name_plural: str, category: str):
        """gets all entries within a category of a data type"""

        try:
            if not os.path.exists(os.path.join(DATA_PATH, type_name_plural, category)):
                return "no such category!"

            return [name.replace(".md", "") for name in os.listdir(os.path.join(DATA_PATH, type_name_plural, category))]
        except Exception as e:
            return [f"error: {e}"]

    def get_data_entry(type_name_plural: str, category: str, name: str):
        """gets the content of a data entry"""

        utils.console_log(f"reading entry {name} of type {type_name_plural}")

        name, category = filter_data_path(type_name_plural, category, name)
        return open(os.path.join(DATA_PATH, type_name_plural, category, name+".md"), 'r').read()
    
    def edit_data_entry(type_name_plural: str, category: str, name: str, content: str):
        """edits a data entry"""

        utils.console_log(f"editing entry {name} of type {type_name_plural}")

        name, category = filter_data_path(type_name_plural, category, name)

        with open(os.path.join(DATA_PATH, type_name_plural, category, name+".md"), 'w') as f:
            f.write(body)
            f.write("\n")
        
        return "success"
    
    def delete_data_entry(type_name_plural: str, category: str, name: str): 
        """deletes a data entry by name"""

        utils.console_log(f"deleting {name} of type {type_name_plural}")

        name, category = filter_data_path(type_name_plural, category, name)
        os.remove(os.path.join(DATA_PATH, type_name_plural, category, name+".md"))
        return "success"

    def search_in_data(type_name_plural: str, query: str):
        """searches a given data type for a given query across all its categories"""

        utils.console_log(f"searching {type_name_plural} for {query}")

        results = []
        for category in os.listdir(os.path.join(DATA_PATH, type_name_plural)):
            for entry_filename in os.listdir(os.path.join(DATA_PATH, type_name_plural, category)):
                entry_name = os.path.splitext(entry_filename)[0]
                entry_content = open(os.path.join(DATA_PATH, type_name_plural, category, note_filename)).read()

                if query in entry_name or query in entry_content:
                    results.append({"category": category, "name": entry_name, "content": entry_content})

        return results

    # ------
    # now for the secret sauce!
    # -----------
    def add_data_type(mcp, type_name_plural, type_name_singular, additional_instructions=None):
        # create a function that's an alias to the data entry function
        # and then overwrite the name and docstring passed to the LLM
        # using mcp.tool()'s keyword arguments

        # get categories
        def dyn_func1(_type=type_name_plural):
            return get_data_categories(_type)
        # then register it to the mcp server
        mcp.tool(
            dyn_func1,
            name=f"get_{type_name_plural}",
            description=f"returns all {type_name_plural}",
            exclude_args=["_type"]
        )

        # repeat for all other data functions

        # add data entry
        def dyn_func2(category: str, name: str, content: str, _type=type_name_plural):
            return add_data_entry(_type, category, name, content)
        mcp.tool(
            dyn_func2,
            name=f"create_{type_name_singular}",
            description=f"""
creates a {type_name_singular} and adds it to the {type_name_singular} storage.
please use markdown format!
{additional_instructions}
        """,
            exclude_args=["_type"]
        )

        # get entries
        def dyn_func3(category: str, _type=type_name_plural):
            return get_data_entries(_type, category)
        mcp.tool(
            dyn_func3,
            name=f"get_{type_name_plural}_in_category",
            description=f"""returns all {type_name_plural} within a specified category""",
            exclude_args=["_type"]
        )

        # get singular entry
        def dyn_func4(category: str, name: str, _type=type_name_plural):
            return get_data_entry(category, name, _type)
        mcp.tool(
            dyn_func4,
            name=f"read_{type_name_singular}",
            description=f"reads a {type_name_singular} that's already in storage",
            exclude_args=["_type"]
        )

        # edit entry
        def dyn_func5(category: str, name: str, content: str, _type=type_name_plural):
            return edit_data_entry(_type, category, name, content)
        mcp.tool(
            dyn_func5,
            name=f"edit_{type_name_singular}",
            description=f"edits an existing {type_name_singular}. please use markdown format!",
            exclude_args=["_type"]
        )

        # delete entry
        def dyn_func6(category: str, name: str, _type=type_name_plural):
            return delete_data_entry(_type, category, name)
        mcp.tool(
            dyn_func6,
            name=f"delete_{type_name_singular}",
            description=f"deletes a {type_name_singular} by name",
            exclude_args=["_type"]
        )
        
        # search for entry
        def dyn_func7(query: str, _type=type_name_plural):
            return search_in_data(_type, query)
        mcp.tool(
            dyn_func7,
            name=f"search_{type_name_plural}",
            description=f"searches within the name and contents of all stored {type_name_plural} for your given query",
            exclude_args=["_type"]
        )

    @mcp.tool()
    def get_data_types():
        """lists all available data entry types"""
        return [name for name in os.listdir(DATA_PATH) if name not in ("trash")]

    # ------------
    # add data types here!
    # ----------------------
    add_data_type(mcp, "notes", "note")
    add_data_type(mcp, "tasks", "task")
    add_data_type(mcp, "events", "event")
    add_data_type(mcp, "contacts", "contact")
    add_data_type(mcp, "bookmarks", "bookmark", additional_instructions="add a description of the bookmark!")
