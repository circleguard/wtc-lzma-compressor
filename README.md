# WTC

WTC is an extension of the lzma compression format, specifically designed to make osu!std replays smaller before storing them. It reduces the size of certain datatypes in the original .osr format, achieving ~40% lossy compression ratios.

| Part | Original lzma datatype | WTC datatype |
| --- | --- | --- |
| w (ms since preivous frame) | Long (8 bytes) | 24bit Integer (3 bytes)|
| x (x-cord) | Float (4 bytes) | Short (2 bytes) |
| y (y-cord) | Float (4 bytes) | Short (2 bytes) |
| z (bit combination of keypresses) | Integer (4 bytes) | Char (1 byte) |

This compresses the original 20 byte frame to an 8 byte frame, but not without losses. Precision is lost on w, x, and y, but not z, because the keypressed bit combination will never go above 4 bits for osu!standard. Though it may be larger for other gamemodes such as 7k mania, this compressor is explicitly for osu!standard.

WTC compression achieves an average of 40% ±5 compression (Not a formally calculated number - simply based on experience).

Installation:

```bash
$ pip install git+git://github.com/osu-anticheat/wtc-lzma-compressor
```

Usage:

```python
import wtc

# to compress an lzma bytestring
wtc_bytestring = wtc.compress(lzma_bytestring)

# to decompress a wtc bytestring into an lzma bytestring
lzma_bytestring = wtc.decompress(wtc_bytestring)

# compress and decompress are (almost) inverse operations, so lzma_bytestring ≈ wtc.decompress(wtc.compress(lzma_bytestring)).
# some precision is lost, so the strings are not identical.
```
