import sys
import traceback
from pathlib import Path

from zmake import ZMakeContext

VERSION = "v1.5"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"zmake v{VERSION} by melianmiko")
        print('------------------------------------------------------------------')
        print("Usage: zmake PATH, where PATH is file/dir path")
        print("In Windows, you can drag file/dir to this EXE.")
        print()
        print("- If PATH is bin-file, we'll try to unpack it as watchface")
        print("- If PATH was an empty dir, new project struct will be created")
        print("- If PATH contains app.json, we'll build this project")
        print("- If PATH was file, we'll convert them to PNG/TGA")
        print("- Otherwise, we'll convert all images in that PATH")
        print()
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
