import platform
import shutil
import utils

OS = platform.system().lower()

def register_mcp(mcp):
    ### --- networking ---
    @mcp.tool()
    def get_network_info() -> dict:
        """returns information about the network interfaces on user's PC"""

        if OS == "linux":
            if shutil.which("nmcli"):
                # if network manager is installed, that gives better info
                return utils.sh_exec("nmcli -o")
            else:
                return utils.sh_exec("ip addr")
        elif OS == "windows":
            return utils.sh_exec("ipconfig")
        elif OS == "darwin":
            return utils.sh_exec("ifconfig")

    @mcp.tool()
    def ping(addr: str) -> dict:
        """pings a specified IP address or domain"""

        result = utils.sh_exec(f"ping -c 1 {addr}")
        if len(result) <= 1:
            return {"error": "could not reach address"}
        return result 

    @mcp.tool()
    def list_open_ports() -> dict:
        """list currently open ports on user's pc"""
        return utils.sh_exec(f"lsof -i")

    @mcp.tool()
    def traceroute(addr: str) -> dict:
        """performs a traceroute on an ip address or domain"""
        return utils.sh_exec(f"traceroute {addr}")

    @mcp.tool()
    def whois(addr: str) -> dict:
        """performs a WHOIS request on an ip address or domain"""
        return utils.sh_exec(f"whois {addr}")
