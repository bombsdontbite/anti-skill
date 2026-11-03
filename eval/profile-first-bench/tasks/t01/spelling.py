"""Spelling correction for search queries: any word one edit away from a catalogue word maps to it."""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_LETTERS = "abcdefghijklmnopqrstuvwxyz"


def _load_vocab():
    with open(os.path.join(_HERE, "vocab.txt"), encoding="utf-8") as f:
        return [w.strip() for w in f if w.strip()]


def _edits1(word):
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes = [a + b[1:] for a, b in splits if b]
    transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b) > 1]
    replaces = [a + c + b[1:] for a, b in splits if b for c in _LETTERS]
    inserts = [a + c + b for a, b in splits for c in _LETTERS]
    return deletes + transposes + replaces + inserts


def _build_variants(vocab):
    table = {}
    for word in vocab:  # vocab.txt is ordered by popularity, so the commoner word wins a tie
        for variant in _edits1(word):
            table.setdefault(variant, word)
    for word in vocab:
        table[word] = word
    return table


VOCAB = _load_vocab()
VARIANTS = _build_variants(VOCAB)


def correct(word):
    return VARIANTS.get(word, word)
