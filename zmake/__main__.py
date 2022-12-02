import logging
import os.path
import sys
import traceback
from pathlib import Path

from zmake import ZMakeContext, GUIDE


if __name__ == "__main__":
    if os.path.isfile(".zmake_debug"):
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    if len(sys.argv) < 2:
        print(GUIDE)
        print("Press any key to exit")
        input()
        raise SystemExit

    path = Path(sys.argv[1]).resolve()

    try:
        ctx = ZMakeContext(path)
        ctx.perform_auto()
    except Exception:
        traceback.print_exc()
        print("FAILED")
        input()
