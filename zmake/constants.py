import sys
from pathlib import Path

VERSION = "v1.8.2"

GUIDE = f"""zmake {VERSION} by melianmiko

This application can build and unpack Smart Band 7 & Amazfit Band 7
apps and watch faces. Give input file via drag to this application icon
to process them. And it will be processed, maybe.

If you push
- `bin`-file, we'll try to unpack them
- empty directory, we'll init an empty template inside them
- directory with `app.json`, we'll try to build it as project
- other directory or file, we'll try to convert it to PNG or back to TGA

https://melianmiko.ru/en/zmake
https://github.com/melianmiko/zmake
"""

if sys.platform == "win32":
    CONFIG_DIR = Path.home() / "AppData/Roaming"
elif sys.platform == "darwin":
    CONFIG_DIR = Path.home() / "Library/Application Support"
else:
    CONFIG_DIR = Path.home() / ".config"

BACKUP_DIR = CONFIG_DIR / "backup"
