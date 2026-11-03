from collections import OrderedDict

HFRAC = 0.02
SMUL = 5.0
MARGIN = 2.0


class Cache:
    """LIRS with a bounded recency stack and a stale-bottom promotion rule.

    A non-resident key in the stack is promoted to LIR only when the oldest LIR key has gone
    unused for more than MARGIN times the candidate's own reuse gap; this keeps a fixed LIR set
    through loops longer than the cache instead of churning it."""

    def __init__(self, capacity):
        self.c = capacity
        self.hmax = max(1, int(capacity * HFRAC))
        self.lmax = capacity - self.hmax
        self.lir = {}
        self.hir_res = OrderedDict()
        self.s = OrderedDict()
        self.last = {}
        self.store = {}
        self.smax = int(capacity * SMUL)
        self.nonres = 0
        self.now = 0

    def _prune_iter(self):
        s, lir, store, last = self.s, self.lir, self.store, self.last
        drop = []
        for k in s:
            if k in lir:
                break
            drop.append(k)
        for k in drop:
            del s[k]
            del last[k]
            if k not in store:
                self.nonres -= 1

    def _demote_lir(self):
        s, lir = self.s, self.lir
        k = next(iter(s))
        del s[k]
        del self.last[k]
        del lir[k]
        self.hir_res[k] = True
        self._prune_iter()

    def access(self, key):
        s, lir, hir_res, store, last = self.s, self.lir, self.hir_res, self.store, self.last
        self.now += 1
        now = self.now
        if key in lir:
            if next(iter(s)) == key:
                s.move_to_end(key)
                last[key] = now
                self._prune_iter()
            else:
                s.move_to_end(key)
                last[key] = now
            return True
        if key in hir_res:
            if key in s:
                s.move_to_end(key)
                last[key] = now
                del hir_res[key]
                lir[key] = True
                if len(lir) > self.lmax:
                    self._demote_lir()
            else:
                s[key] = True
                last[key] = now
                hir_res.move_to_end(key)
            return True
        # miss
        if len(lir) < self.lmax and not hir_res:
            lir[key] = True
            s[key] = True
            last[key] = now
            store[key] = True
            return False
        if len(store) >= self.c:
            if not hir_res:
                self._demote_lir()
            k, _ = hir_res.popitem(last=False)
            del store[k]
            if k in s:
                self.nonres += 1
        store[key] = True
        if key in s:
            self.nonres -= 1
            gap = now - last[key]
            bottom = next(iter(s))
            s.move_to_end(key)
            last[key] = now
            if now - last[bottom] > MARGIN * gap:
                lir[key] = True
                if len(lir) > self.lmax:
                    self._demote_lir()
            else:
                hir_res[key] = True
        else:
            s[key] = True
            last[key] = now
            hir_res[key] = True
        if self.nonres > self.smax:
            target = self.smax // 2
            drop = []
            for k in s:
                if k not in store:
                    drop.append(k)
                    if self.nonres - len(drop) <= target:
                        break
            for k in drop:
                del s[k]
                del last[k]
            self.nonres -= len(drop)
            self._prune_iter()
        return False
