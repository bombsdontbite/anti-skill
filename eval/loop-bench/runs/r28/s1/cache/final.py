import heapq
from collections import OrderedDict, deque
class LIRS:
    """LIRS with 1% HIR resident."""
    def __init__(self, capacity):
        self.c=capacity; self.hc=max(2,capacity//100); self.lc=capacity-self.hc
        self.S=OrderedDict()  # key -> True if LIR
        self.Q=OrderedDict()  # resident HIR
        self.store=set(); self.nl=0; self.nonres=0
    def _prune(self):
        S=self.S
        while S:
            k=next(iter(S))
            if S[k]: break
            del S[k]
            if k not in self.store: self.nonres-=1
    def _limit(self):
        S=self.S
        if self.nonres>self.c*2:
            for k in [k for k,v in S.items() if not v and k not in self.store][:self.c]:
                del S[k]; self.nonres-=1
    def access(self, key):
        S=self.S; Q=self.Q; st=self.store
        if key in st:
            if S.get(key):
                S.move_to_end(key); self._prune(); return True
            if key in S:
                S[key]=True; S.move_to_end(key); del Q[key]
                k,_=S.popitem(last=False); S[k]=False; del S[k]; Q[k]=1
                # demoted LIR k: remove from stack
                self._prune(); return True
            S[key]=False; Q.move_to_end(key); return True
        # miss
        if self.nl<self.lc:
            S[key]=True; S.move_to_end(key); self.nl+=1; st.add(key); return False
        if len(st)>=self.c:
            k,_=Q.popitem(last=False); st.discard(k)
            if k in S: self.nonres+=1
        if key in S:
            self.nonres-=1
            S[key]=True; S.move_to_end(key)
            k,_=S.popitem(last=False); Q[k]=1
            self._prune()
        else:
            S[key]=False; Q[key]=1
        st.add(key); self._limit(); return False
class ARC:
    def __init__(self, capacity):
        self.c=capacity; self.p=0
        self.t1=OrderedDict(); self.t2=OrderedDict(); self.b1=OrderedDict(); self.b2=OrderedDict()
        self.store=set()
    def _rep(self, inb2):
        t1=self.t1
        if t1 and (len(t1)>self.p or (inb2 and len(t1)==self.p)):
            k,_=t1.popitem(last=False); self.b1[k]=1
        else:
            k,_=self.t2.popitem(last=False); self.b2[k]=1
        self.store.discard(k)
    def access(self, key):
        c=self.c
        if key in self.t1:
            del self.t1[key]; self.t2[key]=1; return True
        if key in self.t2:
            self.t2.move_to_end(key); return True
        if key in self.b1:
            self.p=min(c,self.p+max(len(self.b2)//len(self.b1),1))
            self._rep(False); del self.b1[key]; self.t2[key]=1; self.store.add(key); return False
        if key in self.b2:
            self.p=max(0,self.p-max(len(self.b1)//len(self.b2),1))
            self._rep(True); del self.b2[key]; self.t2[key]=1; self.store.add(key); return False
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
                if len(self.store)>=c: self._rep(False)
        self.t1[key]=1; self.store.add(key); return False
class TLFU:
    """W-TinyLFU: window LRU + SLRU main, admission by frequency sketch (exact dict, halved)."""
    def __init__(self, capacity):
        self.c=capacity; self.wc=max(1,capacity//100); mc=capacity-self.wc
        self.pc=int(mc*0.8)
        self.W=OrderedDict(); self.P=OrderedDict(); self.Pr=OrderedDict()
        self.store=set(); self.f={}; self.n=0; self.reset=capacity*10
    def _inc(self,k):
        f=self.f; f[k]=f.get(k,0)+1; self.n+=1
        if self.n>=self.reset:
            self.n//=2; self.f={a:b>>1 for a,b in f.items() if b>1}
    def access(self, key):
        self._inc(key)
        if key in self.W: self.W.move_to_end(key); return True
        if key in self.Pr:
            del self.Pr[key]; self.P[key]=1
            if len(self.P)>self.pc:
                k,_=self.P.popitem(last=False); self.Pr[k]=1
            return True
        if key in self.P: self.P.move_to_end(key); return True
        self.W[key]=1; self.store.add(key)
        if len(self.W)>self.wc:
            k,_=self.W.popitem(last=False)
            if len(self.P)+len(self.Pr)<self.c-self.wc:
                self.Pr[k]=1
            else:
                vk=next(iter(self.Pr)) if self.Pr else next(iter(self.P))
                f=self.f
                if f.get(k,0)>f.get(vk,0):
                    if vk in self.Pr: del self.Pr[vk]
                    else: del self.P[vk]
                    self.store.discard(vk); self.Pr[k]=1
                else:
                    self.store.discard(k)
        return False

class PRED:
    """Evict the key whose predicted next access (last + smoothed interval) is farthest."""
    def __init__(self, capacity):
        self.c=capacity; self.store=OrderedDict(); self.last={}; self.iv={}; self.h=[]; self.t=0
        self.unk=capacity*2
    def access(self, key):
        t=self.t=self.t+1; last=self.last; iv=self.iv; st=self.store
        p=last.get(key)
        if p is not None:
            d=t-p; o=iv.get(key)
            iv[key]=d if o is None else o*(1-0.3)+d*0.3
        last[key]=t
        pr=t+iv.get(key,self.unk)
        if key in st:
            st[key]=pr; st.move_to_end(key); heapq.heappush(self.h,(-pr,key)); return True
        if len(st)>=self.c:
            k=next(iter(st))
            if t-last[k]>1.2*iv.get(k,self.unk): del st[k]
            else:
                h=self.h
                while True:
                    npr,k=heapq.heappop(h)
                    if st.get(k)==-npr: del st[k]; break
        st[key]=pr; heapq.heappush(self.h,(-pr,key)); return False
DECAY_MULT=16
MARGIN=0.02
EXPERTS=(LIRS,ARC,PRED)
class Cache:
    """Follow the expert with the best recently decayed hit rate."""
    def __init__(self, capacity):
        self.c=capacity; self.ex=[E(capacity) for E in EXPERTS]; self.sc=[0.0]*len(self.ex)
        self.lead=0; self.store=set(); self.fifo=deque(); self.d=1-1.0/(capacity*DECAY_MULT)
    def access(self, key):
        st=self.store; hit=key in st
        sc=self.sc; d=self.d
        for i,e in enumerate(self.ex):
            sc[i]=sc[i]*d+e.access(key)
        b=self.lead
        m=max(sc)
        if sc[b]<m*(1-MARGIN): b=self.lead=sc.index(m)
        if hit: return True
        ls=self.ex[b].store
        if key in ls:
            fifo=self.fifo
            if len(st)>=self.c:
                while True:
                    k=fifo.popleft()
                    if k not in st: continue
                    if k in ls: fifo.append(k); continue
                    st.discard(k); break
            st.add(key); fifo.append(key)
        return False
