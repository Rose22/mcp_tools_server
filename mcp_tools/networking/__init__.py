import requests
import utils

def register_mcp(mcp):
    ### --- networking ---
    @mcp.tool()
    def ping(addr: str) -> list:
        """pings a specified IP address or domain"""

        return utils.sh_exec(f"ping -c 1 {addr}")

    @mcp.tool()
    def list_open_ports() -> list:
        """list currently open ports on user's pc"""
        return utils.sh_exec(f"lsof -i")

    @mcp.tool()
    def traceroute(addr: str) -> list:
        """performs a traceroute on an ip address or domain"""
        return utils.sh_exec(f"traceroute {addr}")

    @mcp.tool()
    def whois(addr: str) -> list:
        """performs a WHOIS request on an ip address or domain"""
        return utils.sh_exec(f"whois {addr}")
