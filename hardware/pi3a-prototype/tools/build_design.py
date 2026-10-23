"""Generate editable D0 KiCad boards and OpenSCAD parameters without rendering.

Run with KiCad 8's bundled Python. Generated PCB files are placement studies,
not schematics, electrically checked boards or manufacturing deliverables.
"""
from pathlib import Path
import csv
import hashlib
import json
import math
import uuid
import sys
from layout_data import placements, reservations, write_scad
if __name__ == "__main__" and "--allow-native-kicad" not in sys.argv:
    raise SystemExit("Native KiCad generation suspended after the wxWidgets assertion. Use text prevalidation; resume native tools only after the cause and a non-interactive strategy are reviewed.")
import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[1]
LIB = Path(r"C:\Program Files\KiCad\8.0\share\kicad\footprints")
P = json.loads((ROOT/"parameters/design.json").read_text(encoding="utf-8"))
R = json.loads((ROOT/"references/source-geometry.json").read_text(encoding="utf-8"))
OFFSET = (120,100)
FINGERPRINTS = {}


def vec(x,y): return pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y))
def pt(p): return vec(p[0]+OFFSET[0],p[1]+OFFSET[1])


def line(board,a,b,layer=pcb.Dwgs_User,width=.15):
    s=pcb.PCB_SHAPE(); s.SetShape(pcb.SHAPE_T_SEGMENT); s.SetStart(pt(a)); s.SetEnd(pt(b))
    s.SetLayer(layer); s.SetWidth(pcb.FromMM(width)); board.Add(s)


def polygon(board,points,layer):
    for a,b in zip(points,points[1:]+points[:1]): line(board,a,b,layer)


def text(board,value,xy,layer=pcb.Cmts_User,size=1.0):
    t=pcb.PCB_TEXT(board); t.SetText(value); t.SetPosition(pt(xy)); t.SetLayer(layer)
    t.SetTextSize(vec(size,size)); t.SetTextThickness(pcb.FromMM(.15)); board.Add(t)


def footprint(board,lib,name,ref,value,xy,angle=0):
    path=LIB/(lib+".pretty")/(name+".kicad_mod")
    if not path.is_file(): raise FileNotFoundError(path)
    FINGERPRINTS[lib+":"+name]=hashlib.sha256(path.read_bytes()).hexdigest()
    f=pcb.FootprintLoad(str(path.parent),name)
    if not f: raise RuntimeError("Cannot load footprint "+str(path))
    f.SetReference(ref); f.SetValue(value); f.SetPosition(pt(xy)); f.SetOrientationDegrees(angle)
    f.Reference().SetTextSize(vec(.8,.8)); f.Value().SetVisible(False)
    # Leave model references intact; no model is loaded and no 3D view is generated.
    board.Add(f); return f


def reserve(board,ref,value,xy,size):
    # Reservations are board drawings, never empty footprints: the latter were
    # a suspected trigger of an internal KiCad 8 bbox assertion (not proven).
    x,y=xy; w,h=size
    polygon(board,[[x-w/2,y-h/2],[x+w/2,y-h/2],[x+w/2,y+h/2],[x-w/2,y+h/2]],pcb.Dwgs_User)
    text(board,ref+" RESERVE",xy,size=.8)


def board(name):
    b=pcb.BOARD(); b.SetCopperLayerCount(2)
    b.GetDesignSettings().SetBoardThickness(pcb.FromMM(P["boards"][name]["thickness"]))
    polygon(b,P["boards"][name]["outline"],pcb.Edge_Cuts)
    text(b,"NATHAN D0 / "+name.upper()+" / UNROUTED - NOT FOR FABRICATION",[0,-51],size=1.2)
    text(b,"No verified schematic; zero tracks/zones. Dimensions and footprints need review.",[0,-48],size=1)
    text(b,"Codex/OpenAI nathan_bom - 2026-10-22",[0,45],size=.9)
    for i,p in enumerate(P["boards"][name]["mounts"],1):
        footprint(b,"MountingHole","MountingHole_2.7mm_M2.5","H"+str(i),"PROPOSED M2.5",p)
    return b


