import shutil
import subprocess
import sys

from zmake import ZMakeContext
from zmake.context import QuietExitException

NO_TOOL_MSG = """        
Please install them, or disable usage of that tool in config,
if it don't required to build your application.

For more information, check https://mmk.pw/en/zmake/guide/."""


def run_ext_tool(command, context: ZMakeContext, display_name: str):
    if sys.platform == "win32":
        possible_location = [f"{command[0]}.cmd", f"{command[0]}.exe"]
    elif sys.platform == "darwin":
        possible_location = [command[0], f"/opt/homebrew/bin/{command[0]}"]
    else:
        possible_location = [command[0]]

    for variant in possible_location:
        location = shutil.which(variant)
        if location is not None:
            command[0] = location
            break

    try:
        p = subprocess.run(command, capture_output=True, text=True)
        if p.stdout != "":
            context.logger.info(p.stdout)
        if p.stderr != "":
            context.logger.error(p.stderr)
        assert p.returncode == 0
    except FileNotFoundError:
        err = f"ERROR: External tool {display_name} not found\n" \
              f"Tried locations: {possible_location}" \
              f"{NO_TOOL_MSG}"
        context.logger.error(err)
        raise QuietExitException()


