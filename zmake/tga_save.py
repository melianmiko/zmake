from pathlib import Path

from PIL import Image


def save_truecolor_tga(img: Image.Image, path: Path, depth, encode_mode="dialog"):
    img = img.convert("RGBA")
    data = bytearray()

    data.append(46)                                                     # ID len
    data.append(0)                                                      # Has colormap
    data.append(2)                                                      # Mode
    data.extend(b'\x00' * 9)                                            # Palette config, origin
    data.extend(img.width.to_bytes(2, byteorder="little"))              # width
    data.extend(img.height.to_bytes(2, byteorder="little"))             # height
    data.append(depth)                                                  # color mode
    data.append(32)                                                     # misc

    # ID data
    data.extend(b"\x53\x4f\x4d\x48")
    data.extend(img.width.to_bytes(2, byteorder="little"))
    data.extend(b"\0" * 40)

    # Image data
    if depth == 16:
        for pixel in img.getdata():
            r = round(31/255 * pixel[0])
            g = round(63/255 * pixel[1])
            b = round(31/255 * pixel[2])

            if encode_mode == "nxp":
                r, b = b, r

            data.append(((g & 0b111) << 5) + b)
            data.append((r << 3) + (g >> 3))
    elif depth == 32:
        for r, g, b, a in img.getdata():
            if encode_mode == "nxp":
                data.extend([r, g, b, a])
            else:
                data.extend([b, g, r, a])
    else:
        raise ValueError("Not supported")

    with open(path, "wb") as f:
        f.write(data)


def _prep_palette_base(img, encode_mode):
    """
    Prepare data with palette header and data.

    :param img: Source image
    :return: bytes and palette
    """
    data = bytearray()

    # TGA Width fix
    real_width = img.width
    if encode_mode == "nxp" and real_width % 16 != 0:
        tga_width = real_width + 16 - (real_width % 16)
        assert tga_width % 16 == 0
        new_img = Image.new(img.mode, (tga_width, img.height))
        new_img.paste(img)
        img = new_img

    # Palette data
    palette = []
    assert img.getcolors() is not None

    for _, val in img.getcolors():
        palette.append(val)

    while len(palette) < 256:
        palette.append((0, 0, 0, 255))

    # Build TGA header
    data.append(46)                                                     # ID len
    data.append(1)                                                      # Has colormap
    data.append(1)                                                      # Mode
    data.extend(b'\x00\x00')                                            # CM origin
    data.extend(len(palette).to_bytes(2, byteorder="little"))           # Palette length
    data.append(32)                                                     # Palette entry length, bits
    data.extend([0, 0, 0, 0])                                           # X\Y origin of image, locked
    data.extend(img.width.to_bytes(2, byteorder="little"))              # width
    data.extend(img.height.to_bytes(2, byteorder="little"))             # height
    data.append(8)                                                      # mapped pixel size
    data.append(32)                                                     # misc

    # ID data
    data.extend(b"\x53\x4f\x4d\x48")
    data.extend(real_width.to_bytes(2, byteorder="little"))
    data.extend(b"\0" * 40)

    # Palette
    for r, g, b, a in palette:
        if encode_mode == "nxp":
            value = r, g, b, a
        else:
            value = b, g, r, a
        data.extend(value)

    return img, data, palette


def save_rl_palette_tga(img: Image.Image, path: Path, encode_mode="dialog"):
    """
    Write PIL image to TGA file with DATA TYPE 9

    :param encode_mode:
    :param img: source img
    :param path: dest path
    :return:
    """
    img = img.convert("RGBA")
    img, data, palette = _prep_palette_base(img, encode_mode)
    data[2] = 9

    # Image data
    out = bytearray(b"\x00")
    head_index = 0

    for pixel in img.getdata():
        index = palette.index(pixel)
        head = out[head_index]
        if len(out) == 1:
            # First index
            out.append(index)
        elif head & 128 and index == out[-1] and head < 255:
            # Add to exiting RL pkg
            out[head_index] += 1
        elif out[-1] == index and head_index != len(out) - 1:
            # Create new RL package here
            if head == 0:
                # Empty RGB
                out[head_index] += 128 + 1
            else:
                out[head_index] -= 1
                if head_index == len(out) - 2:
                    out.append(index)
                head_index = len(out) - 1
                out[head_index] = 128 + 1
                out.append(index)
        elif head < 127:
            # Add to exiting RGB pkg
            out.append(index)
            out[head_index] += 1
        else:
            # Start new RGB pkg
            out.append(0)
            out.append(index)
            head_index = len(out) - 2

    data.extend(out)
    with open(path, "wb") as f:
        f.write(data)


def save_palette_tga(img: Image.Image, path: Path, encode_mode="dialog"):
    """
    Write PIL image to TGA file with DATA TYPE 1

    :param encode_mode: Swap red and blue channels
    :param img: source img
    :param path: dest path
    :return:
    """
    img = img.convert("RGBA")
    img, data, palette = _prep_palette_base(img, encode_mode)

    # Image data
    for pixel in img.getdata():
        index = palette.index(pixel)
        data.append(index)

    with open(path, "wb") as f:
        f.write(data)
