import heapq
from collections import OrderedDict, deque


class Lirs:
    """LIRS with bounded non-resident history and a hill-climbed HIR queue size."""

    GHOSTS = 4
    SAMPLE = 1
    STEP = 0.03
    ADAPT = False

    def __init__(self, capacity, hir):
        self.capacity = capacity
        self.hcap = max(1, int(capacity * hir))
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.ghost = OrderedDict()
        self.lir = set()
        self.store = {}
        self.gcap = self.GHOSTS * capacity
        self.period = self.SAMPLE * capacity
        self.n = self.hits = 0
        self.prev = 0.0
        self.step = max(1, int(capacity * self.STEP))

    def _prune(self):
        S, lir = self.S, self.lir
        while S:
            k = next(iter(S))
            if k in lir:
                break
            del S[k]
            self.ghost.pop(k, None)

    def _demote(self):
        k, _ = self.S.popitem(last=False)
        self.lir.discard(k)
        self.Q[k] = True
        self._prune()

    def _climb(self):
        rate = self.hits / self.n
        if rate < self.prev:
            self.step = -self.step
        self.prev = rate
        self.n = self.hits = 0
        self.hcap = min(self.capacity - 1, max(1, self.hcap + self.step))
        while len(self.lir) > self.capacity - self.hcap:
            self._demote()
        while len(self.Q) > self.hcap:
            self._evict_q()

    def _evict_q(self):
        v, _ = self.Q.popitem(last=False)
        del self.store[v]
        if v in self.S:
            self.ghost[v] = True
            if len(self.ghost) > self.gcap:
                g, _ = self.ghost.popitem(last=False)
                del self.S[g]

    def access(self, key):
        hit = self._access(key)
        if self.ADAPT:
            self.n += 1
            self.hits += hit
            if self.n >= self.period:
                self._climb()
        return hit

    def _access(self, key):
        S, Q, lir = self.S, self.Q, self.lir
        if key in lir:
            S.move_to_end(key)
            self._prune()
            return True
        if key in Q:
            if key in S:
                del S[key]
                S[key] = True
                del Q[key]
                lir.add(key)
                self._demote()
            else:
                S[key] = True
                Q.move_to_end(key)
            return True
        if len(lir) < self.capacity - self.hcap:
            lir.add(key)
            S.pop(key, None)
            self.ghost.pop(key, None)
            S[key] = True
            self.store[key] = True
            return False
        while len(Q) >= self.hcap:
            self._evict_q()
        self.store[key] = True
        if key in S:
            del S[key]
            self.ghost.pop(key, None)
            S[key] = True
            lir.add(key)
            self._demote()
        else:
            S[key] = True
            Q[key] = True
        return False


