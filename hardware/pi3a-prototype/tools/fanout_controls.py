"""Replace congested mux escapes with a staggered through-via fanout."""
import json,math,hashlib
import repair_controls as r
from repair_controls import p,ROOT,FILE,v,pos,cell,segment

def main():
    b=p.LoadBoard(str(FILE));fp={f.GetReference():f for f in b.GetFootprints()}
    pads={x.GetNumber():x for x in fp['U8'].Pads()}
    names={x.GetNetname() for x in pads.values() if x.GetNetCode() and x.GetNetname() not in ['GND','3V3_PI']}
    names.add('FACE_R_RIGHT')
    removed=0
    for t in list(b.GetTracks()):
        bb=t.GetBoundingBox();x=p.ToMM(bb.GetX());y=p.ToMM(bb.GetY());w=p.ToMM(bb.GetWidth());h=p.ToMM(bb.GetHeight())
        near=(x<128 and x+w>110 and y<82 and y+h>70) or (x<126 and x+w>122 and y<90.5 and y+h>87)
        if t.GetNetname() in names or near and t.GetNetname() in ['GND','3V3_PI']:
            b.Delete(t);removed+=1
    # Move the reset capacitor out of the mux escape lane; move an enclosed pullup.
    fp['C13'].SetPosition(v(110,83));fp['R35'].SetPosition(v(130,84.5))
    vias=[]
    def via(x,y,n):
        a=p.PCB_VIA(b);a.SetPosition(v(x,y));a.SetWidth(p.FromMM(.6));a.SetDrill(p.FromMM(.3));a.SetViaType(p.VIATYPE_THROUGH);a.SetLayerPair(p.F_Cu,p.B_Cu);a.SetNetCode(n);b.Add(a);vias.append(a)
    for key,pad in pads.items():
        if not pad.GetNetCode():continue
        n=int(key);x,y=pos(pad);vx=(115.4 if n%2 else 114.4) if n<=12 else (124.6 if n%2 else 125.6)
        segment(b,(x,y),(vx,y),pad.GetNetCode(),0,.2);via(vx,y,pad.GetNetCode())
    # Restore local decoupler/reference-plane accesses that were deliberately removed.
    for f in b.GetFootprints():
        for pad in f.Pads():
            x,y=pos(pad)
            if pad.GetAttribute()!=p.PAD_ATTRIB_SMD or pad.GetNetname() not in ['GND','3V3_PI']:continue
            if f.GetReference() not in ['C13','R35'] and not (110<x<128 and 70<y<82):continue
            if f.GetReference()=='U8':continue
            dy=-.8 if int(pad.GetNumber())%2==0 else .8
            segment(b,(x,y),(x,y+dy),pad.GetNetCode(),0,.2);via(x,y+dy,pad.GetNetCode())
    p.SaveBoard(str(FILE),b);print('FANOUT_SAVED removed='+str(removed),flush=True)
    r.MARGIN=.02;g=r.Grid(b,.2);failed=[]
    for name in sorted(names,key=lambda n:(n not in ['CTRL_RESET_N','H1_SCL','H4_SCL','FACE_R_RIGHT'],n)):
        items=[pad for f in b.GetFootprints() for pad in f.Pads() if pad.GetNetname()==name];n=items[0].GetNetCode();connected=[items[0]];remaining=items[1:]
        def endpoints(a):return [(*cell(*pos(a)),z) for z in ([0] if a.GetAttribute()==p.PAD_ATTRIB_SMD else [0,1,2])]
        while remaining:
            _,a,c=min(((math.dist(pos(a),pos(c)),a,c) for a in connected for c in remaining),key=lambda t:t[0]);path=g.route(endpoints(a),endpoints(c),n)
            if path:g.emit(path,n,pos(a),pos(c))
            else:failed.append({'net':name,'from':pos(a),'to':pos(c)})
            connected.append(c);remaining.remove(c)
        p.SaveBoard(str(FILE),b);print(name+' failures='+str(len(failed)),flush=True)
    b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(FILE),b)
    (ROOT/'validation/controls-fanout-d1.json').write_text(json.dumps({'status':'Needs native DRC','failures':failed,'board_sha256':hashlib.sha256(FILE.read_bytes()).hexdigest()},indent=2)+'\n')
if __name__=='__main__':main()
