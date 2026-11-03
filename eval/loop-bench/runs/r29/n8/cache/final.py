from collections import deque
from collections import OrderedDict
class LIRS:
    def __init__(self, capacity, hir=0.05, nr=4.0, fg=0, adapt=0, period=5, decay=10):
        self.cap=capacity; self.hcap=max(1,int(capacity*hir)); self.lcap=capacity-self.hcap
        self.S=OrderedDict(); self.Q=OrderedDict(); self.NR=OrderedDict()
        self.lir=set(); self.store=set()
        self.nrmax=max(1,int(nr*capacity)); self.fg=fg
        self.freq={}; self.n=0; self.reset=capacity*decay
        self.adapt=adapt; self.period=capacity*period; self.cnt=0; self.hits=0; self.prev=-1; self.dir=1
        self.step=max(1,capacity//32)
    def _prune(self):
        S=self.S
        while S:
            k=next(iter(S))
            if S[k]: break
            del S[k]; self.NR.pop(k,None)
    def _demote(self):
        k,_=self.S.popitem(last=False); self.lir.discard(k); self.Q[k]=1; self._prune()
    def _hit(self):
        self.hits+=1; return True
    def _tick(self):
        self.cnt+=1
        if self.cnt>=self.period:
            r=self.hits/self.cnt
            if r<self.prev: self.dir=-self.dir
            self.prev=r; self.cnt=0; self.hits=0
            self.lcap=min(self.cap-1,max(self.cap//4,self.lcap+self.dir*self.step))
            while len(self.lir)>self.lcap: self._demote()
            while len(self.Q)>0 and len(self.store)>self.cap:
                v,_=self.Q.popitem(last=False); self.store.discard(v)
    def access(self, k):
        if self.fg:
            f=self.freq; f[k]=f.get(k,0)+1; self.n+=1
            if self.n>=self.reset:
                self.n//=2; self.freq={a:b>>1 for a,b in f.items() if b>1}
        if self.adapt: self._tick()
        S=self.S
        if k in self.lir:
            first = next(iter(S))==k
            S.move_to_end(k)
            if first: self._prune()
            return self._hit()
        if k in self.Q:
            if k in S and self._ok(k):
                del self.Q[k]; S.move_to_end(k); S[k]=True; self.lir.add(k); self._demote()
            else:
                S[k]=False; S.move_to_end(k); self.Q.move_to_end(k)
            return self._hit()
        if len(self.lir)<self.lcap and len(self.store)<self.cap:
            self.NR.pop(k,None)
            self.lir.add(k); S[k]=True; S.move_to_end(k); self.store.add(k); return False
        if len(self.store)>=self.cap:
            v,_=self.Q.popitem(last=False); self.store.discard(v)
            if v in S:
                self.NR[v]=1
                if len(self.NR)>self.nrmax:
                    x,_=self.NR.popitem(last=False); del S[x]
        self.store.add(k)
        if k in S and self._ok(k):
            del self.NR[k]; S.move_to_end(k); S[k]=True; self.lir.add(k); self._demote()
        else:
            if k in self.NR: del self.NR[k]
            S[k]=False; S.move_to_end(k); self.Q[k]=1
        return False
    def _ok(self,k):
        if not self.fg: return True
        b=next(iter(self.S)); f=self.freq
        return f.get(k,0)*self.fg>=f.get(b,0)


class TLFU:
    def __init__(self, capacity, win=0.01, step=0.0625, period=5, resetm=6, prot=0.6):
        self.cap=capacity; self.wcap=max(1,int(capacity*win))
        self.protf=prot
        self.win=OrderedDict(); self.prob=OrderedDict(); self.prot=OrderedDict()
        self.freq={}; self.n=0; self.reset=capacity*resetm
        self.store=set()
        self.step=max(1,int(capacity*step)); self.dir=1
        self.period=capacity*period; self.cnt=0; self.hits=0; self.prev=-1.0
    def _inc(self,k):
        f=self.freq; f[k]=f.get(k,0)+1; self.n+=1
        if self.n>=self.reset:
            self.n//=2
            self.freq={a:b>>1 for a,b in f.items() if b>1}
    def _climb(self):
        r=self.hits/self.cnt
        if r<self.prev: self.dir=-self.dir
        self.prev=r; self.cnt=0; self.hits=0
        self.wcap=min(self.cap-1,max(1,self.wcap+self.dir*self.step))
        self._fix()
    def _fix(self):
        mcap=self.cap-self.wcap
        while len(self.win)>self.wcap:
            k,_=self.win.popitem(last=False)
            if len(self.prob)+len(self.prot)<mcap: self.prob[k]=1
            else: self._admit(k)
        while len(self.prob)+len(self.prot)>mcap:
            q=self.prob if self.prob else self.prot
            k,_=q.popitem(last=False); self.store.discard(k)
        pc=int(mcap*self.protf)
        while len(self.prot)>pc:
            d,_=self.prot.popitem(last=False); self.prob[d]=1
    def _admit(self,cand):
        vq=self.prob if self.prob else self.prot
        victim=next(iter(vq)); f=self.freq
        if f.get(cand,0)>f.get(victim,0):
            del vq[victim]; self.store.discard(victim); self.prob[cand]=1
        else: self.store.discard(cand)
    def access(self, k):
        self._inc(k); self.cnt+=1
        if self.cnt>=self.period: self._climb()
        if k in self.win:
            self.win.move_to_end(k); self.hits+=1; return True
        if k in self.prob:
            del self.prob[k]; self.prot[k]=1
            if len(self.prot)>int((self.cap-self.wcap)*self.protf):
                d,_=self.prot.popitem(last=False); self.prob[d]=1
            self.hits+=1; return True
        if k in self.prot:
            self.prot.move_to_end(k); self.hits+=1; return True
        self.win[k]=1; self.store.add(k)
        if len(self.win)>self.wcap:
            cand,_=self.win.popitem(last=False)
            if len(self.prob)+len(self.prot)<self.cap-self.wcap: self.prob[cand]=1
            else: self._admit(cand)
        return False


class ARC:
    def __init__(self, capacity):
        self.c=capacity; self.p=0
        self.t1=OrderedDict(); self.t2=OrderedDict(); self.b1=OrderedDict(); self.b2=OrderedDict()
        self.store=set()
    def _rep(self, inb2):
        if self.t1 and (len(self.t1)>self.p or (inb2 and len(self.t1)==self.p)):
            k,_=self.t1.popitem(last=False); self.b1[k]=1
        else:
            k,_=self.t2.popitem(last=False); self.b2[k]=1
        self.store.discard(k)
    def access(self, k):
        c=self.c
        if k in self.t1:
            del self.t1[k]; self.t2[k]=1; return True
        if k in self.t2:
            self.t2.move_to_end(k); return True
        if k in self.b1:
            self.p=min(c, self.p+max(len(self.b2)//len(self.b1),1))
            self._rep(False); del self.b1[k]; self.t2[k]=1; self.store.add(k); return False
        if k in self.b2:
            self.p=max(0, self.p-max(len(self.b1)//len(self.b2),1))
            self._rep(True); del self.b2[k]; self.t2[k]=1; self.store.add(k); return False
        l1=len(self.t1)+len(self.b1)
        if l1==c:
            if len(self.t1)<c:
                self.b1.popitem(last=False); self._rep(False)
            else:
                k2,_=self.t1.popitem(last=False); self.store.discard(k2)
        elif l1<c and l1+len(self.t2)+len(self.b2)>=c:
            if l1+len(self.t2)+len(self.b2)==2*c: self.b2.popitem(last=False)
            self._rep(False)
        self.t1[k]=1; self.store.add(k); return False


class S3:
    def __init__(self, capacity):
        self.cap=capacity; self.scap=max(1,capacity//10)
        self.S=deque(); self.M=deque(); self.G=dict(); self.gq=deque()
        self.f={}; self.store=set()
    def _evictS(self):
        while self.S:
            k=self.S.popleft()
            if self.f[k]>0:
                self.M.append(k); self.f[k]=0
                if len(self.M)>self.cap-self.scap: self._evictM()
            else:
                del self.f[k]; self.store.discard(k)
                self.G[k]=1; self.gq.append(k)
                while len(self.gq)>self.cap:
                    g=self.gq.popleft(); self.G.pop(g,None)
                return
    def _evictM(self):
        while True:
            k=self.M.popleft()
            if self.f[k]>0: self.f[k]-=1; self.M.append(k)
            else:
                del self.f[k]; self.store.discard(k); return
    def access(self, k):
        if k in self.store:
            if self.f[k]<3: self.f[k]+=1
            return True
        if len(self.store)>=self.cap:
            if len(self.S)>=self.scap or not self.M: self._evictS()
            else: self._evictM()
            if len(self.store)>=self.cap: self._evictM()
        self.store.add(k); self.f[k]=0
        if k in self.G:
            del self.G[k]; self.M.append(k)
        else: self.S.append(k)
        return False

import heapq
class LFU:
    def __init__(self, capacity, decay=8):
        self.cap=capacity; self.store=set(); self.f={}; self.h=[]; self.t=0; self.n=0; self.reset=capacity*decay
    def access(self, k):
        self.t+=1; self.n+=1
        if self.n>=self.reset:
            self.n=0; self.f={a:b>>1 for a,b in self.f.items() if b>1 or a in self.store}
            self.h=[(self.f[x],self.t,x) for x in self.store]; heapq.heapify(self.h)
        f=self.f; f[k]=f.get(k,0)+1
        if k in self.store:
            heapq.heappush(self.h,(f[k],self.t,k)); return True
        if len(self.store)>=self.cap:
            while True:
                c,t,x=heapq.heappop(self.h)
                if x in self.store and f.get(x,0)==c:
                    if c>=f[k]: heapq.heappush(self.h,(c,t,x)); return False
                    self.store.discard(x); break
        self.store.add(k); heapq.heappush(self.h,(f[k],self.t,k)); return False

class Cache:
    def __init__(self, capacity, decay=10.0, margin=0.0, which=(0,2,3,5)):
        allx=[lambda c:LIRS(c), lambda c:TLFU(c), lambda c:ARC(c), lambda c:S3(c), lambda c:LFU(c), lambda c:LIRS(c,hir=0.01), lambda c:LIRS(c,hir=0.2), lambda c:LIRS(c,hir=0.003), lambda c:LIRS(c,hir=0.01,nr=8.0), lambda c:LIRS(c,hir=0.01,nr=2.0)]
        self.ex=[allx[i](capacity) for i in which]
        self.sc=[0.0]*len(self.ex); self.d=1-1/(capacity*decay)
        self.lead=0; self.margin=margin
        self.cap=capacity; self.store=OrderedDict()
    def access(self, k):
        sc=self.sc; d=self.d; b=0
        for i,e in enumerate(self.ex):
            sc[i]=sc[i]*d+(1.0 if e.access(k) else 0.0)
            if sc[i]>sc[b]: b=i
        if sc[b]>sc[self.lead]*(1+self.margin)+1e-9: self.lead=b
        st=self.store
        if k in st:
            st.move_to_end(k); return True
        L=self.ex[self.lead].store
        if k in L:
            if len(st)>=self.cap:
                while True:
                    x=next(iter(st))
                    if x in L: st.move_to_end(x)
                    else: del st[x]; break
            st[k]=True
        return False
