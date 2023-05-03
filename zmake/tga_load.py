from PIL import Image
import logging

log = logging.getLogger("TgaLoad")


def _apply_zepp_header(image: Image.Image, id_data: bytes):
    if len(id_data) < 46 or id_data[0:4] != b"SOMH":
        return

    # Use width from ZeppOS ID string
    # GTR/GTS/AB compatibility
    zepp_width = int.from_bytes(id_data[4:6], "little")
    if zepp_width != image.width:
        log.debug(f"use width from tga header, zepp_width={zepp_width}")
        image = image.crop((0, 0, zepp_width, image.height))
    return image


def _parse_tga_header(header):
    palette_length = int.from_bytes(header[5:7], "little")
    width = int.from_bytes(header[12:14], "little")
    height = int.from_bytes(header[14:16], "little")

    log.debug(f"palette_length={palette_length}, size={width}x{height}")
    return palette_length, width, height


def _fetch_palette(f, palette_length, swap_red_and_blue):
    palette_raw = bytearray()
    for i in range(palette_length):
        if swap_red_and_blue:
            r, g, b, a = f.read(4)
        else:
            b, g, r, a = f.read(4)
        palette_raw.extend([r, g, b, a])

    return palette_raw


def load_palette_tga(f, swap_red_and_blue=False):
    """
    Read Tga with DATA TYPE 1
    :param swap_red_and_blue: Swap red and blue channels (some devices require that)
    :param f: opened file
    :return: PIL image
    """
    header = f.read(18)

    assert header[1] == 1
    assert header[2] == 1
    assert header[7] == 32

    # Skip ID
    id_length = header[0]
    id_data = f.read(id_length)
    palette_length, width, height = _parse_tga_header(header)

    # Read RAW img data
    palette_raw = _fetch_palette(f, palette_length, swap_red_and_blue)
    img_data = f.read(width*height)
    if len(f.peek()) > 0:
        log.debug("WARNING: NOT ALL DATA PARSED, looks like it's a bug")
        log.debug(f"peek_size={len(f.peek())}")

    image = Image.new("P", (width, height))
    image.putpalette(palette_raw, "RGBA")
    image.putdata(img_data)

    image = _apply_zepp_header(image, id_data)

    return image.convert("RGBA")


def load_rl_palette_tga(f, swap_red_and_blue=False):
    """
    Read Tga with DATA TYPE 9
    :param swap_red_and_blue: Swap red and blue channels (some devices require that)
    :param f: opened file
    :return: PIL image
    """
    header = f.read(18)

    assert header[1] == 1
    assert header[2] == 9
    assert header[7] == 32

    # Skip ID
    id_length = header[0]
    id_data = f.read(id_length)
    palette_length, width, height = _parse_tga_header(header)

    # Read RAW img data
    palette_raw = _fetch_palette(f, palette_length, swap_red_and_blue)
    img_data = bytearray()

    while len(img_data) < width * height:
        pkg_head = f.read(1)[0]
        count = (pkg_head & 127) + 1
        if pkg_head & 128:
            # RL pkg
            index = f.read(1)[0]
            # print("Read RL", pkg_head, index)
            for i in range(count):
                img_data.append(index)
        else:
            # RAW pkg
            # print("Read RGB", pkg_head)
            for i in range(count):
                val = f.read(1)[0]
                # print(val)
                img_data.append(val)

    image = Image.new("P", (width, height))
    image.putpalette(palette_raw, "RGBA")
    image.putdata(img_data)

    return image.convert("RGBA")


def load_truecolor_tga(f, swap_red_and_blue=False):
    """
    Read TGA with DATA TYPE 2
    :param swap_red_and_blue: Swap red and blue channels (some devices require that)
    :param f: opened file
    :return: PIL image
    """
    header = f.read(18)

    assert header[1] == 0
    assert header[2] == 2

    colormode = header[16]
    id_length = header[0]
    width = int.from_bytes(header[12:14], "little")
    height = int.from_bytes(header[14:16], "little")

    # Skip ID
    f.read(id_length)

    if colormode == 16:
        unpacked = []
        for i in range(height * width):
            b2, b1 = f.read(2)
            v = (b1 << 8) + b2
            r = (v & 0b1111100000000000) >> 11
            g = (v & 0b0000011111100000) >> 5
            b = v & 0b0000000000011111

            if swap_red_and_blue:
                r, b = b, r

            unpacked.append((int(r * 255/31),
                             int(g * 255/63),
                             int(b * 255/31),
                             255))
    elif colormode == 32:
        unpacked = []
        for i in range(height * width):
            if swap_red_and_blue:
                r, g, b, a = f.read(4)
            else:
                b, g, r, a = f.read(4)
            unpacked.append((r, g, b, a))
    else:
        raise Exception("Not implemented")

    image = Image.new("RGBA", (width, height))
    # noinspection PyTypeChecker
    image.putdata(unpacked)

    return image, f"TGA-{colormode}"
