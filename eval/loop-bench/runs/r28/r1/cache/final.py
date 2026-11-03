from collections import OrderedDict, deque


class Lru:
    def __init__(self, capacity):
        self.capacity = capacity
        self.store = OrderedDict()
        self.ev = []

    def access(self, key):
        st = self.store
        if key in st:
            st.move_to_end(key)
            return True
        if len(st) >= self.capacity:
            k, _ = st.popitem(last=False)
            self.ev.append(k)
        st[key] = True
        return False


class Lirs:
    freq = None

    def __init__(self, capacity, hcap, ghost_mult=4):
        self.capacity = capacity
        self.lcap = capacity - hcap
        self.glimit = capacity * ghost_mult
        self.S = OrderedDict()   # key -> True if LIR
        self.Q = OrderedDict()
        self.nlir = 0
        self.ghosts = 0
        self.store = {}
        self.ev = []

    def _prune(self):
        S = self.S; st = self.store
        while S:
            k = next(iter(S))
            if S[k]:
                return
            del S[k]
            if k not in st:
                self.ghosts -= 1

    def _demote_bottom(self):
        k, _ = self.S.popitem(last=False)
        self.nlir -= 1
        self.Q[k] = True
        self._prune()

    def _limit_ghosts(self):
        if self.ghosts <= self.glimit:
            return
        S = self.S; st = self.store
        target = self.glimit * 3 // 4
        for k in [k for k in S if not S[k] and k not in st]:
            del S[k]
            self.ghosts -= 1
            if self.ghosts <= target:
                return

    def access(self, key):
        S = self.S; Q = self.Q; st = self.store
        if key in st:
            if S.get(key):
                S.move_to_end(key)
                self._prune()
            elif key in S:
                del S[key]
                S[key] = True
                del Q[key]
                self.nlir += 1
                if self.nlir > self.lcap:
                    self._demote_bottom()
            else:
                S[key] = False
                Q.move_to_end(key)
            return True
        if len(st) >= self.capacity:
            if not Q:
                self._demote_bottom()
            k, _ = Q.popitem(last=False)
            del st[k]
            self.ev.append(k)
            if k in S:
                self.ghosts += 1
        st[key] = True
        if key in S and self.freq is not None and self.nlir >= self.lcap:
            fq = self.freq
            if fq.est(key) <= fq.est(next(iter(S))):
                del S[key]
                S[key] = False
                Q[key] = True
                return False
        if key in S:
            del S[key]
            self.ghosts -= 1
            S[key] = True
            self.nlir += 1
            if self.nlir > self.lcap:
                self._demote_bottom()
        elif self.nlir < self.lcap:
            S[key] = True
            self.nlir += 1
        else:
            S[key] = False
            Q[key] = True
            self._limit_ghosts()
        return False


