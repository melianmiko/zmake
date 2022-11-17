import os.path
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
    spec_file = "zmake.spec"
    result_file = "zmake.exe"
elif sys.platform == "darwin":
    pyinstaller = "./venv/bin/pyinstaller"
    spec_file = "zmake-qt.spec"
    result_file = "zmake.app"
else:
    pyinstaller = "./venv/bin/pyinstaller"
    spec_file = "zmake.spec"
    result_file = "zmake"

# Build
subprocess.Popen([pyinstaller, spec_file]).wait()

# Package OSX
if sys.platform == "darwin":
    shutil.make_archive(f"dist/ZMake_{VERSION}_macos",
                        "zip",
                        "dist",
                        "zmake.app")
    raise SystemExit

# Package other platform
with ZipFile(f"dist/ZMake_{VERSION}_{sys.platform}.zip", "w", ZIP_DEFLATED) as f:
    f.write(f"dist/{result_file}", result_file)

    f.write('GUIDE.txt', 'GUIDE.txt')
    for ff in Path("zmake/data").rglob("**/*"):
        f.write(ff, f"data/{ff.name}")
