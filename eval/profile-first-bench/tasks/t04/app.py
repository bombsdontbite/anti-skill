"""Tag report for a community feed: the tag list in first-use order and the tags most often used together.

usage: python3 app.py posts.jsonl
"""
import json
import sys
from collections import Counter

TOP = 50


def load_posts(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def normalise_tags(raw):
    return [t.strip().lstrip("#").lower() for t in raw if t.strip("# ")]


def unique_in_order(items):
    seen = []
    for x in items:
        if x not in seen:
            seen.append(x)
    return seen


def similarity_matrix(top, index):
    """Jaccard similarity of the post sets of every pair of top tags."""
    n = len(top)
    m = [[0.0] * n for _ in range(n)]
    for i in range(n):
        m[i][i] = 1.0
        for j in range(i + 1, n):
            a, b = index[top[i]], index[top[j]]
            inter = len(a & b)
            m[i][j] = m[j][i] = inter / (len(a) + len(b) - inter)
    return m


def main(argv):
    posts = load_posts(argv[0])
    all_tags, index = [], {}
    for post in posts:
        tags = normalise_tags(post["tags"])
        all_tags.extend(tags)
        for t in tags:
            index.setdefault(t, set()).add(post["id"])
    ordered = unique_in_order(all_tags)
    counts = Counter(all_tags)
    top = sorted(counts, key=lambda t: (-counts[t], t))[:TOP]
    m = similarity_matrix(top, index)
    pairs = sorted(((m[i][j], top[i], top[j]) for i in range(len(top)) for j in range(i + 1, len(top))),
                   key=lambda p: (-p[0], p[1], p[2]))
    print(f"posts: {len(posts)}  tag uses: {len(all_tags)}  distinct tags: {len(ordered)}")
    print("first used: " + ", ".join(ordered[:20]))
    print("last new:   " + ", ".join(ordered[-5:]))
    for score, a, b in pairs[:10]:
        print(f"{score:.4f}  {a} + {b}")


if __name__ == "__main__":
    main(sys.argv[1:])
