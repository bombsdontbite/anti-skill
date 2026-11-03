from collections import OrderedDict


class _LRU:
    def __init__(self, cap):
        self.cap = cap; self.d = OrderedDict()

    def access(self, key):
        d = self.d
        if key in d:
            d.move_to_end(key); return True
        if self.cap <= 0: return False
        if len(d) >= self.cap: d.popitem(last=False)
        d[key] = None
        return False


class _LIRS:
    def __init__(self, capacity, hir_frac=0.01, s_mult=3):
        self.hcap = max(1, int(capacity * hir_frac))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict(); self.Q = OrderedDict(); self.lir = set()
        self.smax = capacity * s_mult
        self.d = {}

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if k in self.lir: break
            del S[k]

    def access(self, key):
        S, Q, lir = self.S, self.Q, self.lir
        if key in lir:
            S.move_to_end(key); self._prune(); return True
        if key in Q:
            if key in S:
                S.move_to_end(key); del Q[key]; lir.add(key)
                k = next(iter(S)); del S[k]; lir.discard(k); Q[k] = None
                self._prune()
            else:
                S[key] = None; Q.move_to_end(key)
            return True
        self.d[key] = None
        if len(lir) < self.lcap:
            lir.add(key); S[key] = None; S.move_to_end(key)
            return False
        if len(Q) >= self.hcap:
            k, _ = Q.popitem(last=False); del self.d[k]
        if key in S:
            S.move_to_end(key); lir.add(key)
            k = next(iter(S)); del S[k]; lir.discard(k); Q[k] = None
            self._prune()
        else:
            S[key] = None; Q[key] = None
        if len(S) > 2 * self.smax:
            keep = len(S) - self.smax
            for k in list(S):
                if keep <= 0: break
                if k not in lir and k not in Q: del S[k]; keep -= 1
        return False


class Cache:
    """Shadow-simulate LIRS and LRU; the real cache follows whichever scored more recent hits.
    On a miss the real cache evicts its least recently used key that the leader does not hold."""

    def __init__(self, capacity, decay=0.999):
        self.cap = capacity
        # LIRS needs at least one LIR and one HIR slot
        self.ex = [_LIRS(capacity), _LRU(capacity)] if capacity >= 2 else [_LRU(capacity)]
        self.sc = [0.0] * len(self.ex)
        self.decay = decay
        self.store = OrderedDict()

    def access(self, key):
        sc, dec = self.sc, self.decay
        for i, e in enumerate(self.ex):
            sc[i] = sc[i] * dec + (1.0 if e.access(key) else 0.0)
        st = self.store
        if key in st:
            st.move_to_end(key); return True
        if self.cap <= 0:
            return False
        if len(st) >= self.cap:
            lead = self.ex[max(range(len(sc)), key=lambda i: sc[i])].d
            victim = None
            for i, k in enumerate(st):
                if k not in lead:
                    victim = k; break
                if i >= 64: break
            if victim is None:
                # long run of keys the leader holds: rotate them to the back so later scans skip them
                for _ in range(len(st)):
                    victim = next(iter(st))
                    if victim not in lead: break
                    st.move_to_end(victim)
            del st[victim]
        st[key] = None
        return False
