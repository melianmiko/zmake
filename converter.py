import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image

import tga_io

DIRECTION_TGA = True
DIRECTION_PNG = False
DIRECTION_ASK = None


def get_backup_path():
    if getattr(sys, 'frozen', False):
        file_path = os.path.dirname(sys.executable)
    else:
        file_path = os.path.dirname(__file__)

    backup_path = file_path + "/backups"
    if not os.path.isdir(backup_path):
        os.mkdir(backup_path)

    return Path(backup_path)


def load_from_path(path: Path):
    paths = []

    if not path.exists():
        return []

    if path.is_file():
        paths.append((path, path))
        return paths

    for file in path.rglob("*.png"):
        # source == dest
        paths.append((file, file))

    return paths


def prepare_config(paths: list[(Path, Path)]):
    quantize_required = False
    files_tga = 0
    files_png = 0

    for file, _ in paths:
        with file.open("rb") as f:
            if b"PNG" in f.read(4):
                files_png += 1
                if not quantize_required:
                    # Check color limit
                    pil = Image.open(file)
                    if pil.getcolors() is None:
                        quantize_required = True
            else:
                files_tga += 1

    if files_png == 0:
        return DIRECTION_PNG, False
    elif files_tga == 0:
        return DIRECTION_TGA, quantize_required
    else:
        return DIRECTION_ASK, quantize_required


def to_tga(paths: list[(Path, Path)]):
    for file, out in paths:
        img = Image.open(file)
        mode = 0

        if img.format != "PNG":
            print("SKIP: Already converted or not supported", file)
            if file != out:
                print("Copy as RAW")
                shutil.copy(file, out)
            continue

        img = img.convert("RGBA")
        if file.name.endswith(".rgb.png"):
            print(f"WARN: Compress colors to 16bit")
            mode = 16

        if not img.getcolors() and mode == 0:
            print(f"WARN: Color compression applied: {file}")

            # Save fallback
            t = str(datetime.today()).replace(' ', '_').replace(':', '')
            path = get_backup_path() / f"{t}__{file.name}"
            img.save(path)

            # Quantize
            is_rgb = True
            for a in img.getdata():
                if a[3] != 255:
                    is_rgb = False
                    break

            if is_rgb:
                img = img.convert("RGB").quantize(256).convert("RGBA")
            else:
                print("WARN: Color compression applied to image with transparent parts.")
                img = img.quantize(256)

        tga_io.save_tga(img, str(out), mode)


def to_png(paths: list[(Path, Path)]):
    for file, out in paths:
        try:
            img = tga_io.load_tga(str(file))
            img.save(out)
        except AssertionError:
            print("SKIP: Already converted or not supported:", file)
            if file != out:
                print("Copy as RAW")
                shutil.copy(file, out)
