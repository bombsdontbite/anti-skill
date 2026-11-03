"""Writes capture.bin, little-endian 16-bit samples from a vibration sensor (fixed seed).

usage: python3 gen_input.py [--samples N] [--out capture.bin]
"""
import argparse
import array
import math
import random
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=4000000)
    ap.add_argument("--out", default="capture.bin")
    a = ap.parse_args()
    rng = random.Random(2690)
    out = array.array("h")
    phase = 0.0
    for i in range(a.samples):
        phase += 0.013 + 0.004 * math.sin(i / 9000)
        v = 7000 * math.sin(phase) + 2500 * math.sin(phase * 3.7) + rng.gauss(0, 900)
        out.append(max(-32768, min(32767, int(v))))
    if sys.byteorder == "big":
        out.byteswap()
    with open(a.out, "wb") as f:
        f.write(out.tobytes())


if __name__ == "__main__":
    main()
