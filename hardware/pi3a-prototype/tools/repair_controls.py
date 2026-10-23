"""D1 routing iteration: keep 0.20 mm signal clearance, repair from native DRC.

Three routing layers, with In1.Cu reserved for the return plane. Existing
3V3_PI fill on In2.Cu is recomputed around new tracks. No DRC exclusions.
"""
from pathlib import Path
import heapq, json, math, time
import numpy as np
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1];FILE=ROOT/'electrical/controls/nathan-controls.kicad_pcb'
G=.1;X0=40;Y0=50;NX=1601;NY=1001;LAYERS=[p.F_Cu,p.B_Cu,p.In2_Cu]
MARGIN=.04
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def cell(x,y):return round((x-X0)/G),round((y-Y0)/G)
def xy(q):return X0+q[0]*G,Y0+q[1]*G
def pos(obj):q=obj.GetPosition();return p.ToMM(q.x),p.ToMM(q.y)
def connected_endpoints(board,pad,position=None):
    """Reachable endpoints of existing same-net copper, including escaped vias.

    Preserve actual connectivity; never treat all pads of a net as already joined.
    Native DRC still determines the final electrical connectivity.
    """
    from collections import defaultdict,deque
    graph=defaultdict(set);n=pad.GetNetCode()
    def point(x,y,z):return round(x,4),round(y,4),z
    for t in board.GetTracks():
        if t.GetNetCode()!=n:continue
        if isinstance(t,p.PCB_VIA):
            x,y=pos(t);points=[point(x,y,z) for z in range(3)]
            for a in points:graph[a].update(points)
        elif t.GetLayer() in LAYERS:
            a=t.GetStart();c=t.GetEnd();z=LAYERS.index(t.GetLayer());a=point(p.ToMM(a.x),p.ToMM(a.y),z);c=point(p.ToMM(c.x),p.ToMM(c.y),z);graph[a].add(c);graph[c].add(a)
    if isinstance(pad,p.PCB_VIA) or isinstance(pad,p.PAD) and pad.GetAttribute()!=p.PAD_ATTRIB_SMD:zs=[0,1,2]
    else:zs=[LAYERS.index(pad.GetLayer())]
    x,y=position or pos(pad);seen={point(x,y,z) for z in zs};q=deque(seen)
    while q:
        a=q.popleft()
        for c in graph[a]-seen:seen.add(c);q.append(c)
    return list({(*cell(x,y),z) for x,y,z in seen})
def segment(b,a,c,n,z,w):
    if math.dist(a,c)<1e-7:return
    t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*c));t.SetNetCode(n);t.SetLayer(LAYERS[z]);t.SetWidth(p.FromMM(w));b.Add(t)

