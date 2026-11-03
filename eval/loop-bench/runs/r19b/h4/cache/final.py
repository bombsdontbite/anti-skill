from collections import OrderedDict


class LIRS:
    def __init__(self, capacity, hc, nrmax=2.0):
        self.c = capacity
        self.lc = capacity - hc
        self.S = OrderedDict()  # key -> True if LIR
        self.Q = OrderedDict()  # resident HIR
        self.NR = OrderedDict()  # non-resident HIR still in S
        self.lir = 0
        self.store = set()
        self.nrmax = int(nrmax * capacity)

    def _prune(self):
        S = self.S
        NR = self.NR
        while S:
            k = next(iter(S))
            if S[k]:
                break
            del S[k]
            NR.pop(k, None)

    def _demote(self):
        S = self.S
        k = next(iter(S))
        del S[k]
        self.Q[k] = 1
        self._prune()

    def access(self, key):
        S = self.S
        Q = self.Q
        if key in self.store:
            if key in Q:
                if key in S:
                    S[key] = True
                    S.move_to_end(key)
                    del Q[key]
                    self.lir += 1
                    while self.lir > self.lc:
                        self._demote()
                        self.lir -= 1
                else:
                    S[key] = False
                    Q.move_to_end(key)
            else:
                first = next(iter(S)) == key
                S.move_to_end(key)
                if first:
                    self._prune()
            return True
        if len(self.store) >= self.c:
            while not Q:
                self._demote()
                self.lir -= 1
            k, _ = Q.popitem(last=False)
            self.store.discard(k)
            if k in S:
                self.NR[k] = 1
                if len(self.NR) > self.nrmax:
                    j, _ = self.NR.popitem(last=False)
                    del S[j]
        self.store.add(key)
        if key in S:
            del S[key]
            del self.NR[key]
            S[key] = True
            self.lir += 1
        elif self.lir < self.lc:
            S[key] = True
            self.lir += 1
        else:
            S[key] = False
            Q[key] = 1
        while self.lir > self.lc:
            self._demote()
            self.lir -= 1
        return False


STEP = 0.05
FRACS = (0.01, 0.02, 0.05, 0.1, 0.2, 0.35, 0.5)


class Cache:
    def __init__(self, capacity, window=8.0, decay=0.8):
        self.c = capacity
        self.hcs = [max(1, int(capacity * f)) for f in FRACS]
        self.main = LIRS(capacity, self.hcs[1])
        self.store = self.main.store
        self.shadows = [LIRS(capacity, h) for h in self.hcs]
        self.score = [0.0] * len(FRACS)
        self.win = max(50, int(capacity * window))
        self.decay = decay
        self.t = 0

    def access(self, key):
        sc = self.score
        for i, s in enumerate(self.shadows):
            if s.access(key):
                sc[i] += 1
        self.t += 1
        if self.t >= self.win:
            self.t = 0
            best = sc.index(max(sc))
            target = self.c - self.hcs[best]
            lc = self.main.lc
            step = max(1, int(self.c * STEP))
            if target > lc:
                lc = min(target, lc + step)
            else:
                lc = max(target, lc - step)
            self.main.lc = lc
            self.score = [x * self.decay for x in sc]
        return self.main.access(key)
