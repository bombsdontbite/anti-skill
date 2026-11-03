from collections import OrderedDict


class _WT:
    """W-TinyLFU with a fixed window size; frequencies come from the owner."""

    def __init__(self, capacity, wcap, owner, fi=0):
        self.fi = fi
        self.capacity = capacity
        self.wcap = wcap
        self.mcap = capacity - wcap
        self.pcap = int(self.mcap * 0.8)
        self.window = OrderedDict(); self.prob = OrderedDict(); self.prot = OrderedDict()
        self.owner = owner
        self.score = 0.0
        self.ev = None

    def __contains__(self, key):
        return key in self.window or key in self.prob or key in self.prot

    def access(self, key):
        if key in self.window:
            self.window.move_to_end(key); return True
        if key in self.prot:
            self.prot.move_to_end(key); return True
        if key in self.prob:
            del self.prob[key]; self.prot[key] = True
            if len(self.prot) > self.pcap:
                k, _ = self.prot.popitem(last=False); self.prob[k] = True
            return True
        self.window[key] = True
        if len(self.window) > self.wcap:
            k, _ = self.window.popitem(last=False)
            if len(self.prob) + len(self.prot) < self.mcap:
                self.prob[k] = True
            else:
                victim = next(iter(self.prob)) if self.prob else next(iter(self.prot))
                f = self.owner.freqs[self.fi]
                if f.get(k, 0) > f.get(victim, 0):
                    if victim in self.prob: del self.prob[victim]
                    else: del self.prot[victim]
                    self.prob[k] = True
                    self.ev = victim
                else:
                    self.ev = k
        return False


