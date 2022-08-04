from PIL import Image


def save_tga(img: Image.Image, path: str, mode: int):
    """
    Write PIL image to TGA file

    :param img: source img
    :param path: dest path
    :param mode: save mode
    :return:
    """
    img = img.convert("RGBA")
    data = bytearray()

    palette = []
    if mode == 0:
        assert img.getcolors() is not None
        for _, val in img.getcolors():
            palette.append(val)

        while len(palette) < 256:
            palette.append((0, 0, 0, 255))

    # Build TGA header
    data.append(46)                                                     # ID len
    data.append(1 if mode == 0 else 0)                                  # Has colormap
    data.append(1 if mode == 0 else 2)                                  # Mode
    data.extend(b'\x00\x00')                                            # CM origin
    data.extend(len(palette).to_bytes(2, byteorder="little"))           # Palette length
    data.append(32 if mode == 0 else 0)                                 # Palette entry length, bits
    data.extend([0, 0, 0, 0])                                           # X\Y origin of image, locked
    data.extend(img.width.to_bytes(2, byteorder="little"))              # width
    data.extend(img.height.to_bytes(2, byteorder="little"))             # height
    data.append(8 if mode == 0 else mode)                               # mapped pixel size
    data.append(32)                                                     # misc

    # ID data
    data.extend(b"\x53\x4f\x4d\x48")
    data.extend(img.width.to_bytes(2, byteorder="little"))
    data.extend(b"\0" * 40)

    # Palette
    for r, g, b, a in palette:
        data.extend([b, g, r, a])

    # Image data
    for pixel in img.getdata():
        if mode == 0:
            index = palette.index(pixel)
            data.append(index)
        elif mode == 16:
            r = round(31/255 * pixel[0])
            g = round(63/255 * pixel[1])
            b = round(31/255 * pixel[2])
            data.append(((g & 0b111) << 5) + b)
            data.append((r << 3) + (g >> 3))

    with open(path, "wb") as f:
        f.write(data)


def load_tga(path: str):
    """
    Read TGA file and export to PIL.Image
    :param path: file path
    :return: PIL image
    """
    f = open(path, "rb")
    header = f.read(18)

    if header[2] == 2:
        return _load_truecolor_tga(f, header)
    elif header[2] == 1:
        return _load_palette_tga(f, header)

    raise ValueError("Not supported")


def _load_palette_tga(f, header):
    assert header[1] == 1
    assert header[2] == 1
    assert header[7] == 32

    id_length = header[0]
    palette_length = int.from_bytes(header[5:7], "little")
    width = int.from_bytes(header[12:14], "little")
    height = int.from_bytes(header[14:16], "little")

    # Skip ID
    f.read(id_length)

    palette_raw = bytearray()
    for i in range(palette_length):
        b, g, r, a = f.read(4)
        palette_raw.extend([r, g, b, a])

    # Read RAW img data
    img_data = f.read(width*height)

    image = Image.new("P", (width, height))
    image.putpalette(palette_raw, "RGBA")
    image.putdata(img_data)

    f.close()

    return image.convert("RGBA")


def _load_truecolor_tga(f, header):
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
