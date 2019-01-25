import lzma
import struct
 
def compress(lzma_stream):
    """
    Packs replay into a more compact format.
 
    Args:
        String lzma_stream: An lzma stream from a replay.
 
    Returns:
        An lzma compressed bytestring
    """
 
    text = lzma.decompress(lzma_stream).decode('UTF-8')
    raw_list = []
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
        raw_list.append(_pack_int24(w)) #w
        raw_list.append(struct.pack('<hhB', x, y, z)) #x, y, and z
 
    raw = b''.join(raw_list)
    compressed = lzma.compress(raw, format=2)
    return compressed
 
def decompress(wtc_bytes):
    """
    Decompresses a wtc stream into an lzma stream.
 
    Args:
        String wtc_bytes: A wtc compressed bytestring (returned by wtc.compress).
 
    Returns:
        An lzma compressed bytestring, identical to the (decoded) string returned by the get_replay api endpoint.
    """
    output_list = []
    data = lzma.decompress(wtc_bytes)
    #each frame is 8 bytes
    for i in range(0, len(data), 8):
        frame = data[i : i+8]
        #extract W on its own since it's an int24 and cannot be used with struct.unpack
        b_w, frame = frame[:3], frame[3:]
 
        #w: signed 24bit integer
        w = _unpack_int24(b_w)
 
        #x: signed short
        #y: signed short
        #z: unsigned char
        x, y, z = struct.unpack('<hhB', frame)
 
        #X and Y are stored as shorts; convert and scale them back to their float forms
        x /= 16
        y /= 16
 
        output_list.append(f'{w}|{x}|{y}|{z},')
 
    output = ''.join(output_list)
    lzma_stream = lzma.compress(output.encode('UTF-8'), format=2)
    return lzma_stream
 
 
def _pack_int24(integer):
    """
    Converts an integer to a 24 bit bytes object.
 
    Args:
        Integer integer: The number to convert to bytes.
 
    Returns:
        A 24 bit int as bytes.
    """
 
    if not (-0x800000 <= integer < 0x800000):
        raise ValueError('Value must be between -0x800000 and 0x800000')
    output = struct.pack('<i', integer)
    output = output[:-1]
    return output
 
def _unpack_int24(int_bytes):
    """
    Converts a 24 bit bytes object to an integer.
 
    Args:
        Bytes int_bytes: The bytes to convert to int.
 
    Returns:
        An integer representation of the byte input.
    """
 
    if len(int_bytes) != 3:
        raise ValueError('Value must be an int24')
    sign = int_bytes[-1] & 0x80
    if sign:
        int_bytes = int_bytes + b'\xFF'
    else:
        int_bytes = int_bytes + b'\x00'
    return struct.unpack('<i', int_bytes)[0]
