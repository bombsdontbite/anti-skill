from collections import OrderedDict
HF = 0.05
SM = 3
class Cache:
    def __init__(self, capacity):
        self.c = capacity
        self.nh = max(1, int(capacity * HF)); self.nl = capacity - self.nh
        self.S = OrderedDict(); self.Q = OrderedDict()
        self.nlir = 0; self.store = set(); self.maxS = SM * capacity

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            if S[k] == 'L': break
            del S[k]

    def _demote(self):
        S = self.S
        for k in S:
            if S[k] == 'L': break
        del S[k]; self.nlir -= 1; self.Q[k] = 1
        self._prune()

    def access(self, key):
        S = self.S; Q = self.Q
        st = S.get(key)
        if st == 'L':
            S.move_to_end(key); self._prune(); return True
        if st == 'H':
            del Q[key]; S.move_to_end(key); S[key] = 'L'; self.nlir += 1
            self._demote(); return True
        if key in Q:
            Q.move_to_end(key); S[key] = 'H'; return True
        if self.nlir < self.nl:
            S[key] = 'L'; self.nlir += 1; self.store.add(key)
            if st == 'N': pass
            return False
        if len(Q) >= self.nh:
            k, _ = Q.popitem(last=False); self.store.discard(k)
            if k in S: S[k] = 'N'
        self.store.add(key)
        if st == 'N':
            S.move_to_end(key); S[key] = 'L'; self.nlir += 1
            self._demote()
        else:
            S[key] = 'H'; Q[key] = 1
        if len(S) > self.maxS:
            for k in list(S):
                if S[k] == 'N':
                    del S[k]
                    if len(S) <= self.maxS: break
        return False