class Grid:
    def __init__(self,b,width,poly=None):
        self.b=b;self.width=width;self.occ=np.zeros((3,NY,NX),np.int16);self.vo=np.zeros_like(self.occ);self.vias=[]
        D=json.loads((ROOT/'parameters/design.json').read_text());self.poly=poly or [(x+120,y+100) for x,y in D['boards']['controls']['outline']]
        yy,xx=np.mgrid[0:NY,0:NX];xx=X0+xx*G;yy=Y0+yy*G;inside=np.zeros((NY,NX),bool)
        for (ax,ay),(bx,by) in zip(self.poly,self.poly[1:]+self.poly[:1]):inside^=((ay>yy)!=(by>yy))&(xx<(bx-ax)*(yy-ay)/(by-ay+1e-12)+ax)
        self.occ[:,~inside]=-1;self.vo[:,~inside]=-1
        for f in b.GetFootprints():
            for pad in f.Pads():
                x,y=pos(pad);s=pad.GetSize();w,h=p.ToMM(s.x),p.ToMM(s.y);a=math.radians(pad.GetOrientationDegrees());layers=[LAYERS.index(pad.GetLayer())] if pad.GetAttribute()==p.PAD_ATTRIB_SMD else [0,1,2];n=pad.GetNetCode() or -1
                self.rect(self.occ,x,y,w,h,a,n,layers,.2+width/2+MARGIN);self.rect(self.vo,x,y,w,h,a,n,layers,.54)
        for t in b.GetTracks():
            if isinstance(t,p.PCB_VIA):
                q=cell(*pos(t));self.vias.append(q);r=p.ToMM(t.GetWidth())/2
                self.disc(self.occ,q,r+.2+width/2+MARGIN,t.GetNetCode(),[0,1,2]);self.disc(self.vo,q,r+.54,t.GetNetCode(),[0,1,2])
            else:
                if t.GetLayer() not in LAYERS:continue
                a=t.GetStart();c=t.GetEnd();a=(p.ToMM(a.x),p.ToMM(a.y));c=(p.ToMM(c.x),p.ToMM(c.y));z=LAYERS.index(t.GetLayer());r=p.ToMM(t.GetWidth())/2
                self.paint_segment(a,c,t.GetNetCode(),z,r+width/2+.2+MARGIN,r+.54)
        for a,c in zip(self.poly,self.poly[1:]+self.poly[:1]):self.paint_segment(a,c,-1,[0,1,2],.5,.7)
    def rect(self,arr,x,y,w,h,angle,n,layers,e):
        r=math.hypot(w,h)/2+e;ix,iy=cell(x-r,y-r);jx,jy=cell(x+r,y+r);ix=max(0,ix);iy=max(0,iy);jx=min(NX-1,jx);jy=min(NY-1,jy)
        xs=np.arange(ix,jx+1)*G+X0-x;ys=np.arange(iy,jy+1)*G+Y0-y;c=math.cos(angle);s=math.sin(angle)
        mask=(abs(xs[None,:]*c+ys[:,None]*s)<=w/2+e)&(abs(-xs[None,:]*s+ys[:,None]*c)<=h/2+e)
        for z in layers:
            part=arr[z,iy:jy+1,ix:jx+1];old=part[mask];part[mask]=np.where((old==0)|(old==n),n,-1)
    def disc(self,arr,q,r,n,layers):
        cx,cy=q;ix=max(0,int(cx-r/G)-1);jx=min(NX-1,int(cx+r/G)+1);iy=max(0,int(cy-r/G)-1);jy=min(NY-1,int(cy+r/G)+1)
        ys,xs=np.ogrid[iy:jy+1,ix:jx+1];mask=((xs-cx)*G)**2+((ys-cy)*G)**2<=r*r
        for z in layers:
            part=arr[z,iy:jy+1,ix:jx+1];old=part[mask];part[mask]=np.where((old==0)|(old==n),n,-1)
    def paint_segment(self,a,c,n,z,r,vr):
        layers=z if isinstance(z,list) else [z];steps=max(1,math.ceil(math.dist(a,c)/G))
        for k in range(steps+1):
            q=cell(a[0]+(c[0]-a[0])*k/steps,a[1]+(c[1]-a[1])*k/steps);self.disc(self.occ,q,r,n,layers);self.disc(self.vo,q,vr,n,layers)
    def free(self,q,n,a=None):
        x,y,z=q;a=self.occ if a is None else a
        return 0<=x<NX and 0<=y<NY and a[z,y,x] in (0,n)
    def viafree(self,q,n):
        return all(self.free((*q[:2],z),n,self.vo) for z in range(3)) and all(math.dist(q[:2],a)*G>=.56 for a in self.vias)
    def route(self,sources,targets,n,only_layer=None):
        targets=set(targets);xs=[a[0] for a in targets];ys=[a[1] for a in targets];lx,hx,ly,hy=min(xs),max(xs),min(ys),max(ys)
        def h(q):return 10*(max(lx-q[0],0,q[0]-hx)+max(ly-q[1],0,q[1]-hy))
        heap=[];dist={};prev={}
        for s in sources:
            if self.free(s,n):dist[s]=0;heapq.heappush(heap,(h(s),0,s))
        seen=0
        while heap and seen<500000:
            _,cost,q=heapq.heappop(heap)
            if dist.get(q)!=cost:continue
            seen+=1
            if q in targets:
                path=[q]
                while q in prev:q=prev[q];path.append(q)
                return path[::-1]
            x,y,z=q
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
                r=(x+dx,y+dy,z)
                if not self.free(r,n):continue
                if dx and dy and (not self.free((x+dx,y,z),n) or not self.free((x,y+dy,z),n)):continue
                nc=cost+(14 if dx and dy else 10)
                if nc<dist.get(r,1e30):dist[r]=nc;prev[r]=q;heapq.heappush(heap,(nc+h(r),nc,r))
            if only_layer is None and self.viafree(q,n):
                for nz in range(3):
                    if nz==z:continue
                    r=(x,y,nz);nc=cost+400
                    if nc<dist.get(r,1e30):dist[r]=nc;prev[r]=q;heapq.heappush(heap,(nc+h(r),nc,r))
        return None
    def emit(self,path,n,a=None,c=None):
        if a:segment(self.b,a,xy(path[0]),n,path[0][2],self.width)
        pts=[path[0]]
        for i in range(1,len(path)-1):
            a0,b0,c0=path[i-1:i+2]
            if tuple(b0[k]-a0[k] for k in range(3))!=tuple(c0[k]-b0[k] for k in range(3)):pts.append(b0)
        pts.append(path[-1])
        for a0,c0 in zip(pts,pts[1:]):
            if a0[2]==c0[2]:
                segment(self.b,xy(a0),xy(c0),n,a0[2],self.width);self.paint_segment(xy(a0),xy(c0),n,a0[2],self.width+.24,self.width/2+.54)
            else:
                via=p.PCB_VIA(self.b);via.SetPosition(v(*xy(a0)));via.SetWidth(p.FromMM(.6));via.SetDrill(p.FromMM(.3));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNetCode(n);self.b.Add(via);self.vias.append(a0[:2]);self.disc(self.occ,a0[:2],.3+self.width/2+.24,n,[0,1,2]);self.disc(self.vo,a0[:2],.84,n,[0,1,2])
        if c:segment(self.b,xy(path[-1]),c,n,path[-1][2],self.width)

