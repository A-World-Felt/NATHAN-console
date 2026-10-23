"""Read-only flood test for fine-pitch access; never changes a PCB."""
import collections,json
import repair_controls as r
def main():
    r.MARGIN=.005
    b=r.p.LoadBoard(str(r.FILE));g=r.Grid(b,.2)
    for ref,pin in [('U8','3'),('U8','5'),('U8','11'),('R35','1'),('U7','26')]:
        pad=next(x for f in b.GetFootprints() if f.GetReference()==ref for x in f.Pads() if x.GetNumber()==pin)
        n=pad.GetNetCode();x,y=r.cell(*r.pos(pad));source=(x,y,0);q=collections.deque([source]);prev={source:None};viap=None
        while q and len(prev)<20000:
            a=q.popleft()
            if g.viafree(a,n):viap=a;break
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                c=(a[0]+dx,a[1]+dy,0)
                if abs(c[0]-x)>60 or abs(c[1]-y)>60 or c in prev or not g.free(c,n):continue
                prev[c]=a;q.append(c)
        print(json.dumps({'ref':ref,'pin':pin,'n':n,'xy':r.pos(pad),'free':g.free(source,n),'visited':len(prev),'via':r.xy(viap) if viap else None,'neighbours':[[dx,dy,int(g.occ[0,y+dy,x+dx])] for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]]}),flush=True)
if __name__=='__main__':main()
