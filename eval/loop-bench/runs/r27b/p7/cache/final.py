from collections import OrderedDict, deque
DECM=2.0
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
        self.store.discard(k); self.ev.append(k)
    def access(self, k):
        c=self.c
        if k in self.t1:
            del self.t1[k]; self.t2[k]=1; return True
        if k in self.t2:
            self.t2.move_to_end(k); return True
        if k in self.b1:
            self.p=min(c,self.p+max(len(self.b2)//len(self.b1),1))
            self._rep(False); del self.b1[k]; self.t2[k]=1; self.store.add(k); return False
        if k in self.b2:
            self.p=max(0,self.p-max(len(self.b1)//len(self.b2),1))
            self._rep(True); del self.b2[k]; self.t2[k]=1; self.store.add(k); return False
        l1=len(self.t1)+len(self.b1)
        if l1==c:
            if len(self.t1)<c:
                self.b1.popitem(last=False); self._rep(False)
            else:
                kk,_=self.t1.popitem(last=False); self.store.discard(kk); self.ev.append(kk)
        elif l1<c and l1+len(self.t2)+len(self.b2)>=c:
            if l1+len(self.t2)+len(self.b2)==2*c: self.b2.popitem(last=False)
            self._rep(False)
        self.t1[k]=1; self.store.add(k); return False

HF=0.01; SB=6.0; ADAPT=False
class LIRS:
    def __init__(self, capacity):
        self.cap=capacity; self.h=max(1,int(capacity*HF))
        self.S=OrderedDict(); self.Q=OrderedDict(); self.NR=OrderedDict()
        self.lir=set(); self.store=set(); self.ev=[]; self.sb=int(SB*capacity)
    def _demote(self):
        S=self.S
        b=next(iter(S)); del S[b]; self.lir.discard(b); self.Q[b]=1
        while S:
            x=next(iter(S))
            if x in self.lir: break
            del S[x]; self.NR.pop(x,None)
    def _fit(self):
        # keep LIR count == cap - h
        while len(self.lir)>self.cap-self.h: self._demote()
    def access(self,k):
        S=self.S
        if k in self.lir:
            first = next(iter(S))==k
            S.move_to_end(k)
            if first:
                while S:
                    x=next(iter(S))
                    if x in self.lir: break
                    del S[x]; self.NR.pop(x,None)
            return True
        if k in self.store:
            if k in S:
                S.move_to_end(k); del self.Q[k]; self.lir.add(k); self._demote()
            else:
                S[k]=1; self.Q.move_to_end(k)
            return True
        # miss
        if len(self.lir)<self.cap-self.h and not self.Q and len(self.store)<self.cap:
            self.lir.add(k); S[k]=1; self.store.add(k); return False
        if len(self.store)>=self.cap:
            v,_=self.Q.popitem(last=False); self.store.discard(v); self.ev.append(v)
            if v in S: self.NR[v]=1
        self.store.add(k)
        if k in S:
            del self.NR[k]
            if ADAPT and self.h<self.cap//2: self.h+=1
            S.move_to_end(k); self.lir.add(k); self._demote(); self._fit()
        else:
            S[k]=1; self.Q[k]=1
            if ADAPT and self.h>max(1,int(self.cap*HF)) and len(self.NR)==0: pass
        while len(S)>self.sb and self.NR:
            x,_=self.NR.popitem(last=False); del S[x]
            if ADAPT and self.h>1: self.h-=1
        return False

class Cache:
    def __init__(self, capacity):
        self.cap=capacity
        self.ex=[ARC(capacity), LIRS(capacity)]
        self.sc=[0.0,0.0]
        self.pend=[deque(),deque()]
        self.store=OrderedDict()
        self.d=1-1/(capacity*DECM)
    def access(self,k):
        st=self.store
        hit = k in st
        d=self.d; sc=self.sc
        for i,e in enumerate(self.ex):
            h=e.access(k)
            sc[i]=sc[i]*d+(1.0 if h else 0.0)
            if e.ev:
                self.pend[i].extend(e.ev); e.ev.clear()
        if hit:
            st.move_to_end(k); return True
        if len(st)>=self.cap:
            L=0 if sc[0]>sc[1] else 1
            ls=self.ex[L].store; p=self.pend[L]; v=None
            while p:
                x=p.popleft()
                if x in st and x not in ls: v=x; break
            if v is None:
                for x in st:
                    if x not in ls: v=x; break
                if v is None: v=next(iter(st))
            del st[v]
            if len(self.pend[1-L])>4*self.cap:
                q=self.pend[1-L]
                for _ in range(len(q)-2*self.cap): q.popleft()
        st[k]=True
        return False
