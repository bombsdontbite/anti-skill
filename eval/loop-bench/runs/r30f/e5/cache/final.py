from collections import OrderedDict


class Cache:
    """Adaptive LIRS. The HIR queue grows when a plain LRU of the same size (shadow of the last
    `capacity` distinct keys) would have hit a miss, and shrinks when a key demoted from the LIR
    set and evicted is requested again (ghost), or slowly when HIR slots go unused."""

    STEP_UP = 1
    STEP_DOWN = 25
    DECAY_EVERY = 8

    def __init__(self, capacity):
        self.capacity = capacity
        self.hmin = max(1, capacity // 100)
        self.hmax = max(self.hmin, capacity // 2)
        self.hirs = self.hmin
        self.S = OrderedDict()
        self.Q = OrderedDict()   # key -> 2 demoted from LIR, 1 hit while in Q, 0 fresh
        self.shadow = OrderedDict()
        self.dg = OrderedDict()  # demoted-then-evicted ghost
        self.lir = set()
        self.store = {}
        self.unused = 0

    def _prune(self):
        S = self.S; lir = self.lir
        while S:
            k = next(iter(S))
            if k in lir: break
            del S[k]

    def _demote_lir(self):
        k = next(iter(self.S))
        del self.S[k]; self.lir.discard(k)
        self.Q[k] = 2
        self._prune()

    def _evict(self):
        if not self.Q:
            self._demote_lir()
        v, st = self.Q.popitem(last=False)
        del self.store[v]
        if st == 2:
            self.dg[v] = True
            if len(self.dg) > 2 * self.capacity:
                self.dg.popitem(last=False)
        elif st == 0:
            self.unused += 1
            if self.unused >= self.DECAY_EVERY:
                self.unused = 0
                self.hirs = max(self.hmin, self.hirs - 1)

    def access(self, key):
        sh = self.shadow
        if key in sh:
            sh.move_to_end(key); in_sh = True
        else:
            sh[key] = True; in_sh = False
            if len(sh) > self.capacity:
                sh.popitem(last=False)
        if key in self.lir:
            self.S.move_to_end(key); self._prune(); return True
        if key in self.store:
            if key in self.S:
                self.S.move_to_end(key); del self.Q[key]; self.lir.add(key)
                if len(self.lir) > self.capacity - self.hirs:
                    self._demote_lir()
            else:
                self.Q.move_to_end(key); self.Q[key] = 1; self.S[key] = True
            return True
        # miss
        if key in self.dg:
            del self.dg[key]
            self.hirs = max(self.hmin, self.hirs - self.STEP_DOWN)
        elif in_sh:
            self.hirs = min(self.hmax, self.hirs + self.STEP_UP)
        lirs = self.capacity - self.hirs
        while len(self.lir) > lirs:
            self._demote_lir()
        if len(self.store) >= self.capacity:
            self._evict()
        self.store[key] = True
        if key in self.S:
            self.S.move_to_end(key); self.lir.add(key)
            if len(self.lir) > lirs:
                self._demote_lir()
        elif len(self.lir) < lirs:
            self.S[key] = True; self.lir.add(key)
        else:
            self.S[key] = True; self.Q[key] = 0
        while len(self.S) > self.capacity * 3:
            k = next(iter(self.S))
            if k in self.lir: break
            del self.S[k]
        return False
