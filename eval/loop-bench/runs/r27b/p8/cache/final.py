from collections import OrderedDict


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



class WT:
    """W-TinyLFU: LRU window, SLRU main, frequency-based admission, adaptive window."""

    def __init__(self, capacity, window_frac=0.01, prot_frac=0.8, sample_mult=10, climb=True):
        self.capacity = capacity
        self.store = {}
        self.wmax = max(1, int(capacity * window_frac))
        self.prot_frac = prot_frac
        self.window = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.freq = {}
        self.ops = 0
        self.sample = sample_mult * capacity
        self.climb = climb
        self.step = max(1, capacity // 16)
        self.hits = 0
        self.n = 0
        self.prev_rate = 0.0
        self.period = 10 * capacity

    def _inc(self, key):
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.sample:
            self.ops = 0
            self.freq = {k: v >> 1 for k, v in f.items() if v > 1}

    def _climb(self):
        rate = self.hits / self.n
        if rate < self.prev_rate:
            self.step = -self.step
        self.prev_rate = rate
        self.hits = self.n = 0
        w = self.wmax + self.step
        lo, hi = 1, self.capacity - 2
        self.wmax = min(hi, max(lo, w))

    def access(self, key):
        self._inc(key)
        if self.climb:
            self.n += 1
            if self.n >= self.period:
                self._climb()
        if key in self.store:
            self.hits += 1
            if key in self.window:
                self.window.move_to_end(key)
            elif key in self.prot:
                self.prot.move_to_end(key)
            else:
                del self.prob[key]
                self.prot[key] = True
                pmax = int((self.capacity - self.wmax) * self.prot_frac)
                while len(self.prot) > pmax:
                    k, _ = self.prot.popitem(last=False)
                    self.prob[k] = True
            return True
        self.store[key] = True
        self.window[key] = True
        while len(self.window) > self.wmax:
            cand, _ = self.window.popitem(last=False)
            self.prob[cand] = True
        while len(self.store) > self.capacity:
            # evict from main: compare probation head (victim) vs most recent window-evicted candidate
            if self.prob:
                it = iter(self.prob)
                victim = next(it)
                cand = next(reversed(self.prob))
                if cand != victim and cand not in self.window:
                    f = self.freq
                    if f.get(cand, 0) > f.get(victim, 0):
                        del self.prob[victim]
                        del self.store[victim]
                    else:
                        del self.prob[cand]
                        del self.store[cand]
                    continue
                del self.prob[victim]
                del self.store[victim]
            elif self.prot:
                k, _ = self.prot.popitem(last=False)
                del self.store[k]
            else:
                k, _ = self.window.popitem(last=False)
                del self.store[k]
        pmax = int((self.capacity - self.wmax) * self.prot_frac)
        while len(self.prot) > pmax:
            k, _ = self.prot.popitem(last=False)
            self.prob[k] = True
        return False



class LIRS:
    """LIRS with a bounded number of non-resident entries."""

    def __init__(self, capacity, hir_frac=0.01, nr_mult=2.0):
        self.capacity = capacity
        self.hsize = max(1, int(capacity * hir_frac))
        self.lsize = capacity - self.hsize
        self.store = {}
        self.S = OrderedDict()   # key -> True (recency stack)
        self.Q = OrderedDict()   # resident HIR
        self.lir = set()
        self.NR = OrderedDict()  # non-resident HIR still in S
        self.nrmax = int(nr_mult * capacity)

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if k in self.lir:
                return
            del S[k]
            if k in self.NR:
                del self.NR[k]

    def _demote_bottom(self):
        k, _ = self.S.popitem(last=False)
        self.lir.discard(k)
        self.Q[k] = True
        self._prune()

    def access(self, key):
        S = self.S
        if key in self.lir:
            S.move_to_end(key)
            self._prune()
            return True
        if key in self.store:
            if key in S:
                S.move_to_end(key)
                del self.Q[key]
                self.lir.add(key)
                self._demote_bottom()
            else:
                S[key] = True
                self.Q.move_to_end(key)
            return True
        if len(self.lir) < self.lsize and not self.Q:
            self.lir.add(key)
            S[key] = True
            S.move_to_end(key)
            self.store[key] = True
            self.NR.pop(key, None)
            return False
        if len(self.store) >= self.capacity:
            v, _ = self.Q.popitem(last=False)
            del self.store[v]
            if v in S:
                self.NR[v] = True
                if len(self.NR) > self.nrmax:
                    o, _ = self.NR.popitem(last=False)
                    del S[o]
        self.store[key] = True
        if key in S:
            del self.NR[key]
            S.move_to_end(key)
            self.lir.add(key)
            self._demote_bottom()
        else:
            S[key] = True
            self.Q[key] = True
        return False


class Cache:
    """Follow the leader among shadow policies, by decayed recent hit counts."""

    def __init__(self, capacity, half=4.0, members=None, hyst=0.98, long_half=32.0):
        self.capacity = capacity
        self.store = OrderedDict()
        if members is None:
            members = [lambda c: LRU(c), lambda c: WT(c, sample_mult=20, climb=False),
                       lambda c: WT(c, sample_mult=2), lambda c: LIRS(c, nr_mult=5.0)]
        self.sh = [m(capacity) for m in members]
        self.score = [0.0] * len(self.sh)
        self.decay = 0.5 ** (1.0 / (half * capacity))
        self.leader = 0
        self.long = [0.0] * len(self.sh)
        self.decay_long = 0.5 ** (1.0 / (long_half * capacity))
        self.hyst = hyst

    def access(self, key):
        sc = self.score
        lg = self.long
        d = self.decay
        dl = self.decay_long
        best = -1.0
        for i, s in enumerate(self.sh):
            h = s.access(key)
            v = sc[i] * d + h
            sc[i] = v
            lg[i] = lg[i] * dl + h
            if v > best:
                best = v; bi = i
        ld = self.leader
        if sc[ld] < best * self.hyst and lg[bi] > lg[ld]:
            self.leader = bi
        st = self.store
        if key in st:
            st.move_to_end(key)
            return True
        lead = self.sh[self.leader].store
        if key not in lead:
            return False
        if len(st) >= self.capacity:
            for k in st:
                if k not in lead:
                    break
            del st[k]
        st[key] = True
        return False
