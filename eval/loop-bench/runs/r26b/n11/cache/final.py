import heapq
from collections import OrderedDict, deque
LIR, HIR, NR = 0, 1, 2

class LogSet(set):
    def discard(self, k):
        if k in self:
            set.remove(self, k); self.log.append(k)

class Lru:
    def __init__(self, capacity):
        self.c=capacity; self.od=OrderedDict(); self.store=set()
    def access(self, k):
        if k in self.od: self.od.move_to_end(k); return True
        if len(self.od)>=self.c:
            v,_=self.od.popitem(last=False); self.store.discard(v)
        self.od[k]=1; self.store.add(k); return False
class Lirs:
    """LIRS."""
    HIRF=0.01; NRMAX=2.0
    def __init__(self, capacity):
        self.c=capacity; self.hc=max(1,int(capacity*self.HIRF)); self.lc=capacity-self.hc
        self.S=OrderedDict(); self.Q=OrderedDict(); self.st={}; self.nlir=0
        self.store=set(); self.nr=OrderedDict(); self.nrmax=int(capacity*self.NRMAX)
    def _prune(self):
        S=self.S; st=self.st
        while S:
            k=next(iter(S))
            s=st[k]
            if s==LIR: return
            del S[k]
            if s==NR: del st[k]; del self.nr[k]
    def _demote_bottom(self):
        S=self.S; k,_=S.popitem(last=False)
        self.st[k]=HIR; self.Q[k]=1; self.nlir-=1
        self._prune()
    def access(self,k):
        st=self.st; S=self.S; s=st.get(k)
        if s==LIR:
            S.move_to_end(k); self._prune(); return True
        if s==HIR:
            if k in S:
                S.move_to_end(k); del self.Q[k]; st[k]=LIR; self.nlir+=1
                self._demote_bottom()
            else:
                S[k]=1; self.Q.move_to_end(k)
            return True
        if len(self.store)>=self.c:
            v,_=self.Q.popitem(last=False); self.store.discard(v)
            if v in S: st[v]=NR; self.nr[v]=1
            else: del st[v]
            while len(self.nr)>self.nrmax:
                x,_=self.nr.popitem(last=False); del S[x]; del st[x]
        self.store.add(k); s=st.get(k)
        if self.nlir<self.lc:
            if s==NR: del self.nr[k]
            st[k]=LIR; self.nlir+=1; S[k]=1; S.move_to_end(k); return False
        if s==NR:
            del self.nr[k]; st[k]=LIR; self.nlir+=1; S.move_to_end(k)
            self._demote_bottom()
        else:
            st[k]=HIR; S[k]=1; self.Q[k]=1
        return False

class Lfu:
    """LFU over all-history counts with periodic halving; bypass if not more frequent than the min."""
    AGE=200
    def __init__(self, capacity):
        self.c=capacity; self.store=set(); self.f={}; self.h=[]; self.n=0; self.t=0
    def access(self, k):
        f=self.f; c=f.get(k,0)+1; f[k]=c; self.n+=1; self.t+=1
        st=self.store
        if self.n>=self.c*self.AGE:
            self.n=0; self.f=f={a:b>>1 for a,b in f.items() if b>1}
            self.h=[(f.get(x,0),x) for x in st]; heapq.heapify(self.h)
        h=self.h
        if k in st:
            heapq.heappush(h,(c,k)); return True
        if len(st)>=self.c:
            while True:
                fc,v=h[0]
                if v in st and f.get(v,0)==fc: break
                heapq.heappop(h)
                if v in st: heapq.heappush(h,(f.get(v,0),v))
            if c<=fc: return False
            heapq.heappop(h); st.discard(v)
        st.add(k); heapq.heappush(h,(c,k)); return False


class Cache:
    """Follow the shadow policy with the most recent hits."""
    POLICIES=(Lirs, Lru, Lfu); DECAY=10.0; MARGIN=1.02
    def __init__(self, capacity):
        self.c=capacity; self.store=set()
        self.sh=[]
        for P in self.POLICIES:
            p=P(capacity); s=LogSet(); s.log=deque(maxlen=4*capacity); p.store=s; self.sh.append(p)
        self.sc=[0.0]*len(self.sh); self.d=1-1/(capacity*self.DECAY); self.lead=0
    def access(self, k):
        sc=self.sc; d=self.d
        for i,p in enumerate(self.sh):
            sc[i]=sc[i]*d+p.access(k)
        best=self.lead
        for i in range(len(sc)):
            if sc[i]>sc[best]*self.MARGIN: best=i
        self.lead=best
        st=self.store
        if k in st: return True
        if len(st)>=self.c:
            L=self.sh[best]; ls=L.store; log=ls.log; v=None
            while log:
                x=log.popleft()
                if x in st and x not in ls: v=x; break
            if v is None:
                for x in st:
                    if x not in ls: v=x; break
                else: v=next(iter(st))
            st.discard(v)
        st.add(k); return False
