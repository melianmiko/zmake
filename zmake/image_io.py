from pathlib import Path

from PIL import Image

from zmake import tga_save, tga_load

PNG_SIGNATURE = b"\211PNG"


def get_format(path: Path):
    with path.open("rb") as f:
        header = f.read(4)

        if header == PNG_SIGNATURE:
            return "PNG"
        elif header[2] == 2:
            return "TGA-16"
        elif header[2] == 1:
            return "TGA-P"
        elif header[2] == 9:
            return "TGA-RLP"
        else:
            return None, "N/A"


def load_auto(path: Path):
    with path.open("rb") as f:
        header = f.read(4)
        f.seek(0)

        if header == PNG_SIGNATURE:
            return Image.open(path), "PNG"
        elif header[2] == 2:
            return tga_load.load_truecolor_tga(f)
        elif header[2] == 1:
            return tga_load.load_palette_tga(f), "TGA-P"
        elif header[2] == 9:
            return tga_load.load_rl_palette_tga(f), "TGA-RLP"
        else:
            return None, "N/A"


def save_auto(img: Image.Image, out: Path, dest_type: str):
    if dest_type == "PNG":
        img.save(out)
        return True
    elif dest_type == "TGA-P":
        tga_save.save_palette_tga(img, out)
        return True
    elif dest_type == "TGA-16":
        tga_save.save_truecolor_tga(img, out, 16)
        return True
    elif dest_type == "TGA-32":
        tga_save.save_truecolor_tga(img, out, 32)
        return True
    elif dest_type == "TGA-RLP":
        tga_save.save_rl_palette_tga(img, out)
        return True
    else:
        return False
