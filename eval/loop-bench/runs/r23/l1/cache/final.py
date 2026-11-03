from collections import OrderedDict, deque



class LRU:
    """Least recently used."""

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



class LIRS:
    """LIRS: keep blocks with short inter-reference recency (LIR); HIR residents in a small queue."""

    def __init__(self, capacity, hfrac=0.01, smax=3):
        self.c = capacity
        self.hc = max(1, int(capacity * hfrac))
        self.lc = capacity - self.hc
        self.S = OrderedDict()   # key -> True ; recency stack
        self.Q = OrderedDict()   # resident HIR
        self.lir = set()
        self.store = set()
        self.smax = smax * capacity

    def _prune(self):
        S, lir = self.S, self.lir
        while S:
            k = next(iter(S))
            if k in lir:
                break
            del S[k]

    def access(self, key):
        S, Q, lir, store = self.S, self.Q, self.lir, self.store
        if key in lir:
            S.move_to_end(key)
            self._prune()
            return True
        hit = key in store
        if hit:
            del Q[key]
        else:
            if len(store) >= self.c:
                k, _ = Q.popitem(last=False)
                store.discard(k)
            store.add(key)
        if len(lir) < self.lc:
            lir.add(key)
            S[key] = True
            S.move_to_end(key)
            return hit
        if key in S:
            lir.add(key)
            S.move_to_end(key)
            b = next(iter(S))
            lir.discard(b)
            del S[b]
            Q[b] = True
            self._prune()
        else:
            S[key] = True
            Q[key] = True
            while len(S) > self.smax:
                k = next(iter(S))
                if k in lir:
                    break
                del S[k]
        return hit



class ARC:
    """ARC: adaptive split between recency (T1) and frequency (T2), steered by ghost hits."""

    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1 = OrderedDict()
        self.t2 = OrderedDict()
        self.b1 = OrderedDict()
        self.b2 = OrderedDict()
        self.store = set()

    def _replace(self, in_b2):
        if self.t1 and (len(self.t1) > self.p or (in_b2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False)
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
        if key in self.b1:
            self.p = min(c, self.p + max(len(self.b2) // len(self.b1), 1))
            self._replace(False)
            del self.b1[key]
            self.t2[key] = True
        elif key in self.b2:
            self.p = max(0, self.p - max(len(self.b1) // len(self.b2), 1))
            self._replace(True)
            del self.b2[key]
            self.t2[key] = True
        else:
            l1 = len(self.t1) + len(self.b1)
            if l1 == c:
                if len(self.t1) < c:
                    self.b1.popitem(last=False)
                    self._replace(False)
                else:
                    k, _ = self.t1.popitem(last=False)
                    self.store.discard(k)
            else:
                tot = l1 + len(self.t2) + len(self.b2)
                if tot >= c:
                    if tot == 2 * c:
                        self.b2.popitem(last=False)
                    if len(self.t1) + len(self.t2) >= c:
                        self._replace(False)
            self.t1[key] = True
        self.store.add(key)
        return False



class TinyLFU:
    """W-TinyLFU: LRU window, segmented-LRU main, frequency sketch admission with aging."""

    def __init__(self, capacity, wfrac=0.01, reset=10):
        self.c = capacity
        self.wc = max(1, int(capacity * wfrac))
        mc = capacity - self.wc
        self.pc = max(1, int(mc * 0.8))
        self.mc = mc
        self.win = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.freq = {}
        self.ops = 0
        self.reset = reset * capacity
        self.store = set()

    def _inc(self, k):
        f = self.freq
        f[k] = f.get(k, 0) + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = {a: b >> 1 for a, b in f.items() if b > 1}

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
            if len(self.prot) > self.pc:
                k, _ = self.prot.popitem(last=False)
                self.prob[k] = True
            return True
        self.store.add(key)
        self.win[key] = True
        if len(self.win) > self.wc:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mc:
                self.prob[cand] = True
            else:
                victim = next(iter(self.prob)) if self.prob else next(iter(self.prot))
                f = self.freq
                if f.get(cand, 0) > f.get(victim, 0):
                    if victim in self.prob:
                        del self.prob[victim]
                    else:
                        del self.prot[victim]
                    self.store.discard(victim)
                    self.prob[cand] = True
                else:
                    self.store.discard(cand)
        return False



class S3:
    """S3-FIFO: small probationary FIFO, main FIFO with reinsertion, ghost FIFO."""

    def __init__(self, capacity, small_frac=0.1):
        self.c = capacity
        self.ss = max(1, int(capacity * small_frac))
        self.S = deque()
        self.M = deque()
        self.G = deque()
        self.gset = set()
        self.freq = {}
        self.store = self.freq
        self.ins = set()

    def _evict_m(self):
        M, f = self.M, self.freq
        while True:
            k = M.popleft()
            if f[k] > 0:
                f[k] -= 1
                M.append(k)
            else:
                del f[k]
                return

    def _evict(self):
        if len(self.S) >= self.ss or not self.M:
            f = self.freq
            while self.S:
                k = self.S.popleft()
                if f[k] > 0:
                    f[k] = 0
                    self.M.append(k)
                    if len(self.M) > self.c - self.ss:
                        self._evict_m()
                        if len(f) < self.c:
                            return
                else:
                    del f[k]
                    self.G.append(k)
                    self.gset.add(k)
                    if len(self.G) > self.c:
                        self.gset.discard(self.G.popleft())
                    return
        self._evict_m()

    def access(self, key):
        f = self.freq
        if key in f:
            if f[key] < 3:
                f[key] += 1
            return True
        while len(f) >= self.c:
            self._evict()
        if key in self.gset:
            self.gset.discard(key)
            f[key] = 0
            self.M.append(key)
        else:
            f[key] = 0
            self.S.append(key)
        return False


class Cache:
    """Runs several policies as shadows; the real cache follows whichever has hit most lately."""

    def __init__(self, capacity, decay=0.9998, margin=50):
        self.c = capacity
        self.experts = [LIRS(capacity), LRU(capacity), TinyLFU(capacity), TinyLFU(capacity, 0.01, 40), TinyLFU(capacity, 0.01, 150), S3(capacity)]
        self.w = [0.0] * len(self.experts)
        self.decay = decay
        self.margin = margin
        self.lead = 0
        self.store = OrderedDict()

    def access(self, key):
        w, d = self.w, self.decay
        for i, e in enumerate(self.experts):
            w[i] = w[i] * d + (1.0 if e.access(key) else 0.0)
        best = self.lead
        top = max(range(len(w)), key=lambda i: w[i])
        if w[top] > w[best] + self.margin:
            best = top
        self.lead = best
        st = self.store
        if key in st:
            st.move_to_end(key)
            return True
        if len(st) >= self.c:
            order = sorted(range(len(w)), key=lambda i: -w[i])
            ls = self.experts[best].store
            l2 = self.experts[order[1] if order[0] == best else order[0]].store
            victim = None
            fallback = None
            for k in st:
                if k not in ls:
                    if k not in l2:
                        victim = k
                        break
                    if fallback is None:
                        fallback = k
            if victim is None:
                victim = fallback if fallback is not None else next(iter(st))
            del st[victim]
        st[key] = True
        return False
