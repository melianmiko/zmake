import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

import image_io

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
        file_type = image_io.get_format(file)
        if file_type == "PNG":
            files_png += 1
            img, _ = image_io.load_auto(file)
            if not quantize_required and img.getcolors() is None:
                quantize_required = True
        elif file_type.startswith("TGA"):
            files_tga += 1

    if files_png == 0:
        return DIRECTION_PNG, False
    elif files_tga == 0:
        return DIRECTION_TGA, quantize_required
    else:
        return DIRECTION_ASK, quantize_required


def to_tga(paths: list[(Path, Path)]):
    for file, out in paths:
        img, file_type = image_io.load_auto(file)
        if file_type != "PNG" and file != out:
            print(file, "COPY WITHOUT CONVERT")
            shutil.copy(file, out)
            continue
        elif file_type != "PNG":
            print(file, "SKIP, NOT SUPPORTED")
            continue

        mode = "TGA-RLP"
        img = img.convert("RGBA")
        if file.name.endswith(".rgb.png"):
            mode = "TGA-16"

        if not img.getcolors() and mode == "TGA-RLP":
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

        print(file, file_type, "->", mode)
        image_io.save_auto(img, out, mode)


def to_png(paths: list[(Path, Path)]):
    for file, out in paths:
        img, file_type = image_io.load_auto(file)
        if file_type != "N/A":
            print(file, file_type, "-> PNG")
            img.save(out)
        elif file != out:
            print(file, "COPY WITHOUT CONVERT")
            shutil.copy(file, out)
        else:
            print(file, "SKIP, NOT SUPPORTED")

#
# if __name__ == "__main__":
#     img, t = image_io.load_auto(Path("test.png"))
#     image_io.save_auto(img, Path("test.tga"), "TGA-RLP")
#
#     img, _ = image_io.load_auto(Path("test.tga"))
#     image_io.save_auto(img, Path("test_r.png"), "PNG")
