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
                return utils.sh_exec_result("nmcli -o")
            else:
                return utils.sh_exec_result("ip addr")
        elif OS == "windows":
            return utils.sh_exec_result("ipconfig")
        elif OS == "darwin":
            return utils.sh_exec_result("ifconfig")

    def ping(addr: str) -> dict:
        """pings a specified IP address or domain"""

        result = utils.sh_exec_result(f"ping -c 1 {addr}")
        if len(result) <= 1:
            return utils.result(None, "could not reach address")
        return utils.result(result)
    mcp.tool(ping) if shutil.which("ping") else None

    def list_open_ports() -> dict:
        """list currently open ports on user's pc"""
        return utils.sh_exec_result(f"lsof -i")
    mcp.tool(list_open_ports) if shutil.which("lsof") else None

    def traceroute(addr: str) -> dict:
        """performs a traceroute on an ip address or domain"""
        return utils.sh_exec_result(f"traceroute {addr}")
    mcp.tool(traceroute) if shutil.which("traceroute") else None

    def whois(addr: str) -> dict:
        """performs a WHOIS request on an ip address or domain"""
        return utils.sh_exec_result(f"whois {addr}")
    mcp.tool(whois) if shutil.which("whois") else None

    def nmap(target: str) -> dict:
        """runs an NMAP port scan on your chosen target"""
        return utils.sh_exec_result(f"nmap {target}")
    mcp.tool(nmap) if shutil.which("nmap") else None

