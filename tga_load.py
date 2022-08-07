from PIL import Image


def _parse_tga_header(header):
    id_length = header[0]
    palette_length = int.from_bytes(header[5:7], "little")
    width = int.from_bytes(header[12:14], "little")
    height = int.from_bytes(header[14:16], "little")
    return id_length, palette_length, width, height


def _fetch_palette(f, palette_length):
    palette_raw = bytearray()
    for i in range(palette_length):
        b, g, r, a = f.read(4)
        palette_raw.extend([r, g, b, a])

    return palette_raw


def load_palette_tga(f):
    """
    Read Tga with DATA TYPE 1
    :param f: opened file
    :return: PIL image
    """
    header = f.read(18)

    assert header[1] == 1
    assert header[2] == 1
    assert header[7] == 32

    # Skip ID
    id_length, palette_length, width, height = _parse_tga_header(header)
    f.read(id_length)

    # Read RAW img data
    palette_raw = _fetch_palette(f, palette_length)
    img_data = f.read(width*height)

    image = Image.new("P", (width, height))
    image.putpalette(palette_raw, "RGBA")
    image.putdata(img_data)

    return image.convert("RGBA")


def load_rl_palette_tga(f):
    """
    Read Tga with DATA TYPE 9
    :param f: opened file
    :return: PIL image
    """
    header = f.read(18)

    assert header[1] == 1
    assert header[2] == 9
    assert header[7] == 32

    # Skip ID
    id_length, palette_length, width, height = _parse_tga_header(header)
    f.read(id_length)

    # Read RAW img data
    palette_raw = _fetch_palette(f, palette_length)
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


def load_truecolor_tga(f):
    """
    Read TGA with DATA TYPE 2
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

            unpacked.append((int(r * 255/31),
                             int(g * 255/63),
                             int(b * 255/31)))
    else:
        raise Exception("Not implemented")

    image = Image.new("RGB", (width, height))
    # noinspection PyTypeChecker
    image.putdata(unpacked)
    return image
