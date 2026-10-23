"""Connect only gaps from the latest native DRC, retaining existing routing."""
import json, hashlib
import repair_controls as r
from repair_controls import p, ROOT, FILE, pos, cell

def main():
    r.MARGIN=.01
    b=p.LoadBoard(str(FILE))
    report=json.loads((ROOT/'validation/native-current/controls-repaired-drc.json').read_text())
    byid={obj.m_Uuid.AsString():obj for f in b.GetFootprints() for obj in f.Pads()}
    byid.update({obj.m_Uuid.AsString():obj for obj in b.GetTracks()})
    g=r.Grid(b,.2);out=[]
    def endpoint(item,obj):
        # DRC positions may identify an endpoint of a track, not its midpoint.
        x,y=item['pos']['x'],item['pos']['y']
        zs=[0,1,2] if isinstance(obj,p.PCB_VIA) or isinstance(obj,p.PAD) and obj.GetAttribute()!=p.PAD_ATTRIB_SMD else [r.LAYERS.index(obj.GetLayer())]
        return (x,y),[(*cell(x,y),z) for z in zs]
    for issue in report['unconnected_items']:
        ia,ic=issue['items'];a,c=byid[ia['uuid']],byid[ic['uuid']];n=a.GetNetCode();name=a.GetNetname()
        pa,qa=endpoint(ia,a);pc,qc=endpoint(ic,c)
        print('ATTEMPT',name,qa,qc,[g.free(q,n) for q in qa],[g.free(q,n) for q in qc],flush=True)
        path=g.route(qa,qc,n)
        if path:g.emit(path,n,pa,pc)
        out.append({'net':name,'from':pa,'to':pc,'connected':bool(path)})
        print('RESULT',name,bool(path),flush=True)
        p.SaveBoard(str(FILE),b)
    b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(FILE),b)
    (ROOT/'validation/controls-links-d1.json').write_text(json.dumps({'links':out,'board_sha256':hashlib.sha256(FILE.read_bytes()).hexdigest()},indent=2)+'\n')

if __name__=='__main__':main()
