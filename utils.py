import subprocess
import os

def get_root_path():
    return os.path.dirname(os.path.abspath(__file__))

def get_data_path():
    path = os.path.join(get_root_path(), "data")
    if not os.path.exists(path):
        os.mkdir(path)

    return path

def result(obj, error=None):
    output = {
        "data": obj,
        "status": "success" if not error else "error"
    }

    if error:
        output["error"] = error

    return output

def strip_filename(filename):
    return filename.strip().lower().replace(" ", "_")

def console_log(text):
    print(f"\033[1;34m[MCP] {text}\033[0m")

def sh_exec(cmd):
    """executes a command and returns the output as a string"""

    console_log(f"sh: {cmd}")
    try:
        proc = subprocess.run(cmd.split(" "), capture_output=True, text=True)
    except Exception as e:
        return {"error": f"error while executing command '{cmd}': {e}"}

    cmd_result = proc.stdout.splitlines()
    if len(cmd_result) == 0:
        # just return the output as a string if it was only one line
        cmd_result = cmd_result[0]

    if cmd_result:
        return cmd_result
    elif len(proc.stderr) > 0:
        cmd_result = proc.stderr.splitlines()
    else:
        return f"unknown error!: {cmd_result}"

def sh_exec_result(cmd) -> dict:
    return result({
        "cmd": cmd,
        "output": sh_exec(cmd)
    })

def sizeof_format(num, suffix="B"):
    for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"

def get_dir_size(start_path):
    total_size = 0
    console_log(f"getting dir size of {start_path}..")
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size
