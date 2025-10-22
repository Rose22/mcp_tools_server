import os
import shutil
import utils

def register_mcp(mcp):
    @mcp.tool()
    def list_dir(path: str, query: str = None) -> list:
        """
        list the files in a directory.
        you can optionally supply a query to search based on filename.
        """
        try:
            files = os.listdir(os.path.expanduser(path))
        except Exception as e:
            return [f"error: {e}"]

        utils.console_log(f"listing dir {path}")
        if query:
            utils.console_log(f"using query {query}")

        result = []
        for file_name in files:
            if query:
                if query not in file_name:
                    continue

            file_path = os.path.expanduser(f"{path}/{file_name}")
            file_ext = os.path.splitext(file_name)[-1]
            file_type = "file" if os.path.isfile(file_path) else "directory"

            data = {
                "path": file_path,
                "type": file_type,
                "size": utils.sizeof_format(int(
                    # depends on if it's a file or folder'
                    utils.get_dir_size(file_path) if file_type == "directory" else os.path.getsize(file_path)
                ))
            }

            result.append(data)

        utils.console_log("done")

        return result

    #@mcp.tool()
    #def list_dir_recursive(path: str) -> list:
    #    """list the files in a directory recursively"""
    #
    #    utils.console_log(f"listing {path} recursively")
    #    result = []
    #    path = os.path.expanduser(path)
    #    for root, dirs, files in os.walk(path):
    #        for file in files:
    #            result.append(os.path.join(root, file))
    #        for dir in dirs:
    #            result.append(os.path.join(root, dir))
    #    return result

    @mcp.tool()
    def create_dir(path: str) -> list:
        """creates a directory. takes an absolute path, will automatically create any directories in the path to it (uses mkdir -p internally)"""

        return utils.sh_exec(f"mkdir -p {path}")

    @mcp.tool()
    def create_file(path: str, body: str) -> str:
        """create a file with your specified content"""
        if os.path.exists(path):
            return "error: file already exists!"

        open(path, 'w').write(body)
        return "success"

    @mcp.tool()
    def write_file(path: str, body: str) -> str:
        """write to file. always makes a backup for safety."""

        utils.console_log(f"writing to file {path}:\n---\n{body}\n---\n")
        # first, make a backup
        if os.path.exists(path):
            try:
                timestamp = datetime.datetime.now().strftime("%d%M%Y%H%M%S")
                shutil.copy(path, f"{path}.{timestamp}.old")
            except Exception as e:
                return f"error while backing up file: {e}"

        try:
            open(path, 'w').write(body)
            return "success"
        except Exception as e:
            return f"error: {e} "

    @mcp.tool()
    def append_to_file(path: str, body: str) -> str:
        """append to file. always makes a backup for safety."""
        if not os.path.exists(path):
            return f"error: file did not exist"

        utils.console_log(f"appending to file {path}:\n---\n{body}\n---\n")

        # first, make a backup
        try:
            timestamp = datetime.datetime.now().strftime("%d%M%Y%H%M%S")
            shutil.copy(path, f"{path}.{timestamp}.old")
        except Exception as e:
            return f"error while backing up file: {e}"

        try:
            with open(path, 'a') as f:
                f.write("\n"+body)
            return "success"
        except Exception as e:
            return f"error: {e}"

    @mcp.tool()
    def move_file(src_path: str, target_path: str) -> str:
        """moves a file from src_path to target_path. can also be used to rename files. always use absolute paths for both src_path and target_path!"""

        utils.console_log(f"mv {src_path} -> {target_path}")

        try:
            shutil.move(src_path, target_path)
            return "success"
        except Exception as e:
            return f"error: {e}"

    @mcp.tool()
    def move_multiple_files(list_of_moves: list) -> list:
        """
        moves multiple files from source to destination.
        list_of_moves is structured as such:
        [
            {
                source_path: "source path",
                target_path: "target path"
            },
            {
                source_path: "source path",
                target_path: "target path"
            },
            {
                source_path: "source path",
                target_path: "target path"
            },
        ]

        and so on
        """

        result = []
        for file_data in list_of_moves:
            result.append([
                    file_data['source_path'],
                    move_file(file_data['source_path'], file_data['target_path'])
            ])

        return result

    @mcp.tool()
    def delete_file(path: str) -> str:
        """moves a file to trash. never outright deletes, for safety's sake"""

        trash_path = os.path.expanduser("~/.trash")

        utils.console_log(f"trashing file {path}")

        try:
            shutil.move(path, trash_path+"/"+os.path.basename(path))
            return "success"
        except Exception as e:
            return f"error: {e}"

    @mcp.tool()
    def empty_trash() -> str:
        """empties the trash folder. use with caution!"""
        trash_path = os.path.expanduser("~/.trash")

        for file in os.listdir(trash_path):
            if os.path.isdir(file):
                shutil.rmtree(f"{trash_path}/{file}")
            else:
                os.remove(f"{trash_path}/{file}")

        return "success"
