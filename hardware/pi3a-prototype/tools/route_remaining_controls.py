"""Join existing copper components, rather than re-searching already-routed escapes."""
import json,math,hashlib
import repair_controls as r
from repair_controls import p,ROOT,FILE,pos
def main():
    b=p.LoadBoard(str(FILE));r.MARGIN=.01;g=r.Grid(b,.2);failed=[]
    names={pad.GetNetname() for f in b.GetFootprints() if f.GetReference()=='U8' for pad in f.Pads() if pad.GetNetCode() and pad.GetNetname() not in ['GND','3V3_PI']};names.add('FACE_R_RIGHT')
    for name in sorted(names):
        pads=[pad for f in b.GetFootprints() for pad in f.Pads() if pad.GetNetname()==name];n=pads[0].GetNetCode();connected=[pads[0]];remaining=pads[1:]
        while remaining:
            _,a,c=min(((math.dist(pos(a),pos(c)),a,c) for a in connected for c in remaining),key=lambda t:t[0]);qa=r.connected_endpoints(b,a);qc=r.connected_endpoints(b,c)
            if set(qa)&set(qc):path=[next(iter(set(qa)&set(qc)))]
            else:path=g.route(qa,qc,n)
            if path and len(path)>1:g.emit(path,n)
            elif path is None:failed.append({'net':name,'from':pos(a),'to':pos(c),'source_nodes':len(qa),'target_nodes':len(qc)})
            connected.append(c);remaining.remove(c)
        p.SaveBoard(str(FILE),b);print(name+' failures='+str(len(failed)),flush=True)
    b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(FILE),b)
    (ROOT/'validation/controls-connected-copper-d1.json').write_text(json.dumps({'status':'Native DRC still required','failures':failed,'board_sha256':hashlib.sha256(FILE.read_bytes()).hexdigest()},indent=2)+'\n')
if __name__=='__main__':main()
