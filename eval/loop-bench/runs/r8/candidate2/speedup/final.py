from bisect import bisect_left, bisect_right
from itertools import accumulate, repeat
from operator import itemgetter, mul

_s, _e, _r = itemgetter(0), itemgetter(1), itemgetter(2)


def usage_report(sessions, windows):
    """Usage over [lo, hi) is G(hi) - G(lo), G(x) = sum of rate * (time of a session before x),
    read off prefix sums over sessions sorted by start and by end. The loops run in C."""
    if not sessions:
        return [(0, 0)] * len(windows)
    if not windows:
        return []
    a = sorted(sessions, key=_s)
    b = sorted(a, key=_e)  # nearly sorted already when sessions are short
    starts = list(map(_s, a))
    ends = list(map(_e, b))
    sr = list(accumulate(map(_r, a), initial=0))
    srs = list(accumulate(map(mul, map(_r, a), starts), initial=0))
    er = list(accumulate(map(_r, b), initial=0))
    ers = list(accumulate(map(mul, map(_r, b), ends), initial=0))
    los = list(map(_s, windows))
    his = list(map(_e, windows))
    # Sessions ending exactly at lo add zero to G(lo), so the count's bisect_right index serves both.
    return [(hi * (sr[i] - er[j]) - srs[i] + ers[j] - lo * (sr[k] - er[l]) + srs[k] - ers[l], i - l)
            for lo, hi, i, j, k, l in zip(los, his,
                                          map(bisect_left, repeat(starts), his),
                                          map(bisect_left, repeat(ends), his),
                                          map(bisect_left, repeat(starts), los),
                                          map(bisect_right, repeat(ends), los))]