def connector(b,xy):
    f=footprint(b,"Connector_PinHeader_2.54mm","PinHeader_2x08_P2.54mm_Vertical","J_LINK","PROPOSED 2x08 - MPN TBD",xy,90)
    rows=list(csv.DictReader((ROOT/"pcb/interboard-interface.csv").open(encoding="utf-8")))
    net_by_name={}
    for row in rows:
        if row["net"] not in net_by_name:
            n=pcb.NETINFO_ITEM(b,row["net"]); b.Add(n); net_by_name[row["net"]]=n
    for pad in f.Pads():
        row=next(r for r in rows if r["pin"]==pad.GetNumber()); pad.SetNet(net_by_name[row["net"]])
    # Names represent the proposed cable contract only, not completed circuitry.


def controls():
    b=board("controls")
    positions=placements(P)
    for ref,xy,size in reservations(P): reserve(b,ref,"UNQUALIFIED RESERVATION",xy,size)
    for i,p in enumerate(P["controls"]["switches"],2):
        footprint(b,"Button_Switch_THT","SW_PUSH-12mm","SW"+str(i),"B3F-4055 candidate - VERIFY DRAWING",[p[0]-6.25,p[1]-2.5])
    for i,p in enumerate(P["controls"]["motors"],1):
        driver=P["controls"]["drivers"][i-1]
        footprint(b,"Package_SO","VSSOP-10_3x3mm_P0.5mm","U"+str(i),"DRV2604LDGSR",driver)
        for j,dx in enumerate([-3,3],1):
            footprint(b,"Capacitor_SMD","C_0603_1608Metric","C"+str((i-1)*2+j),"1uF - voltage/tolerance TBD",[driver[0]+dx,driver[1]-4])
    footprint(b,"Package_SO","SOIC-16_3.9x9.9mm_P1.27mm","U6","MCP3008-I/SL",positions["U6"])
    connector(b,positions["J_LINK"])
    for i,(xy,label) in enumerate(zip(P["controls"]["switches"],P["controls"]["switch_labels"]),2):
        text(b,"SW"+str(i)+" "+label,[xy[0],xy[1]-9],size=.7)
    return b


def base():
    b=board("base")
    for ref,key in [("MOD_PI","pi_3_a_plus"),("MOD_UPS","pisugar_3_plus"),("A1","audio")]:
        e=P["envelopes"][key]; reserve(b,ref,key,e["xy"],e["size"][:2])
    footprint(b,"Connector_PinSocket_2.54mm","PinSocket_2x20_P2.54mm_Vertical","J1","Pi header - alignment/height UNVERIFIED",[-24.13,-22.5],90)
    connector(b,[-9,27])
    reserve(b,"USB_IF","USB VBUS limit/reverse block/ESD TBD",[0,-24],[18,10])
    text(b,"PiSugar IN and OUT must remain separate; no direct PC VBUS tie",[0,40],size=.8)
    return b


def scad():
    write_scad(ROOT,P,R)


def main():
    for name,build in [("controls",controls),("base",base)]:
        out=ROOT/"pcb"/name; out.mkdir(parents=True,exist_ok=True)
        b=build(); target=out/("nathan-"+name+".kicad_pcb")
        if not pcb.SaveBoard(str(target),b): raise RuntimeError("Board save failed")
        (out/("nathan-"+name+".kicad_pro")).write_text(json.dumps({"meta":{"filename":"nathan-"+name+".kicad_pro","version":1},"text_variables":{"DESIGN_STATUS":"D0 UNROUTED - NOT FOR FABRICATION","AUTHOR":"Codex/OpenAI nathan_bom"}},indent=2)+"\n",encoding="utf-8")
        print(name+": "+str(len(b.GetFootprints()))+" footprints/reservations, "+str(len(b.GetTracks()))+" tracks")
    scad()
    (ROOT/"references/library-footprints.json").write_text(json.dumps({"library":"KiCad 8.0.2 installed standard footprints","source_root":str(LIB),"sha256":FINGERPRINTS,"note":"Library presence is not manufacturer footprint qualification. No original project custom library reused."},indent=2)+"\n",encoding="utf-8")


if __name__=="__main__": main()
