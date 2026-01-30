import utils
import datetime

def register_mcp(mcp):
    @mcp.tool
    def get_datetime() -> dict:
        """gets the current time and date. ALWAYS call this before assuming what date today is! NEVER assume or guess today's date."""

    return utils.result(datetime.datetime.now().strftime("%c"))

    @mcp.tool
    def get_time() -> dict:
        """gets the current time"""
        return utils.result(datetime.datetime.now().strftime("%X"))

    @mcp.tool
    def get_date() -> dict:
        """gets the current date (without time)"""
        return utils.result(datetime.datetime.now().strftime("%x"))
