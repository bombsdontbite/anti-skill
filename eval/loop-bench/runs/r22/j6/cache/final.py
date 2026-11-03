from collections import OrderedDict, deque
import heapq


class Lru:
    def __init__(self, capacity):
        self.c = capacity
        self.store = OrderedDict()
        self.evicted = deque()

    def access(self, key):
        if key in self.store:
            self.store.move_to_end(key)
            return True
        if len(self.store) >= self.c:
            k, _ = self.store.popitem(last=False)
            self.evicted.append(k)
        self.store[key] = True
        return False


class Lirs:
    def __init__(self, capacity, hir=0.03):
        self.c = capacity
        self.hc = max(1, int(capacity * hir))
        self.lc = capacity - self.hc
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.lir = set()
        self.store = set()
        self.maxS = capacity * 3
        self.evicted = deque()

    def _demote(self):
        S = self.S
        b = next(iter(S))
        self.lir.discard(b)
        del S[b]
        self.Q[b] = True
        while S:
            k = next(iter(S))
            if k in self.lir:
                break
            del S[k]

    def access(self, key):
        S, Q, lir = self.S, self.Q, self.lir
        if key in lir:
            S.move_to_end(key)
            while S:
                k = next(iter(S))
                if k in lir:
                    break
                del S[k]
            return True
        if key in Q:
            if key in S:
                del Q[key]
                lir.add(key)
                S.move_to_end(key)
                self._demote()
            else:
                Q.move_to_end(key)
                S[key] = True
            return True
        if len(lir) < self.lc:
            lir.add(key)
            self.store.add(key)
            S[key] = True
            S.move_to_end(key)
            return False
        if len(Q) >= self.hc:
            v, _ = Q.popitem(last=False)
            self.store.discard(v)
            self.evicted.append(v)
        self.store.add(key)
        if key in S:
            lir.add(key)
            S.move_to_end(key)
            self._demote()
        else:
            Q[key] = True
            S[key] = True
        if len(S) > self.maxS + self.c:
            for k in list(S)[: len(S) - self.maxS]:
                if k not in lir:
                    del S[k]
        return False


class Tlfu:
    def __init__(self, capacity, wfrac=0.01):
        self.c = capacity
        self.wc = max(1, int(capacity * wfrac))
        self.mc = capacity - self.wc
        self.pc = int(self.mc * 0.8)
        self.win = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.f = {}
        self.n = 0
        self.reset = 10 * capacity
        self.store = set()
        self.evicted = deque()

    def access(self, key):
        f = self.f
        f[key] = f.get(key, 0) + 1
        self.n += 1
        if self.n >= self.reset:
            self.n //= 2
            self.f = {k: v >> 1 for k, v in f.items() if v > 1}
            f = self.f
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
        self.win[key] = True
        self.store.add(key)
        if len(self.win) > self.wc:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mc:
                self.prob[cand] = True
            else:
                vq = self.prob if self.prob else self.prot
                victim = next(iter(vq))
                if f.get(cand, 0) > f.get(victim, 0):
                    del vq[victim]
                    self.store.discard(victim)
                    self.evicted.append(victim)
                    self.prob[cand] = True
                else:
                    self.store.discard(cand)
                    self.evicted.append(cand)
        return False


class Pred:
    """Exact eviction of the key with the furthest predicted next use:
    max(last + mean gap, last + over * time since last), via a heap and an LRU list."""

    def __init__(self, capacity, unk=16, hist=10, over=1.5, cap_n=16):
        self.c = capacity
        self.unk = unk * capacity
        self.hmax = int(hist * capacity)
        self.over = over
        self.capn = cap_n
        self.store = OrderedDict()   # key -> [last, first, n], LRU order
        self.h = []
        self.ghost = OrderedDict()
        self.t = 0
        self.evicted = deque()

    def _push(self, key, v):
        n = v[2]
        g = (v[0] - v[1]) / n if n else self.unk
        heapq.heappush(self.h, (-(v[0] + g), v[0], key))

    def _touch(self, v, t):
        v[0] = t
        if v[2] < self.capn:
            v[2] += 1
        else:
            v[1] += (t - v[1]) / v[2]

    def access(self, key):
        self.t += 1
        t = self.t
        st = self.store
        if key in st:
            v = st[key]
            self._touch(v, t)
            st.move_to_end(key)
            self._push(key, v)
            return True
        v = self.ghost.pop(key, None)
        if v is None:
            v = [t, t, 0]
        else:
            self._touch(v, t)
        if len(st) >= self.c:
            h = self.h
            while True:
                na, lt, k = h[0]
                w = st.get(k)
                if w is not None and w[0] == lt:
                    break
                heapq.heappop(h)
            lk = next(iter(st))
            l0 = st[lk][0]
            if -na >= l0 + self.over * (t - l0):
                heapq.heappop(h)
            else:
                k = lk
            self.ghost[k] = st.pop(k)
            self.evicted.append(k)
            if len(self.ghost) > self.hmax:
                self.ghost.popitem(last=False)
        st[key] = v
        self._push(key, v)
        if len(self.h) > 8 * self.c:
            self.h = []
            for k, w in st.items():
                self._push(k, w)
        return False


class Cache:
    """Runs several policies as shadows; evicts what the recently best one has evicted."""

    def __init__(self, capacity):
        self.c = capacity
        self.experts = [Lirs(capacity, 0.01), Lru(capacity), Tlfu(capacity), Pred(capacity)]
        self.score = [0.0] * len(self.experts)
        self.decay = 1.0 - 1.0 / (capacity * 40)
        self.lead = 0
        self.store = set()

    def access(self, key):
        sc = self.score
        d = self.decay
        for i, e in enumerate(self.experts):
            sc[i] = sc[i] * d + (1.0 if e.access(key) else 0.0)
        best = 0
        for i in range(1, len(sc)):
            if sc[i] > sc[best]:
                best = i
        if sc[best] > sc[self.lead] * 1.02:
            self.lead = best
        store = self.store
        if key in store:
            return True
        if len(store) >= self.c:
            lead = self.experts[self.lead]
            ls = lead.store
            log = lead.evicted
            victim = None
            while log:
                k = log.popleft()
                if k in store and k not in ls:
                    victim = k
                    break
            if victim is None:
                for k in store:
                    if k not in ls:
                        victim = k
                        break
            store.discard(victim)
        store.add(key)
        for e in self.experts:
            if len(e.evicted) > 4 * self.c:
                e.evicted = deque(k for k in e.evicted if k in store and k not in e.store)
        return False
