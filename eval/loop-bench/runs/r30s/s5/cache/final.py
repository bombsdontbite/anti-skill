from collections import OrderedDict
class ELRU:
    def __init__(s,c): s.c=c; s.store=OrderedDict()
    def access(s,k):
        if k in s.store: s.store.move_to_end(k); return True
        if len(s.store)>=s.c: s.store.popitem(last=False)
        s.store[k]=1; return False
class EARC:
    def __init__(s,c):
        s.c=c; s.p=0
        s.t1=OrderedDict(); s.t2=OrderedDict(); s.b1=OrderedDict(); s.b2=OrderedDict()
        s.store={}
    def _replace(s,in_b2):
        if s.t1 and (len(s.t1)>s.p or (in_b2 and len(s.t1)==s.p)):
            k,_=s.t1.popitem(last=False); s.b1[k]=1
        else:
            k,_=s.t2.popitem(last=False); s.b2[k]=1
        del s.store[k]
    def access(s,k):
        c=s.c
        if k in s.t1:
            del s.t1[k]; s.t2[k]=1; return True
        if k in s.t2:
            s.t2.move_to_end(k); return True
        if k in s.b1:
            s.p=min(c,s.p+max(1,len(s.b2)//max(1,len(s.b1))))
            del s.b1[k]; s._replace(False); s.t2[k]=1; s.store[k]=1; return False
        if k in s.b2:
            s.p=max(0,s.p-max(1,len(s.b1)//max(1,len(s.b2))))
            del s.b2[k]; s._replace(True); s.t2[k]=1; s.store[k]=1; return False
        l1=len(s.t1)+len(s.b1)
        if l1==c:
            if len(s.t1)<c:
                s.b1.popitem(last=False); s._replace(False)
            else:
                kk,_=s.t1.popitem(last=False); del s.store[kk]
        else:
            tot=l1+len(s.t2)+len(s.b2)
            if tot>=c:
                if tot>=2*c: s.b2.popitem(last=False)
                if len(s.t1)+len(s.t2)>=c: s._replace(False)
        s.t1[k]=1; s.store[k]=1; return False

class EWTL:
    WIN=0.01; PROT=0.8; SAMPLE=10
    def __init__(s,c):
        s.c=c; s.wmax=max(1,int(c*s.WIN)); s.mmax=c-s.wmax
        s.pmax=int(s.mmax*s.PROT)
        s.win=OrderedDict(); s.prob=OrderedDict(); s.prot=OrderedDict()
        s.store={}; s.f={}; s.n=0; s.lim=c*s.SAMPLE
    def _inc(s,k):
        s.f[k]=s.f.get(k,0)+1; s.n+=1
        if s.n>=s.lim:
            s.n=0
            for x in list(s.f):
                v=s.f[x]>>1
                if v: s.f[x]=v
                else: del s.f[x]
    def access(s,k):
        s._inc(k)
        if k in s.prot: s.prot.move_to_end(k); return True
        if k in s.prob:
            del s.prob[k]; s.prot[k]=1
            if len(s.prot)>s.pmax:
                x,_=s.prot.popitem(last=False); s.prob[x]=1
            return True
        if k in s.win: s.win.move_to_end(k); return True
        s.win[k]=1; s.store[k]=1
        if len(s.win)>s.wmax:
            x,_=s.win.popitem(last=False)
            if len(s.prob)+len(s.prot)<s.mmax:
                s.prob[x]=1
            else:
                v=next(iter(s.prob)) if s.prob else next(iter(s.prot))
                if s.f.get(x,0)>s.f.get(v,0):
                    if s.prob: del s.prob[v]
                    else: del s.prot[v]
                    del s.store[v]; s.prob[x]=1
                else: del s.store[x]
        return False


class Cache:
    DECAY = 0.999
    def __init__(self, capacity):
        self.capacity = capacity
        self.ex = [ELRU(capacity), EARC(capacity), EWTL(capacity)]
        self.score = [0.0] * len(self.ex)
        self.lead = 0
        self.store = OrderedDict()
        self.d = 1.0 - 1.0 / max(50, capacity * 5)

    def access(self, key):
        sc = self.score
        d = self.d
        best = 0
        for i, e in enumerate(self.ex):
            sc[i] = sc[i] * d + (1.0 if e.access(key) else 0.0)
        lead = self.lead
        for i in range(len(sc)):
            if sc[i] > sc[lead] * 1.02 + 0.5:
                lead = i
        self.lead = lead
        ls = self.ex[lead].store
        st = self.store
        if key in st:
            st.move_to_end(key)
            return True
        if key in ls:
            if len(st) >= self.capacity:
                victim = None
                for x in st:
                    if x not in ls:
                        victim = x
                        break
                if victim is None:
                    victim = next(iter(st))
                del st[victim]
            st[key] = True
        return False
