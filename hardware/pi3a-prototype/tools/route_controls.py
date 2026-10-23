"""Conservative grid routing proposal from the existing D1 pad nets.

Not a substitute for native DRC, power integrity or fabrication review. The
router never assigns a net or joins different net IDs. Failed links stay open.
Requires only KiCad's bundled numpy; no external autorouter is installed.
"""
from pathlib import Path
import collections, heapq, json, math, time
import numpy as np
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/'electrical/controls/nathan-controls.kicad_pcb'
G=.1;X0=40;Y0=50;NX=1601;NY=1001
LAYERS=[p.F_Cu,p.B_Cu]
def mm(v):return p.ToMM(v)
def xy(q):return (X0+q[0]*G,Y0+q[1]*G)
def cell(x,y):return (round((x-X0)/G),round((y-Y0)/G))
def vec(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def main():
    start=time.monotonic();b=p.LoadBoard(str(FILE));print('BOARD_LOADED',flush=True)
    if b.GetTracks() or b.Zones():raise ValueError('Route a clean generated D1 board only; existing routing must not be silently overwritten')
    occ=np.zeros((2,NY,NX),np.int16);viaocc=np.zeros_like(occ);pads=[];by_net=collections.defaultdict(list)
    outline=json.loads((ROOT/'parameters/design.json').read_text())['boards']['controls']['outline'];poly=[(a+120,c+100) for a,c in outline]
    yy,xx=np.mgrid[0:NY,0:NX];xx=X0+xx*G;yy=Y0+yy*G;inside=np.zeros((NY,NX),bool)
    for (ax,ay),(bx,by) in zip(poly,poly[1:]+poly[:1]):
        inside ^= ((ay>yy)!=(by>yy)) & (xx < (bx-ax)*(yy-ay)/(by-ay+1e-12)+ax)
    occ[:,~inside]=-1;viaocc[:,~inside]=-1
    def rect(a,x,y,w,h,angle,net,layers,extra):
        r=math.hypot(w,h)/2+extra;ix,iy=cell(x-r,y-r);jx,jy=cell(x+r,y+r);ix=max(0,ix);iy=max(0,iy);jx=min(NX-1,jx);jy=min(NY-1,jy)
        xs=np.arange(ix,jx+1)*G+X0-x;ys=np.arange(iy,jy+1)*G+Y0-y
        c=math.cos(angle);s=math.sin(angle);rx=xs[None,:]*c+ys[:,None]*s;ry=-xs[None,:]*s+ys[:,None]*c
        mask=(abs(rx)<=w/2+extra)&(abs(ry)<=h/2+extra)
        for layer in layers:
            part=a[layer,iy:jy+1,ix:jx+1];old=part[mask];part[mask]=np.where((old==0)|(old==net),net,-1)
    def disc(a,cx,cy,r,net,layers):
        ix=max(0,int(cx-r/G)-1);jx=min(NX-1,int(cx+r/G)+1);iy=max(0,int(cy-r/G)-1);jy=min(NY-1,int(cy+r/G)+1)
        ys,xs=np.ogrid[iy:jy+1,ix:jx+1];mask=((xs-cx)*G)**2+((ys-cy)*G)**2 <=r*r
        for layer in layers:
            part=a[layer,iy:jy+1,ix:jx+1];old=part[mask];part[mask]=np.where((old==0)|(old==net),net,-1)
    for f in b.GetFootprints():
        for pad in f.Pads():
            at=pad.GetPosition();x,y=mm(at.x),mm(at.y);size=pad.GetSize();w,h=mm(size.x),mm(size.y);net=pad.GetNetCode() or -1
            through=pad.GetAttribute()!=p.PAD_ATTRIB_SMD;layers=[0,1] if through else [0]
            a=math.radians(pad.GetOrientationDegrees());rect(occ,x,y,w,h,a,net,layers,.28);rect(viaocc,x,y,w,h,a,net,layers,.48)
            item={'ref':f.GetReference(),'pin':pad.GetNumber(),'net':net,'name':pad.GetNetname(),'xy':(x,y),'cell':cell(x,y),'layers':layers,'size':(w,h),'angle':a,'through':through}
            pads.append(item)
            if net>0:by_net[net].append(item)
    # Keep routes at least 0.4 mm from the outline (track edge included).
    for (ax,ay),(bx,by) in zip(poly,poly[1:]+poly[:1]):
        count=max(1,int(math.hypot(bx-ax,by-ay)/G))
        for k in range(count+1):
            q=cell(ax+(bx-ax)*k/count,ay+(by-ay)*k/count);disc(occ,*q,.45,-1,[0,1]);disc(viaocc,*q,.65,-1,[0,1])
    def free(q,n,which=occ):
        x,y,z=q
        return 0<=x<NX and 0<=y<NY and (which[z,y,x]==0 or which[z,y,x]==n)
    def viafree(q,n):return free((q[0],q[1],0),n,viaocc) and free((q[0],q[1],1),n,viaocc)
    def route(source,targets,n,allow_vias=True,limit=200000):
        goals=set(targets);gx=[a[0] for a in goals];gy=[a[1] for a in goals]
        def heuristic(q):return min(abs(q[0]-a[0])+abs(q[1]-a[1])+25*(q[2]!=a[2]) for a in goals)
        heap=[];prev={};dist={}
        for s in source:
            if free(s,n):dist[s]=0;heapq.heappush(heap,(heuristic(s),0,s))
        seen=0
        while heap and seen<limit:
            _,cost,q=heapq.heappop(heap)
            if cost!=dist.get(q):continue
            seen+=1
            if q in goals:
                path=[q]
                while q in prev:q=prev[q];path.append(q)
                return path[::-1]
            x,y,z=q
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
                r=(x+dx,y+dy,z)
                if not free(r,n):continue
                if dx and dy and (not free((x+dx,y,z),n) or not free((x,y+dy,z),n)):continue
                nc=cost+(14 if dx and dy else 10)
                if nc<dist.get(r,1e30):dist[r]=nc;prev[r]=q;heapq.heappush(heap,(nc+10*heuristic(r),nc,r))
            if allow_vias and viafree(q,n):
                r=(x,y,1-z);nc=cost+500
                if nc<dist.get(r,1e30):dist[r]=nc;prev[r]=q;heapq.heappush(heap,(nc+10*heuristic(r),nc,r))
        return None
    def track(a,c,n,layer,width=.2):
        if math.dist(a,c)<1e-7:return
        t=p.PCB_TRACK(b);t.SetStart(vec(*a));t.SetEnd(vec(*c));t.SetWidth(p.FromMM(width));t.SetLayer(LAYERS[layer]);t.SetNetCode(n);b.Add(t)
    viaset=set()
    def addvia(q,n):
        key=(q[0],q[1],n)
        if key in viaset:return
        viaset.add(key);v=p.PCB_VIA(b);v.SetPosition(vec(*xy(q)));v.SetWidth(p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNetCode(n);b.Add(v)
        disc(occ,q[0],q[1],.59,n,[0,1]);disc(viaocc,q[0],q[1],.79,n,[0,1])
    def emit(path,n,actual_start=None,actual_end=None):
        if not path:return
        if actual_start:track(actual_start,xy(path[0]),n,path[0][2])
        points=[path[0]]
        for a,c in zip(path,path[1:]):
            if a[2]!=c[2]:addvia(a,n)
            else:
                disc(occ,c[0],c[1],.39,n,[c[2]]);disc(viaocc,c[0],c[1],.59,n,[c[2]])
        # Compress only strictly collinear grid steps.
        for i in range(1,len(path)-1):
            a,c,d=path[i-1:i+2]
            if (c[0]-a[0],c[1]-a[1],c[2]-a[2])!=(d[0]-c[0],d[1]-c[1],d[2]-c[2]):points.append(c)
        points.append(path[-1])
        for a,c in zip(points,points[1:]):
            if a[2]==c[2]:track(xy(a),xy(c),n,a[2])
        if actual_end:track(xy(path[-1]),actual_end,n,path[-1][2])
    failures=[];done=[];plane_names={'GND':p.In1_Cu,'3V3_PI':p.In2_Cu,'3V3_HAPTIC':p.B_Cu}
    # Plane access first, with a short local trace to a through via outside pad.
    for n,items in by_net.items():
        name=items[0]['name']
        if name not in plane_names:continue
        for item in items:
            if item['through']:continue
            cx,cy=item['cell'];candidates=[]
            for radius in [.8,1.1,1.5,2,2.8,3.6]:
                for i in range(24):
                    angle=i*math.pi/12;q=(cx+round(math.cos(angle)*radius/G),cy+round(math.sin(angle)*radius/G),0)
                    if viafree(q,n):candidates.append(q)
            if not candidates:failures.append({'plane_pad':item['ref']+'.'+item['pin'],'net':name,'reason':'no via site'});continue
            path=route([(cx,cy,0)],candidates,n,False,25000)
            if path:emit(path,n,item['xy']);addvia(path[-1],n);done.append(name+' '+item['ref']+'.'+item['pin'])
            else:failures.append({'plane_pad':item['ref']+'.'+item['pin'],'net':name,'reason':'no local path'})
        print('PLANE_ACCESS '+name,flush=True)
    # Short local nets first; multi-drop signals use a growing minimum-distance tree.
    work=[(n,items) for n,items in by_net.items() if items[0]['name'] not in plane_names]
    work.sort(key=lambda x:max(math.dist(a['xy'],c['xy']) for a in x[1] for c in x[1]))
    for n,items in work:
        if len(items)<2:continue
        connected=[items[0]];remaining=items[1:]
        while remaining:
            _,a,c=min(((math.dist(a['xy'],c['xy']),a,c) for a in connected for c in remaining),key=lambda v:v[0])
            source=[(*a['cell'],z) for z in a['layers']];targets=[(*c['cell'],z) for z in c['layers']]
            path=route(source,targets,n)
            if path:emit(path,n,a['xy'],c['xy']);done.append(a['ref']+'.'+a['pin']+' -> '+c['ref']+'.'+c['pin'])
            else:failures.append({'net':a['name'],'from':a['ref']+'.'+a['pin'],'to':c['ref']+'.'+c['pin'],'reason':'grid path not found; left open'})
            connected.append(c);remaining.remove(c)
        print('NET '+items[0]['name']+' / failed='+str(len(failures)),flush=True)
    for name,layer in plane_names.items():
        n=next(n for n,items in by_net.items() if items[0]['name']==name);zone=p.ZONE(b);zone.SetLayer(layer);zone.SetNetCode(n);zone.SetLocalClearance(p.FromMM(.2));zone.SetPadConnection(p.ZONE_CONNECTION_FULL)
        polygon=zone.Outline();polygon.NewOutline()
        for x,y in poly:polygon.Append(p.FromMM(x),p.FromMM(y))
        b.Add(zone)
    p.SaveBoard(str(FILE),b);print('ROUTES_SAVED',flush=True)
    b.BuildConnectivity();filler=p.ZONE_FILLER(b);filler.Fill(b.Zones());p.SaveBoard(str(FILE),b);print('ZONES_FILLED',flush=True)
    report={'status':'routing proposal; native DRC must be assessed, not fabrication approved','elapsed_seconds':round(time.monotonic()-start,1),'connected_operations':len(done),'failures':failures,'tracks_and_vias':len(b.GetTracks()),'vias':len(viaset),'plane_layers':plane_names,'board_sha256':__import__('hashlib').sha256(FILE.read_bytes()).hexdigest(),'limitations':['All neck traces are 0.2 mm; supply trunks need widening or plane verification before current qualification.','No impedance/length/skew validation.','B.Cu is filled with motor 3V3; inner GND shields digital/ADC reference but noise remains to measure.']}
    (ROOT/'validation/controls-routing-d1.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
if __name__=='__main__':main()
