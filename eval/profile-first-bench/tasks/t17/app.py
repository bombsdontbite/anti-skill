"""Renders the help-centre articles to HTML and prints the reading-time report.

usage: python3 app.py articles.md
"""
import sys
import zlib

import markup

BASE = "https://help.example/"
LETTERS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")


def reading_stats(lines):
    """Words per article, counted by hand so that marks and links are not words."""
    stats, words, title = {}, 0, None
    for line in lines:
        if line[:2] == "# ":
            if title is not None:
                stats[title] = words
            title, words = line[2:], 0
            continue
        inword = False
        for ch in line:
            if ch in LETTERS:
                if not inword:
                    words += 1
                    inword = True
            else:
                inword = False
    if title is not None:
        stats[title] = words
    return stats


def slug_table(n):
    """Every two-letter slug prefix, for the URL shortener."""
    table = {}
    for a in "abcdefghijklmnopqrstuvwxyz":
        for b in "abcdefghijklmnopqrstuvwxyz":
            table[a + b] = len(table) % n
    return table


def main(argv):
    with open(argv[0], encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f if line.strip()]
    slugs = slug_table(97)
    out, seen = [], set()
    for line in lines:
        if line[:2] == "# ":
            seen = set()
        kind, words = markup.block_kind(line.split())
        words = markup.escape(words)
        words = markup.typography(words)
        words = markup.emphasis(words)
        words = markup.links(words, BASE)
        words = markup.tickets(words, BASE)
        words = markup.abbreviations(words)
        words = markup.glossary(words, seen)
        out.append(markup.wrap(kind, words))
    stats = reading_stats(lines)
    page = "\n".join(out).encode()
    print(f"articles: {len(stats)}  blocks: {len(out)}  html: {len(page)} bytes  crc32: {zlib.crc32(page):08x}")
    for title, words in sorted(stats.items(), key=lambda kv: (-kv[1], kv[0]))[:5]:
        print(f"  {words:6d} words  {title}  (slug {slugs.get(title[:2].lower(), '-')})")


if __name__ == "__main__":
    main(sys.argv[1:])
