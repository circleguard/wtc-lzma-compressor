import struct

import numpy as np

from itertools import zip_longest

def pack_word_byte(word):
    if abs(word) < 128:
        return np.int8((word,))
    else:
        return np.int8((-128, word & 0xFF, word >> 8))

def pack_bytes(bs):
        return struct.pack(f'<I{len(bs)}b', len(bs), *bs)

def pack_words(words):
        return struct.pack(f'<I{len(words)}H', len(words), *words)

def unpack_bytes(data):
    size, = struct.unpack('<I', data[:4])
    data = data[4:]
    bs = struct.unpack(f'<{size}b', data[:size])
    data = data[size:]

    return bs, data

def unpack_words(data):
    size, = struct.unpack('<I', data[:4])
    data = data[4:]
    words = struct.unpack(f'<{size}H', data[:2 * size])
    data = data[2 * size:]

    return words, data

def unsorted_diff_pack_16_8(int16s):
    """
    Packs the differential of the input to bytes in little endian order.

    Args:
        List ints16s: The list of shorts to differentially compress.

    Returns:
        The differential data as a list of bytes.
    """

    small = 2 ** 7 - 1
    start = int16s[0]
    diff = np.diff(int16s)
    packed = []

    packed.extend(pack_word_byte(start))
    for word in diff:
        packed.extend(pack_word_byte(word))

    return np.int8(packed)

def unsorted_diff_unpack_8_16(ints8):
    """
    Unpacks the differential data in little endian order to words.

    Args:
        List ints8s: The list of bytes to decompress.

    Returns:
        The decompressed shorts.
    """
    decoded = []

    i = 0
    while i < len(ints8):
        byte = ints8[i]

        if byte == -128:
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
    """Packs the data in little endian order."""
    packed = []
    small = 2 ** 7 - 1
    
    for dword in ints32:
        if abs(dword) <= small:
            packed.append(dword)
        else:
            packed.append(-128)
            packed.append(dword & 0xFF)
            dword = dword >> 8
            packed.append(dword & 0xFF)
            dword = dword >> 8
            packed.append(dword & 0xFF)
            dword = dword >> 8
            packed.append(dword)
            
    return np.int8(packed)

def unpack_8_32(ints8):
    """Unpacks the data in little endian order."""
    unpacked = []
    i = 0
    while i < len(ints8):
        byte = ints8[i]
        
        if byte == -128:
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

def scolvr(sparse):
    """
    Sparse clustered data to offset, length and value reduction.

    Args:
        List sparse: The sparse data to compress.

    Returns:
        The list of short data formatted as offset, length, value.
    """

    marker = 0
    offset = 0
    length = 0
    current = 0

    shorts = []

    for i, e in enumerate(sparse):
        if current > 0:
            if e == current:
                length += 1
            else:
                #non-zero to non-zero transition
                #also non-zero to zero transition but zero isn't tracked
                shorts.append(offset)
                shorts.append(length)
                shorts.append(current)
                
                offset = 0
                marker = i
                length = 1
                current = e
        elif e > 0:
            #zero to non-zero transition
            offset = i - marker
            length = 1
            current = e

    if current > 0:
        shorts.append(offset)
        shorts.append(length)
        shorts.append(current)
        
    return np.uint16(shorts)

def grouper(iterable, n, fillvalue=None):
    #https://docs.python.org/3/library/itertools.html#itertools-recipes

    #duplicate the iterable n times
    args = [iter(iterable)] * n
    #zip the same iterable together n times
    #taking the 1st element removes it from the iterable
    #taking the 1st again now takes actually the 2nd from the original, up to n
    return zip_longest(*args, fillvalue=fillvalue)

def olvsco(olv_data):
    """
    Decompresses the offset, length and value data to sparse data.

    Args:
        List olv_data: The short data of the format offset, length, value.

    Returns:
        The sparse data represented by olv_data.
    """

    if len(olv_data) % 3:
        raise ValueError(f"Offset, length, value data length is not a multiple of 3. Length: {len(ilv_data)}")

    last = 0
    sparse = []
    
    for o, l, v in grouper(olv_data, 3):
        sparse.extend(o * [0])
        sparse.extend(l * [v])

    return np.uint8(sparse)
