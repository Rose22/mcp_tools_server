import os
import platform
import shutil
import datetime
import json

import utils

OS = platform.system().lower()
# temporary override
#OS = "windows"

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
            data['environment_vars'] = dict(os.environ)

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
            data["pci_devices"] = utils.sh_exec("lspci"),
            data['system_root'] = os.listdir("/")

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
    def get_disk_usage() -> list:
        """returns information about disk space usage"""

        if OS in ("linux", "darwin"):
            return utils.sh_exec("df -h")
        elif OS == "windows":
            return utils.sh_exec("wmic logicaldisk")

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

        if OS == "linux":
            if pid:
                return utils.sh_exec(f"kill -9 {pid}")
            elif process_name:
                return utils.sh_exec(f"killall -9 {process_name}")
        elif OS == "windows":
            return utils.sh_exec(f"taskkill /f /im {process_name}")
        elif OS == "darwin":
            if pid:
                return utils.sh_exec(f"kill -9 {pid}")
            elif process_name:
                return utils.sh_exec(f"pkill -f {process_name}")

        return False

    @mcp.tool()
    def lock_screen() -> list:
        """
        locks the user's pc screen
        """

        if OS == "linux":
            return utils.sh_exec("loginctl lock-session")
        elif OS == "windows":
            return utils.sh_exec("rundll32.exe user32.dll,LockWorkStation")
        elif OS == "darwin":
            return utils.sh_exec("osascript -e 'tell application \"System Events\" to click button \"Lock\" of window \"Login Window\"'")

    # ----------------------
    # linux specific tools
    # ----
    # we don't use the mcp.tool() decorator here
    # because we check later on if we want to
    # register these tools with the mcp server
    # based on if user's OS is linux
    def get_linux_distro():
        try:
            distro_info = platform.freedesktop_os_release()
            distro = distro_info['ID']
            related_distros = distro_info['ID_LIKE'].split(" ") if "ID_LIKE" in distro_info.keys() else []

            return (distro, related_distros)

        except Exception as e:
            return False

    def get_system_diagnostic_info_linux():
        """returns extra diagnostic info such as: attached usb devices, mount points, kernel modules, lsirq, lsipc"""

        return {
            "mounts": utils.sh_exec("mount"),
            "usb_devices": utils.sh_exec("lsusb"),
            "kernel_modules": utils.sh_exec("lsmod"),
            "usb_devices": utils.sh_exec("lsusb"),
            "lsirq": utils.sh_exec("lsirq"),
            "lsipc": utils.sh_exec("lsipc")
        }

    def fetch_man_page(cmd: str) -> list:
        """returns a unix manpage for a specified command"""

        if OS not in ("linux", "darwin"):
            return "this is not a linux or mac system, man pages are not available"

        cmd = cmd.split(" ")[0]

        return utils.sh_exec(f"man --pager '' {cmd}")

    def get_user_environment_variables() -> dict:
        """get environment variables for the user's current session"""

        return dict(os.environ)

    def list_logged_in_users() -> list:
        """get users currently logged in to user's linux system"""

        return utils.sh_exec("w")

    # --- package management ---
    def get_installed_packages() -> dict:
        """get all installed packages on user's linux system"""

        result = {}

        if shutil.which("pacman"):
            result['system_packages'] = utils.sh_exec("pacman -Qe")
        elif shutil.which("apt"):
            # todo
            pass
        elif shutil.which("rpm"):
            # todo
            pass
        else:
            pass

        if shutil.which("flatpak"):
            result['flatpak_packages'] = utils.sh_exec("flatpak list")

        if shutil.which("snap"):
            result['snap_packages'] = utils.sh_exec("snap list")

        return result

    def search_linux_packages(query: str) -> dict:
        """search for a package in user's linux package manager"""

        distro, related_distros = get_linux_distro()
        result = {}

        if shutil.which("pacman"):
            result['system_packages'] = utils.sh_exec(f"pacman -Ss {query}")
        else:
            result['system_packages'] =  f"package manager for linux distribution {distro} unsupported"

        if shutil.which("flatpak"):
            result['flatpak_packages'] = utils.sh_exec(f"flatpak search {query}")

        if shutil.which("snap"):
            result['snap_packages'] = utils.sh_exec(f"snap find {query}")

        return result

    def flatpak_install_package(name: str):
        """install a flatpak package"""

        # only add this to the mcp tools if flatpak is detected
        # (this is done further down outside the function definitions)

        return utils.sh_exec(f"flatpak install --noninteractive {name}")

    def flatpak_remove_package(name: str) -> list:
        """remove a flatpak package"""

        return utils.sh_exec(f"flatpak uninstall --noninteractive {name}")

    # --- systemd services ---
    def list_user_services() -> list:
        """list systemd user services"""

        return utils.sh_exec("systemctl --user list-unit-files --type service")

    def list_system_services() -> list:
        """list systemd system services"""

        return utils.sh_exec("systemctl list-unit-files --type service")

    def system_service_status(name: str) -> list:
        """get the status of a systemd system service"""

        return {
                "status": utils.sh_exec(f"systemctl status {name}"),
                "journal": utils.sh_exec(f"journalctl -I -n 50 -u {name}")
        }

    def user_service_status(name: str) -> list:
        """get the status of a systemd user service"""

        return {
                "status": utils.sh_exec(f"systemctl --user status {name}"),
                "journal": utils.sh_exec(f"journalctl --user -I -n 50 -u {name}")
        }

    def start_user_service(name: str) -> list:
        """start a systemd user service"""

        if OS == "windows":
            return utils.sh_exec(f"sc start {name}")
        elif OS == "darwin":
            return utils.sh_exec(f"launchctl load -w /Library/LaunchDaemons/{name}.plist")
        else:  # Linux
            return utils.sh_exec(f"systemctl --user start {name}")

    def restart_user_service(name: str) -> list:
        """restart a systemd user service"""

        return utils.sh_exec(f"systemctl --user restart {name}")

    def stop_user_service(name: str) -> list:
        """stop a systemd user service"""

        return utils.sh_exec(f"systemctl --user stop {name}")

    def kill_user_service(name: str) -> list:
       """forcefully kill a systemd user service"""
    
       return utils.sh_exec(f"systemctl --user kill {name}")

    def systemd_user_logs() -> list:
        """returns systemd user level logs (last 1000 lines)"""

        return utils.sh_exec("journalctl --user -b -n1000")
    def systemd_kernel_logs() -> list:
        """returns systemd kernel logs (journalctl -k)"""

        return utils.sh_exec("journalctl -k")

    # --- network control ---
    def turn_network_off():
        """turns off user's internet"""
        return utils.sh_exec("nmcli network off")
    def turn_network_on():
        """turns on user's internet"""
        return utils.sh_exec("nmcli network on")

    # --- media control ---
    def media_currently_playing() -> list:
        """fetch what media is currently playing on user's device"""

        return utils.sh_exec("playerctl metadata")

    def media_toggle_pause():
        """toggle media play/pause"""

        return utils.sh_exec("playerctl play-pause")

    def media_next():
        """skip to next media"""

        return utils.sh_exec("playerctl next")

    def media_previous():
        """go back to previous media"""

        return utils.sh_exec("playerctl previous")

    def media_toggle_shuffle():
        """toggle media player shuffle"""

        return utils.sh_exec("playerctl shuffle Toggle")

    def media_stop():
        """stop playing media"""
        return utils.sh_exec("playerctl stop")

    if OS == "linux":
        # register all the linux-specific tools into the mcp server

        mcp.tool(get_system_diagnostic_info_linux, name="get_system_diagnostic_info")
        mcp.tool(fetch_man_page)

        # if using a supported package manager, add package management tools!
        if (
            shutil.which("pacman") or
            shutil.which("apt") or
            shutil.which("rpm") or

            shutil.which("flatpak") or
            shutil.which("snap")
        ):

            mcp.tool(get_installed_packages)
            mcp.tool(search_linux_packages)

        # TODO: broken, needs fix
        #if shutil.which("flatpak"):
        #    mcp.tool(flatpak_install_package)
        #    mcp.tool(flatpak_remove_package)

        # add systemd control if systemd is installed
        if shutil.which("systemctl"):
            mcp.tool(list_user_services)
            mcp.tool(list_system_services)
            mcp.tool(system_service_status)
            mcp.tool(user_service_status)
            mcp.tool(start_user_service)
            mcp.tool(restart_user_service)
            mcp.tool(stop_user_service)
            mcp.tool(kill_user_service)
            mcp.tool(systemd_user_logs)
            mcp.tool(systemd_kernel_logs)

        # only add player controls if user's os is linux
        # this is temporary until i figure out how to
        # control media players on other platforms
        if shutil.which("playerctl"):
            mcp.tool(media_currently_playing)
            mcp.tool(media_toggle_pause)
            mcp.tool(media_next)
            mcp.tool(media_previous)
            mcp.tool(media_toggle_shuffle)
            mcp.tool(media_stop)
