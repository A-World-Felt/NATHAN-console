"""Create native editable assembly and review STEP in the approved portable CAD.

Real PCB STEP geometry is imported. Unknown purchased parts are explicitly
named ALLOCATION and distinguished from designed printable solids.
"""
from pathlib import Path
import json, math, re, hashlib
import FreeCAD as A
import Part
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'mechanical/assembly'
D=json.loads((ROOT/'parameters/design.json').read_text());P=json.loads((ROOT/'parameters/assembly-d1.json').read_text())
profile=json.loads(re.search(r'shell_profile = (.*);',(ROOT/'mechanical/parameters.scad').read_text()).group(1))
# Increase the front bridge locally; the first review identified FR4 intersection
# at X about +/-40..47 mm, rather than an electronic-component collision.
profile=[(x,P.get('front_notch_y',y) if abs(y+36.9126)<.001 else y) for x,y in profile]
doc=A.newDocument('NATHAN_D1_assembly');report={'status':'review assembly; unqualified purchased envelopes explicitly tagged','objects':[],'collisions':[],'input_sha256':{}}
for name in ['parameters/design.json','parameters/assembly-d1.json','mechanical/parameters.scad']:
    report['input_sha256'][name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
def feature(name,label,shape,status,source='Agent design proposal',already_cad=False):
    if not already_cad:
        mirror=A.Matrix();mirror.A22=-1;shape=shape.transformGeometry(mirror)
    print('CREATED '+name,flush=True)
    obj=doc.addObject('Part::Feature',name);obj.Label=label;obj.Shape=shape
    obj.addProperty('App::PropertyString','Qualification','Evidence');obj.Qualification=status
    obj.addProperty('App::PropertyString','Source','Evidence');obj.Source=source
    report['objects'].append({'name':name,'label':label,'status':status,'valid':shape.isValid(),'volume_mm3':shape.Volume})
    return obj
def face(points):
    return Part.Face(Part.Wire(Part.makePolygon([A.Vector(x,y,0) for x,y in points+[points[0]]]).Edges))
def at(shape,z):s=shape.copy();s.translate(A.Vector(0,0,z));return s
def box(size,xy,z):return Part.makeBox(*size,A.Vector(xy[0]-size[0]/2,xy[1]-size[1]/2,z))
def cylinder(radius,height,x,y,z):return Part.makeCylinder(radius,height,A.Vector(x,y,z))
outer=face(profile);innerwire=outer.OuterWire.makeOffset2D(-P['wall'],0,False,False,False);inner=Part.Face(innerwire)
height=P['shell_height'];seam=P['seam_z'];wall=P['wall']
bottom=outer.extrude(A.Vector(0,0,seam)).cut(at(inner.extrude(A.Vector(0,0,seam)),wall))
top=at(outer.extrude(A.Vector(0,0,height-seam)),seam).cut(at(inner.extrude(A.Vector(0,0,height-seam)),seam-wall))
# Individually guided caps preserve ten distinct commands (8 face + 2 centre).
buttons=[]
switch_contact_z=P['controls_pcb_z']+1.6+P['button_switch_height']
for i,(x,y) in enumerate(D['controls']['switches'],2):
    pcbtop=P['controls_pcb_z']+1.6
    switch=box([12,12,4.3],[x,y],pcbtop).fuse(box([3.8,3.8,3],[x,y],pcbtop+4.3))
    feature('Switch_SW'+str(i),'B3F-4055 SW'+str(i)+' / nominal body',switch,'Nominal Omron body/plunger dimensions; simplified terminals and travel, actual part still to qualify','https://components.omron.com/us-en/datasheet_pdf/A070-E1.pdf')
    r=P['button_diameter']/2;top=top.cut(cylinder(r+P['button_guide_clearance_radial'],wall+2,x,y,height-wall-1))
    cap=cylinder(r,3,x,y,P['button_top_z']-3).fuse(cylinder(2.5,P['button_top_z']-3-switch_contact_z,x,y,switch_contact_z))
    cap=cap.fuse(cylinder(r+1,1,x,y,height-wall-6.35))
    buttons.append(feature('Cap_SW'+str(i),'Cap SW'+str(i)+' / printed prototype',cap,'Actuator length and 0.35 mm travel are design allowances; verify preload, guides and overload stop'))
    # Guide ring is part of the cover, with a low retaining shoulder.
    ring=cylinder(r+2.2,5,x,y,height-wall-5).cut(cylinder(r+.35,6,x,y,height-wall-5.5));top=top.fuse(ring)
for x,y in D['controls']['joysticks']:
    top=top.cut(cylinder(P['joystick_allocation']['aperture_radius'],wall+3,x,y,height-wall-1))
# Bounded shoulder openings and separate hinge support arms. They define a
# proposed mechanism, not a verified sensor, spring or overload stop.
for side,x in [('L',-57),('R',57)]:
    for number,z in P['shoulder_levels']:
        top=top.cut(box([22.4,16,8.2 if number==1 else 13.2],[x,-45],z-1.2))
        bottom=bottom.cut(box([22.4,16,8.2 if number==1 else 13.2],[x,-45],z-1.2))
        for sign in [-1,1]:
            bx=x+sign*13
            arm=box([2.8,9,5],[bx,-45.5],z)
            lug=Part.makeCylinder(3.4,2.8,A.Vector(bx-1.4,-42,z+2.5),A.Vector(1,0,0))
            bore=Part.makeCylinder(1.65,4,A.Vector(bx-2,-42,z+2.5),A.Vector(1,0,0))
            top=top.fuse(arm.fuse(lug).cut(bore))
        # The removable shaft also traverses nearby cover material, not only lugs.
        top=top.cut(Part.makeCylinder(1.65,36,A.Vector(x-18,-42,z+2.5),A.Vector(1,0,0)))
bottom_obj=feature('LowerShell','Lower shell / new design',bottom,'Designed solid; no print fit, thermal or strength qualification')
top_obj=feature('UpperShell','Upper shell / new design',top,'Designed solid with button/stick and shoulder openings, proposed hinge supports; USB-C/audio port placement awaits carrier revision')
# Removable stand-offs for each custom PCB. No screw is driven into the battery allocation.
for board,z in [('base',P['base_pcb_z']),('controls',P['controls_pcb_z'])]:
    mounts=P['base_board_d1']['mounts'] if board=='base' else D['boards'][board]['mounts']
    for i,(x,y) in enumerate(mounts,1):
        bottomz=wall if board=='base' else seam
        sh=cylinder(3.6,z-bottomz,x,y,bottomz).cut(cylinder(1.15,z-bottomz+1,x,y,bottomz))
        feature(board+'_Post_'+str(i),board+' post '+str(i),sh,'Proposed pilot hole for M2.5 fastening; material and thread process unqualified')
# Import native board/component STEP from KiCad, then map its Y-up export back to design Y.
for board,filename,z in [('controls','controls-D1.step',P['controls_pcb_z']),('base','base-D1.step',P['base_pcb_z'])]:
    path=OUT/filename
    if not path.exists():raise FileNotFoundError('Export PCB STEP first: '+str(path))
    report['input_sha256'][str(path.relative_to(ROOT)).replace('\\','/')]=hashlib.sha256(path.read_bytes()).hexdigest()
    shape=Part.read(str(path));shape.translate(A.Vector(0,0,z))
    feature('PCB_'+board,'PCB '+board+' D1',shape,'Actual KiCad STEP; standard library bodies may not match exact purchased variants',str(path.relative_to(ROOT)),already_cad=True)
# Purchased-module geometries: nominal PCB sizes plus explicit component allowances.
pi=feature('Pi3A_Board','Pi 3 Model A+ / board-size model',box(P['pi_board_size'],[0,2],P['pi_pcb_z']),'65 x 56 mm board outline from Raspberry Pi; thickness/location proposed; connectors simplified','https://pip.raspberrypi.com/categories/512')
sugar=feature('PiSugar3Plus_Board','PiSugar 3 Plus / board-size model',box(P['pisugar_board_size'],[0,2],P['pisugar_pcb_z']),'65 x 56 mm documented; exact kit revision, contacts and heights unqualified','https://docs.pisugar.com/docs/product-wiki/battery/pisugar3/pisugar-3-series')
battery=P['battery_allocation'];battery_obj=feature('Battery_ALLOCATION','BATTERY SPACE ALLOCATION / measure supplied cell',box(battery['size'],battery['centre_xy'],battery['bottom_z']),battery['status'])
feature('Pi_Connectors_ALLOCATION','Pi connectors / clearance allocation',box([65,18,13.5],[0,-17],P['pi_pcb_z']+1.6),'Reserve only; not exact connector body or orientation')
for i,(x,y) in enumerate(D['controls']['joysticks'],1):
    e=P['joystick_allocation'];shape=box(e['size'],[x,y],e['bottom_z'])
    shape=shape.fuse(cylinder(2,e['shaft_top_from_mount']-e['size'][2],x,y,e['bottom_z']+e['size'][2]))
    feature('Joystick_'+str(i)+'_NOMINAL','RKJXV122400R stick '+str(i)+' / nominal simplified model',shape,e['status'],'https://tech.alpsalpine.com/e/products/detail/RKJXV122400R/')
    cap=cylinder(9,3,x,y,e['bottom_z']+e['shaft_top_from_mount']).cut(cylinder(2,2.5,x,y,e['bottom_z']+e['shaft_top_from_mount']))
    feature('Joystick_cap_'+str(i),'Stick cap '+str(i)+' / printed proposal',cap,'Shaft interface simplified; neutral and 23 degree sweep fit to verify against actual purchased part')
for i,(x,y) in enumerate(P['motor_centres'],1):
    motor=cylinder(P['motor_diameter']/2,P['motor_height'],x,y,P['motor_bottom_z'])
    feature('LRA_'+str(i),'LRA '+str(i)+' / VG0832013D nominal body',motor,P['motor_status'],'https://www.vybronics.com/linear-resonant-actuators-lras/v-g0832013d')
    saddle=cylinder(5.5,P['motor_bottom_z']-wall+.5,x,y,wall).cut(cylinder(4.15,1,x,y,P['motor_bottom_z']))
    feature('Motor_saddle_'+str(i),'Motor saddle '+str(i)+' / prototype',saddle,'Adhesive gap, vibration coupling and compliance unqualified')
# Four distinct shoulder levers with pivot bores, printable proposal rather than cubes.
for side,x in [('L',-57),('R',57)]:
    for number,z in P['shoulder_levels']:
        pts=[(x-10,-49),(x+10,-49),(x+10,-41),(x+6,-38),(x-6,-38),(x-10,-41)]
        lever=at(face(pts).extrude(A.Vector(0,0,5 if number==1 else 10)),z)
        bore=Part.makeCylinder(1.65,24,A.Vector(x-12,-42,z+2.5),A.Vector(1,0,0));lever=lever.cut(bore)
        feature('Lever_'+side+str(number),side+str(number)+' shoulder lever / prototype',lever,P['shoulder_status'])
        shaft=Part.makeCylinder(1.5,32,A.Vector(x-16,-42,z+2.5),A.Vector(1,0,0))
        feature('Shaft_'+side+str(number),side+str(number)+' pivot shaft / proposed 3 mm',shaft,'Dimensional proposal; retaining feature, material, spring and shaft purchase reference not qualified')
# Exact solid interference checks for the supplied representations, not a fit certification.
check=[o for o in doc.Objects if hasattr(o,'Shape') and not o.Shape.isNull()]
doc.recompute();doc.saveAs(str(OUT/'nathan-D1-review.FCStd'));print('NATIVE_SAVED',flush=True)
for i,a in enumerate(check):
    for c in check[i+1:]:
        if not a.Shape.BoundBox.intersect(c.Shape.BoundBox):continue
        if a.Name.startswith('PCB_') or c.Name.startswith('PCB_'):
            report['collisions'].append({'a':a.Name,'b':c.Name,'type':'bounding-box screening only; exact PCB interference not evaluated in this bounded pass'});continue
        overlap=a.Shape.common(c.Shape)
        if overlap.Volume>.1:report['collisions'].append({'a':a.Name,'b':c.Name,'volume_mm3':round(overlap.Volume,3),'interpretation':'Review intersection; some retention/support interfaces are intentional. Envelope intersections are risks, not measured part collisions.'})
doc.recompute();OUT.mkdir(exist_ok=True,parents=True)
doc.saveAs(str(OUT/'nathan-D1-review.FCStd'))
Part.export(check,str(OUT/'nathan-D1-review.step'))
report['native_file']='mechanical/assembly/nathan-D1-review.FCStd';report['step_file']='mechanical/assembly/nathan-D1-review.step';report['all_shapes_valid']=all(x['valid'] for x in report['objects'])
(ROOT/'validation/freecad-assembly-d1.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'objects':len(report['objects']),'all_shapes_valid':report['all_shapes_valid'],'intersections_for_review':len(report['collisions']),'native_file':report['native_file']}),flush=True)
