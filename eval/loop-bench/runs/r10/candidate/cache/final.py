from collections import OrderedDict


class Cache:
    """LIRS whose HIR share adapts ARC-style: misses on recently evicted HIR keys grow it,
    misses on evicted former-LIR keys shrink it."""

    def __init__(self, capacity, hfrac=0.02, nrmult=8, hmax=0.5, delta=1.0, gmult=1.0):
        self.cap = capacity
        self.h = max(1.0, capacity * hfrac)
        self.hmin = max(1.0, capacity * 0.01); self.hmax = capacity * hmax
        self.delta = delta
        if capacity < 2:  # no room for a HIR block: plain LRU over the LIR stack
            self.h = self.hmin = self.hmax = 0.0
        self.S = OrderedDict(); self.Q = OrderedDict()
        self.lir = set(); self.nr = OrderedDict()
        self.nrcap = int(capacity * nrmult)
        self.wl = set()            # resident HIR that were demoted from LIR
        self.gl = OrderedDict()    # evicted former-LIR keys
        self.gh = OrderedDict()    # recently evicted HIR keys
        self.gmult = gmult
        self.store = set()

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if k in self.lir: return
            del S[k]
            self.nr.pop(k, None)

    def _demote(self):
        lcap = self.cap - int(self.h)
        while len(self.lir) > lcap:
            k, _ = self.S.popitem(last=False)
            self.lir.discard(k); self.Q[k] = None; self.wl.add(k)
            self._prune()

    def access(self, key):
        S = self.S
        if key in self.lir:
            first = next(iter(S)) == key
            S.move_to_end(key)
            if first: self._prune()
            return True
        if key in self.Q:
            if key in S:
                del self.Q[key]; self.wl.discard(key); self.lir.add(key); S.move_to_end(key)
                self._demote()
            else:
                S[key] = None; self.Q.move_to_end(key)
            return True
        # miss: adapt
        if key in self.gl:
            del self.gl[key]
            self.h = max(self.hmin, self.h - self.delta)
        elif key in self.gh:
            del self.gh[key]
            self.h = min(self.hmax, self.h + self.delta)
        if len(self.store) >= self.cap:
            if self.Q:
                v, _ = self.Q.popitem(last=False)
                g = max(2, int(self.h * self.gmult))
                if v in self.wl:
                    self.wl.discard(v); self.gl[v] = None
                    while len(self.gl) > g: self.gl.popitem(last=False)
                else:
                    self.gh[v] = None
                    while len(self.gh) > g: self.gh.popitem(last=False)
                if v in S:
                    self.nr[v] = None
                    if len(self.nr) > self.nrcap:
                        o, _ = self.nr.popitem(last=False); del S[o]
            else:
                v = next(iter(S)); del S[v]; self.lir.discard(v); self._prune()
            self.store.discard(v)
        self.store.add(key)
        if len(self.lir) < self.cap - int(self.h):
            self.lir.add(key); S[key] = None; S.move_to_end(key); self.nr.pop(key, None)
            self._prune()
            return False
        if key in S:
            del self.nr[key]; S.move_to_end(key); self.lir.add(key)
            self._demote()
        else:
            S[key] = None; self.Q[key] = None
        return False
