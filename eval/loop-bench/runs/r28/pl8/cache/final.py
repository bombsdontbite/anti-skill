from collections import OrderedDict


class LRU:
    def __init__(self, capacity, ev):
        self.cap = capacity
        self.store = OrderedDict()
        self.ev = ev

    def access(self, key):
        s = self.store
        if key in s:
            s.move_to_end(key)
            return True
        if len(s) >= self.cap:
            k, _ = s.popitem(last=False)
            self.ev.append(k)
        s[key] = True
        return False


class ARC:
    def __init__(self, capacity, ev):
        self.c = capacity
        self.p = 0
        self.t1 = OrderedDict()
        self.t2 = OrderedDict()
        self.b1 = OrderedDict()
        self.b2 = OrderedDict()
        self.store = set()
        self.ev = ev

    def _replace(self, in_b2):
        if self.t1 and (len(self.t1) > self.p or (in_b2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False)
            self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False)
            self.b2[k] = True
        self.store.discard(k)
        self.ev.append(k)

    def access(self, key):
        c = self.c
        if key in self.t1:
            del self.t1[key]
            self.t2[key] = True
            return True
        if key in self.t2:
            self.t2.move_to_end(key)
            return True
        if key in self.b1:
            self.p = min(c, self.p + max(len(self.b2) // max(len(self.b1), 1), 1))
            self._replace(False)
            del self.b1[key]
            self.t2[key] = True
        elif key in self.b2:
            self.p = max(0, self.p - max(len(self.b1) // max(len(self.b2), 1), 1))
            self._replace(True)
            del self.b2[key]
            self.t2[key] = True
        else:
            l1 = len(self.t1) + len(self.b1)
            if l1 == c:
                if len(self.t1) < c:
                    self.b1.popitem(last=False)
                    self._replace(False)
                else:
                    k, _ = self.t1.popitem(last=False)
                    self.store.discard(k)
                    self.ev.append(k)
            else:
                tot = l1 + len(self.t2) + len(self.b2)
                if tot >= c:
                    if tot == 2 * c:
                        self.b2.popitem(last=False)
                    self._replace(False)
            self.t1[key] = True
        self.store.add(key)
        return False


class TinyLFU:
    """LRU window + SLRU main, admission by aged frequency."""

    def __init__(self, capacity, ev, sample, win=0.01, prot=0.8):
        self.wcap = max(1, int(capacity * win))
        self.mcap = capacity - self.wcap
        self.pcap = int(self.mcap * prot)
        self.win = OrderedDict()
        self.prob = OrderedDict()
        self.prot = OrderedDict()
        self.freq = {}
        self.ops = 0
        self.reset = capacity * sample
        self.store = set()
        self.ev = ev

    def access(self, key):
        f = self.freq
        f[key] = f.get(key, 0) + 1
        self.ops += 1
        if self.ops >= self.reset:
            self.ops //= 2
            self.freq = f = {k: v >> 1 for k, v in f.items() if v > 1}
        if key in self.win:
            self.win.move_to_end(key)
            return True
        if key in self.prot:
            self.prot.move_to_end(key)
            return True
        if key in self.prob:
            del self.prob[key]
            self.prot[key] = True
            if len(self.prot) > self.pcap:
                k, _ = self.prot.popitem(last=False)
                self.prob[k] = True
            return True
        self.win[key] = True
        self.store.add(key)
        if len(self.win) > self.wcap:
            cand, _ = self.win.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mcap:
                self.prob[cand] = True
            else:
                src = self.prob if self.prob else self.prot
                vict = next(iter(src))
                if f.get(cand, 0) > f.get(vict, 0):
                    del src[vict]
                    self.store.discard(vict)
                    self.ev.append(vict)
                    self.prob[cand] = True
                else:
                    self.store.discard(cand)
                    self.ev.append(cand)
        return False


class LIRS:
    def __init__(self, capacity, ev, hir=0.01, hist=2):
        self.cap = capacity
        self.lcap = max(1, capacity - max(1, int(capacity * hir)))
        self.s = OrderedDict()
        self.q = OrderedDict()
        self.lir = set()
        self.nonres = OrderedDict()
        self.store = set()
        self.hist = hist * capacity
        self.ev = ev

    def _prune(self):
        s = self.s
        lir = self.lir
        while s:
            k = next(iter(s))
            if k in lir:
                break
            del s[k]
            self.nonres.pop(k, None)

    def _demote(self):
        k, _ = self.s.popitem(last=False)
        self.lir.discard(k)
        self.q[k] = True
        self._prune()

    def access(self, key):
        s = self.s
        if key in self.lir:
            bottom = next(iter(s)) == key
            s.move_to_end(key)
            if bottom:
                self._prune()
            return True
        if key in self.q:
            if key in s:
                del self.q[key]
                self.lir.add(key)
                s.move_to_end(key)
                self._demote()
            else:
                s[key] = True
                self.q.move_to_end(key)
            return True
        st = self.store
        if len(st) >= self.cap:
            k, _ = self.q.popitem(last=False)
            st.discard(k)
            self.ev.append(k)
            if k in s:
                self.nonres[k] = True
                if len(self.nonres) > self.hist:
                    o, _ = self.nonres.popitem(last=False)
                    del s[o]
        st.add(key)
        if key in s:
            del self.nonres[key]
            self.lir.add(key)
            s.move_to_end(key)
            self._demote()
        elif len(self.lir) < self.lcap:
            self.lir.add(key)
            s[key] = True
        else:
            s[key] = True
            self.q[key] = True
        return False


class Cache:
    """Runs several policies as shadows and mirrors the one with most recent hits.

    The real store is the leader's store plus leftover keys from earlier leaders,
    which are dropped only when space is needed.
    """

    DECAY_PERIOD = 16
    MARGIN = 1.02

    def __init__(self, capacity):
        self.cap = capacity
        self.evs = [[] for _ in range(12)]
        e = self.evs
        self.experts = [
            TinyLFU(capacity, e[0], 10),
            TinyLFU(capacity, e[1], 4),
            TinyLFU(capacity, e[2], 30),
            TinyLFU(capacity, e[3], 10, win=0.2),
            ARC(capacity, e[4]),
            LRU(capacity, e[5]),
            TinyLFU(capacity, e[6], 2),
            TinyLFU(capacity, e[7], 100),
            TinyLFU(capacity, e[8], 10, prot=0.5),
            LIRS(capacity, e[9]),
            LIRS(capacity, e[10], hir=0.1),
            LIRS(capacity, e[11], hist=6),
        ]
        self.score = [0.0] * len(self.experts)
        self.decay = 1.0 - 1.0 / (capacity * self.DECAY_PERIOD)
        self.lead = 0
        self.store = set()
        self.stale = set()

    def access(self, key):
        hit = key in self.store
        sc = self.score
        d = self.decay
        for i, ex in enumerate(self.experts):
            sc[i] = sc[i] * d + ex.access(key)
        lead = self.lead
        best = lead
        for i in range(len(sc)):
            if sc[i] > sc[best]:
                best = i
        if best != lead and sc[best] > sc[lead] * self.MARGIN + 1e-9:
            lead = self.lead = best
            ls = self.experts[lead].store
            self.stale = {k for k in self.store if k not in ls}
        ls = self.experts[lead].store
        stale = self.stale
        for i, ev in enumerate(self.evs):
            if ev:
                if i == lead:
                    for k in ev:
                        if k in self.store:
                            stale.add(k)
                ev.clear()
        if hit:
            if key in stale and key in ls:
                stale.discard(key)
        elif key in ls:
            st = self.store
            if len(st) >= self.cap:
                st.discard(stale.pop())
            st.add(key)
            stale.discard(key)
        return hit
