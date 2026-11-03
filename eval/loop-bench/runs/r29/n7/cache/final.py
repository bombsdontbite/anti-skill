from collections import OrderedDict, deque

class LRU:
    def __init__(self, capacity):
        self.capacity=capacity; self.store=OrderedDict(); self.ev=[]
    def access(self, key):
        if key in self.store:
            self.store.move_to_end(key); return True
        if len(self.store)>=self.capacity: self.ev.append(self.store.popitem(last=False)[0])
        self.store[key]=True; return False

class ARC:
    def __init__(self, capacity):
        self.c=capacity; self.p=0
        self.t1=OrderedDict(); self.t2=OrderedDict(); self.b1=OrderedDict(); self.b2=OrderedDict()
        self.store=EvSet(); self.ev=self.store.ev
    def _rep(self, inb2):
        if self.t1 and (len(self.t1)>self.p or (inb2 and len(self.t1)==self.p)):
            k,_=self.t1.popitem(last=False); self.b1[k]=1
        else:
            k,_=self.t2.popitem(last=False); self.b2[k]=1
        self.store.discard(k)
    def access(self, x):
        c=self.c
        if x in self.t1:
            del self.t1[x]; self.t2[x]=1; return True
        if x in self.t2:
            self.t2.move_to_end(x); return True
        if x in self.b1:
            self.p=min(c,self.p+max(1,len(self.b2)//len(self.b1)))
            self._rep(False); del self.b1[x]; self.t2[x]=1; self.store.add(x); return False
        if x in self.b2:
            self.p=max(0,self.p-max(1,len(self.b1)//len(self.b2)))
            self._rep(True); del self.b2[x]; self.t2[x]=1; self.store.add(x); return False
        l1=len(self.t1)+len(self.b1)
        if l1==c:
            if len(self.t1)<c:
                self.b1.popitem(last=False); self._rep(False)
            else:
                k,_=self.t1.popitem(last=False); self.store.discard(k)
        else:
            tot=l1+len(self.t2)+len(self.b2)
            if tot>=c:
                if tot==2*c: self.b2.popitem(last=False)
                self._rep(False)
        self.t1[x]=1; self.store.add(x); return False

class TLFU:
    """W-TinyLFU: small LRU window, SLRU main, frequency-sketch admission."""
    def __init__(self, capacity, win=0.01, reset=10):
        self.cap=capacity
        self.wcap=max(1,int(capacity*win))
        self.mcap=capacity-self.wcap
        self.pcap=int(self.mcap*0.8)
        self.win=OrderedDict(); self.prob=OrderedDict(); self.prot=OrderedDict()
        self.store=EvSet(); self.ev=self.store.ev
        self.freq={}; self.ops=0; self.reset=capacity*reset
    def _inc(self,k):
        f=self.freq; v=f.get(k,0)
        if v<15: f[k]=v+1
        self.ops+=1
        if self.ops>=self.reset:
            self.ops=0
            self.freq={a:b>>1 for a,b in f.items() if b>1}
    def access(self, k):
        self._inc(k)
        if k in self.win:
            self.win.move_to_end(k); return True
        if k in self.prot:
            self.prot.move_to_end(k); return True
        if k in self.prob:
            del self.prob[k]; self.prot[k]=1
            if len(self.prot)>self.pcap:
                d,_=self.prot.popitem(last=False); self.prob[d]=1
            return True
        self.win[k]=1; self.store.add(k)
        if len(self.win)>self.wcap:
            cand,_=self.win.popitem(last=False)
            if len(self.prob)+len(self.prot)<self.mcap:
                self.prob[cand]=1
            else:
                if self.prob:
                    vic=next(iter(self.prob)); src=self.prob
                else:
                    vic=next(iter(self.prot)); src=self.prot
                f=self.freq
                if f.get(cand,0)>f.get(vic,0):
                    del src[vic]; self.store.discard(vic); self.prob[cand]=1
                else:
                    self.store.discard(cand)
        return False

class S3:
    """S3-FIFO."""
    def __init__(self, capacity):
        self.cap=capacity; self.scap=max(1,capacity//10)
        self.S=deque(); self.M=deque(); self.G=deque(); self.gset=set()
        self.freq={}; self.store=EvSet(); self.ev=self.store.ev; self.ins=set(); self.inm=set()
    def _evm(self):
        while True:
            k=self.M.popleft(); f=self.freq[k]
            if f>0: self.freq[k]=f-1; self.M.append(k)
            else:
                self.inm.discard(k); self.store.discard(k); del self.freq[k]; return
    def _evs(self):
        while self.S:
            k=self.S.popleft(); self.ins.discard(k)
            if self.freq[k]>0:
                self.freq[k]=0; self.M.append(k); self.inm.add(k)
                continue
            else:
                self.store.discard(k); del self.freq[k]
                self.G.append(k); self.gset.add(k)
                if len(self.G)>self.cap-self.scap:
                    g=self.G.popleft(); self.gset.discard(g)
                return
    def access(self, k):
        if k in self.store:
            if self.freq[k]<3: self.freq[k]+=1
            return True
        n=len(self.store)
        while len(self.store)>=self.cap:
            if self.S and (len(self.ins)>=self.scap or not self.inm):
                self._evs()
                if len(self.store)<n: break
            self._evm() if len(self.store)>=self.cap else None
        self.store.add(k); self.freq[k]=0
        if k in self.gset:
            self.M.append(k); self.inm.add(k)
        else:
            self.S.append(k); self.ins.add(k)
        return False

class EvSet(set):
    def __init__(self):
        set.__init__(self); self.ev=[]
    def discard(self, x):
        if x in self:
            set.discard(self, x); self.ev.append(x)

class LIRS:
    def __init__(self, capacity):
        self.cap=capacity; self.hcap=max(1,capacity//100); self.lcap=capacity-self.hcap
        self.S=OrderedDict(); self.Q=OrderedDict(); self.lir=set()
        self.store=EvSet(); self.ev=self.store.ev
    def _prune(self):
        S=self.S
        while S:
            k=next(iter(S))
            if k in self.lir: return
            del S[k]
    def _demote(self):
        k,_=self.S.popitem(last=False); self.lir.discard(k); self.Q[k]=1; self._prune()
    def access(self, x):
        S=self.S
        if x in self.lir:
            S.move_to_end(x); self._prune(); return True
        if x in self.store:
            if x in S:
                S.move_to_end(x); del self.Q[x]; self.lir.add(x); self._demote()
            else:
                S[x]=1; self.Q.move_to_end(x)
            return True
        if len(self.store)>=self.cap:
            k,_=self.Q.popitem(last=False); self.store.discard(k)
        self.store.add(x)
        if len(self.lir)<self.lcap:
            self.lir.add(x); S[x]=1; S.move_to_end(x)
        elif x in S:
            S.move_to_end(x); self.lir.add(x); self._demote()
        else:
            S[x]=1; self.Q[x]=1
        return False

class Cache:
    """Runs several policies in shadow and imitates whichever has hit most lately."""
    DECAY=4
    MARGIN=2.0
    def __init__(self, capacity):
        self.cap=capacity
        self.pols=[LRU(capacity), ARC(capacity), TLFU(capacity), S3(capacity), LIRS(capacity)]
        self.sc=[0.0]*len(self.pols)
        self.d=1-1/(self.DECAY*capacity)
        self.store=OrderedDict()
        self.lead=0; self.D=set()
    def access(self, k):
        d=self.d; sc=self.sc; pols=self.pols
        for i in range(len(pols)):
            p=pols[i]; p.ev.clear()
            sc[i]=sc[i]*d+(1 if p.access(k) else 0)
        b=self.lead
        for i in range(len(sc)):
            if sc[i]>sc[self.lead]*1.1+self.MARGIN and sc[i]>sc[b]: b=i
        R=self.store
        L=pols[b].store
        if b!=self.lead:
            self.lead=b; self.D={x for x in R if x not in L}
        else:
            D=self.D
            for x in pols[b].ev:
                if x in R: D.add(x)
        if k in R:
            R.move_to_end(k); return True
        if k not in L: return False
        if len(R)>=self.cap:
            D=self.D; vic=None
            while D:
                x=D.pop()
                if x not in L and x in R: vic=x; break
            if vic is None: vic=next(iter(R))
            del R[vic]
        R[k]=True
        return False
