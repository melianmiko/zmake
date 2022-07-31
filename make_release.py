import os.path
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from zmake import VERSION

if os.path.isdir("dist"):
    shutil.rmtree("dist")

subprocess.Popen(["./venv/bin/pyinstaller", "-F", "zmake.py"]).wait()

with ZipFile(f"dist/ZMake_{VERSION}_{sys.platform}.zip", "w", ZIP_DEFLATED) as f:
    if os.path.isfile("dist/zmake"):
        f.write("dist/zmake", "zmake")
    if os.path.isfile("dist/zmake.exe"):
        f.write("dist/zmake.exe", "zmake.exe")

    for ff in Path("data").rglob("**/*"):
        f.write(ff)
