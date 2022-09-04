import os
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image

if getattr(sys, 'frozen', False):
    APP_PATH = Path(os.path.dirname(sys.executable))
else:
    APP_PATH = Path(os.path.dirname(__file__))


def get_app_asset(name: str):
    with open(APP_PATH / "data" / name, "r") as f:
        data = f.read()
    return data


def image_color_compress(image: Image.Image, file: Path | None):
    # Save fallback
    if file is not None:
        print(f"WARN: Color compression applied: {file}")
        time_tag = str(datetime.today()).replace(' ', '_').replace(':', '')
        path = APP_PATH / "backup" / f"{time_tag}__{file.name}"
        print(f"Backup at {path}")
        image.save(path)

    # Quantize
    is_rgb = True
    for a in image.getdata():
        if a[3] != 255:
            is_rgb = False
            break

    if is_rgb:
        image = image.convert("RGB").quantize(256).convert("RGBA")
    else:
        image = image.quantize(256)

    return image