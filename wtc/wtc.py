import lzma
import struct

import numpy as np

def unsorted_diff_pack_16_8(int16s):
    """
    Packs the differential of the input to bytes in little endian order.

    Args:
        List ints16s: The list of shorts to differentially compress.

    Returns:
        The differential data as a list of bytes.
    """

    escape = -2 ** 7
    small = 2 ** 7 - 1
    start = int16s[0]
    diff = np.diff(int16s)
    packed = []

    def pack(word):
        if abs(word) <= small:
            packed.append(word)
        else:
            packed.append(escape)
            packed.append(word & 0xFF)
            word = word >> 8
            packed.append(word)

    pack(start)
    for word in diff:
        pack(word)

    return np.int8(packed)

def unsorted_diff_unpack_8_16(ints8):
    """
    Unpacks the differential data in little endian order to words.

    Args:
        List ints8s: The list of bytes to decompress.

    Returns:
        The decompressed shorts.
    """

    escape = -2 ** 7
    decoded = []

    i = 0
    while i < len(ints8):
        byte = ints8[i]

        if byte == escape:
            i += 1
            word = ints8[i] & 0xFF
            i += 1
            word += ints8[i] << 8
            decoded.append(word)
        else:
            decoded.append(byte)

        i += 1

    decompressed = np.cumsum(decoded)

    return np.int16(decompressed)

def pack_32_8(ints32):
    """
    Packs the input to bytes in little endian order.

    Args:
        List ints32s: The list of shorts to compress.

    Returns:
        The data as a list of bytes.
    """

    escape = -2 ** 7
    small = 2 ** 7 - 1
    packed = []

    for dword in ints32:
        if abs(dword) <= small:
            packed.append(dword)
        else:
            packed.append(escape)
            packed.append(dword & 0xFF)
            dword = dword >> 8
            packed.append(dword & 0xFF)
            dword = dword >> 8
            packed.append(dword & 0xFF)
            dword = dword >> 8
            packed.append(dword)

    return np.int8(packed)

def unpack_8_32(ints8):
    """
    Unpacks the data in little endian order.

    Args:
        List ints8s: The list of bytes to decompress.

    Returns:
        The decompressed integers.
    """

    escape = -2 ** 7
    unpacked = []

    i = 0
    while i < len(ints8):
        byte = ints8[i]

        if byte == escape:
            i += 1
            dword = ints8[i] & 0xFF
            i += 1
            dword += (ints8[i] << 8) & 0xFF00
            i += 1
            dword += (ints8[i] << 16) & 0xFF0000
            i += 1
            dword += ints8[i] << 24
            unpacked.append(dword)
        else:
            unpacked.append(byte)

        i += 1

    return np.int32(unpacked)

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

    xs = unsorted_diff_pack_16_8(xs)
    ys = unsorted_diff_pack_16_8(ys)

    ws = pack_32_8(ws)
    zs = np.int8(zs)
    #store all data as arrays of bytes with their lenght stored in the first 4 bytes
    def pack_bytes(bs):
        return struct.pack(f'<I{len(bs)}b', len(bs), *bs)

    buf = b''.join([pack_bytes(bs) for bs in (xs, ys, zs, ws)])

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

    def unpack_bytes(data):
        size, = struct.unpack('<I', data[:4])
        data = data[4:]
        bs = struct.unpack(f'<{size}b', data[:size])
        data = data[size:]

        return bs, data

    xs, data = unpack_bytes(data)
    ys, data = unpack_bytes(data)
    zs, data = unpack_bytes(data)
    ws, data = unpack_bytes(data)

    xs = unsorted_diff_unpack_8_16(xs)
    ys = unsorted_diff_unpack_8_16(ys)

    ws = unpack_8_32(ws)

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
