"""Suspended native checks: KiCad may show an assertion dialog even in CLI use."""
from pathlib import Path
import json
import math
import sys
if __name__ == "__main__" and "--allow-native-kicad" not in sys.argv:
    raise SystemExit("Native validation suspended: previous run triggered a wxWidgets overflow assertion. Run preflight_text.py instead. Do not bypass this guard without reviewing the incident.")
import pcbnew as pcb

ROOT=Path(__file__).resolve().parents[1]
P=json.loads((ROOT/"parameters/design.json").read_text(encoding="utf-8"))
R=json.loads((ROOT/"references/source-geometry.json").read_text(encoding="utf-8"))


def inside(point,poly):
    x,y=point; result=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if (a[1]>y)!=(b[1]>y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]: result=not result
    return result


def distance(p,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]
    t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy)))
    return math.dist(p,[a[0]+t*dx,a[1]+t*dy])


def main():
    out={"status":"D0 placement checks only; NOT an electrical or manufacturing qualification", "boards":{},"mechanical":{},
         "not_executed":["OpenSCAD compile/render (not installed in searched locations; rendering forbidden)","ERC (no electrical schematic yet)","3D interference analysis","fabrication exports","hardware measurements","ergonomics tests"]}
    for name in ["controls","base"]:
        path=ROOT/"pcb"/name/("nathan-"+name+".kicad_pcb")
        b=pcb.LoadBoard(str(path))
        if b is None: raise RuntimeError("Native board read failed")
        refs=[f.GetReference() for f in b.GetFootprints()]
        outside=[]; min_edge=999
        poly=P["boards"][name]["outline"]
        for f in b.GetFootprints():
            for pad in f.Pads():
                x,y=pcb.ToMM(pad.GetPosition().x)-120,pcb.ToMM(pad.GetPosition().y)-100
                if not inside([x,y],poly): outside.append(f.GetReference()+"."+pad.GetNumber())
                min_edge=min(min_edge,min(distance([x,y],a,c) for a,c in zip(poly,poly[1:]+poly[:1])))
        report=ROOT/"validation"/(name+"-drc.txt")
        drc=pcb.WriteDRCReport(b,str(report),pcb.EDA_UNITS_MILLIMETRES,True)
        out["boards"][name]={"native_load":True,"footprints_and_reservations":len(refs),"duplicate_refs":sorted({r for r in refs if refs.count(r)>1}),
                               "pads_centres_outside_outline":outside,"min_pad_centre_to_edge_mm":round(min_edge,3),"tracks":len(b.GetTracks()),"zones":len(b.Zones()),
                               "drc_report_generated":bool(drc),"drc_note":"Read report; generation success is not DRC pass. Unassigned circuitry is not tested by DRC."}
        print(name+" native read complete; DRC report "+str(bool(drc)),flush=True)
    profile=R["legacy_outline"]["outer_points_centered"]
    scale=P["shell"]["width"]/R["legacy_outline"]["outer_span_source_units"][0]
    profile=[[x*scale,y*scale] for x,y in profile]
    outside={name:[p for p in P["boards"][name]["outline"] if not inside(p,profile)] for name in ["controls","base"]}
    out["mechanical"]={"nominal_profile_width_mm":P["shell"]["width"],"nominal_profile_length_mm":round((max(p[1] for p in profile)-min(p[1] for p in profile)),3),
                       "allocated_height_mm":P["shell"]["height"],"width_le_160":P["shell"]["width"]<=160,
                       "pcb_vertices_outside_full_size_profile":outside,
                       "joystick_reserved_top_z_mm":P["boards"]["controls"]["z"]+P["boards"]["controls"]["thickness"]+P["envelopes"]["joystick"]["size"][2],
                       "note":"Plan-only check at full-size profile. Does not validate wall clearance, Z taper, connector movement, fasteners, battery or motor mounting."}
    # Deliberately do not classify the assembly as collision-free: the uncertain
    # modules, THT tails, cable bends and motor attachment do not have qualified shapes.
    out["known_open_items"]=["Component and reserved-area overlaps must be resolved after the schematic/footprint choices",
                              "LRA attachment height and clearance to through-hole tails unqualified",
                              "Pi/PiSugar fixing and pogo/header alignment unqualified",
                              "USB VBUS source current and reverse flow unresolved",
                              "Case openings/bosses deliberately disabled"]
    (ROOT/"validation/checks.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")


if __name__=="__main__":
    (ROOT/"validation").mkdir(parents=True,exist_ok=True)
    main()
