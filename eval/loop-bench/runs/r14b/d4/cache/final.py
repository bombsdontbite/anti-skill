from collections import OrderedDict
import heapq


class Lirs:
    """LIRS."""

    def __init__(self, capacity, hir=0.01):
        self.c = capacity
        self.hcap = max(1, int(capacity * hir))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict()   # key -> True ; recency stack (LIR, resident HIR, nonresident HIR)
        self.Q = OrderedDict()   # resident HIR
        self.lir = set()
        self.store = {}
        self.nonres = 0

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if k in self.lir:
                break
            del S[k]
            if k not in self.store:
                self.nonres -= 1

    def access(self, key):
        self.out = None
        S, Q, lir, store = self.S, self.Q, self.lir, self.store
        if key in lir:
            first = next(iter(S)) == key
            S.move_to_end(key)
            if first:
                self._prune()
            return True
        if key in store:
            if key in S:
                S.move_to_end(key)
                del Q[key]
                lir.add(key)
                k = next(iter(S))
                lir.discard(k); del S[k]; Q[k] = True
                self._prune()
            else:
                S[key] = True
                Q.move_to_end(key)
            return True
        # miss
        if len(lir) < self.lcap:
            lir.add(key); store[key] = True
            if key in S:
                self.nonres -= 1
            S[key] = True
            return False
        if len(Q) >= self.hcap:
            k, _ = Q.popitem(last=False)
            del store[k]
            self.out = k
            if k in S:
                self.nonres += 1
        store[key] = True
        if key in S:
            self.nonres -= 1
            S.move_to_end(key)
            lir.add(key)
            k = next(iter(S))
            lir.discard(k); del S[k]; Q[k] = True
            self._prune()
        else:
            S[key] = True
            Q[key] = True
        # bound nonresident history
        if self.nonres > 2 * self.c:
            for k in list(S):
                if k not in store:
                    del S[k]; self.nonres -= 1
                    if self.nonres <= self.c:
                        break
            self._prune()
        return False



class Pred:
    """Approximate Belady: evict the key whose predicted next access is furthest away."""

    def __init__(self, capacity, alpha=0.5, new=16.0, overdue=1.1, hist=4, N=16):
        self.c = capacity
        self.store = OrderedDict()
        self.last = {}
        self.gap = {}
        self.heap = []
        self.t = 0
        self.alpha = alpha
        self.new = new * capacity
        self.overdue = overdue
        self.hist = hist * capacity
        self.N = N
        self.cnt = {}

    def _pred(self, key):
        g = self.gap.get(key)
        return self.last[key] + (self.new if g is None else g)

    def access(self, key):
        self.out = None
        t = self.t = self.t + 1
        last, gap = self.last, self.gap
        if key in last:
            ng = t - last[key]
            g = gap.get(key)
            if g is None:
                gap[key] = ng
                self.cnt[key] = 1
            else:
                n = self.cnt[key] = min(self.cnt[key] + 1, self.N)
                a = max(self.alpha, 1 - 1 / n)
                gap[key] = a * g + (1 - a) * ng
        last[key] = t
        store = self.store
        if key in store:
            store.move_to_end(key)
            heapq.heappush(self.heap, (-self._pred(key), t, key))
            return True
        if len(store) >= self.c:
            old = next(iter(store))
            g = gap.get(old)
            if t - last[old] > self.overdue * (self.new if g is None else g):
                victim = old
            else:
                h = self.heap
                while True:
                    p, tt, k = heapq.heappop(h)
                    if k in store and last[k] == tt:
                        victim = k
                        break
            del store[victim]
            self.out = victim
        store[key] = True
        heapq.heappush(self.heap, (-self._pred(key), t, key))
        if len(last) > 2 * self.hist + self.c:
            cut = t - self.hist
            for k in [k for k, v in last.items() if v < cut and k not in store]:
                del last[k]
                gap.pop(k, None)
                self.cnt.pop(k, None)
        if len(self.heap) > 8 * self.c:
            self.heap = [e for e in self.heap if e[2] in store and last[e[2]] == e[1]]
            heapq.heapify(self.heap)
        return False


class Tlfu:
    """W-TinyLFU: LRU window, SLRU main, frequency-gated admission."""

    def __init__(self, capacity, window=0.01, protected=0.4, sample=10, maxf=7):
        self.capacity = capacity
        self.store = {}
        self.wcap = max(1, int(capacity * window))
        self.mcap = capacity - self.wcap
        self.pcap = int(self.mcap * protected)
        self.win = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.freq = {}
        self.ops = 0
        self.reset = sample * capacity
        self.maxf = maxf

    def _count(self, key):
        f = self.freq
        v = f.get(key, 0)
        if v < self.maxf:
            f[key] = v + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops //= 2
            self.freq = {k: v >> 1 for k, v in f.items() if v > 1}

    def access(self, key):
        self.out = None
        self._count(key)
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
            if len(self.prob) + len(self.prot) < self.mcap:
                self.prob[cand] = True
            else:
                victim = next(iter(self.prob)) if self.prob else next(iter(self.prot))
                f = self.freq
                if f.get(cand, 0) > f.get(victim, 0):
                    if victim in self.prob:
                        del self.prob[victim]
                    else:
                        del self.prot[victim]
                    del self.store[victim]
                    self.out = victim
                    self.prob[cand] = True
                else:
                    del self.store[cand]
                    self.out = cand
        return False


