from collections import OrderedDict


class _Log(set):
    def discard(self, k):
        set.discard(self, k)
        self.ev.append(k)


class _LIRS:
    """LIRS with the resident-HIR share hill-climbed on the hit rate."""

    HIR = 0.05
    GHOST = 2.0
    SAMPLE = 10
    STEP = 0.03
    DECAY = 0.98
    HMAX = 0.5

    def __init__(self, capacity):
        self.cap = capacity
        self.hcap = max(1, int(capacity * self.HIR))
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.lir = set(); self.store = set()
        self.nghost = 0
        self.period = self.SAMPLE * capacity
        self.n = 0; self.hits = 0; self.prev = -1.0
        self.step = capacity * self.STEP

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if k in self.lir: return
            del S[k]
            if k not in self.store: self.nghost -= 1

    def _demote(self):
        k = next(iter(self.S))
        self.lir.discard(k); self.Q[k] = True
        self._prune()

    def _climb(self):
        rate = self.hits / self.n
        if rate < self.prev:
            self.step = -self.step
        self.step *= self.DECAY
        if abs(self.step) < 1:
            self.step = 1 if self.step > 0 else -1
        self.prev = rate; self.n = 0; self.hits = 0
        self.hcap = int(min(self.cap * self.HMAX, max(1, self.hcap + self.step)))

    def _hit(self, key):
        S, lir = self.S, self.lir
        if key in lir:
            first = next(iter(S)) == key
            S.move_to_end(key)
            if first: self._prune()
            return True
        if key in self.store:
            if key in S:
                S.move_to_end(key); del self.Q[key]; lir.add(key)
                self._demote()
            else:
                S[key] = True; self.Q.move_to_end(key)
            return True
        return False

    def access(self, key):
        self.n += 1
        if self.n >= self.period:
            self._climb()
        if self._hit(key):
            self.hits += 1
            return True
        S, Q, lir = self.S, self.Q, self.lir
        lcap = self.cap - self.hcap
        while len(lir) > lcap:
            self._demote()
        if len(self.store) >= self.cap:
            if not Q: self._demote()
            v, _ = Q.popitem(last=False); self.store.discard(v)
            if v in S: self.nghost += 1
        self.store.add(key)
        ghost = key in S
        if ghost: self.nghost -= 1
        S[key] = True; S.move_to_end(key)
        if len(lir) < lcap:
            lir.add(key)
        elif ghost:
            lir.add(key); self._demote()
        else:
            Q[key] = True
        if self.nghost > self.GHOST * self.cap:
            for k in [k for k in S if k not in self.store][: self.nghost // 2]:
                del S[k]
            self.nghost = sum(1 for k in S if k not in self.store)
            self._prune()
        return False


class _TLFU:
    """W-TinyLFU with a hill-climbed window size."""

    WIN0 = 0.01
    PROT = 0.8
    AGE = 5
    SAMPLE = 10
    STEP = 0.0625
    DECAY = 0.98
    TIE = 0

    def __init__(self, capacity):
        self.cap = capacity
        self.wcap = max(1, int(capacity * self.WIN0))
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.freq = {}; self.ops = 0; self.reset = self.AGE * capacity
        self.store = set()
        self.period = self.SAMPLE * capacity
        self.n = 0; self.hits = 0; self.prev = -1.0
        self.step = capacity * self.STEP

    def _inc(self, k):
        self.freq[k] = self.freq.get(k, 0) + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = {k: v >> 1 for k, v in self.freq.items() if v > 1}

    def _climb(self):
        rate = self.hits / self.n
        if rate < self.prev:
            self.step = -self.step
        self.step *= self.DECAY
        if abs(self.step) < 1:
            self.step = 1 if self.step > 0 else -1
        self.prev = rate; self.n = 0; self.hits = 0
        self.wcap = int(min(self.cap - 1, max(1, self.wcap + self.step)))

    def _hit(self, key):
        if key in self.win:
            self.win.move_to_end(key); return True
        if key in self.prot:
            self.prot.move_to_end(key); return True
        if key in self.prob:
            del self.prob[key]; self.prot[key] = True
            pcap = int((self.cap - self.wcap) * self.PROT)
            while len(self.prot) > pcap:
                k, _ = self.prot.popitem(last=False); self.prob[k] = True
            return True
        return False

    def _main_victim(self):
        return next(iter(self.prob)) if self.prob else next(iter(self.prot))

    def _drop_main(self, k):
        if k in self.prob: del self.prob[k]
        else: del self.prot[k]
        self.store.discard(k)

    def access(self, key):
        self._inc(key)
        self.n += 1
        if self.n >= self.period:
            self._climb()
        if self._hit(key):
            self.hits += 1
            return True
        self.win[key] = True; self.store.add(key)
        while len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.store) <= self.cap:
                self.prob[cand] = True
                continue
            if not (self.prob or self.prot):
                self.store.discard(cand); continue
            victim = self._main_victim()
            f = self.freq.get
            if f(cand, 0) + self.TIE > f(victim, 0):
                self._drop_main(victim); self.prob[cand] = True
            else:
                self.store.discard(cand)
        while len(self.store) > self.cap:
            if self.prob or self.prot:
                self._drop_main(self._main_victim())
            else:
                k, _ = self.win.popitem(last=False); self.store.discard(k)
        return False


