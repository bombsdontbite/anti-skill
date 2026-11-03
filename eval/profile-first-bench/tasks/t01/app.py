"""Corrects the spelling of a day's shop search queries and reports the commonest corrections.

usage: python3 app.py queries.txt
"""
import math
import sys

import spelling


def confusion_cube(n=10):
    """Keyboard-distance weight for every (typed length, intended length, edit position) triple."""
    cube = [[[0.0] * n for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            for k in range(n):
                cube[i][j][k] = math.exp(-abs(i - j) / (k + 1)) / (1 + k * k)
    return cube


def first_difference(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    return min(len(a), len(b))


def confidence(typed, fixed, cube):
    n = len(cube)
    return cube[len(typed) % n][len(fixed) % n][first_difference(typed, fixed) % n]


def correct_queries(lines):
    corrected, fixes = [], {}
    for line in lines:
        words = []
        for word in line.lower().split():
            fixed = spelling.correct(word)
            if fixed != word:
                fixes[(word, fixed)] = fixes.get((word, fixed), 0) + 1
            words.append(fixed)
        corrected.append(" ".join(words))
    return corrected, fixes


def main(argv):
    with open(argv[0], encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f]
    cube = confusion_cube()
    corrected, fixes = correct_queries(lines)
    changed = sum(1 for a, b in zip(lines, corrected) if a.lower() != b)
    print(f"queries: {len(lines)}  corrected: {changed}  distinct fixes: {len(fixes)}")
    top = sorted(fixes.items(), key=lambda kv: (-kv[1], kv[0]))[:15]
    for (typed, fixed), count in top:
        print(f"{count:5d}  {typed} -> {fixed}  confidence {confidence(typed, fixed, cube):.4f}")


if __name__ == "__main__":
    main(sys.argv[1:])
