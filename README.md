
![Icon](docs/logo_docs.png) ZMake 
--------------------------------

*(aka. ZeppOS Make)*

Unofficial ZeppOS build tool. This application was developed
for community-driven watchface and application development
for Xiaomi Smart Band 7. But you also can use it for any other
ZeppOS-device, if want.

It can:
- Convert PNG images into ZeppOS-specific TGA and back
- Build JS code with `esbuild` and/or `uglifyjs`
- Automatically generate preview, if `zepp-preview` is installed
- Automatically build an installation-ready `bin`-file

Installation & Usage
--------------------

Prebuild binaries can be downloaded 
[here](https://melianmiko.ru/en/zmake).
Unpack downloaded ZIP somewhere. And that's all.

Windows and macOS users can run program via drag and  drop. 
Just drag file to process to application icon.

Linux's users should call zmake from terminal. Open terminal
in application folder and just run:

    ./zmake file_to_process

**But in first of all, set `encode_mode` for your device.**
Different Amazfit devices has some differences in their graphic encoding formats.
By default, ZMake is configured to work with Mi Band 7, but if you want to use them with other
device, change `encode_mode` in `zmake.json` to match your device:

| `encode_mode`       | Devices                                            |
|---------------------|----------------------------------------------------|
| `dialog`            | Mi Band 7, Amazfit Band 7, Amazfit GTS 4 Mini      |
| `nxp`               | GTS 3/4, GTR 3/4, GTR 3 Pro, T-Rex 2/Ultra, Falcon |
| Not supported (MHS) | GTR Mini                                           |

What they can do?
-----------------

Action to be taken by application depends on what you 
give to the input.

| You give...                                                | ZMake will...                                                                                            |
|------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **App/watchface as bin-file**                              | unpack this file and convert all graphic assets into PNG. New folder appear near source bin-file         |
| **Empty directory**                                        | generate new project template inside this folder. Type of project will be asked in prompt.               |
| **Unpacked app/watchface**(directory with app.json inside) | build your project, see action order bellow.                                                             |
| **Any other files/directories**                            | try to convert them into PNG or ZeppOS TGA. Direction will be asked, if can't be detected automatically. |

What actions will be performed when you attempt to build a project
1.  Convert all graphics to ZeppOS TGA
2.  If `src` dir exists, combine files into `index.js`
3.  If enabled, process all files in `page/watchface` dir via esbuild
4.  If enabled, process all files in `page/watchface` dir via uglifyjs
5.  If enabled, will create preview image via ZeppPlayer
6.  If enabled, will place smaller preview into assets dir
7.  If enabled, will upload result watchface to your phone via ADB |

Graphics processing
----------------------

ZeppOS support images compressed in different ways. 
So, you can describe how zmake should process some 
images. When converting PNG to TGA, app selects 
compression method due to filename ending. There 
is a list of available compression options with 
some notices.

| Name...     | Format     | Description                                                                                                                                                                                                                                                                                                                           |
|-------------|------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `.p.png`    | `TGA-P`    | Palette-encoded image. You can use any RGBA colors inside your image, but single image can't contain more than 256 different colors (one color with different transparency layer wasn't the same color). No specific compression will be applied. Final image filesize will be `64 + (count_of_colors * 4) + (width * height)` bytes. |
| `.rlp.png`  | `TGA-RLP`  | Same as `TGA-P`, but also use per-line pixel compression. E.g. same pixels in one line will be written once. But images encoded in that way can't be rotated, so don't use this format for clock pointers.                                                                                                                            |
| `.rgb.png`  | `TGA-16`  | 16-bit RGB images, e.g. 5-6 bits per channel. Images in that format can't contain transparent parts. File size will be `64 + (2 * width * height)` bytes.                                                                                                                                                                             |
| `.rgba.png` | `TGA-32` | Full 32-bit RGBA image, e.g. 8 bit for channel. No color limitations, but very big file size: `64 + (4 * width * height)` bytes.                                                                                                                                                                                                      |

If you don't set compression format via filename, default
will be used (TGA-P).

If some images have too much colors for TGA-RLP/TGA-P, they 
will be automatically quantized. Backup file will appear in 
backup directory near application.

Build from source code
-----------------------

Python 3.10+ with pip and venv is required.

### Windows/linux
```bash
git clone https://github.com/melianmiko/zmake.git
cd zmake
python3 -m venv venv
pip3 install -r requirements.txt
python3 make_release.py
```

Result will appear in `dist` directory.

### macOS
```bash
# Grab sources
git clone https://github.com/melianmiko/zmake.git
cd zmake

# Create and activate venv
python3.10 -m venv venv
source venv/bin/active

# Install deps and build
pip install -r requirements.txt
python make_release.py
```

Result will appear in `dist` directory.

Donate
-------

If you're from Russia, Belarus or other near country
[look here](https://melianmiko.ru/donate/).

Due to all known reasons I can't receive donations from
other countries for now, only in cryptocurrency. Or,
if you're in Turkey, to OlduBill virtual card. List
of actual addresses can be seen 
[here](https://melianmiko.ru/en/donate).

License
---------

    zmake - Unofficial ZeppOS build tool
    Copyright (C) 2022 MelianMiko <melianmiko@yandex.ru>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
