from collections import OrderedDict


class LRU:
    def __init__(self, capacity):
        self.capacity = capacity
        self.store = OrderedDict()
        self.ev = []

    def access(self, key):
        if key in self.store:
            self.store.move_to_end(key)
            return True
        if len(self.store) >= self.capacity:
            self.ev.append(self.store.popitem(last=False)[0])
        self.store[key] = True
        return False


class LIRS:
    """LIRS: keys with short reuse distance (LIR) keep 99% of the space; others share a small FIFO."""

    def __init__(self, capacity, h=0.01, nr=2):
        self.c = capacity
        self.lirc = capacity - max(1, int(capacity * h))
        self.nr = nr
        self.S = OrderedDict()  # recency stack, end = most recent
        self.Q = OrderedDict()  # resident HIR keys, FIFO
        self.lir = set()
        self.store = set()
        self.ev = []

    def _prune(self):
        S, lir = self.S, self.lir
        while S:
            k = next(iter(S))
            if k in lir:
                break
            del S[k]

    def _demote_bottom(self):
        S = self.S
        b = next(iter(S))
        self.lir.discard(b)
        del S[b]
        self.Q[b] = None
        self._prune()

    def access(self, key):
        S, Q, lir, store = self.S, self.Q, self.lir, self.store
        if key in lir:
            S.move_to_end(key)
            self._prune()
            return True
        if key in store:
            if key in S:
                S.move_to_end(key)
                del Q[key]
                lir.add(key)
                self._demote_bottom()
            else:
                S[key] = None
                Q.move_to_end(key)
            return True
        if len(lir) < self.lirc:
            lir.add(key)
            S[key] = None
            store.add(key)
            return False
        if len(store) >= self.c:
            v, _ = Q.popitem(last=False)
            store.discard(v)
            self.ev.append(v)
        store.add(key)
        if key in S:
            S.move_to_end(key)
            lir.add(key)
            self._demote_bottom()
        else:
            S[key] = None
            Q[key] = None
        if len(S) > (self.nr + 1) * self.c:
            # cap the history of non-resident keys
            for k in list(S):
                if len(S) <= self.nr * self.c:
                    break
                if k not in store:
                    del S[k]
        return False


class Cache:
    """Simulates LIRS and LRU side by side and evicts like whichever hit more recently.

    LIRS wins on loops, scans and hot sets; LRU wins when popularity shifts or recency rules.
    On a miss the real cache evicts a key the leading policy no longer holds, so its contents
    drift toward the leader's.
    """

    def __init__(self, capacity, win=0.5):
        self.c = capacity
        self.P = [LIRS(capacity), LRU(capacity)]
        self.sc = [0.0] * len(self.P)          # exponentially decayed hit counts
        self.D = [dict() for _ in self.P]      # keys we hold that policy i does not
        self.d = 1.0 - 1.0 / (win * capacity)
        self.lead = 0
        self.store = {}

    def access(self, key):
        store = self.store
        hit = key in store
        d, sc, D = self.d, self.sc, self.D
        for i, p in enumerate(self.P):
            if p.access(key):
                sc[i] = sc[i] * d + 1.0
            else:
                sc[i] *= d
            if p.ev:
                Di = D[i]
                for k in p.ev:
                    if k in store:
                        Di[k] = 1
                p.ev.clear()
        if not hit:
            b = self.lead
            for i in range(len(sc)):
                if sc[i] > sc[b] + 1e-9:
                    b = i
            self.lead = b
            if len(store) >= self.c:
                Dl = D[b]
                v = next(iter(Dl)) if Dl else next(iter(store))
                del store[v]
                for Di in D:
                    Di.pop(v, None)
            store[key] = 1
        for i, p in enumerate(self.P):
            if key in p.store:
                D[i].pop(key, None)
            else:
                D[i][key] = 1
        return hit
