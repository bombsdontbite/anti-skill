from collections import OrderedDict, deque

LIR, HIR, GHOST = 0, 1, 2


class Lirs:
    """LIRS whose HIR (recency) share can change while running."""

    def __init__(self, capacity, hcap, ghost_mult=2.0):
        self.capacity = capacity
        self.hcap = hcap
        self.lcap = capacity - hcap
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.ghosts = OrderedDict()
        self.gmax = int(capacity * ghost_mult)
        self.nlir = 0
        self.store = {}
        self.ev = None

    def set_params(self, hcap, gmax):
        self.gmax = gmax
        while len(self.ghosts) > gmax:
            g, _ = self.ghosts.popitem(last=False)
            del self.S[g]
        self.hcap = hcap
        self.lcap = self.capacity - hcap
        while self.nlir > self.lcap:
            self._demote_bottom()

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            st = S[k]
            if st == LIR:
                return
            del S[k]
            if st == GHOST:
                del self.ghosts[k]

    def _demote_bottom(self):
        S = self.S
        k = next(iter(S))
        del S[k]
        self.Q[k] = True
        self.nlir -= 1
        self._prune()

    def _promoted(self):
        self.nlir += 1
        if self.nlir > self.lcap:
            self._demote_bottom()
        else:
            self._prune()

    def access(self, key):
        S = self.S
        st = S.get(key)
        if key in self.store:
            if st == LIR:
                S.move_to_end(key)
                self._prune()
            elif st == HIR:
                S.move_to_end(key)
                S[key] = LIR
                del self.Q[key]
                self._promoted()
            else:
                S[key] = HIR
                self.Q.move_to_end(key)
            return True
        if st is None and self.nlir < self.lcap and len(self.store) < self.capacity:
            S[key] = LIR
            self.nlir += 1
            self.store[key] = True
            return False
        if len(self.store) >= self.capacity:
            k, _ = self.Q.popitem(last=False)
            del self.store[k]
            self.ev = k
            if k in S:
                S[k] = GHOST
                self.ghosts[k] = True
                if len(self.ghosts) > self.gmax:
                    g, _ = self.ghosts.popitem(last=False)
                    del S[g]
            st = S.get(key)
        self.store[key] = True
        if st == GHOST:
            del self.ghosts[key]
            S.move_to_end(key)
            S[key] = LIR
            self._promoted()
        else:
            S[key] = HIR
            self.Q[key] = True
        return False



class Wtlfu:
    """W-TinyLFU."""

    def __init__(self, capacity, window_frac=0.01, prot_frac=0.8):
        self.capacity = capacity
        self.wcap = max(1, int(capacity * window_frac))
        self.mcap = capacity - self.wcap
        self.pcap = int(self.mcap * prot_frac)
        self.window = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.store = {}
        self.ev = None
        self.freq = {}
        self.ops = 0
        self.reset_at = capacity * 10

    def _inc(self, key):
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.reset_at:
            self.ops = 0
            self.freq = {k: v >> 1 for k, v in f.items() if v > 1}

    def access(self, key):
        self._inc(key)
        store = self.store
        if key in store:
            if key in self.window:
                self.window.move_to_end(key)
            elif key in self.prot:
                self.prot.move_to_end(key)
            else:
                del self.prob[key]
                self.prot[key] = True
                if len(self.prot) > self.pcap:
                    k, _ = self.prot.popitem(last=False)
                    self.prob[k] = True
            return True
        store[key] = True
        self.window[key] = True
        if len(self.window) > self.wcap:
            cand, _ = self.window.popitem(last=False)
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
                    del store[victim]
                    self.ev = victim
                    self.prob[cand] = True
                else:
                    del store[cand]
                    self.ev = cand
        return False


