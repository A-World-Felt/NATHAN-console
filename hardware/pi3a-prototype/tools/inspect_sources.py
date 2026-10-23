"""Read only the explicitly authorised NATHAN-console geometry; no rendering."""
from pathlib import Path
import hashlib
import json
import math
import re
import struct

OUT = Path(__file__).resolve().parents[1]
SOURCE = Path(r"C:\Projects\Ecole\NATHAN\NATHAN-console")


def stl(path):
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + 50 * count:
        raise ValueError("Expected binary STL: " + path.name)
    faces = []
    for i in range(count):
        values = struct.unpack_from("<12fH", data, 84 + i * 50)
        faces.append([values[j:j + 3] for j in (3, 6, 9)])
    verts = [v for t in faces for v in t]
    lo = [min(v[i] for v in verts) for i in range(3)]
    hi = [max(v[i] for v in verts) for i in range(3)]
    return faces, {"file": str(path.relative_to(SOURCE)), "sha256": hashlib.sha256(data).hexdigest(),
                   "triangles": count, "min": lo, "max": hi, "span": [hi[i]-lo[i] for i in range(3)],
                   "unit_status": "STL is unitless; millimetres assumed for provisional mechanical study"}


def section(faces, z):
    segments = set()
    for face in faces:
        hits = []
        for a, b in zip(face, face[1:] + face[:1]):
            if (a[2] < z < b[2]) or (b[2] < z < a[2]):
                q = (z - a[2]) / (b[2] - a[2])
                hits.append(tuple(round(a[k] + q*(b[k]-a[k]), 4) for k in (0, 1)))
        if len(hits) == 2 and hits[0] != hits[1]:
            segments.add(tuple(sorted(hits)))
    neighbours = {}
    for a,b in segments:
        neighbours.setdefault(a, set()).add(b)
        neighbours.setdefault(b, set()).add(a)
    if any(len(v) != 2 for v in neighbours.values()):
        raise ValueError("Section is not a collection of closed loops")
    loops = []
    remaining = set(neighbours)
    while remaining:
        start = min(remaining); loop = [start]; last = None; cur = start
        while True:
            nxt = sorted(neighbours[cur] - ({last} if last else set()))[0]
            if nxt == start: break
            loop.append(nxt); last, cur = cur, nxt
        remaining.difference_update(loop); loops.append(loop)
    def area(loop):
        return sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(loop,loop[1:]+loop[:1]))/2
    loops.sort(key=lambda x: abs(area(x)), reverse=True)
    outer = loops[0]
    if area(outer) < 0: outer.reverse()
    # Remove nearly collinear samples, preserving the measured silhouette.
    changed = True
    while changed and len(outer) > 12:
        changed = False
        for i in range(len(outer)):
            a,b,c = outer[i-1],outer[i],outer[(i+1)%len(outer)]
            distance = abs((c[0]-a[0])*(a[1]-b[1])-(a[0]-b[0])*(c[1]-a[1])) / max(math.dist(a,c), 1e-9)
            if distance < .15:
                outer.pop(i); changed = True; break
    lo = [min(v[k] for v in outer) for k in (0,1)]
    hi = [max(v[k] for v in outer) for k in (0,1)]
    center = [(a+b)/2 for a,b in zip(lo,hi)]
    points = [[round(v[k]-center[k],4) for k in (0,1)] for v in outer]
    return {"section_z_source_units": z, "closed_loops": len(loops), "outer_points_centered": points,
            "outer_span_source_units": [hi[k]-lo[k] for k in (0,1)], "outer_area_source_units2": abs(area(outer)),
            "simplification_tolerance_source_units": .15}


def sexp(text):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text)
    stack = [[]]
    for token in tokens:
        if token == "(":
            new = []; stack[-1].append(new); stack.append(new)
        elif token == ")": stack.pop()
        else: stack[-1].append(token[1:-1] if token.startswith('"') else token)
    if len(stack) != 1: raise ValueError("Unbalanced s-expression")
    return stack[0][0]


def child(node, key, default=None):
    return next((x for x in node if isinstance(x,list) and x and x[0]==key),default)


def main():
    report = {"source_root": str(SOURCE), "read_only": True, "stl": [], "boards": []}
    candidate_sections=[]
    for name in ["NATHAN-Front-console.STL","NATHAN-Middle-console.STL","NATHAN-Rear-console.STL"]:
        faces, info = stl(SOURCE/"3D Print Models"/name); report["stl"].append(info)
        if "Front" in name or "Middle" in name:
            sections=[]
            for fraction in [.01,.05,.10,.20,.35,.50,.65,.80,.90,.95,.99]:
                try:
                    s=section(faces,info["min"][2]+fraction*(info["max"][2]-info["min"][2]))
                    s["source_file"]=info["file"]
                    sections.append(s)
                except ValueError:
                    continue
            candidate_sections.extend(sections)
    report["legacy_outline"] = max(candidate_sections,key=lambda s:s["outer_area_source_units2"])
    report["section_selection"] = "Largest enclosed area among 22 attempted horizontal sections of Front/Middle; outline only, no old solid imported."
    for rel in ["CAD_Files/PCB/NATHAN-pcb.kicad_pcb", "CAD_Files/PCB/NATHAN-console_KiCAD.kicad_pro/NATHAN-console_KiCAD.kicad_pro.kicad_pcb"]:
        path=SOURCE/rel; data=path.read_bytes(); tree=sexp(data.decode("utf-8-sig"))
        fps=[]; edgepoints=[]
        for node in tree:
            if not isinstance(node,list) or not node: continue
            if node[0]=="footprint":
                props={x[1]:x[2] for x in node if isinstance(x,list) and len(x)>2 and x[0]=="property"}
                fps.append({"library_id":node[1],"reference":props.get("Reference"),"value":props.get("Value"),"at":child(node,"at")})
            if node[0].startswith("gr_") and child(node,"layer")==["layer","Edge.Cuts"]:
                for key in ("start","mid","end","center"):
                    p=child(node,key)
                    if p: edgepoints.append([float(x) for x in p[1:3]])
        report["boards"].append({"file":rel,"sha256":hashlib.sha256(data).hexdigest(),"version":child(tree,"version"),
                                 "footprints":fps,"edge_control_point_bounds_mm": [[min(p[k] for p in edgepoints) for k in (0,1)],[max(p[k] for p in edgepoints) for k in (0,1)]] if edgepoints else None,
                                 "note":"Control-point bounds do not include every possible arc extremum."})
    (OUT/"references").mkdir(parents=True,exist_ok=True)
    (OUT/"references"/"source-geometry.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"section_points":len(report["legacy_outline"]["outer_points_centered"]),"section_span":report["legacy_outline"]["outer_span_source_units"],"boards":[{"file":b["file"],"footprints":len(b["footprints"]),"bounds":b["edge_control_point_bounds_mm"]} for b in report["boards"]]}))


if __name__ == "__main__": main()
