"""Build the D1 carrier from checked pin contracts. No fabrication exports."""
from pathlib import Path
import json,hashlib
import pcbnew as p
from prepare_electronics import uid
ROOT=Path(__file__).resolve().parents[1]
LIB=Path('C:/Program Files/KiCad/8.0/share/kicad/footprints')
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def xy(x,y):return v(x+120,y+100)
def main():
    design=json.loads((ROOT/'parameters/assembly-d1.json').read_text());model=json.loads((ROOT/'electrical/design-networks.json').read_text());out=ROOT/'electrical/base/nathan-base.kicad_pcb'
    b=p.BOARD();b.SetCopperLayerCount(4);b.GetDesignSettings().SetBoardThickness(p.FromMM(1.6))
    poly=design['base_board_d1']['outline']
    for a,c in zip(poly,poly[1:]+poly[:1]):
        s=p.PCB_SHAPE();s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(xy(*a));s.SetEnd(xy(*c));s.SetWidth(p.FromMM(.1));s.SetLayer(p.Edge_Cuts);b.Add(s)
    components=[c for c in model['components'] if c['board']=='base' and not c.get('virtual')]
    nets={}
    for name in sorted({pin['net'] for c in components for pin in c['pins'] if pin['net']}):n=p.NETINFO_ITEM(b,name);b.Add(n);nets[name]=n
    # Interface connectors are on top, outside the nominal module/battery stack.
    places={'J1':(-54,-24,0,False),'J100':(15,37,90,False),'J101':(-35,-27,0,False),'J102':(-26,-27,0,False),'J400':(-31,35,90,False),
            'U400':(-22,-17,0,True),'U401':(-23,-2,0,True),'U402':(-24,19,0,True)}
    for ref,point in {'C400':(-28,-17),'C401':(-16,-17),'C402':(-22,-21),
      'C403':(-30,-5),'C404':(-30,0),'C405':(-16,1),'C406':(-16,-6),'C407':(-12,-6),
      'C408':(-30,4),'C409':(-34,4),'C410':(-30,-9),'C411':(-34,-9),
      'R400':(-14,6),'R401':(-34,9),'R402':(-29,9),'R403':(-34,13),'R404':(-29,13),
      'R405':(-38,13),'R406':(-25,13),'C412':(-38,9),'C413':(-25,9),'C414':(-34,17),'C415':(-29,17),
      'C416':(-24,24),'C417':(-28,24),'C418':(-20,24),'C419':(-18,18)}.items():places[ref]=(*point,0,True)
    # Every additional component requires an explicit placement record.
    usbplaces=ROOT/'parameters/base-usb-placement.json'
    if usbplaces.exists():places.update(json.loads(usbplaces.read_text()))
    records=[];omitted=[]
    for c in components:
        ref=c['reference']
        if not c['footprint'] or ref not in places:
            omitted.append({'reference':ref,'reason':'Footprint or explicit placement pending'});continue
        lib,name=c['footprint'].split(':');source=(ROOT/'electrical' if lib=='NATHAN_USB' else LIB)/(lib+'.pretty')/(name+'.kicad_mod')
        f=p.FootprintLoad(str(source.parent),name)
        if not f:raise ValueError('Footprint missing: '+str(source))
        x,y,angle,back=places[ref];f.SetReference(ref);f.SetValue(c['value']);f.SetFPID(p.LIB_ID(lib,name));f.SetPosition(xy(x,y));f.SetOrientationDegrees(angle);b.Add(f)
        if back:f.Flip(f.GetPosition(),False)
        f.Reference().SetVisible(False);f.Value().SetVisible(False)
        path=p.KIID_PATH()
        for s in [uid('base/root'),uid('base/sheet/'+c['sheet']),uid('base/'+ref)]:path.push_back(p.KIID(s))
        f.SetPath(path)
        pins={pin['number']:pin['net'] for pin in c['pins']}
        for pad in f.Pads():
            net=pins.get(pad.GetNumber())
            if net:pad.SetNet(nets[net])
        records.append({'ref':ref,'footprint':c['footprint'],'xy':[x,y],'angle':angle,'back':back,'library_sha256':hashlib.sha256(source.read_bytes()).hexdigest()});print('PLACED '+ref,flush=True)
    for i,(x,y) in enumerate(design['base_board_d1']['mounts'],1):
        f=p.FootprintLoad(str(LIB/'MountingHole.pretty'),'MountingHole_2.7mm_M2.5');f.SetReference('H'+str(i));f.SetPosition(xy(x,y));f.Reference().SetVisible(False);f.Value().SetVisible(False);b.Add(f)
    p.SaveBoard(str(out),b)
    (ROOT/'validation/base-placement-d1.json').write_text(json.dumps({'status':'Connected placement; routing separate; missing items listed explicitly','components':records,'omitted':omitted,'board_sha256':hashlib.sha256(out.read_bytes()).hexdigest()},indent=2)+'\n')
    pro=out.with_suffix('.kicad_pro');config=json.loads(pro.read_text());config['board']={'design_settings':{'rules':{'min_clearance':.2,'min_track_width':.2,'min_via_diameter':.6,'min_through_hole_diameter':.3,'min_hole_clearance':.25,'min_copper_edge_clearance':.3}}};pro.write_text(json.dumps(config,indent=2)+'\n')
    print(json.dumps({'footprints':len(b.GetFootprints()),'omitted':omitted}))
if __name__=='__main__':main()
