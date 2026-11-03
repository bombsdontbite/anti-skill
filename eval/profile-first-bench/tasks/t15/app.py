"""Archives a scanned page: measures its ink coverage and writes the raw scan, bzip2-compressed.

usage: python3 app.py page.raw
page.raw is 8-bit greyscale, row by row, with a 16-byte header: magic, width, height.
"""
import bz2
import struct
import sys
import zlib

INK_BELOW = 96  # a pixel darker than this counts as ink


def load_scan(path):
    with open(path, "rb") as f:
        raw = f.read()
    magic, width, height = struct.unpack("<8sII", raw[:16])
    if magic != b"GREYSCAN":
        raise SystemExit("not a scan")
    return width, height, raw[16:]


def ink(v):
    return 1 if v < INK_BELOW else 0


def coverage(pixels):
    return sum([ink(v) for v in pixels]) / len(pixels)


def contrast_table():
    """Output level for every (input level, gamma step): 256 x 64 entries."""
    table = []
    for g in range(64):
        gamma = 0.5 + g / 32
        table.append(bytes(min(255, int(255 * (v / 255) ** gamma)) for v in range(256)))
    return table


def pack(raw):
    return bz2.compress(raw, 9)


def main(argv):
    width, height, pixels = load_scan(argv[0])
    table = contrast_table()
    share = coverage(pixels)
    packed = pack(pixels)
    with open("page.bz2", "wb") as f:
        f.write(packed)
    print(f"{width}x{height}  ink: {share:.4%}  archive: {len(packed)} bytes  "
          f"crc32: {zlib.crc32(packed):08x}  gamma table: {len(table)}")


if __name__ == "__main__":
    main(sys.argv[1:])
