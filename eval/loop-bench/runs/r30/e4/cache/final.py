from collections import OrderedDict
import heapq, math, random
class _LRU:
    def __init__(self, capacity):
        self.capacity = capacity
        self.ev = []
        self.store = OrderedDict()
    def access(self, key):
        if key in self.store:
            self.store.move_to_end(key)
            return True
        if len(self.store) >= self.capacity:
            self.ev.append(self.store.popitem(last=False)[0])
        self.store[key] = True
        return False
class _ARC:
    def __init__(self, capacity):
        self.c=capacity; self.p=0; self.ev=[]
        self.t1=OrderedDict(); self.t2=OrderedDict(); self.b1=OrderedDict(); self.b2=OrderedDict()
        self.store=set()
    def _replace(self, in_b2):
        if self.t1 and (len(self.t1)>self.p or (in_b2 and len(self.t1)==self.p)):
            k,_=self.t1.popitem(last=False); self.b1[k]=1
        else:
            k,_=self.t2.popitem(last=False); self.b2[k]=1
        self.store.discard(k); self.ev.append(k)
    def access(self,key):
        c=self.c
        if key in self.t1:
            del self.t1[key]; self.t2[key]=1; return True
        if key in self.t2:
            self.t2.move_to_end(key); return True
        if key in self.b1:
            self.p=min(c,self.p+max(1,len(self.b2)//max(1,len(self.b1))))
            self._replace(False); del self.b1[key]; self.t2[key]=1; self.store.add(key); return False
        if key in self.b2:
            self.p=max(0,self.p-max(1,len(self.b1)//max(1,len(self.b2))))
            self._replace(True); del self.b2[key]; self.t2[key]=1; self.store.add(key); return False
        l1=len(self.t1)+len(self.b1)
        if l1==c:
            if len(self.t1)<c:
                self.b1.popitem(last=False); self._replace(False)
            else:
                k,_=self.t1.popitem(last=False); self.store.discard(k); self.ev.append(k)
        elif l1<c and l1+len(self.t2)+len(self.b2)>=c:
            if l1+len(self.t2)+len(self.b2)>=2*c: self.b2.popitem(last=False)
            self._replace(False)
        self.t1[key]=1; self.store.add(key); return False
class _WTL:
    # window LRU + probation/protected SLRU main with frequency admission (decayed counts)
    def __init__(self, capacity, wf=0.05, decay=10):
        self.c=capacity
        self.w=max(1,capacity//100*1) if capacity>=100 else 1
        self.wsz=max(1,int(capacity*wf))
        self.win=OrderedDict(); self.prob=OrderedDict(); self.prot=OrderedDict()
        self.prot_max=int((capacity-self.wsz)*0.8)
        self.freq={}; self.n=0; self.sample=capacity*decay; self.ev=[]
        self.store=set()
    def _touch(self,k):
        self.freq[k]=self.freq.get(k,0)+1
        self.n+=1
        if self.n>=self.sample:
            self.n=0
            self.freq={a:b>>1 for a,b in self.freq.items() if b>1}
    def access(self,key):
        self._touch(key)
        if key in self.win:
            self.win.move_to_end(key); return True
        if key in self.prot:
            self.prot.move_to_end(key); return True
        if key in self.prob:
            del self.prob[key]; self.prot[key]=1
            if len(self.prot)>self.prot_max:
                k,_=self.prot.popitem(last=False); self.prob[k]=1
            return True
        self.win[key]=1; self.store.add(key)
        if len(self.win)>self.wsz:
            k,_=self.win.popitem(last=False)
            mainmax=self.c-self.wsz
            if len(self.prob)+len(self.prot)<mainmax:
                self.prob[k]=1
            else:
                v=next(iter(self.prob)) if self.prob else None
                if v is None:
                    v=next(iter(self.prot)); 
                    if self.freq.get(k,0)>self.freq.get(v,0):
                        del self.prot[v]; self.store.discard(v); self.ev.append(v); self.prob[k]=1
                    else: self.store.discard(k); self.ev.append(k)
                elif self.freq.get(k,0)>self.freq.get(v,0):
                    del self.prob[v]; self.store.discard(v); self.ev.append(v); self.prob[k]=1
                else:
                    self.store.discard(k); self.ev.append(k)
        return False
class _WTS:
    # window LRU + probation/protected SLRU main with frequency admission (decayed counts)
    def __init__(self, capacity, wf=0.05, decay=10):
        self.c=capacity
        self.w=max(1,capacity//100*1) if capacity>=100 else 1
        self.wsz=max(1,int(capacity*wf))
        self.win=OrderedDict(); self.prob=OrderedDict(); self.prot=OrderedDict()
        self.prot_max=int((capacity-self.wsz)*0.8)
        self.sz=16*capacity+1; self.tab=[0]*self.sz; self.n=0; self.sample=capacity*decay; self.ev=[]
        self.store=set()
    def _touch(self,k):
        i=(k*2654435761)%self.sz
        if self.tab[i]<15: self.tab[i]+=1
        self.n+=1
        if self.n>=self.sample:
            self.n=0
            self.tab=[b>>1 for b in self.tab]
    def access(self,key):
        self._touch(key)
        if key in self.win:
            self.win.move_to_end(key); return True
        if key in self.prot:
            self.prot.move_to_end(key); return True
        if key in self.prob:
            del self.prob[key]; self.prot[key]=1
            if len(self.prot)>self.prot_max:
                k,_=self.prot.popitem(last=False); self.prob[k]=1
            return True
        self.win[key]=1; self.store.add(key)
        if len(self.win)>self.wsz:
            k,_=self.win.popitem(last=False)
            mainmax=self.c-self.wsz
            if len(self.prob)+len(self.prot)<mainmax:
                self.prob[k]=1
            else:
                v=next(iter(self.prob)) if self.prob else None
                if v is None:
                    v=next(iter(self.prot)); 
                    if self.tab[(k*2654435761)%self.sz]>self.tab[(v*2654435761)%self.sz]:
                        del self.prot[v]; self.store.discard(v); self.ev.append(v); self.prob[k]=1
                    else: self.store.discard(k); self.ev.append(k)
                elif self.tab[(k*2654435761)%self.sz]>self.tab[(v*2654435761)%self.sz]:
                    del self.prob[v]; self.store.discard(v); self.ev.append(v); self.prob[k]=1
                else:
                    self.store.discard(k); self.ev.append(k)
        return False
class _LeCaR:
    def __init__(self, capacity, lr=0.45, seed=1):
        self.c=capacity; self.store=OrderedDict()  # key -> None, order = recency
        self.freq={}; self.heap=[]; self.t=0; self.ev=[]
        self.g=[OrderedDict(),OrderedDict(),OrderedDict()]
        self.w=[1/3.]*3; self.lr=lr; self.rng=random.Random(seed)
        self.disc=0.005**(1.0/capacity)
        self.gt=[{},{},{}]; self.ts={}
    def _victim(self,e):
        if e==0:
            return next(iter(self.store))
        if e==2:
            return next(reversed(self.store))
        h=self.heap
        while True:
            f,t,k=h[0]
            if k in self.freq and self.freq[k]==f and self.ts[k]==t: return k
            heapq.heappop(h)

    def access(self,key):
        self.t+=1
        st=self.store
        if key in st:
            st.move_to_end(key); f=self.freq[key]+1; self.freq[key]=f
            self.ts[key]=self.t; heapq.heappush(self.heap,(f,self.t,key)); return True
        # miss: ghost check
        for e in range(3):
            if key in self.g[e]:
                age=self.t-self.gt[e][key]
                pen=math.exp(-self.lr*self.disc**age)
                # penalize e: others gain
                self.w[e]*=pen
                s=sum(self.w); self.w=[max(x/s,0.02) for x in self.w]
                s=sum(self.w); self.w=[x/s for x in self.w]
        if len(st)>=self.c:
            r=self.rng.random(); acc=0; e=2
            for i in range(3):
                acc+=self.w[i]
                if r<acc: e=i; break
            v=self._victim(e)
            del st[v]; del self.freq[v]; del self.ts[v]; self.ev.append(v)
            gg=self.g[e]; gg[v]=1; self.gt[e][v]=self.t
            if len(gg)>self.c:
                o,_=gg.popitem(last=False); del self.gt[e][o]
        st[key]=None; self.freq[key]=1; self.ts[key]=self.t; heapq.heappush(self.heap,(1,self.t,key))
        if len(self.heap)>8*self.c+100:
            self.heap=[(f,self.ts[k],k) for k,f in self.freq.items()]; heapq.heapify(self.heap)
        return False

class Cache:
    GAMMA=4.0; MARGIN=0.3
    def __init__(self, capacity):
        c=capacity
        self.c=c
        self.sh=[_LRU(c),_ARC(c),_WTL(c,0.02),_WTL(c,0.1),_WTL(c,0.3),_LeCaR(c),_WTS(c,0.02,3),_WTS(c,0.1,3)]
        self.sc=[0.0]*len(self.sh)
        self.g=1.0-1.0/(self.GAMMA*c)
        self.cur=0; self.n=0
        self.store=set()
        self.stale={}
    def access(self,key):
        sh=self.sh; sc=self.sc; g=self.g; cur=self.cur
        i=0
        for s_ in sh:
            sc[i]=sc[i]*g+(1.0 if s_.access(key) else 0.0)
            i+=1
        self.n+=1
        st=self.store; stale=self.stale
        if not self.n&7:
            best=cur; bs=sc[cur]*(1+self.MARGIN)+0.5
            for i in range(len(sh)):
                if sc[i]>bs:
                    bs=sc[i]; best=i
            if best!=cur:
                self.cur=cur=best
                ls=sh[cur].store
                self.stale=stale={k:1 for k in st if k not in ls}
                for s_ in sh: s_.ev.clear()
        L=sh[cur].store
        lead=sh[cur]
        for k in lead.ev:
            if k in st: stale[k]=1
        for s_ in sh: s_.ev.clear()
        if key in st:
            if key in L: stale.pop(key,None)
            else: stale[key]=1
            return True
        if key in L:
            if len(st)>=self.c:
                while stale:
                    v=next(iter(stale)); del stale[v]
                    if v in st and v not in L: break
                else:
                    v=next(k for k in st if k not in L)
                st.discard(v)
            st.add(key)
        return False
