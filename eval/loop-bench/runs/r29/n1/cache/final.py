from collections import OrderedDict


class Cache:
    """LIRS whose resident-HIR share is steered by ghost hits."""

    HIR = 0.01
    NR = 3
    STEP = 0.03
    SHRINK = 2.0
    DIST = 0.1
    GH = 1.0

    def __init__(self, capacity):
        self.capacity = capacity
        self.hcap = max(1, int(capacity * self.HIR))
        self.S = OrderedDict()  # key -> True if LIR
        self.Q = OrderedDict()  # resident HIR: key -> (last access, was LIR)
        self.G = OrderedDict()  # evicted HIR: key -> (last access, was LIR)
        self.lir = 0
        self.t = 0
        self.store = {}

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if S[k]:
                return
            del S[k]

    def _demote(self):
        k, _ = self.S.popitem(last=False)
        self.lir -= 1
        self.Q[k] = (self.t, True)
        self._prune()

    def access(self, key):
        S, Q, store = self.S, self.Q, self.store
        self.t += 1
        cap = self.capacity
        if key in store:
            if S.get(key):
                bottom = next(iter(S)) == key
                S.move_to_end(key)
                if bottom:
                    self._prune()
                return True
            if key in S:
                del Q[key]
                S.move_to_end(key)
                S[key] = True
                self.lir += 1
                self._demote()
            else:
                Q[key] = (self.t, Q[key][1])
                Q.move_to_end(key)
                S[key] = False
            return True
        g = self.G.pop(key, None)
        if g is not None:
            d = max(1, int(cap * self.STEP))
            if g[1]:
                self.hcap = max(1, self.hcap - int(d * self.SHRINK))
            elif self.t - g[0] <= self.hcap + cap * self.DIST:
                self.hcap = min(cap - 1, self.hcap + d)
        while self.lir > cap - self.hcap:
            self._demote()
        if len(store) >= cap:
            k, v = Q.popitem(last=False)
            del store[k]
            self.G[k] = v
            if len(self.G) > cap * self.GH:
                self.G.popitem(last=False)
        store[key] = True
        if self.lir < cap - self.hcap:
            S[key] = True
            S.move_to_end(key)
            self.lir += 1
            return False
        if key in S:
            S.move_to_end(key)
            S[key] = True
            self.lir += 1
            self._demote()
        else:
            S[key] = False
            Q[key] = (self.t, False)
        if len(S) > cap * self.NR + cap // 2:
            excess = len(S) - cap * self.NR
            drop = []
            for k, is_lir in S.items():
                if not is_lir and k not in Q:
                    drop.append(k)
                    if len(drop) >= excess:
                        break
            for k in drop:
                del S[k]
        return False
