from collections import OrderedDict



class LIRS:
    """LIRS: stack S holds recency of LIR/HIR blocks, queue Q holds resident HIR blocks."""

    def __init__(self, capacity, hir=0.01, ghost=3):
        self.capacity = capacity
        self.store = {}
        self.hcap = max(1, int(capacity * hir))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict()   # key -> True if LIR
        self.Q = OrderedDict()   # resident HIR
        self.nlir = 0
        self.smax = ghost * capacity

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if S[k]:
                break
            del S[k]

    def _demote_bottom(self):
        S = self.S
        k, _ = S.popitem(last=False)
        self.nlir -= 1
        self.Q[k] = True
        self._prune()

    def access(self, key):
        S, Q = self.S, self.Q
        if key in self.store:
            if S.get(key):
                first = next(iter(S)) == key
                S.move_to_end(key)
                if first:
                    self._prune()
                return True
            if key in S:
                # resident HIR in stack -> becomes LIR
                S.move_to_end(key); S[key] = True
                del Q[key]
                self.nlir += 1
                self._demote_bottom()
            else:
                S[key] = False
                Q.move_to_end(key)
            self._trim()
            return True
        # miss
        if self.nlir < self.lcap:
            self.store[key] = True
            S[key] = True; S.move_to_end(key)
            self.nlir += 1
            return False
        if len(Q) >= self.hcap or len(self.store) >= self.capacity:
            v, _ = Q.popitem(last=False)
            del self.store[v]
        self.store[key] = True
        if key in S:
            S.move_to_end(key); S[key] = True
            self.nlir += 1
            self._demote_bottom()
        else:
            S[key] = False
            Q[key] = True
        self._trim()
        return False

    def _trim(self):
        S = self.S
        if len(S) > self.smax:
            # drop oldest non-resident HIR entries
            n = len(S) - self.smax
            drop = []
            for k, lir in S.items():
                if not lir and k not in self.store:
                    drop.append(k)
                    if len(drop) >= n:
                        break
            for k in drop:
                del S[k]



class ARC:
    def __init__(self, capacity):
        self.c = capacity
        self.store = {}
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.p = 0

    def _replace(self, inb2):
        if self.t1 and (len(self.t1) > self.p or (inb2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = True
        del self.store[k]

    def access(self, x):
        c = self.c
        if x in self.t1:
            del self.t1[x]; self.t2[x] = True; return True
        if x in self.t2:
            self.t2.move_to_end(x); return True
        if x in self.b1:
            self.p = min(c, self.p + max(len(self.b2) // len(self.b1), 1))
            self._replace(False); del self.b1[x]; self.t2[x] = True; self.store[x] = True
            return False
        if x in self.b2:
            self.p = max(0, self.p - max(len(self.b1) // len(self.b2), 1))
            self._replace(True); del self.b2[x]; self.t2[x] = True; self.store[x] = True
            return False
        l1 = len(self.t1) + len(self.b1)
        if l1 == c:
            if len(self.t1) < c:
                self.b1.popitem(last=False); self._replace(False)
            else:
                k, _ = self.t1.popitem(last=False); del self.store[k]
        elif l1 < c and l1 + len(self.t2) + len(self.b2) >= c:
            if l1 + len(self.t2) + len(self.b2) == 2 * c:
                self.b2.popitem(last=False)
            self._replace(False)
        self.t1[x] = True; self.store[x] = True
        return False



class TLFU:
    """W-TinyLFU: small LRU window, segmented LRU main, frequency-gated admission."""

    def __init__(self, capacity, window=0.01, protected=0.8, sample=10):
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

    def _count(self, key):
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops //= 2
            self.freq = {k: v >> 1 for k, v in f.items() if v > 1}

    def access(self, key):
        self._count(key)
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
        self.win[key] = True
        self.store[key] = True
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mcap:
                self.prob[cand] = True
            else:
                vq = self.prob if self.prob else self.prot
                victim = next(iter(vq))
                f = self.freq
                if f.get(cand, 0) > f.get(victim, 0):
                    del vq[victim]
                    del self.store[victim]
                    self.prob[cand] = True
                else:
                    del self.store[cand]
        return False


class LRU:
    def __init__(self, capacity):
        self.capacity = capacity
        self.store = OrderedDict()

    def access(self, key):
        if key in self.store:
            self.store.move_to_end(key)
            return True
        if len(self.store) >= self.capacity:
            self.store.popitem(last=False)
        self.store[key] = True
        return False


class Cache:
    """Follow the leader: shadow policies vote; the real cache evicts what the current leader dropped."""

    def __init__(self, capacity, decay=20.0, scan=100000, close=0.95, margin=1.03):
        self.margin = margin
        self.close = close
        self.capacity = capacity
        self.store = OrderedDict()
        self.shadows = [LIRS(capacity), ARC(capacity), TLFU(capacity), LRU(capacity), TLFU(capacity, sample=40), TLFU(capacity, sample=150)]
        self.scores = [0.0] * len(self.shadows)
        self.d = 1.0 - 1.0 / (decay * capacity)
        self.scan = scan
        self.lead = 0

    def access(self, key):
        sc = self.scores
        d = self.d
        for i, s in enumerate(self.shadows):
            sc[i] = sc[i] * d + s.access(key)
        st = self.store
        if key in st:
            st.move_to_end(key)
            return True
        st[key] = True
        if len(st) > self.capacity:
            b = max(range(len(sc)), key=lambda i: sc[i])
            if sc[b] > sc[self.lead] * self.margin:
                self.lead = b
            lead = self.lead
            r = max((i for i in range(len(sc)) if i != lead), key=lambda i: sc[i])
            ls = self.shadows[lead].store
            rs = self.shadows[r].store
            close = sc[r] >= self.close * sc[lead]
            victim = None
            first = None
            for k in st:
                if k not in ls:
                    if not close or k not in rs:
                        victim = k
                        break
                    if first is None:
                        first = k
            if victim is None:
                victim = first if first is not None else next(iter(st))
            del st[victim]
        return False
