from collections import OrderedDict, deque


class _WTLFU:
    """W-TinyLFU shadow over a shared frequency table."""

    def __init__(self, capacity, wfrac, protected=0.8, aging=0):
        self.capacity = capacity
        self.aging = aging
        self.freq = {}
        self.ops = 0
        self.store = {}
        self.log = None
        self.win = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.wcap = min(capacity - 1, max(1, int(capacity * wfrac)))
        self.pcap = int((capacity - self.wcap) * protected)

    def _drop(self, k):
        del self.store[k]
        if self.log is not None:
            self.log.append(k)

    def access(self, key, f):
        if self.aging:
            f = self.freq
            f[key] = f.get(key, 0) + 1
            self.ops += 1
            if self.ops >= self.aging:
                self.ops = 0
                self.freq = f = {k: v >> 1 for k, v in f.items() if v > 1}
        if key in self.store:
            if key in self.win:
                self.win.move_to_end(key)
            elif key in self.prot:
                self.prot.move_to_end(key)
            else:
                del self.prob[key]
                self.prot[key] = True
                if len(self.prot) > self.pcap:
                    k, _ = self.prot.popitem(last=False)
                    self.prob[k] = True
            return True
        self.store[key] = True
        self.win[key] = True
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.store) <= self.capacity:
                self.prob[cand] = True
            else:
                seg = self.prob or self.prot
                victim = next(iter(seg))
                if f.get(cand, 0) > f.get(victim, 0):
                    del seg[victim]
                    self._drop(victim)
                    self.prob[cand] = True
                else:
                    self._drop(cand)
        return False


class _ARC:
    """Adaptive replacement cache shadow."""

    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1, self.t2, self.b1, self.b2 = OrderedDict(), OrderedDict(), OrderedDict(), OrderedDict()
        self.store = {}
        self.log = None

    def _drop(self, k):
        del self.store[k]
        if self.log is not None:
            self.log.append(k)

    def _replace(self, inb2):
        if self.t1 and (len(self.t1) > self.p or (inb2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False)
            self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False)
            self.b2[k] = True
        self._drop(k)

    def access(self, key, f):
        c = self.c
        if key in self.t1:
            del self.t1[key]
            self.t2[key] = True
            return True
        if key in self.t2:
            self.t2.move_to_end(key)
            return True
        if key in self.b1:
            self.p = min(c, self.p + max(1, len(self.b2) // len(self.b1)))
            self._replace(False)
            del self.b1[key]
            self.t2[key] = True
            self.store[key] = True
            return False
        if key in self.b2:
            self.p = max(0, self.p - max(1, len(self.b1) // len(self.b2)))
            self._replace(True)
            del self.b2[key]
            self.t2[key] = True
            self.store[key] = True
            return False
        l1 = len(self.t1) + len(self.b1)
        if l1 == c:
            if len(self.t1) < c:
                self.b1.popitem(last=False)
                self._replace(False)
            else:
                k, _ = self.t1.popitem(last=False)
                self._drop(k)
        elif l1 < c and l1 + len(self.t2) + len(self.b2) >= c:
            if l1 + len(self.t2) + len(self.b2) == 2 * c:
                self.b2.popitem(last=False)
            self._replace(False)
        self.t1[key] = True
        self.store[key] = True
        return False


class _LIRS:
    """Low inter-reference recency set shadow."""

    def __init__(self, capacity, hir=0.01):
        self.c = capacity
        self.hcap = max(1, int(capacity * hir))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.lir = set()
        self.store = {}
        self.log = None

    def _prune(self):
        S, lir = self.S, self.lir
        while S:
            k = next(iter(S))
            if k in lir:
                return
            del S[k]

    def _demote(self):
        k, _ = self.S.popitem(last=False)
        self.lir.discard(k)
        self.Q[k] = True
        self._prune()

    def access(self, key, f):
        S, Q, lir = self.S, self.Q, self.lir
        if key in lir:
            bottom = next(iter(S)) == key
            S.move_to_end(key)
            if bottom:
                self._prune()
            return True
        if key in Q:
            if key in S:
                del Q[key]
                S.move_to_end(key)
                lir.add(key)
                self._demote()
            else:
                S[key] = True
                Q.move_to_end(key)
            return True
        if len(self.store) >= self.c:
            k, _ = Q.popitem(last=False)
            del self.store[k]
            if self.log is not None:
                self.log.append(k)
        self.store[key] = True
        if len(lir) < self.lcap:
            lir.add(key)
            S[key] = True
            S.move_to_end(key)
        elif key in S:
            S.move_to_end(key)
            lir.add(key)
            self._demote()
        else:
            S[key] = True
            Q[key] = True
        return False


class _LRU:
    """Least recently used shadow."""

    def __init__(self, capacity):
        self.c = capacity
        self.store = OrderedDict()
        self.log = None

    def access(self, key, f):
        s = self.store
        if key in s:
            s.move_to_end(key)
            return True
        if len(s) >= self.c:
            k, _ = s.popitem(last=False)
            if self.log is not None:
                self.log.append(k)
        s[key] = True
        return False


class Cache:
    """Shadow-simulates several policies and mirrors whichever has hit most recently."""

    FRACS = (0.01, 0.1, 0.3, 0.6)

    def __init__(self, capacity, sample=200, memory=4.0, margin=0.01, alpha=1.0):
        self.alpha = alpha
        self.window = memory * capacity
        self.capacity = capacity
        self.store = {}
        self.ghosts = [_WTLFU(capacity, w) for w in self.FRACS] + [_ARC(capacity), _LRU(capacity), _LIRS(capacity),
                                                              _WTLFU(capacity, 0.01, aging=2 * capacity)]
        self.scores = [0.0] * len(self.ghosts)
        self.decay = 1.0 - 1.0 / (memory * capacity)
        self.margin = margin * memory * capacity
        self.freq = {}
        self.ops = 0
        self.reset = sample * capacity
        self.best = 0
        self.rsc = 0.0
        self.doomed = deque()
        self.ghosts[0].log = self.doomed

    def access(self, key):
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = f = {k: v >> 1 for k, v in f.items() if v > 1}
        d = self.decay
        sc = self.scores
        gs = self.ghosts
        for i in range(len(gs)):
            sc[i] = sc[i] * d + gs[i].access(key, f)
        b = self.best
        top = max(sc[b], self.rsc) + self.margin
        for i in range(len(sc)):
            if sc[i] > top:
                b = i
                top = sc[i]
        lead = gs[b]
        if b != self.best:
            ls = lead.store
            s = self.store
            diff = 0
            for k in ls:
                if k not in s:
                    diff += 1
            if sc[b] - max(sc[self.best], self.rsc) < self.alpha * diff * sc[b] / self.window:
                b = self.best
                lead = gs[b]
        if b != self.best:
            gs[self.best].log = None
            self.best = b
            ls = lead.store
            self.doomed = deque(k for k in self.store if k not in ls)
            lead.log = self.doomed
        s = self.store
        self.rsc *= d
        if key in s:
            self.rsc += 1
            return True
        ls = lead.store
        dq = self.doomed
        while len(s) >= self.capacity:
            if not dq:
                del s[next(iter(s))]
                break
            k = dq.popleft()
            if k in s and k not in ls:
                del s[k]
        if key in ls:
            s[key] = True
        return False
