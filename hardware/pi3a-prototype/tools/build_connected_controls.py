"""Build D1 controls from the same pin model as the checked schematic.

Prototype: four copper layers; inner GND / 3V3_PI planes are design choices.
No fabrication outputs. Run with the installed KiCad 8 Python runtime.
"""
from pathlib import Path
import json, hashlib
import pcbnew as p
from prepare_electronics import uid

ROOT=Path(__file__).resolve().parents[1]
LIB=Path(r'C:/Program Files/KiCad/8.0/share/kicad/footprints')
D=json.loads((ROOT/'parameters/design.json').read_text())
E=json.loads((ROOT/'electrical/design-networks.json').read_text())
OUT=ROOT/'electrical/controls/nathan-controls.kicad_pcb'
def v(x,y): return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def xy(x,y): return v(x+120,y+100)
def line(b,a,c,layer):
    s=p.PCB_SHAPE();s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(xy(*a));s.SetEnd(xy(*c));s.SetWidth(p.FromMM(.1));s.SetLayer(layer);b.Add(s)

def main():
    b=p.BOARD();b.SetCopperLayerCount(4);b.GetDesignSettings().SetBoardThickness(p.FromMM(1.6))
    outline=D['boards']['controls']['outline']
    for a,c in zip(outline,outline[1:]+outline[:1]):line(b,a,c,p.Edge_Cuts)
    components=[c for c in E['components'] if c['board']=='controls' and not c.get('virtual')]
    nets={}
    for name in sorted({pin['net'] for c in components for pin in c['pins'] if pin['net']}):
        n=p.NETINFO_ITEM(b,name);b.Add(n);nets[name]=n
    pos={'J100':(-9,39,90),'U7':(-30,28,0),'C15':(-23,33,90),'U6':(20,25,0),'C16':(25,22,90),'C17':(25,26,90),'U8':(0,-24,0),'C18':(6,-24,90),
         'J20':(-47,19,0),'J21':(32,19,0),'J22':(-25,-30,0),'J23':(21,-30,0),'J24':(-36,-32,0),'J25':(32,-32,0),
         'PS2':(0,-3,0),'L1':(4,-3,0),'C30':(-3,-3,90),'C31':(10,1,90),'R60':(3,1,0),'R61':(0,1,0),
         'R11':(-5,-16,90),'R12':(-2.5,-16,90),'R13':(0,-16,90),'R14':(2.5,-16,90),'R15':(5,-16,90),'C13':(-10,-17,90),'C14':(-7.5,-20,90)}
    for i,point in enumerate(D['controls']['switches'],2):pos['SW'+str(i)]=(point[0]-6.25,point[1]-2.5,0)
    for i in range(14):pos['R'+str(30+i)]=(-6+(i%7)*2,-11+(i//7)*3.5,90)
    pos['R35']=(10,-17.5,90)
    for i in range(6):
        pos['R'+str(50+i)]=(12,17+i*2.5,0);pos['C'+str(20+i)]=(8,17+i*2.5,0)
    for i,x in enumerate([-26,-13,0,13,26],1):
        pos['U'+str(i)]=(x,7,0)
        pos['C'+str(i*2-1)]=(x-4.8,5,90);pos['C'+str(i*2)]=(x+4.8,5,90)
        pos['R'+str(i*2-1)]=(x-4.8,9,90);pos['R'+str(i*2)]=(x-4.8,12,90)
        pos['J'+str(i+1)]=(x+2,12,0)
    fp_records=[]
    for c in components:
        ref=c['reference'];lib,name=c['footprint'].split(':');source=LIB/(lib+'.pretty')/(name+'.kicad_mod')
        print('LOAD '+ref+' '+name,flush=True)
        f=p.FootprintLoad(str(source.parent),name)
        if not f:raise ValueError(str(source))
        f.SetReference(ref);f.SetValue(c['value']);f.SetFPID(p.LIB_ID(lib,name));f.SetPosition(xy(*pos[ref][:2]));f.SetOrientationDegrees(pos[ref][2])
        f.Reference().SetVisible(False);f.Value().SetVisible(False)
        path=p.KIID_PATH()
        for part in [uid('controls/root'),uid('controls/sheet/'+c['sheet']),uid('controls/'+ref)]:path.push_back(p.KIID(part))
        f.SetPath(path)
        pinmap={pin['number']:pin['net'] for pin in c['pins']}
        for pad in f.Pads():
            name=pinmap.get(pad.GetNumber())
            if name:pad.SetNet(nets[name])
        b.Add(f);fp_records.append({'ref':ref,'footprint':c['footprint'],'xy':pos[ref][:2],'angle':pos[ref][2],'sha256_library':hashlib.sha256(source.read_bytes()).hexdigest()})
        print('PLACED '+ref,flush=True)
    for i,point in enumerate(D['boards']['controls']['mounts'],1):
        f=p.FootprintLoad(str(LIB/'MountingHole.pretty'),'MountingHole_2.7mm_M2.5');f.SetReference('H'+str(i));f.SetPosition(xy(*point));f.Reference().SetVisible(False);f.Value().SetVisible(False);b.Add(f)
    t=p.PCB_TEXT(b);t.SetText('NATHAN D1 CONTROLS / PROTOTYPE - NOT FOR FABRICATION');t.SetPosition(xy(0,48));t.SetLayer(p.Cmts_User);t.SetTextSize(v(1,1));b.Add(t)
    p.SaveBoard(str(OUT),b)
    (ROOT/'validation/controls-placement-d1.json').write_text(json.dumps({'components':fp_records,'copper_layers':4,'status':'prototype component choices; native DRC and routing reported separately','signal_width_mm':.2,'clearance_mm':.15,'plane_layers':['In1.Cu GND','In2.Cu 3V3_PI']},indent=2)+'\n')
    # Explicit rules, not the more permissive defaults silently selected by a tool.
    pro=OUT.with_suffix('.kicad_pro');j=json.loads(pro.read_text());j['board']={'design_settings':{'rules':{'min_clearance':.15,'min_track_width':.15,'min_via_diameter':.6,'min_through_hole_diameter':.3,'min_hole_clearance':.25,'min_copper_edge_clearance':.3}}};pro.write_text(json.dumps(j,indent=2)+'\n')
    print(json.dumps({'board':str(OUT),'components':len(components),'footprints':len(b.GetFootprints()),'nets':len(nets),'tracks':len(b.GetTracks())}))

if __name__=='__main__':main()
