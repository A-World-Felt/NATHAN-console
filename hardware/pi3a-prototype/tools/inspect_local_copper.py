import json,pcbnew as p
from repair_controls import FILE,pos
b=p.LoadBoard(str(FILE));out=[]
for t in b.GetTracks():
    box=t.GetBoundingBox();x=p.ToMM(box.GetX());y=p.ToMM(box.GetY());w=p.ToMM(box.GetWidth());h=p.ToMM(box.GetHeight())
    if x<107 and x+w>101 and y<109 and y+h>105.5:
        if isinstance(t,p.PCB_VIA):out.append({'kind':'via','net':t.GetNetname(),'xy':pos(t),'uuid':t.m_Uuid.AsString()})
        else:
            a=t.GetStart();c=t.GetEnd();out.append({'kind':'track','net':t.GetNetname(),'a':[p.ToMM(a.x),p.ToMM(a.y)],'c':[p.ToMM(c.x),p.ToMM(c.y)],'layer':t.GetLayerName(),'uuid':t.m_Uuid.AsString()})
print(json.dumps(out,indent=2),flush=True)
