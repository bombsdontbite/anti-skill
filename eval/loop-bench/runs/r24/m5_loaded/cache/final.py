from collections import OrderedDict, deque
from heapq import heappush, heappop


class Arc:
    def __init__(self, capacity, ev):
        self.c = capacity; self.p = 0; self.ev = ev
        self.t1 = OrderedDict(); self.t2 = OrderedDict(); self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = set()

    def _replace(self, inb2):
        if self.t1 and (len(self.t1) > self.p or (inb2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = None
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = None
        self.store.discard(k); self.ev.append(k)

    def access(self, key):
        c = self.c
        if key in self.t1:
            del self.t1[key]; self.t2[key] = None; return True
        if key in self.t2:
            self.t2.move_to_end(key); return True
        if key in self.b1:
            self.p = min(c, self.p + max(len(self.b2) // max(len(self.b1), 1), 1))
            self._replace(False); del self.b1[key]; self.t2[key] = None; self.store.add(key); return False
        if key in self.b2:
            self.p = max(0, self.p - max(len(self.b1) // max(len(self.b2), 1), 1))
            self._replace(True); del self.b2[key]; self.t2[key] = None; self.store.add(key); return False
        l1 = len(self.t1) + len(self.b1)
        if l1 == c:
            if len(self.t1) < c:
                self.b1.popitem(last=False); self._replace(False)
            else:
                k, _ = self.t1.popitem(last=False); self.store.discard(k); self.ev.append(k)
        else:
            tot = l1 + len(self.t2) + len(self.b2)
            if tot >= c:
                if tot == 2 * c:
                    self.b2.popitem(last=False)
                if len(self.store) >= c:
                    self._replace(False)
        self.t1[key] = None; self.store.add(key); return False


class Tlfu:
    """W-TinyLFU: LRU window, SLRU main, frequency admission with halving."""

    def __init__(self, capacity, ev, wfrac=0.01, pfrac=0.8, sample=4):
        self.cap = capacity; self.ev = ev
        self.wcap = max(1, int(capacity * wfrac)); self.mcap = capacity - self.wcap
        self.pcap = max(1, int(self.mcap * pfrac))
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.freq = {}; self.ops = 0; self.reset = capacity * sample
        self.store = set()

    def access(self, key):
        f = self.freq
        f[key] = f.get(key, 0) + 1; self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = f = {a: b >> 1 for a, b in f.items() if b > 1}
        if key in self.win:
            self.win.move_to_end(key); return True
        if key in self.prot:
            self.prot.move_to_end(key); return True
        if key in self.prob:
            del self.prob[key]; self.prot[key] = None
            if len(self.prot) > self.pcap:
                k, _ = self.prot.popitem(last=False); self.prob[k] = None
            return True
        self.win[key] = None; self.store.add(key)
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mcap:
                self.prob[cand] = None
            else:
                src = self.prob if self.prob else self.prot
                victim = next(iter(src))
                if f.get(cand, 0) > f.get(victim, 0):
                    del src[victim]; self.store.discard(victim); self.ev.append(victim)
                    self.prob[cand] = None
                else:
                    self.store.discard(cand); self.ev.append(cand)
        return False


class Lfuda:
    """LFU with dynamic aging: evict the smallest frequency + age."""

    def __init__(self, capacity, ev):
        self.cap = capacity; self.ev = ev
        self.pri = {}; self.heap = []; self.age = 0; self.t = 0
        self.store = set()

    def access(self, key):
        pri = self.pri; self.t += 1
        hit = key in pri
        if hit:
            p = pri[key] + 1
        else:
            p = self.age + 1
            if len(pri) >= self.cap:
                h = self.heap
                while True:
                    q, _, k = heappop(h)
                    if pri.get(k) == q:
                        break
                del pri[k]; self.store.discard(k); self.ev.append(k); self.age = q
            self.store.add(key)
        pri[key] = p
        heappush(self.heap, (p, self.t, key))
        if len(self.heap) > 8 * self.cap:
            self.heap = [(q, t, k) for q, t, k in self.heap if pri.get(k) == q]
        return hit


class Cache:
    """Follows whichever shadow policy has more recent (decayed) hits."""

    def __init__(self, capacity, decay=0.999, margin=8.0, samples=(4, 16, 256), arc=True, lfuda=False):
        self.cap = capacity
        self.ev = deque()
        self.shadows = [Tlfu(capacity, self.ev, sample=x) for x in samples]
        if arc:
            self.shadows.append(Arc(capacity, self.ev))
        if lfuda:
            self.shadows.append(Lfuda(capacity, self.ev))
        self.score = [0.0] * len(self.shadows); self.lead = 0
        self.decay = decay; self.margin = margin
        self.store = set()

    def access(self, key):
        store = self.store
        hit = key in store
        sc = self.score; d = self.decay
        for i, s in enumerate(self.shadows):
            sc[i] = sc[i] * d + s.access(key)
        best = max(range(len(sc)), key=sc.__getitem__)
        if sc[best] > sc[self.lead] + self.margin:
            self.lead = best
        lead = self.shadows[self.lead].store
        if not hit and key in lead:
            store.add(key)
            if len(store) > self.cap:
                self._evict(lead, key)
        ev = self.ev
        while len(ev) > 4 * self.cap:
            ev.popleft()
        return hit

    def _evict(self, lead, key):
        store = self.store; ev = self.ev
        while ev:
            k = ev.pop()
            if k in store and k not in lead and k != key:
                store.discard(k); return
        for k in store:
            if k not in lead:
                store.discard(k); return
