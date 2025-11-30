import subprocess
import os
import aiohttp

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

def remove_duplicates(lst: list):
    # removes duplicates from a list

    new_lst = []
    for item in lst:
        if item not in new_lst:
            new_lst.append(item)
    return new_lst

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

async def http_request(url):
    console_log("fetching remote content..")

    async with aiohttp.ClientSession(
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.3"}
    ) as session:
        async with session.get(url, timeout=10) as response:
            if response.status != 200:
                raise Exception(f"Request failed with status {response.status}")
            return await response.read()

def sh_exec_sandbox(command, timeout=30, workdir=None) -> dict:
    """
    Safely execute shell command with multiple layers of protection
    """
    if workdir is None:
        workdir = tempfile.mkdtemp()

    # Command validation
    dangerous_patterns = ['rm -rf', 'dd if=', 'mkfs', ':(){:|:&};:', 'wget', 'curl']
    for pattern in dangerous_patterns:
        if pattern in command.lower():
            raise SecurityError(f"Dangerous command pattern detected: {pattern}")

    # Restricted environment
    safe_env = {
        'PATH': '/usr/bin:/bin',
        'HOME': workdir,
        'USER': 'nobody',
        'LOGNAME': 'nobody',
        'SHELL': '/bin/sh'
    }

    try:
        result = subprocess.run(
            command,
            shell=True,
            env=safe_env,
            timeout=timeout,
            capture_output=True,
            text=True,
            cwd=workdir,
            preexec_fn=os.setsid  # New process group
        )

        return {
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'timed_out': False
        }

    except subprocess.TimeoutExpired:
        return {'returncode': -1, 'stdout': '', 'stderr': 'Command timed out', 'timed_out': True}
    except Exception as e:
        return {'returncode': -1, 'stdout': '', 'stderr': str(e), 'timed_out': False}
    finally:
        # Cleanup
        if os.path.exists(workdir) and workdir.startswith('/tmp'):
            subprocess.run(['rm', '-rf', workdir])

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
