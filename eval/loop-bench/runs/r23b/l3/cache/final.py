from collections import OrderedDict

class Lirs:
    """LIRS."""
    HIR=0.01; SMUL=3
    def __init__(self, capacity):
        self.cap=capacity; self.hcap=max(1,int(capacity*self.HIR)); self.lcap=capacity-self.hcap
        self.S=OrderedDict()  # key -> True if LIR
        self.Q=OrderedDict()  # resident HIR
        self.lir=set(); self.store=set()
    def _prune(self):
        S=self.S
        while S:
            k=next(iter(S))
            if k in self.lir: break
            del S[k]
        if len(S)>self.cap*self.SMUL:
            # drop oldest non-resident HIR entries
            for k in list(S)[:len(S)-self.cap*self.SMUL]:
                if k not in self.lir and k not in self.store: del S[k]
    def _demote(self):
        k,_=self.S.popitem(last=False); self.lir.discard(k); self.Q[k]=1; self._prune()
    def access(self, k):
        S,Q,lir=self.S,self.Q,self.lir
        if k in lir:
            S.move_to_end(k); self._prune(); return True
        if k in self.store:
            if k in S:
                S.move_to_end(k); del Q[k]; lir.add(k); self._demote()
            else:
                S[k]=1; Q.move_to_end(k)
            return True
        if len(lir)<self.lcap:
            lir.add(k); S[k]=1; S.move_to_end(k); self.store.add(k); return False
        if len(self.store)>=self.cap:
            v,_=Q.popitem(last=False); self.store.discard(v)
        self.store.add(k)
        if k in S:
            S.move_to_end(k); lir.add(k); self._demote()
        else:
            S[k]=1; Q[k]=1
        return False

class ALirs:
    """LIRS whose resident-HIR share is hill-climbed on the recent hit rate."""
    SMUL=4.5; SAMPLE=10; STEP=0.05; HMIN=0.01; HMAX=0.9
    def __init__(self, capacity):
        self.cap=capacity; self.hcap=max(1,int(capacity*0.02))
        self.S=OrderedDict(); self.Q=OrderedDict(); self.lir=set(); self.store=set()
        self.samp=capacity*self.SAMPLE; self.n=0; self.h=0; self.prev=-1.0
        self.step=capacity*self.STEP; self.dir=1; self.smax=int(capacity*self.SMUL)
    def _climb(self):
        rate=self.h/self.n
        if rate<self.prev: self.dir=-self.dir
        if abs(rate-self.prev)>0.05: self.step=self.cap*self.STEP
        else: self.step=max(1,self.step*0.98)
        self.prev=rate; self.n=0; self.h=0
        self.hcap=int(min(self.cap*self.HMAX,max(max(1,self.cap*self.HMIN),self.hcap+self.dir*self.step)))
    def _prune(self):
        S=self.S; lir=self.lir
        while S:
            k=next(iter(S))
            if k in lir: break
            del S[k]
        if len(S)>self.smax:
            st=self.store; drop=len(S)-self.smax*2//3
            for k in [k for k in S if k not in lir and k not in st][:drop]: del S[k]
    def _demote(self):
        k,_=self.S.popitem(last=False); self.lir.discard(k); self.Q[k]=1; self._prune()
    def access(self, k):
        S,Q,lir=self.S,self.Q,self.lir
        self.n+=1
        if self.n>=self.samp: self._climb()
        lcap=self.cap-self.hcap
        if k in lir:
            S.move_to_end(k); self._prune(); hit=True
        elif k in self.store:
            hit=True
            if k in S:
                S.move_to_end(k); del Q[k]; lir.add(k)
                if len(lir)>lcap: self._demote()
            else:
                S[k]=1; Q.move_to_end(k)
        else:
            hit=False
            if len(self.store)>=self.cap:
                if not Q: self._demote()
                v,_=Q.popitem(last=False); self.store.discard(v)
            self.store.add(k)
            if k in S or len(lir)<lcap:
                S[k]=1; S.move_to_end(k); lir.add(k)
            else:
                S[k]=1; Q[k]=1
        while len(lir)>lcap: self._demote()
        if hit: self.h+=1
        return hit

