from collections import OrderedDict

FRACS = (0.01, 0.1, 0.5, 0.95)
DEC = 3
PER = 0.5
HY = 0.02
NR = 2
RESET = 10
ADMS = (False, True)


class LIRS:
    def __init__(self, capacity, frac, f, adm=False):
        self.c = capacity
        self.f = f
        self.adm = adm
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.lir = set()
        self.keys = set()
        self.score = 0.0
        self.lc = 0
        self.resize(frac)

    def resize(self, frac):
        self.lc = max(1, min(self.c - 1, self.c - int(self.c * frac)))
        while len(self.lir) > self.lc:
            self._demote()

    def _prune(self):
        S, lir = self.S, self.lir
        while S:
            k = next(iter(S))
            if k in lir:
                return
            del S[k]

    def _demote(self):
        S = self.S
        k = next(iter(S))
        del S[k]
        self.lir.discard(k)
        self.Q[k] = True
        self._prune()

    def _promote(self, key):
        self.S.pop(key, None)
        self.S[key] = True
        self.Q.pop(key, None)
        self.lir.add(key)
        if len(self.lir) > self.lc:
            self._demote()

    def access(self, key):
        S, Q, lir, keys = self.S, self.Q, self.lir, self.keys
        if key in lir:
            S.move_to_end(key)
            self._prune()
            return True
        if key in keys:
            if key in S:
                self._promote(key)
            else:
                Q.move_to_end(key)
                S[key] = False
            return True
        if len(keys) >= self.c:
            if not Q:
                self._demote()
            v = next(iter(Q))
            if self.adm and key not in S and self.f.get(key, 0) < self.f.get(v, 0):
                return False
            del Q[v]
            keys.discard(v)
        keys.add(key)
        if len(lir) < self.lc or key in S:
            self._promote(key)
        else:
            Q[key] = True
            S[key] = False
            if len(S) > (NR + 1) * self.c:
                for k in list(S):
                    if len(S) <= NR * self.c:
                        break
                    if k not in lir and k not in keys:
                        del S[k]
        return False


class Cache:
    def __init__(self, capacity):
        self.c = capacity
        self.f = {}
        self.n = 0
        self.reset = RESET * capacity
        self.cfg = [(fr, a) for a in ADMS for fr in FRACS]
        self.shadows = [LIRS(capacity, fr, self.f, a) for fr, a in self.cfg]
        self.best = 0
        self.real = LIRS(capacity, FRACS[0], self.f, ADMS[0])
        self.store = self.real.keys
        self.decay = 1.0 - 1.0 / (DEC * capacity)
        self.period = max(1, int(capacity * PER))
        self.t = 0

    def access(self, key):
        f = self.f
        f[key] = f.get(key, 0) + 1
        self.n += 1
        if self.n >= self.reset:
            self.n //= 2
            nf = {a: b >> 1 for a, b in f.items() if b > 1}
            f.clear(); f.update(nf)
        sh = self.shadows
        d = self.decay
        for s in sh:
            s.score = s.score * d + s.access(key)
        self.t += 1
        if self.t >= self.period:
            self.t = 0
            b = max(range(len(sh)), key=lambda i: sh[i].score)
            if b != self.best and sh[b].score > sh[self.best].score * (1 + HY):
                self.best = b
                fr, a = self.cfg[b]
                self.real.adm = a
                self.real.resize(fr)
        return self.real.access(key)
