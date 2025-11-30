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
    def get_datetime() -> dict:
        """gets the current time and date"""

        return utils.result(datetime.datetime.now().strftime("%H:%M %d-%M-%Y"))

    @mcp.tool()
    def get_system_info() -> dict:
        """returns information about user's PC"""

        data = {
            "os": OS,
            "os_release": platform.release(),
            "platform": platform.platform(),
            "architecture": platform.machine() if platform.machine() else "unknown",
            "hostname": platform.node(),
            "home_dir": os.path.expanduser("~"),
            #"processor": platform.processor(),
            #"uname": platform.uname(),
            #"python_version": platform.python_version(),
            #"python_build": platform.python_build(),
            #"python_implementation": platform.python_implementation(),
        }

        if OS == "linux":
            try:
                # get CPU name
                sh_lscpu = "\n".join(utils.sh_exec("lscpu -J"))
                cpu_info = json.loads(sh_lscpu)['lscpu']

                data['cpu'] = "information not found"

                for entry in cpu_info:
                    if entry['field'].lower().startswith("model name"):
                        data['cpu'] = entry['data']
                        break
            except Exception as e:
                data['cpu'] = f"error {e}"

            data['kernel'] = utils.sh_exec("uname -a")

            # get GPU's
            data['gpus'] = []
            for line in utils.sh_exec("lspci"):
                if "vga" in line.lower():
                    data['gpus'].append(line)

            #data["pci_devices"] = utils.sh_exec("lspci"),
            #data['system_root'] = os.listdir("/")

            try:
                # get essential distro info

                distro_info = {}
                for key, value in platform.freedesktop_os_release().items():
                    key = key.lower()

                    if (
                        key.endswith("name") or
                        key.endswith("id") or
                        key.startswith("version") or
                        key.startswith("variant")
                    ):
                        distro_info[key] = value
                data['distro'] = distro_info
            except:
                pass
            
            #data['memory_usage'] = utils.sh_exec("free -m")
            #data['disk_usage'] = utils.sh_exec("df -h")
        elif OS == "darwin":
            data['mac_ver'] = platform.mac_ver()

            # TODO: unverified, these commands may not work.. need someone to test it

            #data["memory_usage"] = utils.sh_exec("sysctl hw.memsize")[1].split()[-1]  # In bytes
            #data['disk_usage'] = utils.sh_exec("df -h")
        elif OS == "windows":
            data['win32_ver'] = platform.win32_ver()
            data['win32_edition'] = platform.win32_edition()
            data['win32_is_iot'] = platform.win32_is_iot()

            # TODO: unverified, these commands may not work.. need someone to test it
            #data["memory_usage"] = utils.sh_exec("wmic memorychip get Capacity")  # Total RAM
            #data['disk_usage'] = utils.sh_exec("wmic logicaldisk get DeviceID, Size, FreeSpace")

        data["_instructions"] = "if you need more information about user's system, use followup tool calls!'"

        return utils.result(data)

    @mcp.tool()
    def get_cpu_info() -> dict:
        """returns full information about the CPU in user's PC"""
        if OS == "linux":
            cpu_info_filtered = {}

            try:
                sh_lscpu = "\n".join(utils.sh_exec("lscpu -J"))
                cpu_info = json.loads(sh_lscpu)['lscpu']

                for entry in cpu_info:
                    key = entry['field']
                    if key.lower() in ("flags"):
                        continue

                    cpu_info_filtered[key] = entry['data']
            except Exception as e:
                return utils.result(None, f"couldn't fetch cpu info: {e}")

            data = cpu_info_filtered
        elif OS == "darwin":
            data = utils.sh_exec("sysctl hw.model")
        elif OS == "windows":
            data = utils.sh_exec("wmic cpu get name")

        return utils.result(data)

    @mcp.tool()
    def get_disk_usage() -> dict:
        """returns information about disk space usage"""

        if OS in ("linux", "darwin"):
            return utils.sh_exec_result("df -h")
        elif OS == "windows":
            return utils.sh_exec_result("wmic logicaldisk")

    # --- processes ---
    @mcp.tool()
    def get_running_system_processes() -> dict:
        """returns processes that are running as the root user"""

        if OS in ("linux", "darwin"):
            # TODO: verify this works on macos
            return utils.sh_exec_result("ps -o pid,comm,%cpu,%mem --sort=-%cpu -U root")
        elif OS == "windows":
            return utils.sh_exec_result("tasklist")

    @mcp.tool()
    def get_running_user_processes() -> dict:
        """returns processes running under user's account"""

        if OS == "windows":
            return utils.sh_exec_result("tasklist")
        else:
            # TODO: verify this works on macos
            return utils.sh_exec_result("ps -xo pid,comm,%cpu,%mem --sort=-%cpu")

    @mcp.tool()
    def get_home_dir_path() -> dict:
        """get path to user's home directory"""

        return utils.result(os.path.expanduser("~"))

    # --- system control ---
    @mcp.tool()
    def kill_process(pid: int = None, process_name: str = None) -> dict:
        """
        kill a process by either pid or name.
        returns a bool representing if it was successful.
        """

        if OS == "linux":
            if pid:
                return utils.sh_exec_result(f"kill -9 {pid}")
            elif process_name:
                return utils.sh_exec_result(f"killall -9 {process_name}")
        elif OS == "windows":
            return utils.sh_exec_result(f"taskkill /f /im {process_name}")
        elif OS == "darwin":
            if pid:
                return utils.sh_exec_result(f"kill -9 {pid}")
            elif process_name:
                return utils.sh_exec_result(f"pkill -f {process_name}")

        return utils.result(False)

    @mcp.tool()
    def lock_screen() -> dict:
        """
        locks the user's pc screen
        """

        if OS == "linux":
            return utils.sh_exec_result("loginctl lock-session")
        elif OS == "windows":
            return utils.sh_exec_result("rundll32.exe user32.dll,LockWorkStation")
        elif OS == "darwin":
            return utils.sh_exec_result("osascript -e 'tell application \"System Events\" to click button \"Lock\" of window \"Login Window\"'")

    # ----------------------
    # linux specific tools
    # ----
    # we don't use the mcp.tool() decorator here
    # because we check later on if we want to
    # register these tools with the mcp server
    # based on if user's OS is linux
    def get_linux_distro() -> dict:
        try:
            distro_info = platform.freedesktop_os_release()
            distro = distro_info['ID']
            related_distros = distro_info['ID_LIKE'].split(" ") if "ID_LIKE" in distro_info.keys() else []

            return (distro, related_distros)

        except Exception as e:
            return False

    def get_system_diagnostic_info_linux() -> dict:
        """returns extra diagnostic info such as: attached usb devices, mount points, kernel modules, lsirq, lsipc"""

        return utils.result({
            "mounts": utils.sh_exec("mount"),
            "usb_devices": utils.sh_exec("lsusb"),
            "kernel_modules": utils.sh_exec("lsmod"),
            "usb_devices": utils.sh_exec("lsusb"),
            "lsirq": utils.sh_exec("lsirq"),
            "lsipc": utils.sh_exec("lsipc")
        })

    def get_env_vars() -> dict:
        """returns user's environment variables"""

        return utils.result(dict(os.environ))
    def fetch_man_page(cmd: str) -> dict:
        """returns a unix manpage for a specified command"""

        if OS not in ("linux", "darwin"):
            return {"error": "this is not a linux or mac system, man pages are not available"}

        cmd = cmd.split(" ")[0]

        return utils.sh_exec_result(f"man --pager '' {cmd}")

    def get_user_environment_variables() -> dict:
        """get environment variables for the user's current session"""

        return utils.result(dict(os.environ))

    def list_logged_in_users() -> dict:
        """get users currently logged in to user's linux system"""

        return utils.sh_exec_result("w")

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

        return utils.result(result)

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

        return utils.result(result)

    def flatpak_install_package(name: str) -> dict:
        """install a flatpak package"""

        # only add this to the mcp tools if flatpak is detected
        # (this is done further down outside the function definitions)

        return utils.sh_exec_result(f"flatpak install --noninteractive {name}")

    def flatpak_remove_package(name: str) -> dict:
        """remove a flatpak package"""

        return utils.sh_exec_result(f"flatpak uninstall --noninteractive {name}")

    # --- systemd services ---
    def list_user_services() -> dict:
        """list systemd user services"""

        return utils.sh_exec_result("systemctl --user list-unit-files --type service")

    def list_system_services() -> dict:
        """list systemd system services"""

        return utils.sh_exec_result("systemctl list-unit-files --type service")

    def system_service_status(name: str) -> dict:
        """get the status of a systemd system service"""

        return utils.result({
            "status": utils.sh_exec(f"systemctl status {name}"),
            "journal": utils.sh_exec(f"journalctl -I -n 50 -u {name}")
        })

    def user_service_status(name: str) -> dict:
        """get the status of a systemd user service"""

        return utils.result({
            "status": utils.sh_exec(f"systemctl --user status {name}"),
            "journal": utils.sh_exec(f"journalctl --user -I -n 50 -u {name}")
        })

    def start_user_service(name: str) -> dict:
        """start a systemd user service"""

        if OS == "linux":
            return utils.sh_exec_result(f"systemctl --user -v start {name}")
        elif OS == "darwin":
            return utils.sh_exec_result(f"launchctl load -w /Library/LaunchDaemons/{name}.plist")
        elif OS == "windows":
            return utils.sh_exec_result(f"sc start {name}")

    def restart_user_service(name: str) -> dict:
        """restart a systemd user service"""

        return utils.sh_exec_result(f"systemctl --user -v restart {name}")

    def stop_user_service(name: str) -> dict:
        """stop a systemd user service"""

        return utils.sh_exec_result(f"systemctl --user -v stop {name}")

    def kill_user_service(name: str) -> dict:
       """forcefully kill a systemd user service"""
    
       return utils.sh_exec_result(f"systemctl --user kill {name}")

    def systemd_user_logs() -> dict:
        """returns systemd user level logs (last 1000 lines)"""

        return utils.sh_exec_result("journalctl --user -b -n1000")
    def systemd_kernel_logs() -> dict:
        """returns systemd kernel logs (journalctl -k)"""

        return utils.sh_exec_result("journalctl -k")

    # --- network control ---
    def turn_network_off() -> dict:
        """turns off user's internet"""
        return utils.sh_exec_result("nmcli network off")
    def turn_network_on() -> dict:
        """turns on user's internet"""
        return utils.sh_exec_result("nmcli network on")

    # --- media control ---
    def media_currently_playing() -> dict:
        """fetch what media is currently playing on user's device"""

        return utils.sh_exec_result("playerctl metadata")

    def media_toggle_pause() -> dict:
        """toggle media play/pause"""

        return utils.sh_exec_result("playerctl play-pause")

    def media_next() -> dict:
        """skip to next media"""

        return utils.sh_exec_result("playerctl next")

    def media_previous() -> dict:
        """go back to previous media"""

        return utils.sh_exec_result("playerctl previous")

    def media_toggle_shuffle() -> dict:
        """toggle media player shuffle"""

        return utils.sh_exec_result("playerctl shuffle Toggle")

    def media_stop() -> dict:
        """stop playing media"""
        return utils.sh_exec_result("playerctl stop")

    if OS == "linux":
        # register all the linux-specific tools into the mcp server

        mcp.tool(get_env_vars)
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
