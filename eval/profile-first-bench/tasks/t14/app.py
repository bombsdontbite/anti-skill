"""Rebuilds the help-centre search index and prints the terms that need a synonym entry.

usage: python3 app.py articles.txt
The tokenizer runs as its own process (indexer.py), so the index can also be rebuilt by hand.
"""
import subprocess
import sys

STOP = {"the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "is", "it", "your", "you"}


def start_indexer(path):
    return subprocess.Popen([sys.executable, "indexer.py", path], stdout=subprocess.PIPE)


def load_titles(path):
    titles = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("# "):
                titles.append(line[2:].strip())
    return titles


def read_postings(proc):
    out, _ = proc.communicate()
    if proc.returncode:
        raise SystemExit(f"indexer failed with {proc.returncode}")
    postings = {}
    for line in out.decode("utf-8").splitlines():
        term, df, tf = line.split("\t")
        postings[term] = (int(df), int(tf))
    return postings


def edit_pairs(terms):
    """Pairs of short terms one edit apart: candidates for the synonym list."""
    short = sorted(t for t in terms if 3 <= len(t) <= 5)[:120]
    pairs = []
    for i, a in enumerate(short):
        for b in short[i + 1:]:
            if len(a) == len(b) and sum(x != y for x, y in zip(a, b)) == 1:
                pairs.append((a, b))
    return pairs


def main(argv):
    proc = start_indexer(argv[0])
    titles = load_titles(argv[0])
    postings = read_postings(proc)
    pairs = edit_pairs(postings)
    top = sorted((t for t in postings if t not in STOP), key=lambda t: (-postings[t][0], t))[:8]
    print(f"articles: {len(titles)}  terms: {len(postings)}  synonym candidates: {len(pairs)}")
    for t in top:
        print(f"  {t:16s} df={postings[t][0]:6d} tf={postings[t][1]:7d}")


if __name__ == "__main__":
    main(sys.argv[1:])
