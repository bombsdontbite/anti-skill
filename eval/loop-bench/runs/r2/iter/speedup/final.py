from bisect import bisect_left, bisect_right
from itertools import accumulate, repeat
from operator import itemgetter, mul, sub


def usage_report(sessions, windows):
    by_s = sorted(sessions, key=itemgetter(0))
    by_e = sorted(sessions, key=itemgetter(1))
    S = [t[0] for t in by_s]
    rs = [t[2] for t in by_s]
    E = [t[1] for t in by_e]
    re_ = [t[2] for t in by_e]
    RS = list(accumulate(rs, initial=0))
    RSS = list(accumulate(map(mul, rs, S), initial=0))
    RE = list(accumulate(re_, initial=0))
    REE = list(accumulate(map(mul, re_, E), initial=0))
    los = [w[0] for w in windows]
    his = [w[1] for w in windows]
    a_h = list(map(bisect_left, repeat(S), his))
    c_h = list(map(bisect_left, repeat(E), his))
    b_l = list(map(bisect_left, repeat(S), los))
    d_l = list(map(bisect_right, repeat(E), los))
    Fh = [x * (RS[a] - RE[c]) - RSS[a] + REE[c] for x, a, c in zip(his, a_h, c_h)]
    Fl = [x * (RS[b] - RE[d]) - RSS[b] + REE[d] for x, b, d in zip(los, b_l, d_l)]
    return list(zip(map(sub, Fh, Fl), map(sub, a_h, d_l)))
