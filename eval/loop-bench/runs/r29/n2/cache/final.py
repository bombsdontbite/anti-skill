from collections import OrderedDict, deque

class LIRS:
    """LIRS: stack S with LIR/HIR status, resident-HIR queue Q, non-resident HIR ghosts."""
    def __init__(self, capacity, HIR=0.01, G=3):
        self.c=capacity; self.hc=max(1,int(capacity*HIR)); self.lc=capacity-self.hc
        self.G=G; self.S=OrderedDict(); self.Q=OrderedDict(); self.lir=set(); self.store=set(); self.ev=[]
    def _prune(self):
        S=self.S
        while S:
            k=next(iter(S))
            if k in self.lir: break
            del S[k]
    def access(self, key):
        S=self.S; Q=self.Q; lir=self.lir
        if key in lir:
            S.move_to_end(key); self._prune(); return True
        hit = key in self.store
        if hit:
            if key in S:
                del Q[key]; lir.add(key); S.move_to_end(key)
                k,_=S.popitem(last=False); lir.discard(k); Q[k]=1; self._prune()
            else:
                Q.move_to_end(key); S[key]=1
            return True
        # miss
        if len(lir)<self.lc:
            lir.add(key); S[key]=1; self.store.add(key); return False
        if len(self.store)>=self.c:
            k,_=Q.popitem(last=False); self._ev(k)
        self.store.add(key)
        if key in S:
            lir.add(key); S.move_to_end(key)
            k,_=S.popitem(last=False); lir.discard(k); Q[k]=1; self._prune()
        else:
            S[key]=1; Q[key]=1
        if len(S)>self.G*self.c:
            # bound ghost memory: drop oldest non-resident HIR entries
            for k in list(S):
                if len(S)<=(self.G-1)*self.c: break
                if k not in lir and k not in self.store: del S[k]
        return False
    def _ev(self, k):
        self.store.discard(k); self.ev.append(k)

class TLFU:
    """W-TinyLFU: small LRU window, SLRU main, frequency-sketch admission with aging."""
    def __init__(self, capacity, W=0.01, R=10):
        self.c=capacity; self.wc=max(1,int(capacity*W)); self.mc=capacity-self.wc
        self.pc=int(self.mc*0.8)
        self.win=OrderedDict(); self.prob=OrderedDict(); self.prot=OrderedDict()
        self.f={}; self.n=0; self.reset=R*capacity
        self.store=set(); self.ev=[]
    def _inc(self,k):
        f=self.f; f[k]=f.get(k,0)+1; self.n+=1
        if self.n>=self.reset:
            self.n//=2
            self.f={a:b>>1 for a,b in f.items() if b>1}
    def access(self, key):
        self._inc(key)
        if key in self.win: self.win.move_to_end(key); return True
        if key in self.prob:
            del self.prob[key]; self.prot[key]=1
            if len(self.prot)>self.pc:
                k,_=self.prot.popitem(last=False); self.prob[k]=1
            return True
        if key in self.prot: self.prot.move_to_end(key); return True
        self.store.add(key); self.win[key]=1
        if len(self.win)>self.wc:
            k,_=self.win.popitem(last=False)
            if len(self.prob)+len(self.prot)<self.mc: self.prob[k]=1
            else:
                vq=self.prob if self.prob else self.prot
                v=next(iter(vq)); f=self.f
                if f.get(k,0)>f.get(v,0):
                    del vq[v]; self._ev(v); self.prob[k]=1
                else: self._ev(k)
        return False
    def _ev(self, k):
        self.store.discard(k); self.ev.append(k)