class _FTLFU:
    """W-TinyLFU: LRU window + SLRU main, admission by aged frequency counts."""
    AGE = 10
    WIN = 0.01
    PROT = 0.8

    def __init__(self, capacity):
        self.cap = capacity
        self.wcap = max(1, int(capacity * self.WIN))
        mcap = capacity - self.wcap
        self.pcap = int(mcap * self.PROT)
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.freq = {}; self.ops = 0; self.reset = self.AGE * capacity
        self.store = set()

    def _inc(self, k):
        self.freq[k] = self.freq.get(k, 0) + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = {k: v >> 1 for k, v in self.freq.items() if v > 1}

    def access(self, key):
        self._inc(key)
        if key in self.win:
            self.win.move_to_end(key); return True
        if key in self.prot:
            self.prot.move_to_end(key); return True
        if key in self.prob:
            del self.prob[key]; self.prot[key] = True
            if len(self.prot) > self.pcap:
                k, _ = self.prot.popitem(last=False); self.prob[k] = True
            return True
        self.win[key] = True; self.store.add(key)
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.cap - self.wcap:
                self.prob[cand] = True
            else:
                victim = next(iter(self.prob)) if self.prob else next(iter(self.prot))
                f = self.freq.get
                if f(cand, 0) > f(victim, 0):
                    if victim in self.prob: del self.prob[victim]
                    else: del self.prot[victim]
                    self.store.discard(victim); self.prob[cand] = True
                else:
                    self.store.discard(cand)
        return False


class _ARC:
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
                    self._replace(False)
            self.t1[key] = True
        self.store.add(key)
        return False


class _FREQ(_FTLFU):
    AGE = 40
    PROT = 0.95


class _LIRS2(_LIRS):
    HIR = 0.01
    HMAX = 0.01


class _LRU:
    def __init__(self, capacity):
        self.cap = capacity
        self.od = OrderedDict()
        self.store = set()

    def access(self, key):
        od = self.od
        if key in od:
            od.move_to_end(key); return True
        if len(od) >= self.cap:
            k, _ = od.popitem(last=False); self.store.discard(k)
        od[key] = True; self.store.add(key)
        return False


class Cache:
    """Simulates several policies and caches what the recently best one would hold."""

    WIN = 20
    MARGIN = 0.02

    def __init__(self, capacity):
        self.cap = capacity
        self.store = set()
        self.pols = [_LIRS(capacity), _TLFU(capacity), _ARC(capacity), _FREQ(capacity), _LIRS2(capacity)]
        for p in self.pols:
            p.store = _Log(); p.store.ev = []
        self.sc = [0.0] * len(self.pols)
        self.d = 1 - 1 / (self.WIN * capacity)
        self.lead = 0
        self.stale = OrderedDict()

    def access(self, key):
        hit = key in self.store
        d = self.d; sc = self.sc
        for i, p in enumerate(self.pols):
            sc[i] = sc[i] * d + p.access(key)
        best = max(range(len(sc)), key=lambda i: sc[i])
        L = self.pols[self.lead]
        st = self.stale; real = self.store
        if best != self.lead and sc[best] > sc[self.lead] * (1 + self.MARGIN) + 1:
            self.lead = best; L = self.pols[best]
            st.clear()
            for k in real:
                if k not in L.store: st[k] = True
        else:
            for k in L.store.ev:
                if k in real: st[k] = True
        for p in self.pols:
            p.store.ev.clear()
        if key in L.store:
            if key in st:
                del st[key]
            elif key not in real:
                if len(real) >= self.cap:
                    k, _ = st.popitem(last=False); real.discard(k)
                real.add(key)
        return hit
