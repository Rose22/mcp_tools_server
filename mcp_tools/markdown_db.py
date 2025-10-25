import os
import shutil
import utils
import datetime

DATA_PATH = utils.get_data_path()

def filter_data_path(type_name_plural: str, category: str, name: str):
    name = utils.strip_filename(name).replace(".md", "")
    category = utils.strip_filename(category)

    if type_name_plural == "trash":
        raise Exception("trash is not a data type!")

    if not os.path.exists(os.path.join(DATA_PATH, type_name_plural, category)):
        raise Exception("invalid category "+os.path.join(DATA_PATH, type_name_plural, category))

    if not os.path.exists(os.path.join(DATA_PATH, type_name_plural, category, name+".md")):
        raise Exception("entry does not exist")

    return (name, category)

def dummy_func():
    # does literally nothing
    pass

def register_mcp(mcp):
    # this is a simple flat-file markdown database system
    # that's flexible and can easily be extended with additional types of data

    mcp.tool(dummy_func, name="describe_database_system", description=f"""
        when the user wants to know, tell the user this:

        the database system is a flat-file database within {DATA_PATH}. every entry is a human-readable markdown file.
        user can easily export and backup the database by simply copying that folder!
    """)

    def add_data_entry(type_name_plural: str, category: str, name: str, content: str) -> dict:
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

        entry_path = os.path.join(data_type_path, category, name+".md")

        if os.path.exists(entry_path):
            return {"error": f"{name} already exists! you should read it and then edit it instead."}

        with open(entry_path, 'w') as f:
            f.write(content)

        return utils.result(True)

    def get_data_categories(type_name_plural: str) -> dict:
        """gets all categories (folders) within a data type"""
        return {"categories": [category for category in os.listdir(os.path.join(DATA_PATH, type_name_plural)) if os.path.isdir(os.path.join(DATA_PATH, type_name_plural, category))]}

    def get_data_entries(type_name_plural: str, category: str) -> dict:
        """gets all entries within a category of a data type"""

        try:
            if not os.path.exists(os.path.join(DATA_PATH, type_name_plural, category)):
                return utils.result(None, "no such category!")

            return {type_name_plural: [name.replace(".md", "") for name in os.listdir(os.path.join(DATA_PATH, type_name_plural, category))]}
        except Exception as e:
            return utils.result(None, e)

    def rename_data_category(type_name_plural: str, category: str, category_new: str) -> dict:
        """rename a category"""
        if not os.path.exists(os.path.join(DATA_PATH, type_name_plural, category)):
            return utils.result(None, "no such category!")

        try:
            shutil.move(os.path.join(DATA_PATH, type_name_plural, category), os.path.join(DATA_PATH, type_name_plural, category_new))
        except Exception as e:
            return utils.result(None, e)

        return utils.result(True)
    
    def delete_data_category(type_name_plural: str, category: str) -> dict:
        if not os.path.exists(os.path.join(DATA_PATH, type_name_plural, category)):
            return utils.result(None, "no such category!")

        try:
            shutil.rmtree(os.path.join(DATA_PATH, type_name_plural, category))
        except Exception as e:
            return utils.result(e)

        return utils.result(True)

    def get_data_entry(type_name_plural: str, category: str, name: str) -> dict:
        """gets the content of a data entry"""

        utils.console_log(f"reading entry {name} of type {type_name_plural}")

        name, category = filter_data_path(type_name_plural, category, name)
        return utils.result(
            open(
                os.path.join(DATA_PATH, type_name_plural, category, name+".md"),
                'r'
            )
            .read()
        )
    
    def edit_data_entry(type_name_plural: str, category: str, name: str, content: str) -> dict:
        """edits a data entry"""

        utils.console_log(f"editing entry {name} of type {type_name_plural}")

        name, category = filter_data_path(type_name_plural, category, name)

        with open(os.path.join(DATA_PATH, type_name_plural, category, name+".md"), 'w') as f:
            f.write(content)
            f.write("\n")
        
        return utils.result(True)
    
    def delete_data_entry(type_name_plural: str, category: str, name: str) -> dict: 
        """deletes a data entry by name"""

        utils.console_log(f"deleting {name} of type {type_name_plural}")

        name, category = filter_data_path(type_name_plural, category, name)
        os.remove(os.path.join(DATA_PATH, type_name_plural, category, name+".md"))
        return utils.result(True)

    def search_in_data(type_name_plural: str, query: str) -> dict:
        """searches a given data type for a given query across all its categories"""

        utils.console_log(f"searching {type_name_plural} for {query}")

        results = []
        for category in os.listdir(os.path.join(DATA_PATH, type_name_plural)):
            for entry_filename in os.listdir(os.path.join(DATA_PATH, type_name_plural, category)):
                entry_name = os.path.splitext(entry_filename)[0]
                entry_content = open(os.path.join(DATA_PATH, type_name_plural, category, entry_filename)).read()

                if query in entry_name or query in entry_content:
                    results.append({"category": category, "name": entry_name, "content": entry_content})

        return utils.result(results)

    @mcp.tool()
    def search_entire_database(query: str, search_within_content: bool) -> dict:
        """
        searches across all data types and categories for a specified query.
        if search_within_content is true, it will search inside every file. otherwise it will only search by name.
        searching by name is faster!
        """

        results = []

        for type_name_plural in os.listdir(DATA_PATH):
            for category in os.listdir(os.path.join(DATA_PATH, type_name_plural)):
                for filename in os.listdir(os.path.join(DATA_PATH, type_name_plural, category)):
                    if search_within_content:
                        try:
                            content = open(os.path.join(DATA_PATH, type_name_plural, category, filename), 'r').read()
                            if query in content:
                                results.append({
                                    "type": type_name_plural,
                                    "category": category,
                                    "name": filename,
                                    "content": content
                                })
                        except Exception as e:
                            results.append({
                                "type": type_name_plural,
                                "category": category,
                                "name": filename,
                                "error": e
                            })
                    else:
                        if query in filename:
                            try:
                                content = open(os.path.join(DATA_PATH, type_name_plural, category, filename), 'r').read()
                            except:
                                content = None

                            results.append({
                                "type": type_name_plural,
                                "category": category,
                                "name": filename,
                                "content": content
                            })

        return utils.result(results)

    # ------
    # now for the secret sauce!
    # -----------
    def add_data_type(mcp, type_name_plural, type_name_singular, additional_instructions=""):
        """
        this dynamically creates MCP tools based on a given data type.
        it does this by defining a wrapper function and passing it
        on to the MCP server with a dynamic name and docstring
        using the mcp.tool() keyword arguments
        """

        # create the folder for this data type
        if not os.path.exists(os.path.join(DATA_PATH, type_name_plural)):
            os.mkdir(os.path.join(DATA_PATH, type_name_plural))

        # create wrapper function for: get categories
        def dyn_func1(_type=type_name_plural) -> dict:
            return get_data_categories(_type)
        # then register it to the mcp server
        mcp.tool(
            dyn_func1,
            name=f"db_get_{type_name_plural}",
            # sheesh this one's particularly tough for an LLM
            description=f"""returns all {type_name_plural} in the database. always call this tool when user explicitly asks for their {type_name_plural} or wants to see what's stored.""",
            exclude_args=["_type"]
        )

        # repeat for all other data functions

        # add data entry
        def dyn_func2(category: str, name: str, content: str, _type=type_name_plural) -> dict:
            return add_data_entry(_type, category, name, content)
        mcp.tool(
            dyn_func2,
            name=f"db_create_{type_name_singular}",
            description=f"""
creates a {type_name_singular} and adds it to the {type_name_singular} storage.
please use markdown format!
{additional_instructions}
        """,
            exclude_args=["_type"]
        )

        # get entries
        def dyn_func3(category: str, _type=type_name_plural) -> dict:
            return get_data_entries(_type, category)
        mcp.tool(
            dyn_func3,
            name=f"db_get_{type_name_plural}_in_category",
            description=f"""returns all {type_name_plural} within a specified category""",
            exclude_args=["_type"]
        )

        # rename category
        def dyn_func4(category: str, category_new: str, _type=type_name_plural) -> dict:
            return rename_data_category(_type, category, category_new)
        mcp.tool(
            dyn_func4,
            name=f"db_rename_{type_name_singular}_category",
            description=f"""renames a {type_name_singular} category""",
            exclude_args=["_type"]
        )

        # delete category
        def dyn_func5(category: str, _type=type_name_plural) -> dict:
            return delete_data_category(_type, category)
        mcp.tool(
            dyn_func5,
            name=f"db_delete_{type_name_singular}_category",
            description=f"""deletes a {type_name_singular} category""",
            exclude_args=["_type"]
        )

        # get singular entry
        def dyn_func6(category: str, name: str, _type=type_name_plural) -> dict:
            return get_data_entry(_type, category, name)
        mcp.tool(
            dyn_func6,
            name=f"db_read_{type_name_singular}",
            description=f"reads a {type_name_singular} that's already in storage",
            exclude_args=["_type"]
        )

        # edit entry
        def dyn_func7(category: str, name: str, content: str, _type=type_name_plural) -> dict:
            return edit_data_entry(_type, category, name, content)
        mcp.tool(
            dyn_func7,
            name=f"db_edit_{type_name_singular}",
            description=f"edits an existing {type_name_singular}. please use markdown format! {additional_instructions}",
            exclude_args=["_type"]
        )

        # delete entry
        def dyn_func8(category: str, name: str, _type=type_name_plural) -> dict:
            return delete_data_entry(_type, category, name)
        mcp.tool(
            dyn_func8,
            name=f"db_delete_{type_name_singular}",
            description=f"deletes a {type_name_singular} by name",
            exclude_args=["_type"]
        )
        
        # search for entry
        def dyn_func9(query: str, _type=type_name_plural) -> dict:
            return search_in_data(_type, query)
        mcp.tool(
            dyn_func9,
            name=f"db_search_{type_name_plural}",
            description=f"searches within the name and contents of all stored {type_name_plural} for your given query",
            exclude_args=["_type"]
        )

    @mcp.tool()
    def get_data_types():
        """lists all available data entry types"""
        return utils.result([
            name for name
            in os.listdir(DATA_PATH)
            if name not in ("trash")
        ])

    # ------------
    # add data types here!
    # ----------------------
    add_data_type(mcp, "notes", "note")
    add_data_type(mcp, "tasks", "task")
    add_data_type(mcp, "ideas", "idea")
    add_data_type(mcp, "checklists", "checklist")
    add_data_type(mcp, "goals", "goal", additional_instructions="use only for longterm goals")
    add_data_type(mcp, "events", "event", additional_instructions="always add a date and time")
    add_data_type(mcp, "contacts", "contact")
    add_data_type(mcp, "conversation_logs", "conversation_log")
    add_data_type(mcp, "bookmarks", "bookmark", additional_instructions="always include the original URL and a description of the bookmark")
    add_data_type(mcp, "recipes", "recipe", additional_instructions="format it like a traditional recipe, with a list of ingredients at the top, a handy shopping list, and step by step instructions")
