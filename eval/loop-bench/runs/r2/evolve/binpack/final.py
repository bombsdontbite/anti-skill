# Sum-of-Squares online bin packing (Csirik et al.) with three changes found by search:
#  1. the function keeps its own count of every open bin's gap across calls (the scorer only shows bins
#     that fit), and rebuilds it from what it is shown whenever the two disagree (new instance, new capacity);
#  2. a gap smaller than the 2% quantile of item sizes seen so far is priced as the waste it is (its size),
#     not as a square-count term;
#  3. ties go to the tightest fit (best fit), not to the oldest bin.
N = []          # N[g] = number of open bins whose remaining capacity is g
H = []          # histogram of item sizes seen for this capacity
ST = [0, 0, 0]  # capacity, items seen, dead-gap threshold

QF = 0.02
LAM = 1.0
AL = 0.5


def priority(item, bins):
    cap = bins[-1]
    k = len(bins) - 1
    if ST[0] != cap:
        ST[0] = cap; ST[1] = 0; ST[2] = 0
        H[:] = [0] * (cap + 1)
        N[:] = [0] * (cap + 1)
    if sum(N[item:cap]) != k or any(N[b] <= 0 for b in bins[:-1]):
        N[:] = [0] * (cap + 1)
        for b in bins[:-1]:
            N[b] += 1
    H[item] += 1
    ST[1] += 1
    n = ST[1]
    if n % 32 == 1:
        lim = QF * n
        acc = 0; th = 0
        for g in range(cap + 1):
            acc += H[g]
            if acc > lim:
                th = g; break
        ST[2] = th
    th = ST[2]
    out = []
    for b in bins:
        g2 = b - item
        if g2 <= 0:
            d = 0
        elif g2 < th:
            d = LAM * g2
        else:
            d = 2 * N[g2] + 1
        if b != cap:
            d += 1 - 2 * N[b]
        out.append(-d - AL * g2 / cap)
    best = 0
    for j in range(1, len(out)):
        if out[j] > out[best]:
            best = j
    b = bins[best]
    if b != cap:
        N[b] -= 1
    if b - item > 0:
        N[b - item] += 1
    return out
