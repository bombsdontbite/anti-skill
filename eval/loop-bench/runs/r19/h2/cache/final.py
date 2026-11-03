from collections import OrderedDict, deque
from heapq import heappush, heappop, heapify


class LRU:
    ev=None
    """Least recently used."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.store = OrderedDict()

    def access(self, key):
        if key in self.store:
            self.store.move_to_end(key)
            return True
        if len(self.store) >= self.capacity:
            self.ev,_=self.store.popitem(last=False)
        self.store[key] = True
        return False


class ARC:
    ev=None
    def __init__(self, capacity):
        self.c=capacity; self.p=0
        self.t1=OrderedDict(); self.t2=OrderedDict(); self.b1=OrderedDict(); self.b2=OrderedDict()
        self.store=set()
    def _rep(self, inb2):
        if self.t1 and (len(self.t1)>self.p or (inb2 and len(self.t1)==self.p)):
            k,_=self.t1.popitem(last=False); self.b1[k]=1
        else:
            k,_=self.t2.popitem(last=False); self.b2[k]=1
        self.store.discard(k); self.ev=k
    def access(self, k):
        c=self.c
        if k in self.t1:
            del self.t1[k]; self.t2[k]=1; return True
        if k in self.t2:
            self.t2.move_to_end(k); return True
        if k in self.b1:
            self.p=min(c, self.p+max(len(self.b2)//max(len(self.b1),1),1))
            self._rep(False); del self.b1[k]; self.t2[k]=1; self.store.add(k); return False
        if k in self.b2:
            self.p=max(0, self.p-max(len(self.b1)//max(len(self.b2),1),1))
            self._rep(True); del self.b2[k]; self.t2[k]=1; self.store.add(k); return False
        l1=len(self.t1)+len(self.b1)
        if l1==c:
            if len(self.t1)<c:
                self.b1.popitem(last=False); self._rep(False)
            else:
                k2,_=self.t1.popitem(last=False); self.store.discard(k2); self.ev=k2
        else:
            tot=l1+len(self.t2)+len(self.b2)
            if tot>=c:
                if tot==2*c: self.b2.popitem(last=False)
                self._rep(False)
        self.t1[k]=1; self.store.add(k); return False


class TLFU:
    ev=None
    """W-TinyLFU: window LRU + segmented LRU main, admission by frequency sketch with aging."""
    WIN=0.01; PROT=0.8; RESETK=10
    def __init__(self, capacity):
        self.c=capacity
        self.wc=max(1,int(capacity*self.WIN)); self.mc=capacity-self.wc
        self.pc=int(self.mc*self.PROT)
        self.w=OrderedDict(); self.pr=OrderedDict(); self.pt=OrderedDict()
        self.f={}; self.n=0; self.reset=capacity*self.RESETK
        self.store=set()
    def _inc(self,k):
        f=self.f; f[k]=f.get(k,0)+1; self.n+=1
        if self.n>=self.reset:
            self.n//=2
            self.f={a:b>>1 for a,b in f.items() if b>1}
    def access(self,k):
        self._inc(k)
        if k in self.w: self.w.move_to_end(k); return True
        if k in self.pt: self.pt.move_to_end(k); return True
        if k in self.pr:
            del self.pr[k]; self.pt[k]=1
            if len(self.pt)>self.pc:
                d,_=self.pt.popitem(last=False); self.pr[d]=1
            return True
        self.store.add(k); self.w[k]=1
        if len(self.w)>self.wc:
            cand,_=self.w.popitem(last=False)
            if len(self.pr)+len(self.pt)<self.mc:
                self.pr[cand]=1
            else:
                vic=next(iter(self.pr)) if self.pr else next(iter(self.pt))
                if self.f.get(cand,0)>self.f.get(vic,0):
                    if vic in self.pr: del self.pr[vic]
                    else: del self.pt[vic]
                    self.store.discard(vic); self.ev=vic; self.pr[cand]=1
                else:
                    self.store.discard(cand); self.ev=cand
        return False


class S3:
    ev=None
    def __init__(self, capacity):
        self.c=capacity; self.sc=max(1,capacity//10)
        self.S=deque(); self.M=deque(); self.G=OrderedDict(); self.fr={}
        self.store=set(); self.ns=0
    def _evict(self):
        while True:
            if len(self.S)>=self.sc or not self.M:
                k=self.S.popleft()
                if self.fr[k]>0:
                    self.fr[k]=0; self.M.append(k)
                else:
                    del self.fr[k]; self.store.discard(k); self.ev=k; self.G[k]=1
                    if len(self.G)>self.c: self.G.popitem(last=False)
                    return
            else:
                k=self.M.popleft()
                if self.fr[k]>0: self.fr[k]-=1; self.M.append(k)
                else: del self.fr[k]; self.store.discard(k); self.ev=k; return
    def access(self,k):
        if k in self.fr:
            if self.fr[k]<3: self.fr[k]+=1
            return True
        if len(self.store)>=self.c: self._evict()
        self.store.add(k); self.fr[k]=0
        if k in self.G: del self.G[k]; self.M.append(k)
        else: self.S.append(k)
        return False


class PRED:
    ev=None
    """Evict the key predicted to return last (last access + reuse interval); overdue keys go first."""
    ALPHA=0.3; MIX=0.5; K=1.0; NEWF=1.0; OVER=1.1; GHOST=16
    def __init__(self, capacity):
        self.c=capacity; self.t=0
        self.store={}; self.iv={}; self.ema={}; self.cnt={}; self.first={}; self.last={}; self.h=[]; self.lru=OrderedDict()
        self.avg=float(capacity)
        self.nn=1.0; self.nr=0.5; self.sd=float(capacity)*0.5
    def _pred(self,k):
        iv=self.iv.get(k)
        if iv is None:
            return self.t+self.NEWF*(self.sd/self.nr)*(self.nn/self.nr)
        return self.t+self.K*iv
    def access(self,k):
        self.t+=1; t=self.t
        l=self.last.get(k)
        if l is not None:
            d=t-l
            self.avg+=0.01*(d-self.avg) if d<self.c*20 else 0
            iv=self.iv.get(k)
            if iv is None:
                self.nr+=1; self.sd+=min(d,self.c*20)
            self.ema[k]=e=d if iv is None else self.ema[k]+self.ALPHA*(d-self.ema[k])
            n=self.cnt[k]=self.cnt.get(k,1)+1
            self.iv[k]=self.MIX*(t-self.first[k])/(n-1)+(1-self.MIX)*e
        else:
            self.first[k]=t
            self.nn+=1
            if self.nn>self.c*10:
                self.nn*=0.5; self.nr*=0.5; self.sd*=0.5
        self.last[k]=t
        st=self.store
        hit = k in st
        if not hit and len(st)>=self.c:
            v=next(iter(self.lru))
            if t-self.last[v] > self.OVER*self.iv.get(v,self.avg*2):
                pass
            else:
                h=self.h
                while True:
                    p,x,ver=heappop(h)
                    if st.get(x)==ver: v=x; break
            del st[v]; del self.lru[v]; self.ev=v
        if hit: self.lru.move_to_end(k)
        else: self.lru[k]=1
        p=self._pred(k)
        st[k]=p; heappush(self.h,(-p,k,p))
        if len(self.last)>self.c*self.GHOST*2:
            keep=sorted(self.last.items(), key=lambda a:-a[1])[:self.c*self.GHOST]
            self.last=dict(keep)
            for x in st: self.last.setdefault(x, t)
            L=self.last
            self.iv={x:v for x,v in self.iv.items() if x in L}
            self.ema={x:v for x,v in self.ema.items() if x in L}
            self.cnt={x:v for x,v in self.cnt.items() if x in L}
            self.first={x:v for x,v in self.first.items() if x in L}
        if len(self.h)>self.c*8:
            self.h=[(-p,x,p) for x,p in st.items()]; heapify(self.h)
        return hit


class Cache:
    """Follows whichever shadow policy has hit most recently."""
    DECAY=10.0; HYST=1.05
    EXPERTS=(LRU,ARC,TLFU,S3,PRED)
    def __init__(self, capacity):
        self.c=capacity
        self.ex=[E(capacity) for E in self.EXPERTS]
        self.sc=[0.0]*len(self.ex)
        self.d=1.0-1.0/(capacity*self.DECAY)
        self.inc=1.0
        self.store=set(); self.q=deque(); self.b=0
    def access(self, k):
        hit = k in self.store
        sc=self.sc; inc=self.inc
        for i,e in enumerate(self.ex):
            if e.access(k): sc[i]+=inc
        self.inc=inc/self.d
        if inc>1e100:
            self.sc=[x/inc for x in sc]; self.inc=1.0
        if hit: return True
        b=self.b; bb=b
        for i in range(len(sc)):
            if sc[i]>sc[bb]: bb=i
        if sc[bb]>sc[b]*self.HYST: b=self.b=bb
        bs=self.ex[b].store
        if k not in bs: return False
        st=self.store; q=self.q
        if len(st)>=self.c:
            v=self.ex[b].ev
            if v in st and v not in bs:
                st.discard(v); st.add(k); q.append(k)
                return False
            while True:
                v=q.popleft()
                if v not in st: continue
                if v in bs: q.append(v); continue
                st.discard(v); break
        st.add(k); q.append(k)
        return False