def main():
    b=p.LoadBoard(str(FILE));drc=json.loads((ROOT/'validation/native-current/controls-routed-drc.json').read_text());print('LOADED',flush=True)
    # Preserve all history in the reports; remove only the redundant same-net via.
    for issue in drc['violations']:
        if issue['type']=='hole_near_hole':
            key=issue['items'][1]['uuid']
            for t in list(b.GetTracks()):
                if t.m_Uuid.AsString()==key:b.Delete(t)
    by_ref={f.GetReference():f for f in b.GetFootprints()};ps={pad.GetNumber():pad for pad in by_ref['PS2'].Pads()}
    segment(b,pos(ps['9']),pos(ps['3']),ps['9'].GetNetCode(),0,.2)
    repair_names=set()
    for issue in drc['violations']+drc['unconnected_items']:
        if issue.get('type')=='clearance' or issue.get('type')=='unconnected_items':
            desc=issue['items'][0]['description'];name=desc.split('[')[1].split(']')[0]
            if name not in ['GND','3V3_PI','3V3_HAPTIC']:repair_names.add(name)
    for t in list(b.GetTracks()):
        if t.GetNetname() in repair_names:b.Delete(t)
    for zone in list(b.Zones()):
        if zone.GetNetname()=='3V3_HAPTIC':b.Delete(zone)
    # Motor supply: explicit 0.5 mm In2 trunks connect the existing short necks.
    haptic=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetname()=='3V3_HAPTIC'];n=haptic[0].GetNetCode();grid=Grid(b,.5);remaining=haptic[1:];connected=[haptic[0]];failures=[]
    while remaining:
        _,a,c=min(((math.dist(pos(a),pos(c)),a,c) for a in connected for c in remaining),key=lambda v:v[0]);pa,pb=cell(*pos(a)),cell(*pos(c));path=grid.route([(*pa,2)],[(*pb,2)],n,2)
        if path:grid.emit(path,n)
        else:failures.append({'net':'3V3_HAPTIC','from':pos(a),'to':pos(c)})
        connected.append(c);remaining.remove(c)
    print('HAPTIC_TRUNKS_DONE '+str(len(failures)),flush=True);p.SaveBoard(str(FILE),b)
    grid=Grid(b,.2)
    for name in sorted(repair_names):
        pads=[pad for f in b.GetFootprints() for pad in f.Pads() if pad.GetNetname()==name];n=pads[0].GetNetCode();remaining=pads[1:];connected=[pads[0]]
        def endpoints(pad):return [(*cell(*pos(pad)),z) for z in ([0] if pad.GetAttribute()==p.PAD_ATTRIB_SMD else [0,1,2])]
        while remaining:
            _,a,c=min(((math.dist(pos(a),pos(c)),a,c) for a in connected for c in remaining),key=lambda v:v[0]);path=grid.route(endpoints(a),endpoints(c),n)
            if path:grid.emit(path,n,pos(a),pos(c))
            else:failures.append({'net':name,'from':pos(a),'to':pos(c)})
            connected.append(c);remaining.remove(c)
        p.SaveBoard(str(FILE),b);print('REPAIRED '+name+' remaining failures '+str(len(failures)),flush=True)
    b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(FILE),b)
    result={'status':'Native DRC needed after repair; no fabrication qualification','clearance_target_mm':.2,'haptic_trunk_width_mm':.5,'signal_width_mm':.2,'failed_links':failures,'tracks_and_vias':len(b.GetTracks()),'board_sha256':__import__('hashlib').sha256(FILE.read_bytes()).hexdigest()}
    (ROOT/'validation/controls-routing-repair-d1.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
