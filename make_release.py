import os.path
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from zmake.__main__ import VERSION

if os.path.isdir("dist"):
    shutil.rmtree("dist")

pyinstaller = "./venv/bin/pyinstaller"
if sys.platform == "win32":
    pyinstaller = "./venv/Scripts/pyinstaller"

subprocess.Popen([pyinstaller, "-n", "zmake", "-F", "zmake/__main__.py"]).wait()

with ZipFile(f"dist/ZMake_{VERSION}_{sys.platform}.zip", "w", ZIP_DEFLATED) as f:
    if os.path.isfile("dist/zmake"):
        f.write("dist/zmake", "zmake")
    if os.path.isfile("dist/zmake.exe"):
        f.write("dist/zmake.exe", "zmake.exe")

    f.write('GUIDE.txt', 'GUIDE.txt')
    for ff in Path("data").rglob("**/*"):
        f.write(ff)
