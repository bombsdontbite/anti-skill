"""Tokenizes help-centre articles and prints one line per term: term, document count, total count.

usage: python3 indexer.py articles.txt
"""
import sys


def tokens(text):
    word = []
    for ch in text:
        if ch.isalnum():
            word.append(ch.lower())
        elif word:
            yield "".join(word)
            word = []
    if word:
        yield "".join(word)


def main(path):
    df, tf = {}, {}
    with open(path, encoding="utf-8") as f:
        doc = []
        for line in f:
            if line.startswith("# ") and doc:
                seen = set()
                for t in tokens("".join(doc)):
                    tf[t] = tf.get(t, 0) + 1
                    seen.add(t)
                for t in seen:
                    df[t] = df.get(t, 0) + 1
                doc = []
            doc.append(line)
    out = sys.stdout
    for t in sorted(tf):
        out.write(f"{t}\t{df.get(t, 0)}\t{tf[t]}\n")


if __name__ == "__main__":
    main(sys.argv[1])