class Awt:
    """W-TinyLFU whose window size is tuned online by hill climbing on hit rate."""

    PROTECTED = 0.8
    SAMPLE = 1
    STEP0 = 0.0625
    DECAY = 0.98

    def __init__(self, capacity, adapt=True):
        self.capacity = capacity
        self.store = {}
        self.window = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.wcap = max(1, capacity // 100)
        self.freq = {}
        self.ops = 0
        self.reset = 10 * capacity
        self.period = self.SAMPLE * capacity if adapt else 1 << 60
        self.n = 0
        self.hits = 0
        self.prev = 0.0
        self.step = -max(1, int(capacity * self.STEP0))

    def _count(self, key):
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = {k: v >> 1 for k, v in f.items() if v > 1}

    def _climb(self):
        rate = self.hits / self.n
        if rate < self.prev:
            self.step = -self.step
        mag = abs(self.step)
        self.prev = rate
        self.n = self.hits = 0
        self.wcap = min(self.capacity - 1, max(1, self.wcap + self.step))
        mag = max(1, int(mag * self.DECAY))
        self.step = mag if self.step > 0 else -mag
        self._fit()

    def _fit(self):
        mcap = self.capacity - self.wcap
        pcap = int(mcap * self.PROTECTED)
        while len(self.prot) > pcap:
            k, _ = self.prot.popitem(last=False)
            self.prob[k] = True
        while len(self.window) > self.wcap:
            k, _ = self.window.popitem(last=False)
            self.prob[k] = True
        while len(self.prob) + len(self.prot) > mcap:
            if self.prob:
                k, _ = self.prob.popitem(last=False)
            else:
                k, _ = self.prot.popitem(last=False)
            del self.store[k]

    def _hit(self, key):
        if key in self.window:
            self.window.move_to_end(key)
            return True
        if key in self.prot:
            self.prot.move_to_end(key)
            return True
        if key in self.prob:
            del self.prob[key]
            self.prot[key] = True
            if len(self.prot) > int((self.capacity - self.wcap) * self.PROTECTED):
                k, _ = self.prot.popitem(last=False)
                self.prob[k] = True
            return True
        return False

    def access(self, key):
        self._count(key)
        self.n += 1
        hit = self._hit(key)
        if hit:
            self.hits += 1
        else:
            self._miss(key)
        if self.n >= self.period:
            self._climb()
        return hit

    def _miss(self, key):
        self.window[key] = True
        self.store[key] = True
        if len(self.window) > self.wcap:
            cand, _ = self.window.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.capacity - self.wcap:
                self.prob[cand] = True
            else:
                victim = next(iter(self.prob)) if self.prob else next(iter(self.prot))
                f = self.freq
                if f.get(cand, 0) > f.get(victim, 0):
                    if victim in self.prob:
                        del self.prob[victim]
                    else:
                        del self.prot[victim]
                    del self.store[victim]
                    self.prob[cand] = True
                else:
                    del self.store[cand]



class S3:
    def __init__(self, capacity):
        self.cap = capacity
        self.scap = max(1, capacity // 10)
        self.small = deque(); self.main = deque()
        self.ghost = {}; self.gq = deque()
        self.freq = {}
        self.store = {}
        self.nmain = 0

    def _evict_small(self):
        while self.small:
            k = self.small.popleft()
            if self.freq[k] > 0:
                self.main.append(k); self.freq[k] = 0; self.nmain += 1
                if self.nmain > self.cap - self.scap:
                    self._evict_main()
            else:
                del self.store[k]; del self.freq[k]
                self.ghost[k] = True; self.gq.append(k)
                if len(self.gq) > self.cap:
                    g = self.gq.popleft(); self.ghost.pop(g, None)
                return

    def _evict_main(self):
        while self.main:
            k = self.main.popleft()
            if self.freq[k] > 0:
                self.freq[k] -= 1; self.main.append(k)
            else:
                del self.store[k]; del self.freq[k]; self.nmain -= 1
                return

    def access(self, key):
        if key in self.store:
            self.freq[key] = min(3, self.freq[key] + 1)
            return True
        while len(self.store) >= self.cap:
            if len(self.small) >= self.scap or not self.main:
                self._evict_small()
            else:
                self._evict_main()
        self.store[key] = True; self.freq[key] = 0
        if key in self.ghost:
            del self.ghost[key]; self.main.append(key); self.nmain += 1
        else:
            self.small.append(key)
        return False


class Lfu:
    """LFU over aged counts of all requests; a miss is admitted only if at least as frequent as the victim."""

    def __init__(self, capacity, reset):
        self.capacity = capacity
        self.store = {}
        self.freq = {}
        self.heap = []
        self.ops = 0
        self.reset = reset * capacity
        self.tick = 0

    def _age(self):
        self.freq = {k: v >> 1 for k, v in self.freq.items() if v > 1 or k in self.store}
        self.heap = [(self.freq[k], i, k) for i, k in enumerate(self.store)]
        heapq.heapify(self.heap)

    def access(self, key):
        self.tick += 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self._age()
        f = self.freq
        c = f.get(key, 0) + 1
        f[key] = c
        if key in self.store:
            heapq.heappush(self.heap, (c, self.tick, key))
            return True
        st = self.store
        if len(st) >= self.capacity:
            h = self.heap
            while True:
                vf, _, v = h[0]
                if v in st and f.get(v, 0) == vf:
                    break
                heapq.heappop(h)
            if c < vf:
                return False
            heapq.heappop(h)
            del st[v]
        st[key] = True
        heapq.heappush(self.heap, (c, self.tick, key))
        return False


class Cache:
    """Follows whichever shadow policy has the most recent hits."""

    HIRS = (0.01, 0.1, 0.3)
    HALF = 40.0
    EXTRA = True
    LFU = (2, 8, 30)

    def __init__(self, capacity):
        self.capacity = capacity
        self.store = set()
        self.experts = [Lirs(capacity, h) for h in self.HIRS] + [Awt(capacity)]
        if self.EXTRA:
            self.experts += [Awt(capacity, False), S3(capacity)]
        self.experts += [Lfu(capacity, r) for r in self.LFU]
        self.score = [0.0] * len(self.experts)
        self.decay = 1.0 - 1.0 / (self.HALF * capacity)
        self.lead = 0
        self.stale = []

    def access(self, key):
        hit = key in self.store
        sc = self.score
        d = self.decay
        for i, e in enumerate(self.experts):
            sc[i] = sc[i] * d + e.access(key)
        for i in range(len(sc)):
            if sc[i] > sc[self.lead] + 1e-9:
                self.lead = i
        lead = self.experts[self.lead].store
        if not hit and key in lead:
            self.store.add(key)
            st = self.store
            while len(st) > self.capacity:
                if not self.stale:
                    self.stale = [k for k in st if k not in lead]
                k = self.stale.pop()
                if k in st and k not in lead:
                    st.discard(k)
        return hit
