import random
from collections import OrderedDict


class Arc:
    def __init__(self, capacity):
        self.c = capacity
        self.p = 0
        self.t1 = OrderedDict()
        self.t2 = OrderedDict()
        self.b1 = OrderedDict()
        self.b2 = OrderedDict()
        self.store = set()

    def _replace(self, in_b2):
        t1, t2, c = self.t1, self.t2, self.c
        if t1 and (len(t1) > self.p or (in_b2 and len(t1) == self.p)):
            k, _ = t1.popitem(last=False)
            self.b1[k] = 1
        else:
            k, _ = t2.popitem(last=False)
            self.b2[k] = 1
        self.store.discard(k)

    def access(self, key):
        t1, t2, b1, b2, c = self.t1, self.t2, self.b1, self.b2, self.c
        if key in t1:
            del t1[key]
            t2[key] = 1
            return True
        if key in t2:
            t2.move_to_end(key)
            return True
        if key in b1:
            self.p = min(c, self.p + max(1, len(b2) // max(1, len(b1))))
            del b1[key]
            self._replace(False)
            t2[key] = 1
            self.store.add(key)
            return False
        if key in b2:
            self.p = max(0, self.p - max(1, len(b1) // max(1, len(b2))))
            del b2[key]
            self._replace(True)
            t2[key] = 1
            self.store.add(key)
            return False
        if len(t1) + len(b1) >= c:
            if len(t1) < c:
                b1.popitem(last=False)
                self._replace(False)
            else:
                k, _ = t1.popitem(last=False)
                self.store.discard(k)
        else:
            tot = len(t1) + len(t2) + len(b1) + len(b2)
            if tot >= c:
                if tot >= 2 * c:
                    b2.popitem(last=False)
                if len(t1) + len(t2) >= c:
                    self._replace(False)
        t1[key] = 1
        self.store.add(key)
        return False



LHIR = 0.02


class Lirs:
    """LIRS with bounded non-resident history."""

    def __init__(self, capacity):
        self.cap = capacity
        self.hcap = max(1, int(capacity * LHIR))
        self.lcap = capacity - self.hcap
        self.S = OrderedDict()  # key -> state: 'L','H','N'
        self.Q = OrderedDict()  # resident HIR
        self.nlir = 0
        self.nnon = 0
        self.store = set()

    def _prune(self):
        S = self.S
        while S:
            k = next(iter(S))
            st = S[k]
            if st == 'L':
                break
            del S[k]
            if st == 'N':
                self.nnon -= 1

    def _evict_hir(self):
        k, _ = self.Q.popitem(last=False)
        self.store.discard(k)
        if k in self.S:
            self.S[k] = 'N'
            self.nnon += 1
            if self.nnon > 8 * self.cap:
                for x in self.S:
                    if self.S[x] == 'N':
                        del self.S[x]
                        self.nnon -= 1
                        break

    def access(self, key):
        S, Q = self.S, self.Q
        st = S.get(key)
        if st == 'L':
            S.move_to_end(key)
            self._prune()
            return True
        if st == 'H':
            if key in Q:
                del Q[key]
                S.move_to_end(key)
                S[key] = 'L'
                self.nlir += 1
                # demote bottom LIR
                bk = next(iter(S))
                # bottom of S is LIR after prune; find it
                for x in S:
                    if S[x] == 'L':
                        bk = x
                        break
                S[bk] = 'H'
                del S[bk]  # re-add as HIR resident at top of Q only
                self.nlir -= 1
                Q[bk] = 1
                self._prune()
                return True
        if st is None and key in Q:
            Q.move_to_end(key)
            return True
        # miss
        if len(self.store) >= self.cap:
            self._evict_hir()
            st = S.get(key)
        self.store.add(key)
        if self.nlir < self.lcap:
            S[key] = 'L'
            self.nlir += 1
            return False
        if st == 'N' or st == 'H':
            # in stack history: promote to LIR
            if st == 'N':
                self.nnon -= 1
            del S[key]
            S[key] = 'L'
            self.nlir += 1
            for x in S:
                if S[x] == 'L':
                    bk = x
                    break
            del S[bk]
            self.nlir -= 1
            Q[bk] = 1
            self._prune()
            return False
        S[key] = 'H'
        Q[key] = 1
        return False



DECAY = 0.995


class Cache:
    def __init__(self, capacity):
        self.cap = capacity
        self.sh = [P(capacity) for P in (Arc, Lirs,)]
        self.score = [0.0] * len(self.sh)
        self.lead = 0
        self.rec = OrderedDict()
        self.store = self.rec

    def access(self, key):
        sc = self.score
        d = DECAY
        for i, s in enumerate(self.sh):
            sc[i] = sc[i] * d + (1.0 if s.access(key) else 0.0)
        lead = self.lead
        for i in range(len(sc)):
            if sc[i] > sc[lead] * 1.05:
                lead = i
        self.lead = lead
        rec = self.rec
        if key in rec:
            rec.move_to_end(key)
            return True
        ls = self.sh[lead].store
        rec[key] = True
        if len(rec) > self.cap:
            for k in rec:
                if k != key and k not in ls:
                    del rec[k]
                    break
            else:
                for k in rec:
                    if k != key:
                        del rec[k]
                        break
        return False
