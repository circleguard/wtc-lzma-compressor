import lzma
import struct
import compression

import numpy as np

def compress(lzma_stream):
    """
    Packs replay into a more compact format.

    Args:
        String lzma_stream: An lzma stream from a replay.

    Returns:
        An lzma compressed bytestring
    """

    #separate the lzma stream to apply different compression for each datatype
    xs, ys, zs, ws = separate(lzma_stream)

    xs = compression.unsorted_diff_pack_16_8(xs)
    ys = compression.unsorted_diff_pack_16_8(ys)
    zs = compression.scolvr(zs)
    ws = compression.pack_32_8(ws)

    bx = compression.pack_bytes(xs)
    by = compression.pack_bytes(ys)
    bz = compression.pack_words(zs)
    bw = compression.pack_bytes(ws)

    buf = b''.join((bx, by, bz, bw))

    return lzma.compress(buf, format=2)

def decompress(compressed_lzma):
    """
    Decompresses a separated and compressed lzma into an lzma stream.

    Args:
        String compressed_lzma: A separated and compressed representation of replay data.

    Returns:
        An lzma compressed bytestring, identical to the (decoded) string returned by the get_replay api endpoint.
    """

    data = lzma.decompress(compressed_lzma)
    
    xs, data = compression.unpack_bytes(data)
    ys, data = compression.unpack_bytes(data)
    zs, data = compression.unpack_words(data)
    ws, data = compression.unpack_bytes(data)

    xs = compression.unsorted_diff_unpack_8_16(xs)
    ys = compression.unsorted_diff_unpack_8_16(ys)
    zs = compression.olvsco(zs)
    ws = compression.unpack_8_32(ws)

    return combine(xs, ys, zs, ws)

def separate(lzma_stream):
    """
    Separates the lzma stream of frames into separate lists of x, y, z and w.

    Args:
        String lzma_stream: The lzma to separate.

    Returns:
        The lists of x, y, z, w.
    """
    text = lzma.decompress(lzma_stream).decode('UTF-8')

    xs = []
    ys = []
    zs = []
    ws = []

    for frame in text.split(','):
        if not frame:
            continue
        w, x, y, z = frame.split('|')
        w = int(w)
        x = float(x)
        y = float(y)
        z = int(z)

        #Everything we need from Z is in the first byte
        z = z & 0xFF

        #To fit x and y into shorts, they can be scaled to retain more precision.
        x = int(round(x * 16))
        y = int(round(y * 16))

        #Prevent the coordinates from being too large for a short. If this happens, the cursor is way offscreen anyway.
        if x <= -0x8000: x = -0x8000
        elif x >= 0x7FFF: x = 0x7FFF
        if y <= -0x8000: y = -0x8000
        elif y >= 0x7FFF: y = 0x7FFF

        #w: signed 24bit integer
        #x: signed short
        #y: signed short
        #z: unsigned char
        xs.append(x)
        ys.append(y)
        zs.append(z)
        ws.append(w)

    return xs, ys, zs, ws

def combine(xs, ys, zs, ws):
    """
    Combines the lists of x, y, z and w into a lzma stream.

    Args:
        List x: All x datapoints.
        List y: All y datapoints.
        List z: All z datapoints.
        List w: All w datapoints.

    Returns:
        The combination as an lzma stream.
    """

    if not len(xs) == len(ys) == len(zs) == len(ws):
        raise ValueError("The bytearrays are of unequal lengths")

    xs = np.array(xs) / 16
    ys = np.array(ys) / 16

    frames = zip(xs, ys, zs, ws)

    frames = [f'{w}|{x}|{y}|{z},' for x, y, z, w in frames]

    output = ''.join(frames)

    return lzma.compress(output.encode('UTF-8'), format=2)
