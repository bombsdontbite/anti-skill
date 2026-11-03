from collections import OrderedDict, deque


class LIRS:
    """LIRS: stack S of recency, queue Q of resident HIR blocks."""

    def __init__(self, capacity, hir_frac=0.01, ghost_mult=2):
        self.c = capacity
        self.hcap = max(1, int(capacity * hir_frac))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict()   # key -> True if LIR
        self.Q = OrderedDict()
        self.store = {}
        self.nlir = 0
        self.smax = capacity * ghost_mult

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if S[k]:
                break
            del S[k]

    def access(self, key):
        S, Q, store = self.S, self.Q, self.store
        if key in store:
            if key in S and S[key]:
                first = next(iter(S)) == key
                S.move_to_end(key)
                if first:
                    self._prune()
            elif key in S:
                del S[key]; S[key] = True; self.nlir += 1; del Q[key]
                k, _ = S.popitem(last=False)
                S[k] = False  # unreachable value placeholder
                del S[k]
                Q[k] = True; self.nlir -= 1
                self._prune()
            else:
                S[key] = False; Q.move_to_end(key)
            return True
        if self.nlir < self.lcap:
            S[key] = True; self.nlir += 1; store[key] = True
            return False
        if len(Q) >= self.hcap:
            k, _ = Q.popitem(last=False); del store[k]
        store[key] = True
        if key in S:
            del S[key]; S[key] = True; self.nlir += 1
            k, _ = S.popitem(last=False)
            Q[k] = True; self.nlir -= 1
            self._prune()
        else:
            S[key] = False; Q[key] = True
        while len(S) > self.smax:
            k = next(iter(S))
            if S[k]:
                break
            del S[k]
        return False


