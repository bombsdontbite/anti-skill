import heapq
import math
from collections import OrderedDict, deque


class Lirs:
    def __init__(self, capacity, hir, nr):
        self.c = capacity
        self.lcap = capacity - max(1, int(capacity * hir))
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.nr = OrderedDict()
        self.nrcap = max(1, int(capacity * nr))
        self.nlir = 0
        self.store = {}
        self.ev = deque()
        self.score = 0.0

    def _prune(self):
        S = self.S
        nr = self.nr
        while S:
            k = next(iter(S))
            if S[k]:
                return
            del S[k]
            nr.pop(k, None)

    def _demote(self):
        S = self.S
        k = next(iter(S))
        del S[k]
        self.nlir -= 1
        self.Q[k] = True
        self._prune()

    def _evict(self):
        k, _ = self.Q.popitem(last=False)
        del self.store[k]
        self.ev.append(k)
        if k in self.S:
            self.nr[k] = True
            if len(self.nr) > self.nrcap:
                old, _ = self.nr.popitem(last=False)
                del self.S[old]

    def access(self, key):
        S, Q, store = self.S, self.Q, self.store
        if key in store:
            if key in S:
                if S[key]:
                    first = next(iter(S))
                    S.move_to_end(key)
                    if first == key:
                        self._prune()
                else:
                    del S[key]
                    S[key] = True
                    del Q[key]
                    self.nlir += 1
                    self._demote()
            else:
                S[key] = False
                Q.move_to_end(key)
            return True
        if self.nlir < self.lcap:
            if len(store) >= self.c:
                self._evict()
            if key in S:
                del S[key]
                self.nr.pop(key, None)
            S[key] = True
            store[key] = True
            self.nlir += 1
            return False
        if len(store) >= self.c:
            self._evict()
        store[key] = True
        if key in S:
            del S[key]
            self.nr.pop(key, None)
            S[key] = True
            self.nlir += 1
            self._demote()
        else:
            S[key] = False
            Q[key] = True
        return False


class Arc:
    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1 = OrderedDict()
        self.t2 = OrderedDict()
        self.b1 = OrderedDict()
        self.b2 = OrderedDict()
        self.store = {}
        self.ev = deque()
        self.score = 0.0

    def _replace(self, in_b2):
        t1 = self.t1
        if t1 and (len(t1) > self.p or (in_b2 and len(t1) == self.p)):
            k, _ = t1.popitem(last=False)
            self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False)
            self.b2[k] = True
        del self.store[k]
        self.ev.append(k)

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
            self.p = min(c, self.p + max(1, len(b2) // max(1, len(b1))))
            self._replace(False)
            del b1[key]
            self.t2[key] = True
            self.store[key] = True
            return False
        if key in b2:
            self.p = max(0, self.p - max(1, len(b1) // max(1, len(b2))))
            self._replace(True)
            del b2[key]
            self.t2[key] = True
            self.store[key] = True
            return False
        l1 = len(self.t1) + len(b1)
        if l1 == c:
            if len(self.t1) < c:
                b1.popitem(last=False)
                self._replace(False)
            else:
                k, _ = self.t1.popitem(last=False)
                del self.store[k]
                self.ev.append(k)
        else:
            tot = l1 + len(self.t2) + len(b2)
            if tot >= c:
                if tot == 2 * c:
                    b2.popitem(last=False)
                if len(self.store) >= c:
                    self._replace(False)
        self.t1[key] = True
        self.store[key] = True
        return False


class Lrfu:
    def __init__(self, capacity, h, ghost=4):
        self.c = capacity
        self.t = 0
        self.h = h * capacity
        self.store = {}
        self.heap = []
        self.hist = {}
        self.ghost = OrderedDict()
        self.gcap = ghost * capacity
        self.ev = deque()
        self.score = 0.0

    def access(self, key):
        self.t += 1
        t = self.t
        hist = self.hist
        h = self.h
        if key in hist:
            lc, last = hist[key]
            c = 1.0 + 2.0 ** (lc - (t - last) / h)
        else:
            c = 1.0
        lc = math.log2(c)
        hist[key] = (lc, t)
        p = lc + t / h
        store = self.store
        if key in store:
            store[key] = p
            heapq.heappush(self.heap, (p, key))
            if len(self.heap) > 8 * self.c:
                self.heap = [(v, k) for k, v in store.items()]
                heapq.heapify(self.heap)
            return True
        self.ghost.pop(key, None)
        if len(store) >= self.c:
            heap = self.heap
            while True:
                v, k = heapq.heappop(heap)
                if store.get(k) == v:
                    break
            del store[k]
            self.ev.append(k)
            self.ghost[k] = True
            if len(self.ghost) > self.gcap:
                gk, _ = self.ghost.popitem(last=False)
                del hist[gk]
        store[key] = p
        heapq.heappush(self.heap, (p, key))
        return False


class Nofifo:
    """FIFO that never readmits a key it evicted while that key is remembered."""

    def __init__(self, capacity, g):
        self.c = capacity
        self.store = OrderedDict()
        self.gh = OrderedDict()
        self.gcap = int(g * capacity)
        self.ev = deque()
        self.score = 0.0

    def access(self, key):
        store = self.store
        if key in store:
            return True
        if key in self.gh:
            return False
        if len(store) >= self.c:
            k, _ = store.popitem(last=False)
            self.ev.append(k)
            self.gh[k] = True
            if len(self.gh) > self.gcap:
                self.gh.popitem(last=False)
        store[key] = True
        return False


class Cache:
    """Follow the leader: shadow policies (LIRS at three HIR sizes, ARC, LRFU, no-readmit FIFO)
    run on metadata only; the real cache admits a key only if the shadow with the most recent
    hits holds it, and evicts a key that shadow dropped, preferring keys few good shadows keep."""

    DECAY = 0.9995
    NR = 16.0
    VOTE = 16

    def __init__(self, capacity):
        self.c = capacity
        if capacity < 4:
            self.store = OrderedDict()
            self.access = self._lru
            return
        self.ex = [Lirs(capacity, 0.01, self.NR), Lirs(capacity, 0.1, self.NR),
                   Lirs(capacity, 0.3, self.NR), Arc(capacity), Lrfu(capacity, 4.0),
                   Nofifo(capacity, 8.0)]
        self.store = {}

    def access(self, key):
        d = self.DECAY
        best = None
        for e in self.ex:
            e.score = e.score * d + e.access(key)
            if len(e.ev) > 4 * self.c:
                e.ev.popleft()
            if best is None or e.score > best.score:
                best = e
        store = self.store
        if key in store:
            return True
        if key not in best.store:
            return False
        if len(store) >= self.c:
            ev = best.ev
            bs = best.store
            victim = None
            cands = []
            while ev and len(cands) < self.VOTE:
                k = ev.pop()
                if k in store and k not in bs:
                    cands.append(k)
            if cands:
                bv = None
                for k in cands:
                    v = 0.0
                    for e in self.ex:
                        if k in e.store:
                            v += e.score
                    if bv is None or v < bv:
                        bv = v
                        victim = k
                for k in cands:
                    if k != victim:
                        ev.append(k)
            else:
                for k in store:
                    if k not in bs:
                        victim = k
                        break
            del store[victim]
        store[key] = True
        return False

    def _lru(self, key):
        store = self.store
        if key in store:
            store.move_to_end(key)
            return True
        if len(store) >= self.c:
            store.popitem(last=False)
        store[key] = True
        return False
