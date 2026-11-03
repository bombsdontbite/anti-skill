from collections import OrderedDict


class Cache:
    """LIRS whose HIR share adapts: misses on keys just evicted from the HIR queue grow it,
    misses on non-resident keys still in the stack shrink it. While the HIR share is small,
    a new key is admitted only if it is at least as frequent as the HIR victim."""

    def __init__(self, capacity, hir_frac=0.05, ghost_mult=3, lo=0.01, hi=0.5, grow=1.0, shrink=1.0, emult=1.0, amax=0.03):
        self.amax = capacity * amax; self.freq = {}; self.ops = 0
        self.emult = emult
        self.cap = capacity
        self.h = capacity * hir_frac
        self.hlo = max(1.0, capacity * lo); self.hhi = capacity * hi
        self.grow = grow; self.shrink = shrink
        self.S = OrderedDict()   # recency stack: key -> is LIR
        self.Q = OrderedDict()   # resident HIR
        self.N = OrderedDict()   # non-resident HIR still in S
        self.E = OrderedDict()   # recently evicted from Q
        self.store = set()
        self.nlir = 0
        self.gcap = int(capacity * ghost_mult)

    def _prune(self):
        S, N = self.S, self.N
        while S:
            k = next(iter(S))
            if S[k]:
                break
            del S[k]
            N.pop(k, None)

    def _demote_bottom(self):
        S = self.S
        k = next(iter(S))
        del S[k]; self.nlir -= 1
        self.Q[k] = True
        self._prune()

    def access(self, key):
        S, Q, N = self.S, self.Q, self.N
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.ops += 1
        if self.ops >= 10 * self.cap:
            self.ops = 0
            self.freq = f = {a: b >> 1 for a, b in f.items() if b > 1}
        if key in self.store:
            if S.get(key):
                first = next(iter(S)) == key
                S.move_to_end(key)
                if first:
                    self._prune()
            elif key in S:
                del S[key]; S[key] = True; self.nlir += 1
                del Q[key]
                self._demote_bottom()
            else:
                S[key] = False
                Q.move_to_end(key)
            return True
        E = self.E
        if key in E:
            del E[key]
            self.h = min(self.hhi, self.h + self.grow)
        elif key in N:
            self.h = max(self.hlo, self.h - self.shrink)
        lcap = self.cap - int(self.h)
        while self.nlir > lcap:
            self._demote_bottom()
        if (len(self.store) >= self.cap and Q and key not in S and self.nlir >= lcap
                and self.h <= self.amax and f.get(key, 0) < f.get(next(iter(Q)), 0)):
            S[key] = False; N[key] = True
            while len(N) > self.gcap:
                k, _ = N.popitem(last=False)
                del S[k]
            return False
        if len(self.store) >= self.cap:
            if Q:
                k, _ = Q.popitem(last=False)
            else:
                k = next(iter(S)); del S[k]; self.nlir -= 1
                self._prune()
            self.store.discard(k)
            E[k] = True
            while len(E) > self.h * self.emult:
                E.popitem(last=False)
            if k in S:
                N[k] = True
        self.store.add(key)
        if key in S:
            del N[key]
            del S[key]; S[key] = True; self.nlir += 1
            if self.nlir > lcap:
                self._demote_bottom()
        elif self.nlir < lcap:
            S[key] = True; self.nlir += 1
        else:
            S[key] = False; Q[key] = True
        while len(N) > self.gcap:
            k, _ = N.popitem(last=False)
            del S[k]
        return False
