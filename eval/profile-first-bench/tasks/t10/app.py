"""Finds near-duplicate marketplace listings by title similarity.

usage: python3 app.py listings.jsonl
"""
import json
import sys

THRESHOLD = 0.6


def load_listings(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def shingles(title, k=3):
    t = " ".join(title.lower().split())
    return {t[i:i + k] for i in range(len(t) - k + 1)}


def shingle_all(listings):
    return [(item["id"], shingles(item["title"])) for item in listings]


def find_duplicates(items, threshold=THRESHOLD):
    pairs = []
    n = len(items)
    for i in range(n):
        a_id, a = items[i]
        for j in range(i + 1, n):
            b_id, b = items[j]
            inter = len(a & b)
            if inter and inter / (len(a) + len(b) - inter) >= threshold:
                pairs.append((a_id, b_id))
    return pairs


def clusters(pairs):
    parent = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b in pairs:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)
    groups = {}
    for x in parent:
        groups.setdefault(find(x), []).append(x)
    return sorted((sorted(g) for g in groups.values()), key=lambda g: (-len(g), g[0]))


def main(argv):
    listings = load_listings(argv[0])
    pairs = find_duplicates(shingle_all(listings))
    groups = clusters(pairs)
    print(f"listings: {len(listings)}  similar pairs: {len(pairs)}  groups: {len(groups)}")
    for g in groups[:10]:
        print("  " + ", ".join(map(str, g)))


if __name__ == "__main__":
    main(sys.argv[1:])
