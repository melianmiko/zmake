from zmake.context import ZMakeContext
import zmake.project_build

VERSION = "v1.6-dev"

GUIDE = f"""zmake {VERSION} by melianmiko
https://melianmiko.ru/zmake

This application can build and unpack Smart Band 7 & Amazfit Band 7
apps and watch faces. Give input file via drag to this application icon
to process them. And it will be processed, maybe.

If you push
- `bin`-file, we'll try to unpack them
- empty directory, we'll init an empty template inside them
- directory with `app.json`, we'll try to build it as project
- other directory or file, we'll try to convert it to PNG or back to TGA
"""
