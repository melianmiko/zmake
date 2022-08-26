import json
import os
import random
import shutil
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from PIL import Image

import build_tool
import converter
import image_io

VERSION = "1.3"
INCLUDE_FILES = [
    "app.json",
    "README.txt",
    "LICENSE.txt",
    "README",
    "LICENSE"
]

if getattr(sys, 'frozen', False):
    DATA_PATH = os.path.dirname(sys.executable) + "/data"
elif __file__:
    DATA_PATH = os.path.dirname(__file__) + "/data"


def perform_new(path: Path):
    inp = ""
    while inp not in ["w", "a"]:
        inp = input("Type: W - watchface, A - app?").lower()

    with open(f"{DATA_PATH}/app_{inp}.json", "r") as f:
        app_json = json.load(f)

    app_json['app']['appId'] = random.randint(1000, 100000)
    app_json['app']['appName'] = path.name
    app_json['app']['vender'] = os.getlogin()

    with (path / "app.json").open("w") as f:
        f.write(json.dumps(app_json, indent=2, sort_keys=True))

    (path / "assets").mkdir()
    (path / "src").mkdir()
    (path / "lib").mkdir()
    shutil.copy(f"{DATA_PATH}/template_index_{inp}.js", path / "src/index.js")


def perform_build(path: Path):
    basename = path.name

    with open(f"{DATA_PATH}/config.json", "r") as f:
        config = json.load(f)
    with open(f"{DATA_PATH}/basement.js", "r") as f:
        basement = f.read()
    with open(f"{DATA_PATH}/comment.js", "r") as f:
        comment = f.read()
    with open(f"{DATA_PATH}/infos.xml", "r") as f:
        infos = f.read()

    if (path / "build").is_dir():
        shutil.rmtree(path / "build")
    if (path / "dist").is_dir():
        shutil.rmtree(path / "dist")

    # Base
    (path / "build").mkdir()
    build_tool.mk_assets(path, config["def_format"])

    for fn in INCLUDE_FILES:
        p = path / fn
        if p.exists():
            print("Copy file", fn)
            shutil.copy(p, path / "build" / fn)

    # AppJS
    if (path / "app.js").is_file():
        if config["esbuild"]:
            build_tool.mk_esbuild(path / "app.js",
                                  path / "build",
                                  config["esbuild_params"],
                                  comment)
        else:
            shutil.copy(path / "app.js", path / "build/app.js")
    else:
        shutil.copy(f"{DATA_PATH}/app.js", path / "build/app.js")

    # Fetch config
    with open(path / "app.json", "r", encoding="utf8") as f:
        app_config = json.loads(f.read())

    target_dir = "watchface"
    if app_config["app"]["appType"] == "app":
        target_dir = "page"

    # Watchface JS
    if (path / target_dir).is_dir():
        if config["esbuild"]:
            print(f"-- Process exiting {target_dir} with esbuild")
            build_tool.mk_esbuild(path / target_dir,
                                  path / "build" / target_dir,
                                  config["esbuild_params"],
                                  comment)
        else:
            print(f"-- Copy exiting '{target_dir}' dir")
            shutil.copytree(path / target_dir, path / 'build' / target_dir)

    if (path / 'src').is_dir():
        content = build_tool.mk_js_content(path)
        content = basement.replace("{content}", content)
        if config["with_uglifyjs"]:
            content = build_tool.mk_run_uglify(content, config['uglifyjs_params'])

        out_dir = path / "build" / target_dir
        if not out_dir.exists():
            out_dir.mkdir()

        with (out_dir / "index.js").open("w") as f:
            f.write(comment + "\n")
            f.write(f"// Build at {datetime.today()}\n")
            f.write(content)

    # Dist folder
    (path / "dist").mkdir()

    # Preview
    dist_preview = None
    try:
        if config["mk_preview"]:
            build_tool.mk_preview(path)
            dist_preview = path / "dist/preview.png"

            if config["add_preview_asset"] and target_dir == "watchface":
                print("-- Add preview.png (128x326) to assets")
                pv = Image.open(path / "dist/preview.png")
                pv.thumbnail((128, 326))
                pv = pv.convert("RGB").quantize(256)
                image_io.save_auto(pv, path / "build/assets/preview.png", "TGA-RLP")
    except AssertionError:
        print("PREVIEW FAILED")

    # BIN
    print("-- Make bin file")
    dist_bin = path / "dist" / f"{basename}.bin"
    with ZipFile(dist_bin, "w", ZIP_DEFLATED) as arc:
        for file in (path / "build").rglob("**/*"):
            fn = str(file)[len(str(path / "build")):]
            arc.write(file, fn)

    # ZIP
    print("-- Make publish-ready ZIP file")
    dist_infos = path / "dist/infos.xml"
    with dist_infos.open("w") as f:
        f.write(infos.replace("{name}", basename))

    dist_zip = path / "dist" / f"{basename}.zip"
    with ZipFile(dist_zip, "w", ZIP_DEFLATED) as arc:
        arc.write(dist_bin, f"{basename}/{basename}.bin")
        arc.write(dist_infos, f"{basename}/infos.xml")
        if dist_preview is not None:
            arc.write(dist_preview, f"{basename}/{basename}.png")

    # Autoinstall
    if config["adb_install"]:
        print("-- Install via ADB")
        path = config["adb_path"]
        subprocess.Popen(["adb", "shell", "mkdir", "-p", path]).wait()
        subprocess.Popen(["adb", "push", dist_zip, path]).wait()
        subprocess.Popen(["adb", "shell", f"cd {path} && unzip -o {basename}.zip"]).wait()
        subprocess.Popen(["adb", "shell", "rm", f"{path}/{basename}.zip"]).wait()

    print('')
    print("Complete")


def perform_convert(path: Path):
    with open(f"{DATA_PATH}/config.json", "r") as f:
        config = json.load(f)

    paths = converter.load_from_path(path)

    print("-- Preparing --")
    direction, quantize_required = converter.prepare_config(paths)
    if quantize_required:
        print("WARN: Color compression will be applied to some images.")
        print(f"We will make backup in {converter.get_backup_path()}")
        print()

    if direction == converter.DIRECTION_ASK:
        print("This dir contains both converted and non-converted images")
        print("Tell what do you want:")
        print("1 - PNG -> TGA")
        print("2 - TGA -> PNG")
        v = ""
        while v not in ["1", "2"]:
            v = input("Enter your choice [1,2]: ")
        direction = v == "1"

    print(f"-- Convert {len(paths)} file(s) --")
    if direction == converter.DIRECTION_TGA:
        converter.to_tga(paths, config["def_format"])
    elif direction == converter.DIRECTION_PNG:
        converter.to_png(paths)


def process_unpack(path: Path):
    dest = Path(str(path)[:-4])
    if dest.is_dir():
        print("Folder already exit.")
        return
    dest.mkdir()

    with ZipFile(path, "r") as f:
        f.extractall(dest)
    perform_convert(dest / "assets")


def process():
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
        return

    path = Path(sys.argv[1]).resolve()

    if path.name.endswith(".bin"):
        print("We think that you want to unpack this file")
        process_unpack(path)
    elif path.is_dir() and next(path.iterdir(), False) is False:
        print("We think that you want to create new project in this empty dir")
        perform_new(path)
    elif path.is_dir() and build_tool.is_project(path):
        print("We think that you want... build this project")
        perform_build(path)
    else:
        print("We think that you want... convert some images")
        perform_convert(path)


if __name__ == "__main__":
    # noinspection PyBroadException
    try:
        process()
    except Exception:
        traceback.print_exc()
        print("FAILED")
        input()