class S3:
    """S3-FIFO."""

    def __init__(self, capacity, small_frac=0.1):
        self.c = capacity
        self.scap = max(1, int(capacity * small_frac))
        self.small = deque(); self.main = deque()
        self.ghost = {}; self.gq = deque()
        self.freq = {}
        self.store = self.freq
        self.ev = None

    def _evict(self):
        f = self.freq
        if len(self.small) >= self.scap or not self.main:
            while self.small:
                k = self.small.popleft()
                if f[k] > 0:
                    f[k] = 0; self.main.append(k)
                    if len(self.main) + len(self.small) < self.c:
                        continue
                    self._evict_main(); return
                del f[k]
                self.ev = k
                self.ghost[k] = True; self.gq.append(k)
                if len(self.gq) > self.c:
                    g = self.gq.popleft(); self.ghost.pop(g, None)
                return
        self._evict_main()

    def _evict_main(self):
        f = self.freq
        while True:
            k = self.main.popleft()
            if f[k] > 0:
                f[k] -= 1; self.main.append(k)
            else:
                del f[k]; self.ev = k; return

    def access(self, key):
        f = self.freq
        if key in f:
            if f[key] < 3:
                f[key] += 1
            return True
        if len(f) >= self.c:
            self._evict()
        if key in self.ghost:
            del self.ghost[key]; f[key] = 0; self.main.append(key)
        else:
            f[key] = 0; self.small.append(key)
        return False


class Arc:
    """ARC."""

    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = {}
        self.ev = None

    def _replace(self, in_b2):
        if self.t1 and (len(self.t1) > self.p or (in_b2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = True
        del self.store[k]
        self.ev = k

    def access(self, key):
        c = self.c
        if key in self.t1:
            del self.t1[key]; self.t2[key] = True; return True
        if key in self.t2:
            self.t2.move_to_end(key); return True
        if key in self.b1:
            self.p = min(c, self.p + max(len(self.b2) // len(self.b1), 1))
            self._replace(False); del self.b1[key]; self.t2[key] = True
        elif key in self.b2:
            self.p = max(0, self.p - max(len(self.b1) // len(self.b2), 1))
            self._replace(True); del self.b2[key]; self.t2[key] = True
        else:
            l1 = len(self.t1) + len(self.b1)
            if l1 == c:
                if len(self.t1) < c:
                    self.b1.popitem(last=False); self._replace(False)
                else:
                    k, _ = self.t1.popitem(last=False); del self.store[k]; self.ev = k
            elif l1 < c:
                tot = l1 + len(self.t2) + len(self.b2)
                if tot >= c:
                    if tot == 2 * c and self.b2:
                        self.b2.popitem(last=False)
                    self._replace(False)
            self.t1[key] = True
        self.store[key] = True
        return False


class Lru:
    """LRU."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.store = OrderedDict()
        self.ev = None

    def access(self, key):
        if key in self.store:
            self.store.move_to_end(key)
            return True
        if len(self.store) >= self.capacity:
            self.ev, _ = self.store.popitem(last=False)
        self.store[key] = True
        return False


class Cache:
    """Follows whichever shadow policy has hit most lately, evicting what it evicted."""

    FRACS = (0.01, 0.03, 0.1, 0.3, 0.6)
    GHOSTS = (1.0, 3.0)

    def __init__(self, capacity, period=1, decay=0.9, margin=1.02):
        self.capacity = capacity
        hs = sorted(set(max(1, min(capacity - 1, int(capacity * f))) for f in self.FRACS))
        self.shadows = [Lirs(capacity, h, g) for h in hs for g in self.GHOSTS]
        self.shadows.append(Wtlfu(capacity))
        self.shadows.append(S3(capacity))
        self.shadows.append(Arc(capacity))
        self.shadows.append(Lru(capacity))
        self.score = [0.0] * len(self.shadows)
        self.period = capacity * period
        self.decay = decay
        self.n = 0
        self.best = len(self.GHOSTS) - 1
        self.store = {}
        self.order = deque()
        self.margin = margin

    def access(self, key):
        sc = self.score
        for i, sh in enumerate(self.shadows):
            sh.ev = None
            if sh.access(key):
                sc[i] += 1
        self.n += 1
        if self.n >= self.period:
            self.n = 0
            b = sc.index(max(sc))
            if sc[b] > sc[self.best] * self.margin:
                self.best = b
            d = self.decay
            self.score = [s * d for s in sc]
        store = self.store
        if key in store:
            return True
        target = self.shadows[self.best]
        tstore = target.store
        if key not in tstore:
            return False
        if len(store) >= self.capacity:
            v = target.ev
            if v is None or v not in store:
                order = self.order
                v = None
                for _ in range(len(order)):
                    k = order.popleft()
                    if k not in store:
                        continue
                    if k not in tstore:
                        v = k
                        break
                    order.append(k)
                if v is None:
                    v = order.popleft()
            del store[v]
        store[key] = True
        self.order.append(key)
        return False
