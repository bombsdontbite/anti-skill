"""Writes page.raw, a scanned text page in 8-bit greyscale with paper grain (fixed seed).

usage: python3 gen_input.py [--width W] [--height H] [--out page.raw]
"""
import argparse
import random
import struct


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=int, default=2976)
    ap.add_argument("--height", type=int, default=4209)
    ap.add_argument("--out", default="page.raw")
    a = ap.parse_args()
    rng = random.Random(2715)
    grain = bytes(rng.randrange(200, 256) for _ in range(65536))
    rows = []
    for y in range(a.height):
        start = rng.randrange(65536 - a.width)
        row = bytearray(grain[start:start + a.width])
        if (y // 40) % 3 != 2:  # a text line: dark strokes on 40-pixel bands
            x = rng.randrange(150)
            while x < a.width - 150:
                w = rng.randrange(2, 9)
                row[x:x + w] = bytes(rng.randrange(0, 90) for _ in range(w))
                x += w + rng.randrange(3, 30)
        rows.append(bytes(row))
    with open(a.out, "wb") as f:
        f.write(struct.pack("<8sII", b"GREYSCAN", a.width, a.height))
        f.write(b"".join(rows))


if __name__ == "__main__":
    main()
