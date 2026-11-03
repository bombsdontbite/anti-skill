from collections import OrderedDict, deque


class LogSet(set):
    def discard(self, k):
        set.discard(self, k)
        self.ev.append(k)


class LIRS:
    """LIRS: low inter-reference recency set; 1% resident HIR, bounded ghost stack."""

    def __init__(self, capacity, hir=0.01, ghost=2.0):
        self.cap = capacity
        self.hcap = max(1, int(capacity * hir))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict()   # key -> True if LIR
        self.Q = OrderedDict()   # resident HIR
        self.lir = 0
        self.nonres = 0
        self.smax = int(capacity * ghost) + capacity
        self.store = LogSet()
        self.store.ev = []

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if S[k]:
                break
            del S[k]
            if k not in self.store:
                self.nonres -= 1

    def _demote_bottom(self):
        S = self.S
        k, _ = S.popitem(last=False)
        self.lir -= 1
        self.Q[k] = True
        self._prune()

    def _limit(self):
        # drop oldest non-resident HIR entries from S when too many ghosts
        excess = self.nonres - (self.smax - self.cap)
        if excess > 0:
            S, store = self.S, self.store
            excess += self.cap // 8
            drop = []
            for k, lir in S.items():
                if not lir and k not in store:
                    drop.append(k)
                    if len(drop) >= excess:
                        break
            for k in drop:
                del S[k]
            self.nonres -= len(drop)

    def access(self, key):
        S, Q, store = self.S, self.Q, self.store
        if key in store:
            if S.get(key):
                first = next(iter(S)) == key
                S.move_to_end(key)
                if first:
                    self._prune()
            elif key in S:
                del S[key]
                del Q[key]
                S[key] = True
                self.lir += 1
                self._demote_bottom()
            else:
                Q.move_to_end(key)
                S[key] = False
            return True
        if self.lir < self.lcap:
            store.add(key)
            if key in S:
                del S[key]
                self.nonres -= 1
            S[key] = True
            self.lir += 1
            return False
        if len(store) >= self.cap:
            v, _ = Q.popitem(last=False)
            store.discard(v)
            if v in S:
                self.nonres += 1
        store.add(key)
        if key in S:
            del S[key]
            self.nonres -= 1
            S[key] = True
            self.lir += 1
            self._demote_bottom()
        else:
            S[key] = False
            Q[key] = True
            self._limit()
        return False



