from collections import OrderedDict, deque


class TrackSet(set):
    """A set that logs what was discarded from it."""

    out = None

    def log(self):
        self.out = deque()
        return self

    def discard(self, k):
        set.discard(self, k)
        self.out.append(k)



class LIRS:
    """LIRS with a bounded ghost list and a hill-climbed HIR share."""

    def __init__(self, capacity, hirfrac=0.05, ghostmult=2, period=0, step=0.05, hmax=0.5):
        self.cap = capacity
        self.hcap = max(1, int(capacity * hirfrac))
        self.S = OrderedDict()   # key -> True if LIR
        self.Q = OrderedDict()   # resident HIR
        self.ghosts = deque()
        self.glimit = int(capacity * ghostmult)
        self.lir = 0
        self.store = TrackSet().log()
        self.period = period * capacity
        self.n = self.hits = 0
        self.prev = 0.0
        self.step = step * capacity
        self.hmax = int(capacity * hmax)

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if S[k]:
                return
            del S[k]

    def _demote(self):
        S = self.S
        k = next(iter(S))
        del S[k]
        self.Q[k] = True
        self.lir -= 1
        self._prune()

    def _climb(self):
        rate = self.hits / self.n
        if rate < self.prev:
            self.step = -self.step
        self.prev = rate
        self.n = self.hits = 0
        self.hcap = int(min(self.hmax, max(1, self.hcap + self.step)))
        while self.lir > self.cap - self.hcap:
            self._demote()

    def _tick(self, hit):
        if self.period:
            self.n += 1
            self.hits += hit
            if self.n >= self.period:
                self._climb()
        return hit

    def access(self, key):
        S, Q = self.S, self.Q
        if key in self.store:
            if S.get(key):
                first = next(iter(S)) == key
                S.move_to_end(key)
                if first:
                    self._prune()
            elif key in S:
                del S[key]; S[key] = True
                del Q[key]
                self.lir += 1
                self._demote()
            else:
                S[key] = False
                Q.move_to_end(key)
            return self._tick(True)
        self.store.add(key)
        if self.lir < self.cap - self.hcap:
            S.pop(key, None); S[key] = True; self.lir += 1
            if len(self.store) > self.cap:
                k, _ = Q.popitem(last=False)
                self.store.discard(k)
            return self._tick(False)
        if len(self.store) > self.cap:
            k, _ = Q.popitem(last=False)
            self.store.discard(k)
            if k in S:
                self.ghosts.append(k)
                if len(self.ghosts) > self.glimit:
                    g = self.ghosts.popleft()
                    if g not in self.store and S.get(g) is False:
                        del S[g]
        if key in S:
            del S[key]; S[key] = True
            self.lir += 1
            self._demote()
        else:
            S[key] = False; Q[key] = True
        return self._tick(False)



class TLFU:
    """W-TinyLFU: small LRU window, SLRU main, frequency-gated admission."""

    def __init__(self, capacity, wfrac=0.01, prot=0.8, reset=10, fmax=15):
        self.cap = capacity
        self.wcap = max(1, int(capacity * wfrac))
        self.mcap = capacity - self.wcap
        self.pcap = int(self.mcap * prot)
        self.win, self.prob, self.prot = OrderedDict(), OrderedDict(), OrderedDict()
        self.freq = {}
        self.ops = 0
        self.reset = reset * capacity
        self.fmax = fmax
        self.store = TrackSet().log()

    def _inc(self, key):
        f = self.freq
        f[key] = min(f.get(key, 0) + 1, self.fmax)
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = {k: v >> 1 for k, v in f.items() if v > 1}

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
            if len(self.prob) + len(self.prot) < self.mcap:
                self.prob[cand] = True
            else:
                vq = self.prob if self.prob else self.prot
                victim = next(iter(vq))
                f = self.freq
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
        self.t1, self.t2, self.b1, self.b2 = OrderedDict(), OrderedDict(), OrderedDict(), OrderedDict()
        self.store = TrackSet().log()

    def _replace(self, key):
        if self.t1 and (len(self.t1) > self.p or (key in self.b2 and len(self.t1) == self.p)):
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
            self.p = min(c, self.p + max(len(self.b2) // max(len(self.b1), 1), 1))
            self._replace(key); del self.b1[key]; self.t2[key] = True
        elif key in self.b2:
            self.p = max(0, self.p - max(len(self.b1) // max(len(self.b2), 1), 1))
            self._replace(key); del self.b2[key]; self.t2[key] = True
        else:
            l1 = len(self.t1) + len(self.b1)
            if l1 == c:
                if len(self.t1) < c:
                    self.b1.popitem(last=False); self._replace(key)
                else:
                    k, _ = self.t1.popitem(last=False); self.store.discard(k)
            elif l1 < c and l1 + len(self.t2) + len(self.b2) >= c:
                if l1 + len(self.t2) + len(self.b2) == 2 * c:
                    self.b2.popitem(last=False)
                self._replace(key)
            self.t1[key] = True
        self.store.add(key)
        return False


class Cache:
    """Follow the leader over shadow policies: the real cache evicts what the best shadow evicted."""

    def __init__(self, capacity, decay=0.999, margin=1.0, kinds=None):
        if kinds is None:
            kinds = [lambda c: ARC(c), lambda c: TLFU(c, reset=20), lambda c: LIRS(c, hirfrac=0.01)]
        self.cap = capacity
        self.shadows = [k(capacity) for k in kinds]
        self.score = [0.0] * len(kinds)
        self.decay = decay
        self.margin = margin
        self.lead = 0
        self.store = set()

    def access(self, key):
        sc, d = self.score, self.decay
        for i, s in enumerate(self.shadows):
            sc[i] = sc[i] * d + s.access(key)
            if len(s.store.out) > 4 * self.cap:
                s.store.out.popleft()
        lead = self.lead
        for i in range(len(sc)):
            if sc[i] > sc[lead] + self.margin:
                lead = i
        self.lead = lead
        st = self.store
        if key in st:
            return True
        st.add(key)
        if len(st) > self.cap:
            ls = self.shadows[self.lead].store
            out = ls.out
            while out:
                k = out.pop()
                if k in st and k not in ls:
                    st.discard(k)
                    return False
            for k in st:
                if k not in ls:
                    st.discard(k)
                    return False
        return False
