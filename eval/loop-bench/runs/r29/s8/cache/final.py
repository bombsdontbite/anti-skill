from collections import OrderedDict


class _Lirs:
    def __init__(self, capacity, hfrac, smax=3.0):
        self.cap = capacity
        self.S = OrderedDict()
        self.Q = OrderedDict()
        self.lir = set()
        self.store = set()
        self.log = []
        self.smax = int(capacity * smax)
        self.set_h(hfrac)

    def set_h(self, hfrac):
        self.hcap = max(1, int(self.cap * hfrac))
        self.lcap = self.cap - self.hcap

    def _prune(self):
        S = self.S
        lir = self.lir
        while S:
            k = next(iter(S))
            if k in lir:
                return
            del S[k]

    def _demote(self):
        k, _ = self.S.popitem(last=False)
        self.lir.discard(k)
        self.Q[k] = 1
        self._prune()

    def access(self, k):
        S = self.S
        Q = self.Q
        lir = self.lir
        while len(lir) > self.lcap:
            self._demote()
        if k in lir:
            S.move_to_end(k)
            self._prune()
            return True
        st = self.store
        hit = k in st
        if not hit:
            if len(st) >= self.cap:
                v, _ = Q.popitem(last=False)
                st.discard(v)
                self.log.append(v)
            st.add(k)
        if k in S:
            S.move_to_end(k)
            Q.pop(k, None)
            lir.add(k)
            self._demote()
        elif len(lir) < self.lcap:
            lir.add(k)
            S[k] = 1
            Q.pop(k, None)
        else:
            S[k] = 1
            Q[k] = 1
            Q.move_to_end(k)
        if len(S) > self.smax + self.cap:
            n = len(S) - self.smax
            for x in list(S):
                if n <= 0:
                    break
                if x not in lir and x not in st:
                    del S[x]
                    n -= 1
        return hit



class _Tlfu:
    def __init__(self, capacity, wfrac=0.01, agef=10, pf=0.8):
        self.cap = capacity
        self.wcap = max(1, int(capacity * wfrac))
        self.mcap = capacity - self.wcap
        self.pcap = int(self.mcap * pf)
        self.win = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.freq = {}
        self.ops = 0
        self.reset = capacity * agef
        self.store = set()
        self.log = []

    def access(self, k):
        f = self.freq
        f[k] = f.get(k, 0) + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops = 0
            self.freq = f = {a: b >> 1 for a, b in f.items() if b > 1}
        if k in self.win:
            self.win.move_to_end(k)
            return True
        if k in self.prot:
            self.prot.move_to_end(k)
            return True
        if k in self.prob:
            del self.prob[k]
            self.prot[k] = 1
            if len(self.prot) > self.pcap:
                d, _ = self.prot.popitem(last=False)
                self.prob[d] = 1
            return True
        self.store.add(k)
        self.win[k] = 1
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mcap:
                self.prob[cand] = 1
            else:
                vq = self.prob if self.prob else self.prot
                vic = next(iter(vq))
                if f.get(cand, 0) > f.get(vic, 0):
                    del vq[vic]
                    self.prob[cand] = 1
                else:
                    vic = cand
                self.store.discard(vic)
                self.log.append(vic)
        return False


class Cache:
    """Several policies run as shadows; the real cache copies whichever hit most recently,
    admitting only keys the leader holds and evicting keys the leader has dropped."""

    def __init__(self, capacity, winf=10.0, margin=5.0, which=("l01", "l50", "tlfu30")):
        self.cap = capacity
        mk = {"l01": lambda: _Lirs(capacity, 0.01), "l50": lambda: _Lirs(capacity, 0.5),
              "l20": lambda: _Lirs(capacity, 0.2), "tlfu": lambda: _Tlfu(capacity),
              "tlfu30": lambda: _Tlfu(capacity, 0.01, 30, 0.5), "tlfu5": lambda: _Tlfu(capacity, 0.01, 5, 0.8)}
        self.shadows = [mk[w]() for w in which]
        self.score = [0.0] * len(self.shadows)
        self.d = 1.0 - 1.0 / (capacity * winf)
        self.margin = margin
        self.cur = 0
        self.store = set()
        self.loglen = capacity * 4

    def _victim(self, lead):
        st = self.store
        ls = lead.store
        log = lead.log
        while log:
            x = log.pop()
            if x in st and x not in ls:
                return x
        for x in st:
            if x not in ls:
                return x
        return None

    def access(self, key):
        d = self.d
        sc = self.score
        for i, s in enumerate(self.shadows):
            sc[i] = sc[i] * d + s.access(key)
            if len(s.log) > 2 * self.loglen:
                del s.log[:self.loglen]
        best = max(range(len(sc)), key=sc.__getitem__)
        if best != self.cur and sc[best] > sc[self.cur] + self.margin:
            self.cur = best
        st = self.store
        if key in st:
            return True
        lead = self.shadows[self.cur]
        if key not in lead.store:
            return False
        if len(st) >= self.cap:
            st.discard(self._victim(lead))
        st.add(key)
        return False
