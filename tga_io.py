from PIL import Image

ID_LENGTH = 46
ID_DATA = b"SOMH\80".ljust(ID_LENGTH, b'\0')


def save_tga(img: Image.Image, path: str):
    """
    Write PIL image to TGA file

    :param img: source img
    :param path: dest path
    :return:
    """
    img = img.convert("RGBA")
    data = bytearray()

    assert img.getcolors() is not None

    palette = []
    for _, val in img.getcolors():
        palette.append(val)

    img_data = []
    for pixel in img.getdata():
        index = palette.index(pixel)
        img_data.append(index)

    while len(palette) < 256:
        palette.append((0, 0, 0, 255))

    # Build TGA header
    data.extend(b"\x2e\x01\x01\x00\x00")                                     # Base
    data.extend(len(palette).to_bytes(2, byteorder="little"))                # Palette length
    data.extend([32])                                                        # Palette entry length, bits
    data.extend([0, 0, 0, 0])                                                # X\Y origin of image, locked
    data.extend(img.width.to_bytes(2, byteorder="little"))                   # width
    data.extend(img.height.to_bytes(2, byteorder="little"))                  # height
    data.append(8)                                                           # mapped pixel size
    data.append(32)                                                          # idk

    # ID data
    data.extend(b"\x53\x4f\x4d\x48")
    data.extend(img.width.to_bytes(2, byteorder="little"))
    data.extend(b"\0" * 40)

    for r, g, b, a in palette:
        data.extend([b, g, r, a])

    data.extend(img_data)

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