class ARC:
    """ARC: adaptive replacement cache."""

    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1 = OrderedDict()
        self.t2 = OrderedDict()
        self.b1 = OrderedDict()
        self.b2 = OrderedDict()
        self.store = LogSet()
        self.store.ev = []

    def _replace(self, in_b2):
        t1 = self.t1
        if t1 and (len(t1) > self.p or (in_b2 and len(t1) == self.p)):
            k, _ = t1.popitem(last=False)
            self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False)
            self.b2[k] = True
        self.store.discard(k)

    def access(self, key):
        c = self.c
        if key in self.t1:
            del self.t1[key]
            self.t2[key] = True
            return True
        if key in self.t2:
            self.t2.move_to_end(key)
            return True
        b1, b2 = self.b1, self.b2
        if key in b1:
            self.p = min(c, self.p + max(1, len(b2) // len(b1)))
            self._replace(False)
            del b1[key]
            self.t2[key] = True
        elif key in b2:
            self.p = max(0, self.p - max(1, len(b1) // len(b2)))
            self._replace(True)
            del b2[key]
            self.t2[key] = True
        else:
            l1 = len(self.t1) + len(b1)
            if l1 == c:
                if len(self.t1) < c:
                    b1.popitem(last=False)
                    self._replace(False)
                else:
                    k, _ = self.t1.popitem(last=False)
                    self.store.discard(k)
            else:
                tot = l1 + len(self.t2) + len(b2)
                if tot >= c:
                    if tot == 2 * c:
                        b2.popitem(last=False)
                    self._replace(False)
            self.t1[key] = True
        self.store.add(key)
        return False




class TLFU:
    """W-TinyLFU: 1% LRU window, SLRU main, frequency-sketch admission with aging."""

    def __init__(self, capacity, win=0.01, reset=10):
        self.cap = capacity
        self.wcap = max(1, int(capacity * win))
        self.mcap = capacity - self.wcap
        self.pcap = int(self.mcap * 0.8)
        self.win = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.freq = {}
        self.ops = 0
        self.reset = reset * capacity
        self.store = LogSet()
        self.store.ev = []

    def _inc(self, key):
        f = self.freq
        f[key] = min(15, f.get(key, 0) + 1)
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = {k: v >> 1 for k, v in f.items() if v > 1}

    def access(self, key):
        self._inc(key)
        if key in self.win:
            self.win.move_to_end(key)
            return True
        if key in self.prot:
            self.prot.move_to_end(key)
            return True
        if key in self.prob:
            del self.prob[key]
            self.prot[key] = True
            if len(self.prot) > self.pcap:
                k, _ = self.prot.popitem(last=False)
                self.prob[k] = True
            return True
        self.store.add(key)
        self.win[key] = True
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mcap:
                self.prob[cand] = True
            else:
                vic = next(iter(self.prob)) if self.prob else next(iter(self.prot))
                f = self.freq
                if f.get(cand, 0) > f.get(vic, 0):
                    if self.prob:
                        self.prob.popitem(last=False)
                    else:
                        self.prot.popitem(last=False)
                    self.store.discard(vic)
                    self.prob[cand] = True
                else:
                    self.store.discard(cand)
        return False



class S3:
    """S3-FIFO: small FIFO (10%), main FIFO with reinsertion, ghost FIFO."""

    def __init__(self, capacity):
        self.cap = capacity
        self.scap = max(1, capacity // 10)
        self.small = deque()
        self.main = deque()
        self.ghost = OrderedDict()
        self.freq = {}
        self.where = {}
        self.store = LogSet()
        self.store.ev = []

    def _evict_main(self):
        while True:
            k = self.main.popleft()
            f = self.freq[k]
            if f > 0:
                self.freq[k] = f - 1
                self.main.append(k)
            else:
                del self.freq[k]
                self.store.discard(k)
                return

    def _evict(self):
        if len(self.small) >= self.scap or not self.main:
            k = self.small.popleft()
            if self.freq[k] > 0:
                self.freq[k] = 0
                self.main.append(k)
                if len(self.main) > self.cap - len(self.small):
                    self._evict_main()
            else:
                del self.freq[k]
                self.store.discard(k)
                self.ghost[k] = True
                if len(self.ghost) > self.cap:
                    self.ghost.popitem(last=False)
        else:
            self._evict_main()

    def access(self, key):
        if key in self.store:
            self.freq[key] = min(3, self.freq[key] + 1)
            return True
        while len(self.store) >= self.cap:
            self._evict()
        self.store.add(key)
        self.freq[key] = 0
        if key in self.ghost:
            del self.ghost[key]
            self.main.append(key)
        else:
            self.small.append(key)
        return False


def TLFU2(capacity):
    return TLFU(capacity, 0.2, 10)


class Cache:
    """Runs several policies as shadows; the real store follows whichever hit most recently."""

    def __init__(self, capacity, half=2.0, margin=0.03, pols=None, away=0.03, beta=0.0, longh=20.0, rho=1.0):
        self.rho = rho
        self.lsc = [0.0] * 8
        self.ld = 1.0 - 1.0 / (longh * capacity)
        self.beta = beta
        self.t = 0
        self.check = 0
        if pols is None:
            pols = (LIRS, ARC, TLFU, TLFU2)
        self.away = away * capacity
        self.cap = capacity
        self.pol = [P(capacity) for P in pols]
        self.score = [0.0] * len(self.pol)
        self.decay = 1.0 - 1.0 / (half * capacity)
        self.margin = margin * capacity
        self.lead = 0
        self.pending = []
        self.store = set()

    def access(self, key):
        store = self.store
        hit = key in store
        sc, d = self.score, self.decay
        lsc, ld = self.lsc, self.ld
        best = 0
        for i, p in enumerate(self.pol):
            h = 1.0 if p.access(key) else 0.0
            sc[i] = sc[i] * d + h
            lsc[i] = lsc[i] * ld + h
            if sc[i] > sc[best]:
                best = i
        lead = self.pol[self.lead]
        if lead.store.ev:
            for k in lead.store.ev:
                store.discard(k)
        for p in self.pol:
            p.store.ev.clear()
        self.t += 1
        gap = sc[best] - sc[self.lead] - (self.away if best else self.margin)
        if gap > 0 and lsc[best] > self.rho * lsc[self.lead] and self.t >= self.check:
            self.check = self.t + 16
            ls = self.pol[best].store
            stale = [k for k in store if k not in ls]
            if gap > self.beta * len(stale):
                self.lead = best
                others = [p.store for p in self.pol if p.store is not ls]
                pend = [(sum(k in o for o in others), k) for k in stale]
                pend.sort(reverse=True)
                self.pending = [k for _, k in pend]
        if hit:
            return True
        ls = self.pol[self.lead].store
        if key not in ls:
            return False
        if len(store) >= self.cap:
            pend = self.pending
            while pend:
                k = pend.pop()
                if k in store and k not in ls:
                    store.discard(k)
                    break
        store.add(key)
        return False
