import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image

from zmake.constants import BACKUP_DIR

if getattr(sys, 'frozen', False):
    APP_PATH = Path(os.path.dirname(sys.executable))
else:
    APP_PATH = Path(os.path.dirname(__file__))


def get_app_asset(name: str):
    with open(APP_PATH / "data" / name, "r") as f:
        data = f.read()
    return data


def increment_or_add(dictionary, key):
    if key not in dictionary:
        dictionary[key] = 1
        return

    dictionary[key] += 1


def image_color_compress(image: Image.Image, file: Path | None, log: logging.Logger):
    log.debug(f"Start color compression for {image.format} {image.mode}")

    # Save fallback
    if file is not None:
        if not BACKUP_DIR.exists():
            BACKUP_DIR.mkdir(parents=True)

        time_tag = str(datetime.today()).replace(' ', '_').replace(':', '')
        path = BACKUP_DIR / f"{time_tag}__{file.name}"
        log.warning(f"  [!] Color compression applied: {file}, backup at {path}")
        image.save(path)

    # Quantize
    is_rgb = True
    if image.mode == "RGBA":
        for a in image.getdata():
            if a[3] != 255:
                is_rgb = False
                break

    if is_rgb:
        image = image.convert("RGB").quantize(256).convert("RGBA")
    else:
        image = image.quantize(256)

    return image