class ARC:
    """ARC."""

    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1, self.t2, self.b1, self.b2 = OrderedDict(), OrderedDict(), OrderedDict(), OrderedDict()
        self.store = {}

    def _replace(self, in_b2):
        if self.t1 and (len(self.t1) > self.p or (in_b2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = True
        del self.store[k]

    def access(self, key):
        t1, t2, b1, b2, c = self.t1, self.t2, self.b1, self.b2, self.c
        if key in t1:
            del t1[key]; t2[key] = True; return True
        if key in t2:
            t2.move_to_end(key); return True
        if key in b1:
            self.p = min(c, self.p + max(1, len(b2) // len(b1)))
            self._replace(False); del b1[key]; t2[key] = True
        elif key in b2:
            self.p = max(0, self.p - max(1, len(b1) // len(b2)))
            self._replace(True); del b2[key]; t2[key] = True
        else:
            if len(t1) + len(b1) == c:
                if len(t1) < c:
                    b1.popitem(last=False); self._replace(False)
                else:
                    k, _ = t1.popitem(last=False); del self.store[k]
            elif len(t1) + len(b1) < c and len(t1) + len(t2) + len(b1) + len(b2) >= c:
                if len(t1) + len(t2) + len(b1) + len(b2) >= 2 * c:
                    b2.popitem(last=False)
                if len(t1) + len(t2) >= c:
                    self._replace(False)
            t1[key] = True
        self.store[key] = True
        return False


class WTLFU:
    """W-TinyLFU: LRU window, SLRU main, frequency-sketch admission with periodic halving."""

    def __init__(self, capacity, window_frac=0.01, protected_frac=0.8, reset_mult=10):
        self.capacity = capacity
        self.store = {}
        self.wcap = max(1, int(capacity * window_frac))
        self.mcap = capacity - self.wcap
        self.pcap = int(self.mcap * protected_frac)
        self.window = OrderedDict()
        self.probation = OrderedDict()
        self.protected = OrderedDict()
        self.freq = {}
        self.ops = 0
        self.reset_at = capacity * reset_mult

    def _inc(self, key):
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.reset_at:
            self.ops = 0
            self.freq = {k: v >> 1 for k, v in f.items() if v > 1}

    def access(self, key):
        self._inc(key)
        if key in self.store:
            if key in self.window:
                self.window.move_to_end(key)
            elif key in self.protected:
                self.protected.move_to_end(key)
            else:
                del self.probation[key]
                self.protected[key] = True
                if len(self.protected) > self.pcap:
                    k, _ = self.protected.popitem(last=False)
                    self.probation[k] = True
            return True
        self.store[key] = True
        self.window[key] = True
        if len(self.window) > self.wcap:
            cand, _ = self.window.popitem(last=False)
            if len(self.probation) + len(self.protected) < self.mcap:
                self.probation[cand] = True
            else:
                victim = next(iter(self.probation)) if self.probation else next(iter(self.protected))
                f = self.freq
                if f.get(cand, 0) > f.get(victim, 0):
                    if victim in self.probation:
                        del self.probation[victim]
                    else:
                        del self.protected[victim]
                    del self.store[victim]
                    self.probation[cand] = True
                else:
                    del self.store[cand]
        return False


class S3:
    """S3-FIFO: small FIFO, main FIFO with reinsertion, ghost FIFO."""

    def __init__(self, capacity, small_frac=0.1):
        self.c = capacity
        self.scap = max(1, int(capacity * small_frac))
        self.small, self.main = deque(), deque()
        self.ghost = OrderedDict()
        self.freq = {}
        self.store = self.freq

    def _evict_small(self):
        while self.small:
            k = self.small.popleft()
            if self.freq[k] > 0:
                self.freq[k] = 0; self.main.append(k)
                if len(self.main) > self.c - self.scap:
                    self._evict_main()
                if len(self.freq) <= self.c - 1:
                    return
            else:
                del self.freq[k]; self.ghost[k] = True
                if len(self.ghost) > self.c:
                    self.ghost.popitem(last=False)
                return

    def _evict_main(self):
        while self.main:
            k = self.main.popleft()
            if self.freq[k] > 0:
                self.freq[k] -= 1; self.main.append(k)
            else:
                del self.freq[k]; return

    def access(self, key):
        f = self.freq
        if key in f:
            if f[key] < 3: f[key] += 1
            return True
        if len(f) >= self.c:
            if len(self.small) >= self.scap or not self.main:
                self._evict_small()
            else:
                self._evict_main()
            if len(f) >= self.c:
                self._evict_main()
        if key in self.ghost:
            del self.ghost[key]; f[key] = 0; self.main.append(key)
        else:
            f[key] = 0; self.small.append(key)
        return False


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


class Cache:
    """Follow the leader: simulate several policies, steer the real store toward the one with most recent hits."""

    def __init__(self, capacity, half_mult=10.0, experts=None, margin=0.0, abs_margin=0.1):
        self.capacity = capacity
        self.experts = experts(capacity) if experts else [
            LIRS(capacity), LIRS(capacity, 0.1), ARC(capacity), WTLFU(capacity), WTLFU(capacity, 0.01, 0.8, 30), S3(capacity), LRU(capacity)]
        self.score = [0.0] * len(self.experts)
        self.decay = 1.0 - 1.0 / (half_mult * capacity)
        self.boost = 1.0
        self.margin = margin
        self.abs_margin = abs_margin * capacity
        self.lead = 0
        self.store = OrderedDict()

    def access(self, key):
        self.boost /= self.decay
        b = self.boost
        sc = self.score
        for i, e in enumerate(self.experts):
            if e.access(key):
                sc[i] += b
        if b > 1e100:
            self.score = sc = [s / b for s in sc]
            self.boost = 1.0
        store = self.store
        if key in store:
            store.move_to_end(key)
            return True
        best = sc.index(max(sc))
        if sc[best] > sc[self.lead] * (1.0 + self.margin) + self.abs_margin * b:
            self.lead = best
        lead = self.experts[self.lead].store
        if key in lead:
            if len(store) >= self.capacity:
                for k in store:
                    if k not in lead:
                        break
                del store[k]
            store[key] = True
        return False
