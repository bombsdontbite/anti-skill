from collections import OrderedDict


class LIRS:
    """LIRS with a hill-climbing HIR size."""

    def __init__(self, capacity, hir_frac=0.01, sample_mult=10, step_frac=0.03, max_frac=0.5):
        self.c = capacity
        self.hcap = max(1, int(capacity * hir_frac))
        self.llirs = capacity - self.hcap
        self.sample = sample_mult * capacity
        self.step = max(1, int(capacity * step_frac))
        self.hmax = max(1, int(capacity * max_frac))
        self.dir = 1
        self.n = self.hits = 0
        self.prev = None
        self.S = OrderedDict()  # key -> True; oldest first
        self.Q = OrderedDict()  # resident HIR keys
        self.lir = set()
        self.store = set()

    def _prune(self):
        S, lir = self.S, self.lir
        while S:
            k = next(iter(S))
            if k in lir:
                return
            del S[k]

    def _demote_bottom(self):
        S = self.S
        k, _ = S.popitem(last=False)
        self.lir.discard(k)
        self.Q[k] = True
        self._prune()

    def access(self, key):
        hit = self._access(key)
        self.n += 1
        if hit:
            self.hits += 1
        if self.n >= self.sample:
            self._climb()
        return hit

    def _climb(self):
        rate = self.hits / self.n
        if self.prev is not None and rate < self.prev:
            self.dir = -self.dir
        self.prev = rate
        self.n = self.hits = 0
        self.hcap = min(self.hmax, max(1, self.hcap + self.dir * self.step))
        self.llirs = self.c - self.hcap
        while len(self.lir) > self.llirs:
            self._demote_bottom()

    def _access(self, key):
        S, Q, lir = self.S, self.Q, self.lir
        if key in lir:
            S.move_to_end(key)
            self._prune()
            return True
        if key in Q:
            if key in S:
                del Q[key]; lir.add(key); S.move_to_end(key)
                self._demote_bottom()
            else:
                S[key] = True; Q.move_to_end(key)
            return True
        if len(self.store) >= self.c:
            k, _ = Q.popitem(last=False)
            self.store.discard(k)
        self.store.add(key)
        if len(lir) < self.llirs:
            lir.add(key); S[key] = True; S.move_to_end(key)
        elif key in S:
            lir.add(key); S.move_to_end(key)
            self._demote_bottom()
        else:
            S[key] = True; Q[key] = True
        return False


class TinyLFU:
    """W-TinyLFU with a hill-climbing window size."""

    def __init__(self, capacity, sample_mult=10, step_frac=0.0625, reset_mult=10, window_frac=0.01, fmax=15, prot=0.8):
        self.c = capacity
        self.fmax = fmax
        self.protf = prot
        self.wcap = max(1, int(capacity * window_frac))
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.freq = {}
        self.ops = 0
        self.reset = reset_mult * capacity
        self.store = set()
        self.sample = sample_mult * capacity
        self.step = max(1, int(capacity * step_frac))
        self.dir = 1
        self.n = 0; self.hits = 0; self.prev = None

    def _climb(self):
        rate = self.hits / self.n
        if self.prev is not None and rate < self.prev:
            self.dir = -self.dir
        self.prev = rate
        self.n = self.hits = 0
        self.wcap = min(self.c - 1, max(1, self.wcap + self.dir * self.step))
        while len(self.win) > self.wcap:
            k, _ = self.win.popitem(last=False); self.prob[k] = True
        self._trim_main()

    def _trim_main(self):
        mcap = self.c - self.wcap
        while len(self.prob) + len(self.prot) > mcap:
            vq = self.prob if self.prob else self.prot
            k, _ = vq.popitem(last=False); self.store.discard(k)
        pcap = int(mcap * self.protf)
        while len(self.prot) > pcap:
            k, _ = self.prot.popitem(last=False); self.prob[k] = True

    def access(self, key):
        hit = self._access(key)
        self.n += 1
        if hit:
            self.hits += 1
        if self.n >= self.sample:
            self._climb()
        return hit

    def _access(self, key):
        f = self.freq
        f[key] = min(f.get(key, 0) + 1, self.fmax)
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = f = {k: v >> 1 for k, v in f.items() if v > 1}
        if key in self.win:
            self.win.move_to_end(key); return True
        if key in self.prot:
            self.prot.move_to_end(key); return True
        if key in self.prob:
            del self.prob[key]; self.prot[key] = True
            if len(self.prot) > int((self.c - self.wcap) * self.protf):
                k, _ = self.prot.popitem(last=False); self.prob[k] = True
            return True
        self.win[key] = True; self.store.add(key)
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.c - self.wcap:
                self.prob[cand] = True
            else:
                vq = self.prob if self.prob else self.prot
                victim = next(iter(vq))
                if f.get(cand, 0) > f.get(victim, 0):
                    del vq[victim]; self.store.discard(victim); self.prob[cand] = True
                else:
                    self.store.discard(cand)
        return False


class ARC:
    """ARC."""

    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = set()

    def _replace(self, in_b2):
        if self.t1 and (len(self.t1) > self.p or (in_b2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = True
        self.store.discard(k)

    def access(self, key):
        c = self.c
        if key in self.t1:
            del self.t1[key]; self.t2[key] = True; return True
        if key in self.t2:
            self.t2.move_to_end(key); return True
        if key in self.b1:
            self.p = min(c, self.p + max(len(self.b2) // len(self.b1), 1))
            self._replace(False); del self.b1[key]; self.t2[key] = True
        elif key in self.b2:
            self.p = max(0, self.p - max(len(self.b1) // len(self.b2), 1))
            self._replace(True); del self.b2[key]; self.t2[key] = True
        else:
            l1 = len(self.t1) + len(self.b1)
            if l1 == c:
                if len(self.t1) < c:
                    self.b1.popitem(last=False); self._replace(False)
                else:
                    k, _ = self.t1.popitem(last=False); self.store.discard(k)
            elif l1 < c:
                tot = l1 + len(self.t2) + len(self.b2)
                if tot >= c:
                    if tot == 2 * c:
                        self.b2.popitem(last=False)
                    if len(self.t1) + len(self.t2) >= c:
                        self._replace(False)
            self.t1[key] = True
        self.store.add(key)
        return False


class Cache:
    """Follows whichever shadow policy has the most recent hits."""

    def __init__(self, capacity, decay_mult=100.0):
        self.c = capacity
        self.shadows = [LIRS(capacity), TinyLFU(capacity, reset_mult=80), ARC(capacity)]
        for sh in self.shadows:
            sh.sample = 1 << 60  # fixed sizes: the meta-policy does the adapting
        self.scores = [0.0] * len(self.shadows)
        self.keep = 1.0 - 1.0 / (decay_mult * capacity)
        self.leader = 0
        self.store = OrderedDict()

    def access(self, key):
        scores = self.scores
        keep = self.keep
        for i, s in enumerate(self.shadows):
            scores[i] = scores[i] * keep + s.access(key)
        best = self.leader
        for i in range(len(scores)):
            if scores[i] > scores[best]:
                best = i
        self.leader = best
        store = self.store
        if key in store:
            store.move_to_end(key)
            return True
        if len(store) >= self.c:
            lead = self.shadows[best].store
            for k in store:
                if k not in lead:
                    break
            del store[k]
        store[key] = True
        return False
