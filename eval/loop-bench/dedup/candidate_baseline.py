def near_duplicates(records):
    """All pairs of records whose token sets are at least 80 % alike.

    records: list of str; a record's tokens are the set of words that str.split() returns
    (split on any run of whitespace, case-sensitive, repeats count once).
    Returns a list of (i, j) with i < j for every pair whose Jaccard similarity
    |A & B| / |A | B| is at least 0.8, computed exactly as 5 * |A & B| >= 4 * |A | B|.
    A record without tokens is never part of a pair. The order of the pairs does not matter.
    """
    sets = [set(r.split()) for r in records]
    pairs = []
    for i in range(len(sets)):
        a = sets[i]
        for j in range(i + 1, len(sets)):
            b = sets[j]
            inter = len(a & b)
            union = len(a) + len(b) - inter
            if union and 5 * inter >= 4 * union:
                pairs.append((i, j))
    return pairs
