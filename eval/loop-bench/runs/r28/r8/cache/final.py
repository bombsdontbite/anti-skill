from collections import OrderedDict

FRACS = (0.01, 0.1, 0.3, 0.6, 0.95)
RESETS = (5, 25)
LIRS_FRACS = (0.01,)
HYST = 0.05


class _WT:
    """W-TinyLFU cache state over a shared frequency table."""

    def __init__(self, capacity, wcap, prot_frac):
        self.capacity = capacity
        self.wcap = wcap
        self.prot_frac = prot_frac
        self.store = {}
        self.window = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.score = 0.0

    def access(self, key, f):
        store = self.store
        if key in store:
            if key in self.window:
                self.window.move_to_end(key)
            elif key in self.prob:
                del self.prob[key]
                self.prot[key] = True
                pcap = int((self.capacity - self.wcap) * self.prot_frac)
                while len(self.prot) > pcap:
                    k, _ = self.prot.popitem(last=False)
                    self.prob[k] = True
            else:
                self.prot.move_to_end(key)
            return True
        store[key] = True
        self.window[key] = True
        mcap = self.capacity - self.wcap
        while len(self.window) > self.wcap:
            cand, _ = self.window.popitem(last=False)
            if len(self.prob) + len(self.prot) < mcap:
                self.prob[cand] = True
                continue
            vq = self.prob if self.prob else self.prot
            victim = next(iter(vq))
            if f.get(cand, 0) > f.get(victim, 0):
                del vq[victim]
                del store[victim]
                self.prob[cand] = True
            else:
                del store[cand]
        while len(self.prob) + len(self.prot) > mcap:
            vq = self.prob if self.prob else self.prot
            victim, _ = vq.popitem(last=False)
            del store[victim]
        return False


class _LIRS:
    """LIRS."""

    def __init__(self, capacity, hir_frac=0.01, ghost_mul=3):
        self.c = capacity
        self.hcap = max(1, int(capacity * hir_frac))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict()   # key -> True if LIR
        self.Q = OrderedDict()   # resident HIR
        self.store = {}
        self.nlir = 0
        self.smax = capacity * ghost_mul

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if S[k]:
                break
            del S[k]

    def _limit(self):
        S = self.S
        while len(S) > self.smax:
            for k in S:
                if not S[k] and k not in self.store:
                    del S[k]
                    break
            else:
                break

    def access(self, key):
        S, Q, st = self.S, self.Q, self.store
        if key in st:
            if S.get(key):
                S.move_to_end(key)
                self._prune()
            elif key in S:
                del S[key]; S[key] = True; del Q[key]
                self.nlir += 1
                k = next(iter(S))
                S[k] = False; del S[k]; Q[k] = True
                self.nlir -= 1
                self._prune()
            else:
                S[key] = False; Q.move_to_end(key)
            return True
        if self.nlir < self.lcap:
            st[key] = True; S[key] = True; self.nlir += 1
            return False
        if len(st) >= self.c:
            k, _ = Q.popitem(last=False); del st[k]
        st[key] = True
        if key in S:
            del S[key]; S[key] = True; self.nlir += 1
            k = next(iter(S))
            del S[k]; Q[k] = True; self.nlir -= 1
            self._prune()
        else:
            S[key] = False; Q[key] = True
        self._limit()
        return False


class Cache:
    """W-TinyLFU tuned by shadow caches; mirrors a LIRS shadow while that one leads clearly."""

    def __init__(self, capacity, prot_frac=0.8, period_mul=1.0, decay=0.8):
        self.capacity = capacity
        wc = lambda fr: min(capacity - 1, max(1, int(capacity * fr)))
        self.wts = []
        for fr in FRACS:
            for t in range(len(RESETS)):
                sh = _WT(capacity, wc(fr), prot_frac)
                sh.t = t
                self.wts.append(sh)
        self.lirs = [_LIRS(capacity, fr) for fr in LIRS_FRACS]
        for s in self.lirs:
            s.score = 0.0
        self.shadows = self.wts + self.lirs
        self.leader = self.shadows[0]
        self.main = _WT(capacity, self.leader.wcap, prot_frac)
        self.main.t = 0
        self.main.store = self.store = OrderedDict()
        self.freqs = [{} for _ in RESETS]
        self.ops = [0] * len(RESETS)
        self.reset_at = [r * capacity for r in RESETS]
        self.period = max(50, int(capacity * period_mul))
        self.n = 0
        self.decay = decay

    def access(self, key):
        fs = self.freqs
        for i, f in enumerate(fs):
            f[key] = f.get(key, 0) + 1
            self.ops[i] += 1
            if self.ops[i] >= self.reset_at[i]:
                self.ops[i] = 0
                fs[i] = {k: v >> 1 for k, v in f.items() if v > 1}
        for s in self.wts:
            if s.access(key, fs[s.t]):
                s.score += 1
        for s in self.lirs:
            if s.access(key):
                s.score += 1
        self.n += 1
        if self.n >= self.period:
            self.n = 0
            best = max(self.shadows, key=lambda s: s.score)
            if ((best in self.lirs) == (self.leader in self.lirs)
                    or best.score > self.leader.score * (1 + HYST) + 1):
                m = self.main
                if self.leader in self.lirs and best not in self.lirs:
                    m.window = OrderedDict()
                    m.prob = OrderedDict((k, True) for k in self.store)
                    m.prot = OrderedDict()
                self.leader = best
                if best not in self.lirs:
                    m.wcap = best.wcap
                    m.t = best.t
            for s in self.shadows:
                s.score *= self.decay
        if self.leader not in self.lirs:
            return self.main.access(key, fs[self.main.t])
        st = self.store
        if key in st:
            st.move_to_end(key)
            return True
        lead = self.leader.store
        if len(st) < self.capacity:
            st[key] = True
        elif key in lead:
            for k in st:
                if k not in lead:
                    break
            else:
                k = next(iter(st))
            del st[k]
            st[key] = True
        return False
