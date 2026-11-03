import random


class Cache:
    """Evict the key whose next use is predicted farthest away (sampled Belady).

    Every key ever seen keeps its last access time and a running mean of its reuse
    gap, so a key evicted and seen again comes back with a prediction. A key's
    predicted wait is gap - age; once it is well past its gap it is taken as dead
    and scored by its age. First-seen keys use a learned prior gap, scaled up by how
    rarely new keys come back, so one-off scans are evicted or never stored.
    """

    K = 16          # random samples per eviction
    P = 16          # best candidates carried to the next eviction
    OD = 1.5        # overdue factor when a key's gap spread is unknown
    K2 = 0.3        # overdue margin in units of gap spread
    A = 0.1         # floor of the gap averaging rate
    D0 = 4          # initial prior gap, in capacities
    BY_SEEN = 1.4   # do not store a returning key that looks this much worse than the victim
    BY_NEW = 0.85   # same, for a first-seen key

    def __init__(self, capacity):
        self.c = capacity
        self.keys = []; self.pos = {}
        self.store = self.pos
        self.last = {}; self.iv = {}; self.cnt = {}; self.dv = {}
        self.t = 0
        self.d = float(capacity * self.D0)
        self.rng = random.Random(1)
        self.n1 = 1.0; self.n2 = 1.0
        self.pool = []

    def _far(self, k, now):
        iv = self.iv.get(k)
        age = now - self.last[k]
        if iv is None:
            dd = self.d * self.n1 / self.n2
            return dd - age if age < self.d * self.OD else age
        dv = self.dv.get(k)
        thr = iv * self.OD if dv is None else iv + self.K2 * dv + 0.1 * iv
        return iv - age if age < thr else age

    def access(self, key):
        t = self.t = self.t + 1
        last = self.last
        p = last.get(key)
        if p is not None:
            gap = t - p
            o = self.iv.get(key)
            n = self.cnt[key] = self.cnt.get(key, 0) + 1
            a = max(1.0 / n, self.A)
            if o is not None:
                dv = self.dv.get(key)
                e = abs(gap - o)
                self.dv[key] = e if dv is None else (1 - a) * dv + a * e
            self.iv[key] = gap if o is None else (1 - a) * o + a * gap
            if o is None:
                self.d += 0.05 * (gap - self.d); self.n2 += 1
        else:
            self.n1 += 1
        if t % 1000 == 0:
            self.n1 *= 0.9; self.n2 *= 0.9
        last[key] = t
        if key in self.pos:
            return True
        keys = self.keys
        if len(keys) >= self.c:
            n = len(keys); r = self.rng.randrange; pos = self.pos; far = self._far
            cand = {k for k in self.pool if k in pos}
            for _ in range(self.K):
                cand.add(keys[r(n)])
            sc = sorted(((far(k, t), k) for k in cand), reverse=True)
            by = self.BY_SEEN if key in self.iv else self.BY_NEW
            if far(key, t) * by > sc[0][0]:
                self.pool = [k for _, k in sc[:self.P]]
                return False
            best = sc[0][1]
            self.pool = [k for _, k in sc[1:self.P + 1]]
            i = pos.pop(best); lk = keys.pop()
            if lk != best: keys[i] = lk; pos[lk] = i
        self.pos[key] = len(keys); keys.append(key)
        return False