class S3:
    """S3-FIFO."""
    def __init__(self, capacity, SF=0.1):
        self.c=capacity; self.sc=max(1,int(capacity*SF)); self.mc=capacity-self.sc
        self.S=deque(); self.M=deque(); self.G=OrderedDict(); self.fr={}; self.inS=set()
        self.store=set(); self.ev=[]
    def _evS(self):
        while self.S:
            k=self.S.popleft(); self.inS.discard(k)
            if self.fr[k]>0:
                self.M.append(k); self.fr[k]=0
                if len(self.M)>self.mc: self._evM()
            else:
                del self.fr[k]; self._ev(k); self.G[k]=1
                if len(self.G)>self.mc: self.G.popitem(last=False)
                return
    def _evM(self):
        while self.M:
            k=self.M.popleft()
            if self.fr[k]>0: self.fr[k]-=1; self.M.append(k)
            else: del self.fr[k]; self._ev(k); return
    def access(self, key):
        if key in self.fr:
            if self.fr[key]<3: self.fr[key]+=1
            return True
        if len(self.store)>=self.c:
            if len(self.S)>=self.sc or not self.M: self._evS()
            else: self._evM()
        self.store.add(key); self.fr[key]=0
        if key in self.G:
            del self.G[key]; self.M.append(key)
        else: self.S.append(key); self.inS.add(key)
        return False
    def _ev(self, k):
        self.store.discard(k); self.ev.append(k)

class ARC:
    def __init__(self, capacity):
        self.c=capacity; self.p=0
        self.t1=OrderedDict(); self.t2=OrderedDict(); self.b1=OrderedDict(); self.b2=OrderedDict()
        self.store=set(); self.ev=[]
    def _rep(self, inb2):
        if self.t1 and (len(self.t1)>self.p or (inb2 and len(self.t1)==self.p)):
            k,_=self.t1.popitem(last=False); self.b1[k]=1
        else:
            k,_=self.t2.popitem(last=False); self.b2[k]=1
        self._ev(k)
    def access(self, key):
        c=self.c
        if key in self.t1:
            del self.t1[key]; self.t2[key]=1; return True
        if key in self.t2:
            self.t2.move_to_end(key); return True
        if key in self.b1:
            self.p=min(c, self.p+max(len(self.b2)//len(self.b1),1))
            self._rep(False); del self.b1[key]; self.t2[key]=1; self.store.add(key); return False
        if key in self.b2:
            self.p=max(0, self.p-max(len(self.b1)//len(self.b2),1))
            self._rep(True); del self.b2[key]; self.t2[key]=1; self.store.add(key); return False
        l1=len(self.t1)+len(self.b1)
        if l1==c:
            if len(self.t1)<c:
                self.b1.popitem(last=False); self._rep(False)
            else:
                k,_=self.t1.popitem(last=False); self._ev(k)
        elif l1<c and l1+len(self.t2)+len(self.b2)>=c:
            if l1+len(self.t2)+len(self.b2)==2*c: self.b2.popitem(last=False)
            self._rep(False)
        self.t1[key]=1; self.store.add(key); return False
    def _ev(self, k):
        self.store.discard(k); self.ev.append(k)



class Cache:
    """Simulates several policies on keys only and follows the one with most recent hits."""
    def __init__(self, capacity, D=0.001, H=0.05):
        self.c=capacity; self.pol=[LIRS(capacity, G=8), TLFU(capacity), S3(capacity),
                  TLFU(capacity, R=100), ARC(capacity)]
        self.sc=[0.0]*len(self.pol); self.d=1-D/ (capacity/100); self.H=H; self.w=0
        self.store=set(); self.pend=deque()
    def access(self, key):
        sc=self.sc; d=self.d
        for i,p in enumerate(self.pol):
            sc[i]=sc[i]*d+p.access(key)
        best=self._best()
        if best!=self.w and sc[best]>sc[self.w]*(1+self.H):
            self.w=best; ws=self.pol[best].store
            self.pend=deque(k for k in self.store if k not in ws)
        W=self.pol[self.w]
        for p in self.pol: 
            if p is W: self.pend.extend(p.ev)
            p.ev.clear()
        if key in self.store: return True
        if key not in W.store: return False
        st=self.store
        if len(st)>=self.c:
            ws=W.store; pend=self.pend
            while True:
                k=pend.popleft()
                if k in st and k not in ws: break
            st.discard(k)
        st.add(key); return False
    def _best(self):
        sc=self.sc; b=0
        for i in range(1,len(sc)):
            if sc[i]>sc[b]: b=i
        return b
