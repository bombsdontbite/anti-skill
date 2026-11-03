from bisect import bisect_left, bisect_right


def _build(points_weights):
    xs = sorted(set(p for p, _, _ in points_weights))
    m = len(xs)
    index = {x: k + 1 for k, x in enumerate(xs)}
    t_r = [0] * (m + 1)
    t_rx = [0] * (m + 1)
    t_c = [0] * (m + 1)
    for p, r, rx in points_weights:
        k = index[p]
        while k <= m:
            t_r[k] += r
            t_rx[k] += rx
            t_c[k] += 1
            k += k & -k
    return xs, t_r, t_rx, t_c


def _query(tree, k):
    total = 0
    while k > 0:
        total += tree[k]
        k -= k & -k
    return total


def usage_report(sessions, windows):
    """Fenwick trees over compressed start and end coordinates."""
    xs_s, sr, srx, sc = _build([(s, r, r * s) for s, _, r in sessions])
    xs_e, er, erx, ec = _build([(e, r, r * e) for _, e, r in sessions])

    def F(t):
        i = bisect_left(xs_s, t)
        j = bisect_left(xs_e, t)
        return t * (_query(sr, i) - _query(er, j)) - _query(srx, i) + _query(erx, j)

    out = []
    for lo, hi in windows:
        cnt = _query(sc, bisect_left(xs_s, hi)) - _query(ec, bisect_right(xs_e, lo))
        out.append((F(hi) - F(lo), cnt))
    return out
