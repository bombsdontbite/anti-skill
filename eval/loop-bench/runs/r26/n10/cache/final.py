from collections import OrderedDict, deque
class LIRS:
    def __init__(self, capacity):
        self.c=capacity; self.hc=max(1,capacity//100); self.lc=capacity-self.hc
        self.S=OrderedDict(); self.Q=OrderedDict(); self.lir=set(); self.store=set(); self.ev=[]
        self.maxS=capacity*10; self.freq={}; self.n=0; self.reset=10*capacity
    def _prune(self):
        while self.S:
            k=next(iter(self.S))
            if k in self.lir: return
            del self.S[k]
    def access(self, k):
        fr=self.freq; fr[k]=fr.get(k,0)+1; self.n+=1
        if self.n>=self.reset:
            self.n//=2; self.freq=fr={a:b//2 for a,b in fr.items() if b>1}
        S=self.S
        if k in self.lir:
            first=next(iter(S))==k
            S.move_to_end(k)
            if first: self._prune()
            return True
        if k in self.store:  # resident HIR
            if k in S:
                S.move_to_end(k); del self.Q[k]; self.lir.add(k)
                v=next(iter(S)); self.lir.discard(v); del S[v]; self.Q[v]=None; self._prune()
            else:
                S[k]=None; self.Q.move_to_end(k)
            return True
        # miss
        if len(self.lir)<self.lc:
            self.lir.add(k); self.store.add(k); S[k]=None; return False
        if len(self.store)>=self.c:
            if k not in S and self.Q and fr.get(k,0)<=fr.get(next(iter(self.Q)),0):
                S[k]=None
                return False
            v,_=self.Q.popitem(last=False); (self.store.discard(v), self.ev.append(v))
        self.store.add(k)
        if k in S:
            S.move_to_end(k); self.lir.add(k)
            v=next(iter(S)); self.lir.discard(v); del S[v]; self.Q[v]=None; self._prune()
        else:
            S[k]=None; self.Q[k]=None
            if len(S)>self.maxS:
                for x in list(S):
                    if x not in self.lir and x not in self.store:
                        del S[x]
                        if len(S)<=self.maxS*0.8: break
        return False

class ARC:
    def __init__(self, capacity):
        self.c=capacity; self.p=0
        self.t1=OrderedDict(); self.t2=OrderedDict(); self.b1=OrderedDict(); self.b2=OrderedDict()
        self.store={}; self.ev=[]
    def _rep(self, inb2):
        if self.t1 and (len(self.t1)>self.p or (inb2 and len(self.t1)==self.p)):
            k,_=self.t1.popitem(last=False); self.b1[k]=None
        else:
            k,_=self.t2.popitem(last=False); self.b2[k]=None
        del self.store[k]; self.ev.append(k)
    def access(self, x):
        c=self.c
        if x in self.t1:
            del self.t1[x]; self.t2[x]=None; return True
        if x in self.t2:
            self.t2.move_to_end(x); return True
        if x in self.b1:
            self.p=min(c, self.p+max(len(self.b2)//max(len(self.b1),1),1))
            self._rep(False); del self.b1[x]; self.t2[x]=None; self.store[x]=None; return False
        if x in self.b2:
            self.p=max(0, self.p-max(len(self.b1)//max(len(self.b2),1),1))
            self._rep(True); del self.b2[x]; self.t2[x]=None; self.store[x]=None; return False
        l1=len(self.t1)+len(self.b1)
        if l1==c:
            if len(self.t1)<c:
                self.b1.popitem(last=False); self._rep(False)
            else:
                k,_=self.t1.popitem(last=False); del self.store[k]; self.ev.append(k)
        elif l1<c and l1+len(self.t2)+len(self.b2)>=c:
            if l1+len(self.t2)+len(self.b2)==2*c: self.b2.popitem(last=False)
            self._rep(False)
        self.t1[x]=None; self.store[x]=None; return False

class TLFU:
    def __init__(self, capacity):
        self.c=capacity; self.wc=max(1,capacity//100); self.mc=capacity-self.wc
        self.pc=int(self.mc*0.8)
        self.W=OrderedDict(); self.P=OrderedDict(); self.Pr=OrderedDict()
        self.store=set(); self.ev=[]; self.freq={}; self.n=0; self.reset=10*capacity
    def _inc(self,k):
        self.freq[k]=self.freq.get(k,0)+1; self.n+=1
        if self.n>=self.reset:
            self.n//=2; self.freq={a:b//2 for a,b in self.freq.items() if b>1}
    def access(self, k):
        self._inc(k)
        if k in self.W: self.W.move_to_end(k); return True
        if k in self.Pr:
            del self.Pr[k]; self.P[k]=None
            if len(self.P)>self.pc:
                v,_=self.P.popitem(last=False); self.Pr[v]=None
            return True
        if k in self.P: self.P.move_to_end(k); return True
        self.W[k]=None; self.store.add(k)
        if len(self.W)>self.wc:
            cand,_=self.W.popitem(last=False)
            if len(self.P)+len(self.Pr)<self.mc: self.Pr[cand]=None
            else:
                vq=self.Pr if self.Pr else self.P
                vic=next(iter(vq))
                if self.freq.get(cand,0)>self.freq.get(vic,0):
                    del vq[vic]; (self.store.discard(vic), self.ev.append(vic)); self.Pr[cand]=None
                else: (self.store.discard(cand), self.ev.append(cand))
        return False

class S3:
    def __init__(self, capacity):
        self.c=capacity; self.sc=max(1,capacity//10); self.mc=capacity-self.sc
        self.S=deque(); self.M=deque(); self.G=OrderedDict(); self.f={}; self.store=self.f; self.ev=[]
        self.ns=0; self.nm=0
    def _evm(self):
        while True:
            k=self.M.popleft()
            if self.f[k]>0: self.f[k]-=1; self.M.append(k)
            else: del self.f[k]; self.ev.append(k); self.nm-=1; return
    def _evs(self):
        while self.S:
            k=self.S.popleft(); self.ns-=1
            if self.f[k]>0:
                if self.nm>=self.mc: self._evm()
                self.f[k]=0; self.M.append(k); self.nm+=1
                if self.ns+self.nm<self.c: return
            else:
                del self.f[k]; self.ev.append(k); self.G[k]=None
                if len(self.G)>self.mc: self.G.popitem(last=False)
                return
    def access(self, k):
        if k in self.f:
            if self.f[k]<3: self.f[k]+=1
            return True
        while self.ns+self.nm>=self.c:
            if self.ns>0 and (self.ns>=self.sc or self.nm==0): self._evs()
            else: self._evm()
        if k in self.G:
            del self.G[k]
            self.M.append(k); self.nm+=1
        else:
            self.S.append(k); self.ns+=1
        self.f[k]=0; return False

class Cache:
    def __init__(self, capacity):
        self.c=capacity
        self.ex=[LIRS(capacity),ARC(capacity),S3(capacity),LRUx(capacity)]
        self.sc=[0.0]*len(self.ex); self.decay=1-1/(2*capacity)
        self.w=0; self.store={}; self.D=OrderedDict()
    def access(self, k):
        hit=k in self.store
        sc=self.sc; d=self.decay
        for i,e in enumerate(self.ex):
            h=e.access(k)
            sc[i]=sc[i]*d+(1 if h else 0)
        b=0
        for i in range(1,len(sc)):
            if sc[i]>sc[b]: b=i
        if sc[b]>sc[self.w]*1.02 and b!=self.w:
            self.w=b; ws=self.ex[b].store
            self.D=OrderedDict((x,None) for x in self.store if x not in ws)
        for e in self.ex:
            if e is self.ex[self.w]:
                for x in e.ev:
                    if x in self.store: self.D[x]=None
            e.ev.clear()
        ws=self.ex[self.w].store
        if k in ws:
            self.D.pop(k,None)
            if not hit:
                if len(self.store)>=self.c:
                    v=self.D.popitem(last=False)[0] if self.D else next(iter(self.store)); del self.store[v]
                self.store[k]=None
        elif hit:
            self.D[k]=None
        return hit

class LRUx:
    def __init__(self, capacity):
        self.c=capacity; self.store=OrderedDict(); self.ev=[]
    def access(self, k):
        if k in self.store: self.store.move_to_end(k); return True
        if len(self.store)>=self.c:
            v,_=self.store.popitem(last=False); self.ev.append(v)
        self.store[k]=None; return False