class Arc:
    def __init__(self, capacity):
        self.c=capacity; self.p=0
        self.t1=OrderedDict(); self.t2=OrderedDict(); self.b1=OrderedDict(); self.b2=OrderedDict()
        self.store={}
    def _rep(self, inb2):
        if self.t1 and (len(self.t1)>self.p or (inb2 and len(self.t1)==self.p)):
            k,_=self.t1.popitem(last=False); self.b1[k]=1
        else:
            k,_=self.t2.popitem(last=False); self.b2[k]=1
        del self.store[k]
    def access(self, x):
        c=self.c
        if x in self.t1:
            del self.t1[x]; self.t2[x]=1; return True
        if x in self.t2:
            self.t2.move_to_end(x); return True
        if x in self.b1:
            self.p=min(c, self.p+max(len(self.b2)//len(self.b1),1))
            self._rep(False); del self.b1[x]; self.t2[x]=1; self.store[x]=1; return False
        if x in self.b2:
            self.p=max(0, self.p-max(len(self.b1)//len(self.b2),1))
            self._rep(True); del self.b2[x]; self.t2[x]=1; self.store[x]=1; return False
        l1=len(self.t1)+len(self.b1)
        if l1==c:
            if len(self.t1)<c:
                self.b1.popitem(last=False); self._rep(False)
            else:
                k,_=self.t1.popitem(last=False); del self.store[k]
        elif l1<c and l1+len(self.t2)+len(self.b2)>=c:
            if l1+len(self.t2)+len(self.b2)==2*c: self.b2.popitem(last=False)
            self._rep(False)
        self.t1[x]=1; self.store[x]=1; return False

class Tlfu:
    RESET=10
    """W-TinyLFU: small LRU window, SLRU main, frequency sketch admission with aging."""
    WIN=0.01; PROT=0.8
    def __init__(self, capacity):
        self.cap=capacity
        self.wcap=max(1,int(capacity*self.WIN)); self.mcap=capacity-self.wcap
        self.pcap=int(self.mcap*self.PROT)
        self.win=OrderedDict(); self.prob=OrderedDict(); self.prot=OrderedDict()
        self.store=set(); self.freq={}; self.ops=0; self.reset=capacity*self.RESET
    def _inc(self, k):
        f=self.freq; f[k]=f.get(k,0)+1; self.ops+=1
        if self.ops>=self.reset:
            self.ops=0; self.freq={a:b>>1 for a,b in f.items() if b>1}
    def access(self, k):
        self._inc(k)
        if k in self.win:
            self.win.move_to_end(k); return True
        if k in self.prob:
            del self.prob[k]; self.prot[k]=1
            if len(self.prot)>self.pcap:
                v,_=self.prot.popitem(last=False); self.prob[v]=1
            return True
        if k in self.prot:
            self.prot.move_to_end(k); return True
        self.win[k]=1; self.store.add(k)
        if len(self.win)>self.wcap:
            c,_=self.win.popitem(last=False)
            if len(self.prob)+len(self.prot)<self.mcap:
                self.prob[c]=1
            else:
                vq=self.prob if self.prob else self.prot
                v=next(iter(vq))
                f=self.freq
                if f.get(c,0)>f.get(v,0):
                    del vq[v]; self.store.discard(v); self.prob[c]=1
                else:
                    self.store.discard(c)
        return False


class Tlfu40(Tlfu):
    RESET=200
    WIN=0.001

class Cache:
    """Simulates several policies and follows the one with the most recent hits."""
    DECAY=0.9995
    def __init__(self, capacity):
        self.cap=capacity
        self.pol=[Lirs(capacity), Arc(capacity), Tlfu40(capacity)]
        self.score=[0.0]*len(self.pol); self.lead=0
        self.store=OrderedDict()
    def access(self, k):
        sc=self.score; d=self.DECAY
        for i,p in enumerate(self.pol):
            sc[i]=sc[i]*d+(1 if p.access(k) else 0)
        st=self.store
        if k in st:
            st.move_to_end(k); hit=True
        else:
            hit=False
        best=sc.index(max(sc))
        if sc[best]>sc[self.lead]*1.01: self.lead=best
        if not hit:
            ls=self.pol[self.lead].store
            if k in ls:
                if len(st)>=self.cap:
                    for v in st:
                        if v not in ls: break
                    del st[v]
                st[k]=1
        return hit
