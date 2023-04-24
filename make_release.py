import os.path
import platform
import shutil
import subprocess
import sys

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from zmake import VERSION

if os.path.isdir("dist"):
    shutil.rmtree("dist")

if sys.platform == "win32":
    pyinstaller = "./venv/Scripts/pyinstaller"
    spec_file = "zmake_win32.spec"
    result_file = "zmake.exe"
elif sys.platform == "darwin":
    pyinstaller = "./venv/bin/pyinstaller"
    if platform.platform().startswith("macOS-10"):
        print("WARN: Build with PySide2, due to macOS lower than 11")
        spec_file = "zmake_darwin_legacy.spec"
    else:
        spec_file = "zmake_darwin.spec"
    result_file = "zmake.app"
else:
    pyinstaller = "./venv/bin/pyinstaller"
    spec_file = "zmake_linux.spec"
    result_file = "zmake"

# Build
subprocess.Popen([pyinstaller, spec_file]).wait()

# Package OSX
if sys.platform == "darwin":
    shutil.make_archive(f"dist/ZMake_{VERSION}_macos",
                        "gztar",
                        "dist",
                        "zmake.app")
    raise SystemExit

# Package other platform
with ZipFile(f"dist/ZMake_{VERSION}_{sys.platform}.zip", "w", ZIP_DEFLATED) as f:
    f.write(f"dist/{result_file}", result_file)

    for ff in Path("zmake/data").rglob("**/*"):
        f.write(ff, f"data/{ff.name}")
