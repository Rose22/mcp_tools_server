import os
import platform
import datetime
import json

import utils

OS = platform.system().lower()

def register_mcp(mcp):
    # --- information ---
    @mcp.tool()
    def get_datetime() -> str:
        """gets the current time and date"""

        return datetime.datetime.now().strftime("%H:%M %d-%M-%Y")

    @mcp.tool()
    def get_system_info() -> dict:
        """returns information about user's PC"""

        data = {
            "os": OS,
            "os_release": platform.release(),
            "platform": platform.platform(),
            "architecture": platform.machine() if platform.machine() else "unknown",
            "hostname": platform.node(),
            "processor": platform.processor(),
            "uname": platform.uname(),
            #"python_version": platform.python_version(),
            #"python_build": platform.python_build(),
            #"python_implementation": platform.python_implementation(),
        }

        if OS == "linux":
            cpu_info_filtered = {}

            try:
                cpu_info = json.loads(utils.sh_exec("lscpu -J"))['lscpu']
                for entry in cpu_info:
                    key = entry['field']
                    if key.lower() in ("flags"):
                        continue

                    cpu_info_filtered[key] = entry['data']
            except:
                pass

            data['shell_uname_cmd'] = utils.sh_exec("uname -a")
            data['cpu'] = cpu_info_filtered
            data['system_root'] = os.listdir("/")
            data['disks'] = utils.sh_exec("lsblk")

            try:
                data['freedesktop_os_release'] = platform.freedesktop_os_release()
            except:
                pass
            
            data['memory_usage'] = utils.sh_exec("free -m")
            data['disk_usage'] = utils.sh_exec("df -h")
        elif OS == "darwin":
            data['mac_ver'] = platform.mac_ver()

            # TODO: unverified, these commands may not work.. need someone to test it
            data['cpu'] = utils.sh_exec("sysctl hw.model")
            data["memory_usage"] = utils.sh_exec("sysctl hw.memsize")[1].split()[-1]  # In bytes
            data['disk_usage'] = utils.sh_exec("df -h")
        elif OS == "windows":
            data['win32_ver'] = platform.win32_ver()
            data['win32_edition'] = platform.win32_edition()
            data['win32_is_iot'] = platform.win32_is_iot()

            # TODO: unverified, these commands may not work.. need someone to test it
            data['cpu'] = utils.sh_exec("wmic cpu get name")
            data["memory_usage"] = utils.sh_exec("wmic memorychip get Capacity")  # Total RAM
            data['disk_usage'] = utils.sh_exec("wmic logicaldisk get DeviceID, Size, FreeSpace")

        return data

    @mcp.tool()
    def get_system_diagnostic_info():
        """returns useful extra information for diagnosing systems"""

        if OS not in ("windows", "darwin"):
            return {
                "mounts": utils.sh_exec("mount"),
                "usb_devices": utils.sh_exec("lsusb"),
                "kernel_modules": utils.sh_exec("lsmod"),
                "pci_devices": utils.sh_exec("lspci"),
                "usb_devices": utils.sh_exec("lsusb"),
                "lsirq": utils.sh_exec("lsirq"),
                "lsipc": utils.sh_exec("lsipc")
            }
        else:
            return "diagnostic info not supported for this OS yet"

    @mcp.tool()
    def get_network_interfaces() -> list:
        """returns information about the network interfaces on user's PC"""

        if OS == "linux":
            return utils.sh_exec("ip addr")
        elif OS == "windows":
            return utils.sh_exec("ipconfig")
        elif OS == "darwin":
            return utils.sh_exec("ifconfig")

    @mcp.tool()
    def get_disk_usage() -> list:
        """returns information about disk space usage"""

        if OS in ("linux", "darwin"):
            return utils.sh_exec("df -h")
        elif OS == "windows":
            return utils.sh_exec("wmic logicaldisk")

    @mcp.tool()
    def fetch_man_page(cmd: str) -> list:
        """returns a unix manpage for a specified command"""

        if OS not in ("linux", "darwin"):
            return "this is not a linux or mac system, man pages are not available"

        cmd = cmd.split(" ")[0]

        return utils.sh_exec(f"man --pager '' {cmd}")

    # --- processes ---
    @mcp.tool()
    def get_running_system_processes() -> list:
        """returns processes that are running as the root user"""

        if OS in ("linux", "darwin"):
            # TODO: verify this works on macos
            return utils.sh_exec("ps -o pid,comm,%cpu,%mem --sort=-%cpu -U root")
        elif OS == "windows":
            return utils.sh_exec("tasklist")

    @mcp.tool()
    def get_running_user_processes() -> list:
        """returns processes running under user's account"""

        if OS == "windows":
            return utils.sh_exec("tasklist")
        else:
            # TODO: verify this works on macos
            return utils.sh_exec("ps -xo pid,comm,%cpu,%mem --sort=-%cpu")

    @mcp.tool()
    def get_home_dir_path() -> str:
        """get path to user's home directory"""

        return os.path.expanduser("~")

    # --- system control ---
    @mcp.tool()
    def kill_process(pid: int = None, process_name: str = None) -> list:
        """
        kill a process by either pid or name.
        returns a bool representing if it was successful.
        """

        if OS == "windows":
            return utils.sh_exec(f"taskkill /f /im {process_name}")
        elif OS == "darwin":
            if pid:
                return utils.sh_exec(f"kill -9 {pid}")
            elif process_name:
                return utils.sh_exec(f"pkill -f {process_name}")
        else:
            if pid:
                return utils.sh_exec(f"kill -9 {pid}")
            elif process_name:
                return utils.sh_exec(f"killall -9 {process_name}")

        return False

    @mcp.tool()
    def lock_screen() -> list:
        """
        locks the user's pc screen
        """
        if OS == "windows":
            return utils.sh_exec("rundll32.exe user32.dll,LockWorkStation")
        elif OS == "darwin":
            return utils.sh_exec("osascript -e 'tell application \"System Events\" to click button \"Lock\" of window \"Login Window\"'")
        else:  # Linux
            return utils.sh_exec("loginctl lock-session")

    # --- systemd services ---
    # disabled for now as this is very specific to arch linux
    #@mcp.tool()
    #def list_user_services() -> list:
    #    """list systemd user services"""

    #    return utils.sh_exec("systemctl --user list-unit-files --type service")
    #@mcp.tool()
    #def list_system_services() -> list:
    #    """list systemd system services"""

    #    return utils.sh_exec("systemctl list-unit-files --type service")
    #@mcp.tool()

    #def system_service_status(name: str) -> list:
    #    """get the status of a systemd system service"""

    #    return {
    #            "status": utils.sh_exec(f"systemctl status {name}"),
    #            "journal": utils.sh_exec(f"journalctl -I -n 50 -u {name}")
    #    }
    #@mcp.tool()
    #def user_service_status(name: str) -> list:
    #    """get the status of a systemd user service"""

    #    return {
    #            "status": utils.sh_exec(f"systemctl --user status {name}"),
    #            "journal": utils.sh_exec(f"journalctl --user -I -n 50 -u {name}")
    #    }

    #@mcp.tool()
    #def start_user_service(name: str) -> list:
    #    """start a systemd user service"""

    #    if OS == "windows":
    #        return utils.sh_exec(f"sc start {name}")
    #    elif OS == "darwin":
    #        return utils.sh_exec(f"launchctl load -w /Library/LaunchDaemons/{name}.plist")
    #    else:  # Linux
    #        return utils.sh_exec(f"systemctl --user start {name}")

    #@mcp.tool()
    #def restart_user_service(name: str) -> list:
    #    """restart a systemd user service"""

    #    return utils.sh_exec(f"systemctl --user restart {name}")
    #@mcp.tool()
    #def stop_user_service(name: str) -> list:
    #    """stop a systemd user service"""

    #    return utils.sh_exec(f"systemctl --user stop {name}")
    #@mcp.tool()
    #def kill_user_service(name: str) -> list:
    #   """forcefully kill a systemd user service"""
    #
    #   return utils.sh_exec(f"systemctl --user kill {name}")

    # --- media control ---
    #@mcp.tool()
    #def media_currently_playing() -> list:
    #    """fetch what media is currently playing on user's device"""

    #    return utils.sh_exec("playerctl metadata")

    #@mcp.tool()
    #def media_toggle_pause():
    #    """toggle media play/pause"""

    #    return utils.sh_exec("playerctl play-pause")

    #@mcp.tool()
    #def media_next():
    #    """skip to next media"""

    #    return utils.sh_exec("playerctl next")

    #@mcp.tool()
    #def media_previous():
    #    """go back to previous media"""

    #    return utils.sh_exec("playerctl previous")

    #@mcp.tool()
    #def media_toggle_shuffle():
    #    """toggle media player shuffle"""

    #    return utils.sh_exec("playerctl shuffle Toggle")

    #@mcp.tool()
    #def media_stop():
    #    """stop playing media"""
    #    return utils.sh_exec("playerctl stop")
