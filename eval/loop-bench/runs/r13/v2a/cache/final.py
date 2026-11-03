from collections import OrderedDict, deque


class LRU:
    def __init__(self, capacity):
        self.cap = capacity; self.store = OrderedDict(); self.evicted = []

    def access(self, key):
        s = self.store
        if key in s:
            s.move_to_end(key); return True
        if len(s) >= self.cap:
            self.evicted.append(s.popitem(last=False)[0])
        s[key] = True
        return False


class LIRS:
    def __init__(self, capacity, hir=0.01, nr=2.0):
        self.cap = capacity
        self.lcap = capacity - max(1, int(capacity * hir))
        self.S = OrderedDict(); self.Q = OrderedDict(); self.N = OrderedDict()
        self.lir = set(); self.store = set(); self.evicted = []
        self.nrmax = int(nr * capacity) + 1

    def _prune(self):
        S, lir, N = self.S, self.lir, self.N
        while S:
            k = next(iter(S))
            if k in lir: break
            del S[k]; N.pop(k, None)

    def _demote(self):
        S = self.S
        k = next(iter(S)); self.lir.discard(k); del S[k]; self.Q[k] = True
        self._prune()

    def access(self, key):
        S, Q, lir = self.S, self.Q, self.lir
        if key in lir:
            first = next(iter(S)) == key
            S.move_to_end(key)
            if first: self._prune()
            return True
        if key in self.store:
            if key in S:
                S.move_to_end(key); del Q[key]; lir.add(key); self._demote()
            else:
                S[key] = True; Q.move_to_end(key)
            return True
        if len(lir) < self.lcap and len(self.store) < self.cap:
            self.N.pop(key, None); S[key] = True; S.move_to_end(key)
            lir.add(key); self.store.add(key); return False
        if len(self.store) >= self.cap:
            k, _ = Q.popitem(last=False); self.store.discard(k); self.evicted.append(k)
            if k in S:
                self.N[k] = True
                if len(self.N) > self.nrmax:
                    j, _ = self.N.popitem(last=False); S.pop(j, None)
        self.store.add(key)
        if key in S:
            self.N.pop(key, None)
            S.move_to_end(key); lir.add(key); self._demote()
        else:
            S[key] = True; Q[key] = True
        return False

class TLFU:
    """W-TinyLFU: small LRU window, SLRU main, frequency sketch admission."""
    WIN = 0.01
    def __init__(self, capacity):
        self.cap = capacity
        self.wcap = max(1, int(capacity * self.WIN))
        self.mcap = capacity - self.wcap
        self.pcap = int(self.mcap * 0.8)
        self.win = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.freq = {}; self.ops = 0; self.reset = capacity * 10
        self.store = set(); self.evicted = []

    def _inc(self, k):
        f = self.freq
        v = f.get(k, 0)
        if v < 15: f[k] = v + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = {a: b >> 1 for a, b in f.items() if b > 1}

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
                src = self.prob if self.prob else self.prot
                victim = next(iter(src))
                f = self.freq
                if f.get(cand, 0) > f.get(victim, 0):
                    del src[victim]; self.store.discard(victim); self.evicted.append(victim); self.prob[cand] = True
                else:
                    self.store.discard(cand); self.evicted.append(cand)
        return False


class ARC:
    def __init__(self, capacity):
        self.c = capacity; self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = set(); self.evicted = []

    def _replace(self, inb2):
        if self.t1 and (len(self.t1) > self.p or (inb2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = True
        self.store.discard(k); self.evicted.append(k)

    def access(self, key):
        c = self.c
        if key in self.t1:
            del self.t1[key]; self.t2[key] = True; return True
        if key in self.t2:
            self.t2.move_to_end(key); return True
        if key in self.b1:
            self.p = min(c, self.p + max(len(self.b2) // max(len(self.b1), 1), 1))
            self._replace(False); del self.b1[key]; self.t2[key] = True; self.store.add(key); return False
        if key in self.b2:
            self.p = max(0, self.p - max(len(self.b1) // max(len(self.b2), 1), 1))
            self._replace(True); del self.b2[key]; self.t2[key] = True; self.store.add(key); return False
        l1 = len(self.t1) + len(self.b1)
        if l1 == c:
            if len(self.t1) < c:
                self.b1.popitem(last=False); self._replace(False)
            else:
                k, _ = self.t1.popitem(last=False); self.store.discard(k); self.evicted.append(k)
        else:
            tot = l1 + len(self.t2) + len(self.b2)
            if tot >= c:
                if tot == 2 * c: self.b2.popitem(last=False)
                self._replace(False)
        self.t1[key] = True; self.store.add(key); return False


class Cache:
    """Runs shadow policies and evicts what the recently best one would not keep."""
    DECAY = 4.0
    HYST = 0.98
    HOLD = 2.0
    JUMP = 0.9

    def __init__(self, capacity):
        self.cap = capacity
        self.shadows = [LRU(capacity), TLFU(capacity), LIRS(capacity)]
        self.queues = [deque() for _ in self.shadows]
        self.score = [0.0] * len(self.shadows)
        self.d = 1.0 - 1.0 / (self.DECAY * capacity)
        self.best = len(self.shadows) - 1
        self.store = OrderedDict(); self.lead = 0

    def access(self, key):
        d = self.d; sc = self.score
        for i, sh in enumerate(self.shadows):
            h = sh.access(key)
            sc[i] = sc[i] * d + (1.0 if h else 0.0)
            if sh.evicted:
                self.queues[i].extend(sh.evicted); sh.evicted.clear()
        b = self.best; top = sc.index(max(sc))
        if top != b and sc[b] < sc[top] * self.HYST:
            self.lead += 1
            if self.lead > self.HOLD * self.cap or sc[b] < sc[top] * self.JUMP:
                b = self.best = top; self.lead = 0
        else:
            self.lead = 0
        st = self.store
        if key in st:
            st.move_to_end(key); return True
        if len(st) >= self.cap:
            win = self.shadows[b].store; q = self.queues[b]
            victim = None
            while q:
                k = q.popleft()
                if k in st and k not in win and k != key:
                    victim = k; break
            if victim is None:
                victim = next(iter(st))
            del st[victim]
        st[key] = True
        for q in self.queues:
            if len(q) > 8 * self.cap:
                for _ in range(len(q) - 4 * self.cap): q.popleft()
        return False