class _ARC:
    def __init__(self, c):
        self.c = c; self.p = 0
        self.t1 = OrderedDict(); self.t2 = OrderedDict()
        self.b1 = OrderedDict(); self.b2 = OrderedDict()
        self.score = 0.0
        self.ev = None

    def __contains__(self, key):
        return key in self.t1 or key in self.t2

    def _replace(self, in_b2):
        if self.t1 and (len(self.t1) > self.p or (in_b2 and len(self.t1) == self.p)):
            k, _ = self.t1.popitem(last=False); self.b1[k] = True
        else:
            k, _ = self.t2.popitem(last=False); self.b2[k] = True
        self.ev = k

    def access(self, key):
        c = self.c
        if key in self.t1:
            del self.t1[key]; self.t2[key] = True; return True
        if key in self.t2:
            self.t2.move_to_end(key); return True
        if key in self.b1:
            self.p = min(c, self.p + max(1, len(self.b2) // len(self.b1)))
            self._replace(False); del self.b1[key]; self.t2[key] = True
            return False
        if key in self.b2:
            self.p = max(0, self.p - max(1, len(self.b1) // len(self.b2)))
            self._replace(True); del self.b2[key]; self.t2[key] = True
            return False
        l1 = len(self.t1) + len(self.b1)
        if l1 == c:
            if len(self.t1) < c:
                self.b1.popitem(last=False); self._replace(False)
            else:
                self.ev, _ = self.t1.popitem(last=False)
        elif l1 < c and l1 + len(self.t2) + len(self.b2) >= c:
            if l1 + len(self.t2) + len(self.b2) == 2 * c:
                self.b2.popitem(last=False)
            self._replace(False)
        self.t1[key] = True
        return False


class _S3:
    """S3-FIFO: small probationary FIFO, main FIFO with reinsertion, ghost FIFO."""

    def __init__(self, c, sfrac=0.1):
        self.scap = max(1, int(c * sfrac)); self.mcap = c - self.scap
        self.small = OrderedDict(); self.main = OrderedDict(); self.ghost = OrderedDict()
        self.cnt = {}
        self.score = 0.0
        self.ev = None

    def __contains__(self, key):
        return key in self.cnt

    def _evict_main(self):
        main = self.main; cnt = self.cnt
        while True:
            k, _ = main.popitem(last=False)
            v = cnt[k]
            if v > 0:
                cnt[k] = v - 1; main[k] = True
            else:
                del cnt[k]; self.ev = k
                return

    def access(self, key):
        cnt = self.cnt
        if key in cnt:
            if cnt[key] < 3:
                cnt[key] += 1
            return True
        if len(self.small) >= self.scap:
            k, _ = self.small.popitem(last=False)
            if cnt[k] > 0:
                cnt[k] = 0; self.main[k] = True
                if len(self.main) > self.mcap:
                    self._evict_main()
            else:
                del cnt[k]; self.ev = k
                self.ghost[k] = True
                if len(self.ghost) > self.mcap:
                    self.ghost.popitem(last=False)
        if key in self.ghost:
            del self.ghost[key]
            self.main[key] = True; cnt[key] = 0
            if len(self.main) > self.mcap:
                self._evict_main()
        else:
            self.small[key] = True; cnt[key] = 0
        return False


class _LIRS:
    def __init__(self, c, hfrac=0.01):
        self.hcap = max(1, int(c * hfrac)); self.lcap = c - self.hcap
        self.S = OrderedDict(); self.Q = OrderedDict()
        self.st = {}
        self.nlir = 0
        self.score = 0.0
        self.ev = None

    def __contains__(self, key):
        st = self.st.get(key)
        return st == 1 or st == 2

    def _prune(self):
        S = self.S; st = self.st
        while S:
            k = next(iter(S))
            v = st[k]
            if v == 1:
                return
            del S[k]
            if v == 3:
                del st[k]

    def _demote(self):
        k, _ = self.S.popitem(last=False)
        self.st[k] = 2; self.Q[k] = True
        self.nlir -= 1
        self._prune()

    def access(self, key):
        S = self.S; st = self.st; Q = self.Q
        v = st.get(key)
        if v == 1:
            S[key] = True; S.move_to_end(key)
            self._prune()
            return True
        if v == 2:
            if key in S:
                S.move_to_end(key); del Q[key]; st[key] = 1; self.nlir += 1
                self._demote()
            else:
                S[key] = True; Q.move_to_end(key)
            return True
        if self.nlir < self.lcap and not Q:
            st[key] = 1; S[key] = True; self.nlir += 1
            return False
        if len(Q) >= self.hcap:
            k, _ = Q.popitem(last=False)
            self.ev = k
            if k in S:
                st[k] = 3
            else:
                del st[k]
        if v == 3:
            S.move_to_end(key); st[key] = 1; self.nlir += 1
            self._demote()
        else:
            st[key] = 2; S[key] = True; Q[key] = True
        if len(S) > 4 * (self.lcap + self.hcap):
            for k in S:
                if st[k] == 3:
                    del S[k]; del st[k]
                    break
        return False


class Cache:
    """Follow the leader: simulate several policies, cache what the recent best one caches."""

    RESETS = (10, 3, 30, 1, 100)
    CONFIGS = ((0.01, 0), (0.2, 0), (0.5, 0), (0.99, 0), (0.01, 1),
               (0.01, 2), (0.05, 2), (0.01, 3), (0.2, 3), (0.01, 4))

    def __init__(self, capacity, decay=0.9995, arc=True):
        self.capacity = capacity
        self.freqs = [{} for _ in self.RESETS]
        self.ops = [0] * len(self.RESETS)
        self.reset_at = [capacity * r for r in self.RESETS]
        self.decay = decay
        w = lambda f: max(1, min(capacity - 1, int(capacity * f)))
        self.shadows = [_WT(capacity, w(f), self, i) for f, i in self.CONFIGS]
        if arc:
            self.shadows.append(_ARC(capacity))
            self.shadows.append(_S3(capacity))
            self.shadows.append(_LIRS(capacity))
        self.best = self.shadows[0]
        self.store = OrderedDict()
        self.stale = []

    def access(self, key):
        freqs = self.freqs
        for i in range(len(freqs)):
            f = freqs[i]
            f[key] = f.get(key, 0) + 1
            self.ops[i] += 1
            if self.ops[i] >= self.reset_at[i]:
                self.ops[i] = 0
                freqs[i] = {k: v >> 1 for k, v in f.items() if v > 1}
        d = self.decay
        best = self.best
        for s in self.shadows:
            s.ev = None
            s.score = s.score * d + s.access(key)
            if s.score > best.score + 6:
                best = s
        self.best = best
        store = self.store
        if best.ev is not None and best.ev in store:
            self.stale.append(best.ev)
        if key in store:
            store.move_to_end(key)
            return True
        if key in best or len(store) < self.capacity:
            store[key] = True
            if len(store) > self.capacity:
                stale = self.stale
                k = None
                while stale:
                    k = stale.pop()
                    if k != key and k in store and k not in best:
                        break
                    k = None
                if k is None:
                    n = 0
                    for k in store:
                        n += 1
                        if n > 300 or k not in best:
                            break
                del store[k]
        return False
