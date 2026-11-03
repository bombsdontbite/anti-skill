from collections import OrderedDict

LIR, HIR, NR = 0, 1, 2


class Lirs:

    def __init__(self, capacity):
        self.capacity = capacity
        self.hcap = max(1, capacity // 100)
        self.lcap = capacity - self.hcap
        self.store = {}
        self.s = OrderedDict()
        self.q = OrderedDict()
        self.state = {}
        self.nlir = 0
        self.nr = 0
        self.nr_max = 3 * capacity

    def set_hcap(self, h):
        self.hcap = h
        self.lcap = self.capacity - h
        s, state, q = self.s, self.state, self.q
        while self.nlir > self.lcap:
            old = next(iter(s))
            state[old] = HIR
            del s[old]
            q[old] = True
            self.nlir -= 1
            self._prune()

    def _prune(self):
        s, state = self.s, self.state
        while s:
            k = next(iter(s))
            st = state[k]
            if st == LIR:
                return
            del s[k]
            if st == NR:
                del state[k]
                self.nr -= 1

    def _trim_nr(self):
        s, state = self.s, self.state
        if self.nr <= self.nr_max:
            return
        target = self.nr_max - self.nr_max // 8
        for k in list(s):
            if self.nr <= target:
                break
            if state[k] == NR:
                del s[k]
                del state[k]
                self.nr -= 1

    def access(self, key):
        s, q, state, store = self.s, self.q, self.state, self.store
        st = state.get(key)
        if st == LIR:
            s.move_to_end(key)
            self._prune()
            return True
        if st == HIR:
            if key in s:
                s.move_to_end(key)
                del q[key]
                state[key] = LIR
                old = next(iter(s))
                state[old] = HIR
                del s[old]
                q[old] = True
                self._prune()
            else:
                s[key] = True
                q.move_to_end(key)
            return True
        # miss
        if len(store) >= self.capacity:
            if q:
                v, _ = q.popitem(last=False)
                del store[v]
                if v in s:
                    state[v] = NR
                    self.nr += 1
                else:
                    del state[v]
        store[key] = True
        if self.nlir < self.lcap:
            if st == NR:
                self.nr -= 1
            state[key] = LIR
            s[key] = True
            s.move_to_end(key)
            self.nlir += 1
            return False
        if st == NR:
            self.nr -= 1
            s.move_to_end(key)
            state[key] = LIR
            old = next(iter(s))
            state[old] = HIR
            del s[old]
            q[old] = True
            self._prune()
        else:
            state[key] = HIR
            s[key] = True
            q[key] = True
        if len(store) > self.capacity:
            v, _ = q.popitem(last=False)
            del store[v]
            if v in s:
                state[v] = NR
                self.nr += 1
            else:
                del state[v]
        self._trim_nr()
        return False


class Cache:
    """LIRS whose sizing follows the best of several shadow LIRS sizings."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.main = Lirs(capacity)
        self.store = self.main.store
        hs = (max(1, capacity // 100), max(1, capacity // 4))
        self.params = [(h, m * capacity) for h in hs for m in (1, 3)]
        self.shadows = []
        for h, nr in self.params:
            sh = Lirs(capacity)
            sh.set_hcap(h)
            sh.nr_max = nr
            self.shadows.append(sh)
        self.score = [0.0] * len(self.params)
        self.n = 0
        self.period = capacity

    def access(self, key):
        sc = self.score
        for i, sh in enumerate(self.shadows):
            if sh.access(key):
                sc[i] += 1
        self.n += 1
        if self.n >= self.period:
            self.n = 0
            best = 0
            for i in range(len(sc)):
                sc[i] *= 0.7
                if sc[i] > sc[best]:
                    best = i
            h, nr = self.params[best]
            m = self.main
            m.nr_max = nr
            m._trim_nr()
            if h != m.hcap:
                m.set_hcap(h)
        return self.main.access(key)
