"""Safe text-only preflight. No pcbnew, wxWidgets, GUI, render or network."""
from pathlib import Path
import ast
import hashlib
import json
import math
import re
from inspect_sources import sexp, child
from layout_data import placements, scad_values

ROOT=Path(__file__).resolve().parents[1]


def walk(node):
    if isinstance(node,list):
        yield node
        for n in node: yield from walk(n)


def board(path):
    data=path.read_bytes(); tree=sexp(data.decode("utf-8"))
    if tree[0]!="kicad_pcb": raise ValueError("Not a KiCad PCB")
    values=[]; numeric_keys={"at","start","end","mid","center","size","offset","xyz"}
    for n in walk(tree):
        if n and n[0] in numeric_keys:
            for value in n[1:]:
                if isinstance(value,str):
                    try: values.append(float(value))
                    except ValueError: pass
    bad=[v for v in values if not math.isfinite(v) or abs(v)>1000]
    footprints=[n for n in tree if isinstance(n,list) and n and n[0]=="footprint"]
    refs=[]; empty=[]; courtyard_boxes=[]
    for f in footprints:
        reference=next((n[2] for n in f if isinstance(n,list) and len(n)>2 and n[:2]==["property","Reference"]),"?")
        refs.append(reference)
        if not any(isinstance(n,list) and n and n[0]=="pad" for n in f): empty.append(reference)
        origin=child(f,"at"); x,y=float(origin[1]),float(origin[2]); angle=float(origin[3]) if len(origin)>3 else 0
        angle=-math.radians(angle); points=[]
        for n in f:
            if not isinstance(n,list) or not n: continue
            if n[0] in {"fp_line","fp_rect","fp_circle","fp_arc"} and child(n,"layer")==["layer","F.CrtYd"]:
                for key in ["start","end","mid","center"]:
                    p=child(n,key)
                    if p:
                        a,b=float(p[1]),float(p[2]); points.append((x+a*math.cos(angle)-b*math.sin(angle),y+a*math.sin(angle)+b*math.cos(angle)))
        if points:
            courtyard_boxes.append((reference,min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)))
    overlaps=[]
    for i,a in enumerate(courtyard_boxes):
        for b in courtyard_boxes[i+1:]:
            if max(a[1],b[1])<min(a[3],b[3])-1e-6 and max(a[2],b[2])<min(a[4],b[4])-1e-6: overlaps.append([a[0],b[0]])
    return {"file":str(path.relative_to(ROOT)),"sha256":hashlib.sha256(data).hexdigest(),"sexpression_balanced":True,
            "geometry_value_range":[min(values),max(values)],"invalid_or_abs_over_1000_values":bad,"empty_footprints":empty,
            "footprint_count":len(footprints),"duplicate_references":sorted({r for r in refs if refs.count(r)>1}),
            "tracks":sum(isinstance(n,list) and bool(n) and n[0] in {"segment","arc","via"} for n in tree),
            "zones":sum(isinstance(n,list) and bool(n) and n[0]=="zone" for n in tree),
            "front_courtyard_aabb_overlaps":overlaps,
            "limitations":"AABB test is only a conservative 2D screen on explicit front courtyards. Does not qualify reserved modules, circuitry, solder tails or 3D fit."}


def main():
    report={"mode":"TEXT ONLY - no KiCad native API","native_validation":"suspended after overflow assertion; exact cause not established",
            "boards":[board(ROOT/"pcb"/name/("nathan-"+name+".kicad_pcb")) for name in ["controls","base"]]}
    p=json.loads((ROOT/"parameters/design.json").read_text(encoding="utf-8"))
    report["parameters_json_valid"]=True
    report["nominal_width_le_160"]=p["shell"]["width"]<=160
    report["openings_and_bosses_disabled"]=not any(p["shell"][k] for k in ["enable_control_cutouts","enable_port_cutouts","enable_mounting_bosses"])
    # The requested face layout must change the PCB and enclosure, not labels alone.
    c=p['controls']; group_errors=[]
    for side,group in c['face_groups'].items():
        cx,cy=group['centre']; radius=group['radius']
        expected={(cx,cy-radius),(cx+radius,cy),(cx,cy+radius),(cx-radius,cy)}
        actual={tuple(c['switches'][i]) for i in group['indices']}
        if len(group['indices'])!=4 or actual!=expected: group_errors.append(side)
    pcb=sexp((ROOT/'pcb/controls/nathan-controls.kicad_pcb').read_text(encoding='utf-8'))
    expected=placements(p); mismatches=[]
    for f in pcb:
        if isinstance(f,list) and f and f[0]=='footprint':
            ref=next(n[2] for n in f if isinstance(n,list) and n[:2]==['property','Reference'])
            pos=child(f,'at'); actual=[float(pos[1])-120,float(pos[2])-100]
            if ref not in expected or any(abs(a-b)>1e-6 for a,b in zip(actual,expected[ref])): mismatches.append(ref)
    r=json.loads((ROOT/'references/source-geometry.json').read_text(encoding='utf-8'))
    generated=(ROOT/'mechanical/parameters.scad').read_text(encoding='utf-8')
    scad_mismatch=[key for key,value in scad_values(p,r).items() if key+' = '+json.dumps(value)+';' not in generated]
    report['layout_consistency']={'cardinal_group_errors':group_errors,'face_count':8,'central_count':len(c['central_switch_indices']),
        'pcb_origin_mismatches':mismatches,'scad_parameter_mismatches':scad_mismatch,
        'sticks_symmetric_and_below_faces':c['joysticks'][0][0]==-c['joysticks'][1][0] and c['joysticks'][0][1]==c['joysticks'][1][1] and all(j[1]>max(s[1] for s in c['switches'][:8]) for j in c['joysticks']),
        'shoulders_stacked_left_right':all(c['shoulders'][side]['bumper']['xy']==c['shoulders'][side]['trigger']['xy'] and c['shoulders'][side]['bumper']['z']>c['shoulders'][side]['trigger']['z'] for side in ['left','right']),
        'bom_delta':c['bom_delta']}
    if group_errors or mismatches or scad_mismatch: raise ValueError('Inconsistent layout sources')
    # Delimiter checks are explicitly not an OpenSCAD compilation.
    scad={}
    for f in (ROOT/"mechanical").glob("*.scad"):
        s=re.sub(r'//[^\n]*','',f.read_text(encoding="utf-8"))
        s=re.sub(r'"(?:\\.|[^"\\])*"','""',s)
        stack=[]; match={')':'(',']':'[','}':'{'}
        for c in s:
            if c in '([{': stack.append(c)
            elif c in ')]}':
                if not stack or stack.pop()!=match[c]: raise ValueError("Unbalanced delimiters in "+f.name)
        if stack: raise ValueError("Unbalanced delimiters in "+f.name)
        scad[f.name]="balanced delimiters only; not compiled"
    report["scad_text_checks"]=scad
    report["python_syntax_checks"]={}
    for f in (ROOT/"tools").glob("*.py"):
        ast.parse(f.read_text(encoding="utf-8"),filename=f.name)
        report["python_syntax_checks"][f.name]="AST parse only; not executed by this check"
    (ROOT/"validation/text-preflight.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__=="__main__": main()
