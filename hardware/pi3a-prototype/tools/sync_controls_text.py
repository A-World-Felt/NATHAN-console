"""Synchronise the D0 controls layout in text, without importing KiCad.

Keeps embedded footprints/pads/nets intact; moves only footprint origins and
rebuilds board drawings from design.json. Never edits the base or consultation.
"""
from pathlib import Path
import hashlib
import json
import re
import uuid
from inspect_sources import sexp, child
from layout_data import placements, reservations, write_scad

ROOT=Path(__file__).resolve().parents[1]


def blocks(s):
    depth=0; quoted=False; escape=False; start=None; out=[]
    for i,c in enumerate(s):
        if quoted:
            if escape: escape=False
            elif c=='\\': escape=True
            elif c=='"': quoted=False
            continue
        if c=='"': quoted=True
        elif c=='(':
            if depth==1: start=i
            depth+=1
        elif c==')':
            depth-=1
            if depth==1: out.append((start,i+1))
            if depth<0: raise ValueError('Unbalanced file')
    if depth or quoted: raise ValueError('Unbalanced file')
    return out


def uid(key): return str(uuid.uuid5(uuid.NAMESPACE_URL,'nathan-d0-layout/'+key))
def num(v): return format(v,'.6f').rstrip('0').rstrip('.') if v else '0'
def xy(p): return num(p[0]+120)+' '+num(p[1]+100)


def drawings(p):
    out=[]
    def line(a,b,layer,key):
        out.append(f'(gr_line (start {xy(a)}) (end {xy(b)}) (stroke (width 0.15) (type default)) (layer "{layer}") (uuid "{uid(key)}"))')
    def label(value,pos,key,size=.8):
        out.append(f'(gr_text {json.dumps(value)} (at {xy(pos)} 0) (layer "Cmts.User") (uuid "{uid(key)}") (effects (font (size {size} {size}) (thickness 0.15))))')
    poly=p['boards']['controls']['outline']
    for i,(a,b) in enumerate(zip(poly,poly[1:]+poly[:1])): line(a,b,'Edge.Cuts','edge'+str(i))
    for ref,pos,size in reservations(p):
        x,y=pos; w,h=size; poly=[[x-w/2,y-h/2],[x+w/2,y-h/2],[x+w/2,y+h/2],[x-w/2,y+h/2]]
        for i,(a,b) in enumerate(zip(poly,poly[1:]+poly[:1])): line(a,b,'Dwgs.User',ref+str(i))
        label(ref+' RESERVE',pos,'label-'+ref)
    label('NATHAN D0 / CONTROLS / UNROUTED - NOT FOR FABRICATION',[0,-58],'title',1.2)
    label('8 FACE + 2 CENTRAL; L1/R1 EXTRA; L2/R2 SENSORS TBD',[0,-55],'layout',1)
    label('No verified schematic; dimensions and footprints need review.',[0,-52],'warning',1)
    label('Codex/OpenAI nathan_bom - PS4-style layout proposal',[0,52],'author',.9)
    for i,(pos,name) in enumerate(zip(p['controls']['switches'],p['controls']['switch_labels']),2):
        label('SW'+str(i)+' '+name,[pos[0],pos[1]-9],'button-'+str(i),.7)
    return out


def main():
    p=json.loads((ROOT/'parameters/design.json').read_text(encoding='utf-8'))
    r=json.loads((ROOT/'references/source-geometry.json').read_text(encoding='utf-8'))
    path=ROOT/'pcb/controls/nathan-controls.kicad_pcb'; before=path.read_bytes(); s=before.decode('utf-8')
    positions=placements(p); revised=[]; seen=[]
    for start,end in blocks(s):
        raw=s[start:end]; tree=sexp(raw); kind=tree[0]
        if kind.startswith('gr_'): continue
        if kind=='footprint':
            ref=next(n[2] for n in tree if isinstance(n,list) and n[:2]==['property','Reference'])
            if ref not in positions: raise ValueError('Unexpected footprint '+ref)
            target=positions[ref]
            raw,n=re.subn(r'(?m)^(\s*)\(at ([^()]*)\)',lambda m:m.group(1)+'(at '+xy(target)+(' 90' if ref=='J_LINK' else '')+')',raw,count=1)
            if n!=1: raise ValueError('Missing footprint origin')
            seen.append(ref)
        revised.append(raw)
    if set(seen)!=set(positions): raise ValueError('Missing expected footprints')
    result='(kicad_pcb\n\t'+'\n\t'.join(revised+drawings(p))+'\n)\n'
    # Parse before replacing; exact embedded pad/copper records remain unchanged.
    sexp(result)
    path.write_text(result,encoding='utf-8',newline='\n')
    write_scad(ROOT,p,r)
    report={'mode':'standard-library text update only','layout':p['controls']['layout_revision'],
            'controls_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'moved_footprint_count':len(seen),'notes':'8 face + 2 central switches; shoulders are drawings/reserves, no added pads. Base and consultation untouched.'}
    (ROOT/'validation/layout-update.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
