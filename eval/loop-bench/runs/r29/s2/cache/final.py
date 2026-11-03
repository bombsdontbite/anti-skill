from collections import OrderedDict


class LIRS:
    """LIRS: keeps keys with short reuse distance; scan- and loop-resistant."""
    def __init__(self, capacity, hfrac=0.01, nrmult=2):
        self.c=capacity; self.hc=max(1,int(capacity*hfrac)); self.lc=capacity-self.hc
        self.S=OrderedDict(); self.Q=OrderedDict(); self.lir=set(); self.nr=OrderedDict()
        self.store=set(); self.nrmax=capacity*nrmult
    def _prune(self):
        S=self.S
        while S:
            k=next(iter(S))
            if k in self.lir: return
            del S[k]; self.nr.pop(k,None)
    def _demote(self):
        k,_=self.S.popitem(last=False); self.lir.discard(k); self.Q[k]=1; self._prune()
    def access(self, x):
        S=self.S; Q=self.Q
        if x in self.lir:
            first=next(iter(S))==x; S.move_to_end(x)
            if first: self._prune()
            return True
        if x in Q:
            if x in S:
                del Q[x]; S.move_to_end(x); self.lir.add(x); self._demote()
            else:
                S[x]=1; Q.move_to_end(x)
            return True
        st=self.store
        if len(self.lir)<self.lc and len(st)<self.c:
            self.lir.add(x); S[x]=1; S.move_to_end(x); st.add(x); self.nr.pop(x,None); return False
        if len(st)>=self.c:
            v,_=Q.popitem(last=False); st.discard(v)
            if v in S:
                self.nr[v]=1
                if len(self.nr)>self.nrmax:
                    o,_=self.nr.popitem(last=False); del S[o]
        st.add(x)
        if x in S:
            del self.nr[x]; S.move_to_end(x); self.lir.add(x); self._demote()
        else:
            S[x]=1; Q[x]=1
        return False

class LRU:
    def __init__(self, capacity):
        self.c=capacity; self.store=OrderedDict()
    def access(self, k):
        s=self.store
        if k in s: s.move_to_end(k); return True
        if len(s)>=self.c: s.popitem(last=False)
        s[k]=True; return False

class Cache:
    """Simulate LRU and LIRS; mirror whichever has more recent (decayed) hits, with hysteresis."""
    def __init__(self, capacity, decay=5000, kinds=(LRU, LIRS), margin=0.05):
        self.m=1+margin
        self.c=capacity; self.sh=[K(capacity) for K in kinds]
        self.sc=[0.0]*len(self.sh); self.lead=1
        self.d=1-1/(decay or capacity*2); self.store=OrderedDict()
    def access(self, k):
        sc=self.sc; d=self.d
        for i,p in enumerate(self.sh):
            sc[i]=sc[i]*d+(1.0 if p.access(k) else 0.0)
        b=self.lead; t=sc[b]*self.m+1e-9
        for i in range(len(sc)):
            if sc[i]>t: b=i; t=sc[i]
        self.lead=b
        s=self.store
        if k in s: s.move_to_end(k); return True
        ls=self.sh[b].store
        if k in ls:
            if len(s)>=self.c:
                for v in s:
                    if v not in ls: break
                del s[v]
            s[k]=True
        return False
