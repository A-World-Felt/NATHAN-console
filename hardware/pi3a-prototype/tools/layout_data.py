"""Shared layout calculations; standard library only, no CAD runtime."""
import json


def placements(p):
    c = p['controls']
    out = {'H'+str(i):xy for i,xy in enumerate(p['boards']['controls']['mounts'],1)}
    out.update({'SW'+str(i):[xy[0]-6.25,xy[1]-2.5] for i,xy in enumerate(c['switches'],2)})
    out.update({'U'+str(i):xy for i,xy in enumerate(c['drivers'],1)})
    for i,xy in enumerate(c['drivers']):
        for j,dx in enumerate([-3,3],1): out['C'+str(i*2+j)]=[xy[0]+dx,xy[1]-4]
    out['U6']=c['adc']; out['J_LINK']=c['link']
    return out


def reservations(p):
    c=p['controls']; rows=[]
    for i,xy in enumerate(c['joysticks'],1): rows.append(('JS'+str(i),xy,p['envelopes']['joystick']['size'][:2]))
    # Same plan projection, two distinct vertical levels. Not sensor footprints.
    for side in ['left','right']:
        s=c['shoulders'][side]
        rows.append((s['bumper']['label']+'/'+s['trigger']['label']+' STACK',s['bumper']['xy'],[22,12]))
    rows.extend(('M'+str(i),xy,[8,8]) for i,xy in enumerate(c['motors'],1))
    for ref,e in c['electronics_reserves'].items(): rows.append((ref,e['xy'],e['size']))
    return rows


def scad_values(p,r):
    scale=p['shell']['width']/r['legacy_outline']['outer_span_source_units'][0]
    v={'shell_profile':[[round(x*scale,4),round(y*scale,4)] for x,y in r['legacy_outline']['outer_points_centered']]}
    for key in ['height','wall','seam_z','lip_height','lip_clearance','enable_control_cutouts','enable_port_cutouts','enable_mounting_bosses']:
        v['shell_height' if key=='height' else key]=p['shell'][key]
    v['pcb_thickness']=p['boards']['base']['thickness']
    for name in ['controls','base']:
        for key in ['outline','z','mounts']: v[name+'_'+key]=p['boards'][name][key]
    for key in ['joysticks','switches','motors']: v[key]=p['controls'][key]
    v['face_switches']=p['controls']['switches'][:8]
    v['central_switches']=p['controls']['switches'][8:]
    v['shoulder_bumpers']=[[*p['controls']['shoulders'][s]['bumper']['xy'],p['controls']['shoulders'][s]['bumper']['z']] for s in ['left','right']]
    v['shoulder_triggers']=[[*p['controls']['shoulders'][s]['trigger']['xy'],p['controls']['shoulders'][s]['trigger']['z']] for s in ['left','right']]
    v['bumper_size']=p['controls']['shoulders']['left']['bumper']['size']
    v['trigger_size']=p['controls']['shoulders']['left']['trigger']['size']
    for key,label in [('pi_3_a_plus','pi'),('pisugar_3_plus','sugar'),('audio','audio')]:
        for attr in ['xy','size','z']: v[label+'_'+attr]=p['envelopes'][key][attr]
    v['joystick_size']=p['envelopes']['joystick']['size']
    v['usb_position']=p['ports']['micro_usb']['centre']; v['jack_position']=p['ports']['audio_jack']['centre']
    return v


def write_scad(root,p,r):
    (root/'mechanical/parameters.scad').write_text('// GENERATED from parameters/design.json and measured source outline; millimetres.\n// D0 ONLY: see design.json for every unvalidated assumption.\n'+'\n'.join(k+' = '+json.dumps(v)+';' for k,v in scad_values(p,r).items())+'\n',encoding='utf-8')
