import heapq
from collections import OrderedDict


class LRU:
    def __init__(self, cap):
        self.cap = cap
        self.store = OrderedDict()
        self.ev = []

    def access(self, key):
        s = self.store
        if key in s:
            s.move_to_end(key)
            return True
        if len(s) >= self.cap:
            self.ev.append(s.popitem(last=False)[0])
        s[key] = True
        return False


class ARC:
    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1 = OrderedDict()
        self.t2 = OrderedDict()
        self.b1 = OrderedDict()
        self.b2 = OrderedDict()
        self.store = set()
        self.ev = []

    def _rm(self, k):
        self.store.discard(k)
        self.ev.append(k)

    def _replace(self, in_b2):
        if self.t1 and (len(self.t1) > self.p or (in_b2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False)
            self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False)
            self.b2[k] = True
        self._rm(k)

    def access(self, key):
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
            self.store.add(key)
            return False
        if key in self.b2:
            self.p = max(0, self.p - max(1, len(self.b1) // len(self.b2)))
            self._replace(True)
            del self.b2[key]
            self.t2[key] = True
            self.store.add(key)
            return False
        l1 = len(self.t1) + len(self.b1)
        if l1 >= c:
            if len(self.t1) < c:
                self.b1.popitem(last=False)
                self._replace(False)
            else:
                k, _ = self.t1.popitem(last=False)
                self._rm(k)
        else:
            tot = l1 + len(self.t2) + len(self.b2)
            if tot >= c:
                if tot >= 2 * c:
                    self.b2.popitem(last=False)
                if len(self.t1) + len(self.t2) >= c:
                    self._replace(False)
        self.t1[key] = True
        self.store.add(key)
        return False


class TLFU:
    def __init__(self, capacity, wfrac=0.01, sm=10):
        self.cap = capacity
        self.wcap = max(1, int(capacity * wfrac))
        self.pcap = max(1, int((capacity - self.wcap) * 0.8))
        self.win = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.freq = {}
        self.n = 0
        self.sample = capacity * sm
        self.store = set()
        self.ev = []

    def _touch(self, key):
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.n += 1
        if self.n >= self.sample:
            self.n = 0
            for k in list(f):
                v = f[k] >> 1
                if v:
                    f[k] = v
                else:
                    del f[k]

    def access(self, key):
        self._touch(key)
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
        if key in self.win:
            self.win.move_to_end(key)
            return True
        self.win[key] = True
        self.store.add(key)
        if len(self.win) > self.wcap:
            k, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) + len(self.win) < self.cap:
                self.prob[k] = True
            else:
                if self.prob:
                    v = next(iter(self.prob))
                    d = self.prob
                else:
                    v = next(iter(self.prot))
                    d = self.prot
                if self.freq.get(k, 0) > self.freq.get(v, 0):
                    del d[v]
                    self.prob[k] = True
                    self.store.discard(v)
                    self.ev.append(v)
                else:
                    self.store.discard(k)
                    self.ev.append(k)
        return False


class LFU:
    def __init__(self, capacity):
        self.cap = capacity
        self.freq = {}
        self.heap = []
        self.seq = 0
        self.n = 0
        self.sample = capacity * sm
        self.store = set()
        self.ev = []

    def access(self, key):
        f = self.freq
        self.n += 1
        if self.n >= self.sample:
            self.n = 0
            for k in list(f):
                v = f[k] >> 1
                if v:
                    f[k] = v
                else:
                    del f[k]
            self.heap = [(f.get(k, 0), q, k) for (_, q, k) in self.heap if k in self.store]
            heapq.heapify(self.heap)
        v = f.get(key, 0) + 1
        f[key] = v
        self.seq += 1
        hit = key in self.store
        if not hit:
            if len(self.store) >= self.cap:
                h = self.heap
                while True:
                    fv, q, k = heapq.heappop(h)
                    if k in self.store and f.get(k, 0) == fv and k != key:
                        break
                self.store.discard(k)
                self.ev.append(k)
            self.store.add(key)
        heapq.heappush(self.heap, (v, self.seq, key))
        return hit


class Cache:
    def __init__(self, capacity):
        self.cap = capacity
        self.ex = [LRU(capacity), ARC(capacity), TLFU(capacity, 0.01, 3), TLFU(capacity, 0.01, 25), TLFU(capacity, 0.05, 10), TLFU(capacity, 0.2, 10)]
        self.sc = [0.0] * len(self.ex)
        self.decay = 1.0 - 1.0 / (capacity * 4)
        self.lead = 0
        self.store = set()
        self.D = OrderedDict()

    def access(self, key):
        ex = self.ex
        sc = self.sc
        dec = self.decay
        for i, e in enumerate(ex):
            sc[i] = sc[i] * dec + (1.0 if e.access(key) else 0.0)
        real = self.store
        hit = key in real
        if not hit:
            real.add(key)
        best = max(range(len(ex)), key=lambda i: sc[i])
        if sc[best] > sc[self.lead] * 1.15 + 2.0:
            self.lead = best
            L = ex[best].store
            self.D = OrderedDict((k, True) for k in real if k not in L)
        L = ex[self.lead]
        Ls = L.store
        D = self.D
        for k in L.ev:
            if k in real and k not in Ls:
                D[k] = True
        if key in D:
            del D[key]
        if len(real) > self.cap:
            k, _ = D.popitem(last=False)
            real.discard(k)
        for e in ex:
            del e.ev[:]
        return hit