class Lru:
    def __init__(self, capacity):
        self.capacity = capacity
        self.store = OrderedDict()
        self.out = None

    def access(self, key):
        self.out = None
        if key in self.store:
            self.store.move_to_end(key)
            return True
        if len(self.store) >= self.capacity:
            self.out = self.store.popitem(last=False)[0]
        self.store[key] = True
        return False


class Hawk:
    """Hawkeye-style: replay Belady on past reuses to label each key cache-friendly or averse;
    evict averse keys first, then the least recently used friendly key."""

    def __init__(self, capacity, quanta=8, window=16, top=3, thr=2, init=1, mru=1, slack=0.8):
        self.c = capacity
        self.q = max(1, capacity // quanta)
        self.W = window * quanta
        self.occ = [0] * self.W
        self.cur = 0
        self.t = 0
        self.lastq = {}
        self.pred = {}
        self.top, self.thr, self.init = top, thr, init
        self.mru = mru
        self.cq = slack * capacity
        self.fr = OrderedDict()
        self.av = OrderedDict()
        self.store = {}

    def _train(self, key):
        cur = self.cur
        lq = self.lastq.get(key)
        self.lastq[key] = cur
        if lq is None or cur - lq >= self.W:
            return
        p = self.pred.get(key, self.init)
        if lq == cur:
            self.pred[key] = min(self.top, p + 1)
            return
        occ, W, c = self.occ, self.W, self.cq
        idx = [i % W for i in range(lq, cur)]
        if max(occ[i] for i in idx) < c:
            for i in idx:
                occ[i] += 1
            self.pred[key] = min(self.top, p + 1)
        else:
            self.pred[key] = max(0, p - 1)

    def access(self, key):
        self.out = None
        self.t += 1
        if self.t % self.q == 0:
            self.cur += 1
            self.occ[self.cur % self.W] = 0
            if len(self.lastq) > 4 * self.W * self.q:
                lim = self.cur - self.W
                self.lastq = {k: v for k, v in self.lastq.items() if v > lim}
                self.pred = {k: v for k, v in self.pred.items() if k in self.lastq or k in self.store}
        self._train(key)
        good = self.pred.get(key, self.init) >= self.thr
        store, fr, av = self.store, self.fr, self.av
        if key in store:
            if key in fr:
                del fr[key]
            else:
                del av[key]
            (fr if good else av)[key] = True
            return True
        if len(store) >= self.c:
            if av:
                k = av.popitem(last=bool(self.mru))[0]
            else:
                k = fr.popitem(last=False)[0]
                self.pred[k] = max(0, self.pred.get(k, self.init) - 1)
            del store[k]
            self.out = k
        store[key] = True
        (fr if good else av)[key] = True
        return False


class Cache:
    """Runs several policies as shadow caches and follows the one with more recent hits.
    Keys the leader has dropped stay cached until room is needed."""

    def __init__(self, capacity, decay=0.00003, margin=30.0, kinds=None):
        self.capacity = capacity
        if kinds is None:
            kinds = ((Lirs, {}), (Pred, {}), (Pred, {"overdue": 2.0}), (Lru, {}), (Tlfu, {}), (Hawk, {}))
        self.shadows = [k(capacity, **kw) for k, kw in kinds]
        self.score = [0.0] * len(self.shadows)
        self.lead = 0
        self.decay = 1 - decay
        self.margin = margin
        self.store = set()
        self.spare = OrderedDict()

    def access(self, key):
        store, spare = self.store, self.spare
        hit = key in store
        sc, d = self.score, self.decay
        for i, s in enumerate(self.shadows):
            sc[i] = sc[i] * d + s.access(key)
        best = 0
        for i in range(1, len(sc)):
            if sc[i] > sc[best]:
                best = i
        lead = self.shadows[self.lead]
        if best != self.lead and sc[best] > sc[self.lead] + self.margin:
            self.lead = best
            lead = self.shadows[best]
            spare.clear()
            for k in store:
                if k not in lead.store:
                    spare[k] = True
        elif lead.out is not None and lead.out in store:
            spare[lead.out] = True
        if key in spare and key in lead.store:
            del spare[key]
        if not hit and key in lead.store:
            store.add(key)
            if len(store) > self.capacity:
                store.discard(spare.popitem(last=False)[0])
        return hit
