import logging
import sys
from pathlib import Path

from PIL import Image

from zmake import tga_save, tga_load

log = logging.getLogger("ImageIo")

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
            return "N/A"


def load_auto(path: Path, encode_mode):
    with path.open("rb") as f:
        header = f.read(4)
        f.seek(0)

        if header == PNG_SIGNATURE:
            return Image.open(path), "PNG"
        elif header[1] == 0 and header[2] == 2:
            log.debug("Load as truecolor TGA")
            return tga_load.load_truecolor_tga(f, encode_mode)
        elif header[1] == 1 and header[2] == 1:
            log.debug("Load as palette TGA")
            return tga_load.load_palette_tga(f, encode_mode), "TGA-P"
        elif header[1] == 1 and header[2] == 9:
            log.debug("Load as palette RLP TGA")
            return tga_load.load_rl_palette_tga(f, encode_mode), "TGA-RLP"
        else:
            return None, "N/A"


def save_auto(img: Image.Image, out: Path, dest_type: str, encode_mode):
    if dest_type == "PNG":
        img.save(out)
        return True
    elif dest_type == "TGA-P":
        tga_save.save_palette_tga(img, out, encode_mode)
        return True
    elif dest_type == "TGA-16":
        tga_save.save_truecolor_tga(img, out, 16, encode_mode)
        return True
    elif dest_type == "TGA-32":
        tga_save.save_truecolor_tga(img, out, 32, encode_mode)
        return True
    elif dest_type == "TGA-RLP":
        tga_save.save_rl_palette_tga(img, out, encode_mode)
        return True
    else:
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    img_path = Path(sys.argv[1]).resolve()
    img_fmt = get_format(img_path)
    if img_fmt == "PNG":
        log.debug("PNG -> TGA-P result.png")
        save_auto(Image.open(img_path), Path("result.png"), "TGA-P")
    else:
        log.debug("ANY -> PNG result.png")
        load_auto(img_path)[0].save("result.png")
