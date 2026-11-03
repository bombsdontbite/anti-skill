import random
from collections import OrderedDict, deque


class LRU:
    def __init__(self, cap):
        self.cap=cap; self.store=OrderedDict(); self.ev=deque(maxlen=64)
    def access(self, key):
        s=self.store
        if key in s:
            s.move_to_end(key); return True
        if len(s)>=self.cap:
            k,_=s.popitem(last=False); self.ev.append(k)
        s[key]=1; return False


class LIRS:
    def __init__(self, cap, hir=0.01, hist=4):
        self.cap=cap; self.hist=hist
        self.hcap=max(1,int(cap*hir)); self.lcap=cap-self.hcap
        self.S=OrderedDict(); self.Q=OrderedDict(); self.lir=set(); self.store=set()
        self.ev=deque(maxlen=64)
    def _prune(self):
        S=self.S; lir=self.lir
        while S:
            k=next(iter(S))
            if k in lir: return
            del S[k]
    def _demote_bottom(self):
        k,_=self.S.popitem(last=False)
        self.lir.discard(k); self.Q[k]=1
        self._prune()
    def access(self, key):
        S=self.S
        if key in self.lir:
            bottom=next(iter(S))==key
            S.move_to_end(key)
            if bottom: self._prune()
            return True
        if key in self.Q:
            if key in S:
                del self.Q[key]; S.move_to_end(key); self.lir.add(key)
                self._demote_bottom()
            else:
                S[key]=1; self.Q.move_to_end(key)
            return True
        if len(self.store)>=self.cap:
            k,_=self.Q.popitem(last=False); self.store.discard(k); self.ev.append(k)
        self.store.add(key)
        if len(self.lir)<self.lcap:
            self.lir.add(key); S[key]=1; S.move_to_end(key); return False
        if key in S:
            S.move_to_end(key); self.lir.add(key); self._demote_bottom()
        else:
            S[key]=1; self.Q[key]=1
            if len(S)>self.hist*self.cap:
                for k in list(S)[:self.cap]:
                    if k not in self.lir and k not in self.Q: del S[k]
        return False


class RD:
    """Evict the sampled key whose next use is predicted farthest away."""
    K=24; NEW=8.0; BYPASS=True
    def __init__(self, capacity):
        self.cap=capacity; self.store={}; self.keys=[]; self.pos={}
        self.last={}; self.gap={}; self.t=0; self.rng=random.Random(1)
        self.newg=capacity*self.NEW; self.ev=deque(maxlen=64)
    def _rem(self, k):
        age=self.t-self.last[k]; g=self.gap.get(k,self.newg)
        return g-age if age<g else age
    def access(self, key):
        self.t+=1; t=self.t; last=self.last
        if key in last:
            g=t-last[key]; og=self.gap.get(key)
            self.gap[key]=g if og is None else (og+g)/2
        last[key]=t
        if key in self.store: return True
        if len(self.keys)>=self.cap:
            ks=self.keys; rem=self._rem; ri=self.rng.randrange; n=len(ks)
            v=None; vr=-1
            for _ in range(self.K):
                k=ks[ri(n)]; r=rem(k)
                if r>vr: vr=r; v=k
            if self.BYPASS and rem(key)>vr: return False
            i=self.pos.pop(v); lk=ks.pop()
            if lk!=v: ks[i]=lk; self.pos[lk]=i
            del self.store[v]; self.ev.append(v)
        self.pos[key]=len(self.keys); self.keys.append(key); self.store[key]=1
        return False


class TLFU:
    """W-TinyLFU: window LRU + SLRU main, frequency-sketch admission with aging."""
    WIN=0.01
    def __init__(self, capacity):
        self.cap=capacity
        self.wcap=max(1,int(capacity*self.WIN)); mcap=capacity-self.wcap
        self.pcap=int(mcap*0.8)
        self.win=OrderedDict(); self.prob=OrderedDict(); self.prot=OrderedDict()
        self.freq={}; self.ops=0; self.reset=capacity*100
        self.store=set(); self.ev=deque(maxlen=64)
    def _inc(self,k):
        f=self.freq; f[k]=f.get(k,0)+1; self.ops+=1
        if self.ops>=self.reset:
            self.ops=0; self.freq={a:b>>1 for a,b in f.items() if b>1}
    def access(self, key):
        self._inc(key)
        if key in self.win:
            self.win.move_to_end(key); return True
        if key in self.prot:
            self.prot.move_to_end(key); return True
        if key in self.prob:
            del self.prob[key]; self.prot[key]=1
            if len(self.prot)>self.pcap:
                k,_=self.prot.popitem(last=False); self.prob[k]=1
            return True
        self.win[key]=1; self.store.add(key)
        if len(self.win)>self.wcap:
            cand,_=self.win.popitem(last=False)
            if len(self.prob)+len(self.prot)<self.cap-self.wcap:
                self.prob[cand]=1
            else:
                vq=self.prob if self.prob else self.prot
                victim=next(iter(vq))
                if self.freq.get(cand,0)>self.freq.get(victim,0):
                    del vq[victim]; self.store.discard(victim); self.ev.append(victim); self.prob[cand]=1
                else:
                    self.store.discard(cand); self.ev.append(cand)
        return False


class Cache:
    """Runs shadow policies and evicts like whichever has hit most recently."""
    DECAY=0.999
    def __init__(self, capacity):
        self.cap=capacity
        self.sh=[LIRS(capacity), LRU(capacity), LIRS(capacity, 0.2), RD(capacity), TLFU(capacity)]
        self.sc=[0.0]*len(self.sh); self.best=0
        self.store=OrderedDict()
        self.d=1-1.0/(capacity*DECAYK)
    def access(self, key):
        sc=self.sc; d=self.d
        for i,p in enumerate(self.sh):
            sc[i]=sc[i]*d+(1 if p.access(key) else 0)
        b=self.best
        m=0
        for i in range(1,len(sc)):
            if sc[i]>sc[m]: m=i
        if sc[m]>sc[b]*1.0+3: self.best=b=m
        s=self.store
        if key in s:
            s.move_to_end(key); return True
        best=self.sh[b]; bs=best.store
        if key not in bs: return False
        if len(s)>=self.cap:
            v=None
            ev=best.ev
            for k in reversed(ev):
                if k in s and k not in bs: v=k; break
            if v is None:
                n=0
                for k in s:
                    if k not in bs: v=k; break
                    n+=1
                    if n>64: break
            if v is None: v=next(iter(s))
            del s[v]
        s[key]=1
        return False
DECAYK=30
