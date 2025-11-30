import os
import platform
import shutil
import datetime
import yaml

import utils

def register_mcp(mcp):
    profile_path = utils.get_data_path()+"/"
    def read_profile():
        pass

    @mcp.tool()
    def user_set_favorite(thing: str, value: str) -> dict:
        """sets the user's favorite {thing} to {value}"""

        return utils.result(True)
