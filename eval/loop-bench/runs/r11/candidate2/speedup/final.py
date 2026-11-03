# v15 plus: skip the end bisect when the session ends before the next query point
from bisect import bisect_left, bisect_right
from itertools import accumulate, repeat


def usage_report(sessions, windows):
    if not windows:
        return []
    los, his = zip(*windows)
    Q = sorted(set(los + his))
    m = len(Q) + 1
    Qs = Q + [float("inf")]
    cr = [0] * m
    cw = [0] * m
    ns = [0] * m
    ne = [0] * m
    br = bisect_right
    bl = bisect_left
    for s, e, r in sessions:
        i = br(Q, s)
        ns[i] += 1
        if e <= Qs[i]:
            ne[i] += 1
            if r:
                cw[i] += r * (e - s)
        else:
            j = bl(Q, e, i)
            ne[j] += 1
            if r:
                cr[i] += r
                cw[i] -= r * s
                cr[j] -= r
                cw[j] += r * e
    F = [q * a + b for q, a, b in zip(Q, accumulate(cr), accumulate(cw))]
    S = list(accumulate(ns))
    E = list(accumulate(ne))
    return [(F[h] - F[l], S[h] - E[l]) for l, h in
            zip(map(bisect_left, repeat(Q), los), map(bisect_left, repeat(Q), his))]
