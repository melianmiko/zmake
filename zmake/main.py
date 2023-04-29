import logging
import os.path
import sys
import traceback
from pathlib import Path

from zmake import ZMakeContext, GUIDE, utils, constants
from zmake.context import QuietExitException

def main():
    if os.path.isfile(".zmake_debug"):
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger("PIL.PngImagePlugin").disabled = True
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    if len(sys.argv) < 2:
        print(GUIDE)
        print("Config locations:")
        print(f'  {utils.APP_PATH / "zmake.json"}')
        print(f'  {constants.CONFIG_DIR / "zmake.json"}')
        print("")
        print("Press any key to exit")
        input()
        raise SystemExit

    path = Path(sys.argv[1]).resolve()

    # noinspection PyBroadException
    try:
        ctx = ZMakeContext(path)
        ctx.perform_auto()
    except QuietExitException:
        input()
    except Exception:
        traceback.print_exc()
        print("FAILED")
        input()
