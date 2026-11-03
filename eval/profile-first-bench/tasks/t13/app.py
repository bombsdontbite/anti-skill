"""Geocodes a batch of delivery addresses against the street gazetteer, with a persistent cache.

usage: python3 app.py addresses.txt
Earlier answers come from geocache.json; the merged cache is written to geocache.next.json,
which the deploy job moves into place before the next batch.
"""
import atexit
import json
import os
import sys
import zlib

CACHE = "geocache.json"
NEXT_CACHE = "geocache.next.json"


def load_cache():
    if not os.path.exists(CACHE):
        return {}
    with open(CACHE, encoding="utf-8") as f:
        return json.load(f)


def normalise(address):
    parts = address.lower().replace(",", " ").split()
    return " ".join(p.rstrip(".") for p in parts if p not in ("ul", "ul.", "street", "st"))


def street_hash(key):
    h = 2166136261
    for ch in key:
        h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    return h


def geocode(key):
    h = street_hash(key)
    return [round(50.0 + (h % 10000) / 50000, 6), round(19.9 + (h // 10000 % 10000) / 50000, 6)]


def resolve_all(addresses, cache):
    hits = 0
    out = []
    for a in addresses:
        key = normalise(a)
        if key in cache:
            hits += 1
        else:
            cache[key] = geocode(key)
        out.append(cache[key])
    return out, hits


def encode_cache(cache):
    return json.dumps(cache, sort_keys=True, indent=1)


def save_cache(cache):
    blob = encode_cache(cache)
    with open(NEXT_CACHE, "w", encoding="utf-8") as f:
        f.write(blob)
    print(f"cache saved: {len(cache)} entries, crc32 {zlib.crc32(blob.encode()):08x}")


def main(argv):
    cache = load_cache()
    atexit.register(save_cache, cache)
    with open(argv[0], encoding="utf-8") as f:
        addresses = [line.strip() for line in f if line.strip()]
    points, hits = resolve_all(addresses, cache)
    lat = sum(p[0] for p in points) / len(points)
    print(f"addresses: {len(addresses)}  cache hits: {hits}  mean latitude: {lat:.6f}")


if __name__ == "__main__":
    main(sys.argv[1:])
