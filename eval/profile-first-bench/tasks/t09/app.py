"""Sensor archive: archives a raw 16-bit capture and prints a histogram of its 8-bit levels.

usage: python3 app.py capture.bin
"""
import array
import lzma
import sys
import zlib
from collections import Counter

PREVIEW_STEP = 16  # the level histogram is a preview at 1/16 of the sample rate


def load_capture(path):
    with open(path, "rb") as f:
        raw = f.read()
    samples = array.array("h", raw)
    if sys.byteorder == "big":
        samples.byteswap()
    return raw, samples


def clamp(v):
    v = (v >> 6) + 128
    return 0 if v < 0 else (255 if v > 255 else v)


def normalise_all(samples):
    return bytes([clamp(v) for v in samples])


def histogram(levels):
    return dict(Counter(levels))


def pack(raw):
    return lzma.compress(raw, preset=9 | lzma.PRESET_EXTREME)


def main(argv):
    raw, samples = load_capture(argv[0])
    levels = normalise_all(samples[::PREVIEW_STEP])
    hist = histogram(levels)
    archive = pack(raw)
    with open("capture.xz", "wb") as f:
        f.write(archive)
    print(f"samples: {len(samples)}  archive: {len(archive)} bytes  crc32: {zlib.crc32(archive):08x}")
    for level, n in sorted(hist.items(), key=lambda kv: (-kv[1], kv[0]))[:8]:
        print(f"  level {level:3d}  {n:8d}")


if __name__ == "__main__":
    main(sys.argv[1:])