class Arc:
    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.store = {}
        self.ev = []

    def _replace(self, in_b2):
        if self.t1 and (len(self.t1) > self.p or (in_b2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = True
        del self.store[k]
        self.ev.append(k)

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
                    k, _ = self.t1.popitem(last=False); del self.store[k]; self.ev.append(k)
            elif l1 < c:
                tot = l1 + len(self.t2) + len(self.b2)
                if tot >= c:
                    if tot == 2 * c:
                        self.b2.popitem(last=False)
                    self._replace(False)
            self.t1[key] = True
        self.store[key] = True
        return False


class S3:
    def __init__(self, capacity):
        self.capacity = capacity
        self.scap = max(1, capacity // 10)
        self.mcap = capacity - self.scap
        self.small = deque(); self.main = deque()
        self.freq = {}
        self.ghost = OrderedDict()
        self.store = {}
        self.ev = []

    def _evict_small(self):
        while self.small:
            k = self.small.popleft()
            if self.freq[k] > 0:
                self.main.append(k); self.freq[k] = 0
                if len(self.main) > self.mcap:
                    self._evict_main()
            else:
                del self.freq[k]; del self.store[k]; self.ev.append(k)
                self.ghost[k] = True
                if len(self.ghost) > self.mcap:
                    self.ghost.popitem(last=False)
                return

    def _evict_main(self):
        while self.main:
            k = self.main.popleft()
            if self.freq[k] > 0:
                self.freq[k] -= 1; self.main.append(k)
            else:
                del self.freq[k]; del self.store[k]; self.ev.append(k); return

    def access(self, key):
        if key in self.store:
            if self.freq[key] < 3:
                self.freq[key] += 1
            return True
        while len(self.store) >= self.capacity:
            if len(self.small) >= self.scap or not self.main:
                self._evict_small()
            else:
                self._evict_main()
        if key in self.ghost:
            del self.ghost[key]; self.main.append(key)
        else:
            self.small.append(key)
        self.freq[key] = 0
        self.store[key] = True
        return False


class Wtlfu:
    def __init__(self, capacity):
        self.capacity = capacity
        self.store = {}
        self.ev = []
        self.wcap = max(1, capacity // 100)
        self.pcap = max(1, int((capacity - self.wcap) * 0.8))
        self.window = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        w = 1
        while w < capacity * 4:
            w <<= 1
        self.mask = w - 1
        self.tab = [0] * w
        self.adds = 0
        self.reset_at = capacity * 10

    def _inc(self, key):
        t = self.tab; m = self.mask
        h = key * 0x9E3779B1
        for s in (0, 8, 16, 24):
            i = (h >> s) & m
            h = h * 31 + 7
            if t[i] < 15:
                t[i] += 1
        self.adds += 1
        if self.adds >= self.reset_at:
            self.adds = 0
            self.tab = [x >> 1 for x in self.tab]

    def _est(self, key):
        t = self.tab; m = self.mask
        h = key * 0x9E3779B1
        best = 15
        for s in (0, 8, 16, 24):
            i = (h >> s) & m
            h = h * 31 + 7
            if t[i] < best:
                best = t[i]
        return best

    def access(self, key):
        self._inc(key)
        st = self.store
        if key in st:
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
        st[key] = True
        self.window[key] = True
        if len(self.window) > self.wcap:
            cand, _ = self.window.popitem(last=False)
            if len(st) <= self.capacity:
                self.prob[cand] = True
            else:
                victim = next(iter(self.prob)) if self.prob else next(iter(self.prot))
                if self._est(cand) > self._est(victim):
                    if victim in self.prob:
                        del self.prob[victim]
                    else:
                        del self.prot[victim]
                    del st[victim]
                    self.ev.append(victim)
                    self.prob[cand] = True
                else:
                    del st[cand]
                    self.ev.append(cand)
        return False


class Sketch:
    def __init__(self, capacity):
        w = 1
        while w < capacity * 4:
            w <<= 1
        self.mask = w - 1
        self.tab = [0] * w
        self.adds = 0
        self.reset_at = capacity * 10

    def inc(self, key):
        t = self.tab; m = self.mask
        h = key * 0x9E3779B1
        for s in (0, 8, 16, 24):
            i = (h >> s) & m
            h = h * 31 + 7
            if t[i] < 15:
                t[i] += 1
        self.adds += 1
        if self.adds >= self.reset_at:
            self.adds = 0
            self.tab = [x >> 1 for x in self.tab]

    def est(self, key):
        t = self.tab; m = self.mask
        h = key * 0x9E3779B1
        best = 15
        for s in (0, 8, 16, 24):
            i = (h >> s) & m
            h = h * 31 + 7
            if t[i] < best:
                best = t[i]
        return best


class Cache:
    """Runs several policies as shadows; evictions drop real keys the recent best shadow does not hold."""

    LIRS_FRACS = (0.01, 0.05, 0.2, 0.5)
    OTHERS = ("wtlfu", "s3", "arc", "lirsf")
    HALF_LIFE = 16.0
    PERIOD = 1.0
    MARGIN = 0.02

    def __init__(self, capacity):
        self.capacity = capacity
        sh = [Lirs(capacity, max(1, int(capacity * f))) for f in self.LIRS_FRACS]
        self.sketch = Sketch(capacity)

        def lirsf(c, frac):
            x = Lirs(c, max(1, int(c * frac)))
            x.freq = self.sketch
            return x
        make = {"wtlfu": Wtlfu, "s3": S3, "arc": Arc, "lru": Lru,
                "lirsf": lambda c: lirsf(c, 0.01), "lirsf20": lambda c: lirsf(c, 0.2)}
        sh += [make[n](capacity) for n in self.OTHERS]
        self.shadows = sh
        self.scores = [0.0] * len(sh)
        self.decay = 0.5 ** (1.0 / (self.HALF_LIFE * capacity))
        self.period = max(1, int(self.PERIOD * capacity))
        self.n = 0
        self.lead = 0
        self.store = {}
        self.diff = OrderedDict()

    def access(self, key):
        self.sketch.inc(key)
        d = self.decay; sc = self.scores
        for i, s in enumerate(self.shadows):
            sc[i] = sc[i] * d + s.access(key)
        st = self.store; diff = self.diff
        self.n += 1
        if self.n >= self.period:
            self.n = 0
            best = self.lead
            for i in range(len(sc)):
                if sc[i] > sc[best] * (1 + self.MARGIN):
                    best = i
            if best != self.lead:
                self.lead = best
                ls = self.shadows[best].store
                diff.clear()
                for k in st:
                    if k not in ls:
                        diff[k] = True
        L = self.shadows[self.lead]
        ls = L.store
        for e in L.ev:
            if e in st and e not in ls:
                diff[e] = True
        for s in self.shadows:
            s.ev.clear()
        if key in st:
            if key in ls:
                diff.pop(key, None)
            elif key in diff:
                diff.move_to_end(key)
            return True
        st[key] = True
        if key not in ls:
            diff[key] = True
        if len(st) > self.capacity:
            k, _ = diff.popitem(last=False)
            del st[k]
        return False
