import os
import datetime

import utils

def register_mcp(mcp):
    # --- information ---
    @mcp.tool()
    def get_datetime() -> str:
        """gets the current time and date"""

        return datetime.datetime.now().strftime("%H:%M %d-%M-%Y")

    @mcp.tool()
    def get_system_info() -> list:
        """returns information about user's PC"""

        return utils.sh_exec("fastfetch -l none")

    @mcp.tool()
    def get_network_interfaces() -> list:
        """returns information about the network interfaces on user's PC"""

        return utils.sh_exec("ip addr")

    @mcp.tool()
    def get_disk_usage() -> list:
        """returns information about disk space usage"""

        return utils.sh_exec("df -h")

    @mcp.tool()
    def fetch_man_page(cmd: str) -> list:
        """returns a linux manpage for a specified command"""
        cmd = cmd.split(" ")[0]

        return utils.sh_exec(f"man --pager '' {cmd}")

    # --- processes ---
    @mcp.tool()
    def get_running_system_processes() -> list:
        """returns processes that are running as the root user"""

        return utils.sh_exec("ps -o pid,comm,%cpu,%mem --sort=-%cpu -U root")

    @mcp.tool()
    def get_running_user_processes() -> list:
        """returns processes running under user's account"""

        return utils.sh_exec("ps -xo pid,comm,%cpu,%mem --sort=-%cpu")

    @mcp.tool()
    def get_home_dir_path() -> str:
        """get path to user's home directory"""

        return os.path.expanduser("~")

    # --- packages ---
    def get_installed_packages() -> list:
        """get packages installed on user's system"""

        return utils.sh_exec("pacman -Qe")

    def get_installed_applications() -> list:
        """get application .desktop files in /usr/share/applications"""

        result = []
        for filename in os.listdir("/usr/share/applications"):
            result.append(f"/usr/share/applications/{filename}")

        return result

    # --- system control ---
    @mcp.tool()
    def kill_process(pid: int = None, process_name: str = None) -> list:
        """
        kill a process by either pid or name.
        returns a bool representing if it was successful.
        """

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
        return utils.sh_exec("loginctl lock-session")

    # --- systemd services ---
    @mcp.tool()
    def list_user_services() -> list:
        """list systemd user services"""

        return utils.sh_exec("systemctl --user list-unit-files --type service")
    @mcp.tool()
    def list_system_services() -> list:
        """list systemd system services"""

        return utils.sh_exec("systemctl list-unit-files --type service")
    @mcp.tool()

    def system_service_status(name: str) -> list:
        """get the status of a systemd system service"""

        return {
                "status": utils.sh_exec(f"systemctl status {name}"),
                "journal": utils.sh_exec(f"journalctl -I -n 50 -u {name}")
        }
    @mcp.tool()
    def user_service_status(name: str) -> list:
        """get the status of a systemd user service"""

        return {
                "status": utils.sh_exec(f"systemctl --user status {name}"),
                "journal": utils.sh_exec(f"journalctl --user -I -n 50 -u {name}")
        }

    @mcp.tool()
    def start_user_service(name: str) -> list:
        """start a systemd user service"""

        return utils.sh_exec(f"systemctl --user start {name}")
    @mcp.tool()
    def restart_user_service(name: str) -> list:
        """restart a systemd user service"""

        return utils.sh_exec(f"systemctl --user restart {name}")
    @mcp.tool()
    def stop_user_service(name: str) -> list:
        """stop a systemd user service"""

        return utils.sh_exec(f"systemctl --user stop {name}")
    @mcp.tool()
    def kill_user_service(name: str) -> list:
        """forcefully kill a systemd user service"""

        return utils.sh_exec(f"systemctl --user kill {name}")

    # --- media control ---
    @mcp.tool()
    def media_currently_playing() -> list:
        """fetch what media is currently playing on user's device"""

        return utils.sh_exec("playerctl metadata")

    @mcp.tool()
    def media_toggle_pause():
        """toggle media play/pause"""

        return utils.sh_exec("playerctl play-pause")

    @mcp.tool()
    def media_next():
        """skip to next media"""

        return utils.sh_exec("playerctl next")

    @mcp.tool()
    def media_previous():
        """go back to previous media"""

        return utils.sh_exec("playerctl previous")

    @mcp.tool()
    def media_toggle_shuffle():
        """toggle media player shuffle"""

        return utils.sh_exec("playerctl shuffle Toggle")

    @mcp.tool()
    def media_stop():
        """stop playing media"""
        return utils.sh_exec("playerctl stop")
