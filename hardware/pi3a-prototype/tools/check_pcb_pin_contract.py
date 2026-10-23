"""Compare every physical pad (including duplicates and DNPs) to the pin model."""
from pathlib import Path
import json,hashlib
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
model=ROOT/'electrical/design-networks.json'
data=json.loads(model.read_text());reports=[]
for board in ['controls','base']:
    path=ROOT/f'electrical/{board}/nathan-{board}.kicad_pcb';pcb=p.LoadBoard(str(path))
    expected={c['reference']:c for c in data['components'] if c['board']==board and not c.get('virtual')}
    seen=set();errors=[];count=0;dupes={}
    for f in pcb.GetFootprints():
        ref=f.GetReference()
        if ref.startswith('H') and ref not in expected:continue
        if ref not in expected:errors.append({'ref':ref,'error':'unexpected footprint'});continue
        if ref in seen:errors.append({'ref':ref,'error':'duplicate reference'})
        seen.add(ref);pins={str(a['number']):a['net'] or '' for a in expected[ref]['pins']};numbers={}
        for pad in f.Pads():
            number=pad.GetNumber()
            if not number:continue
            count+=1;numbers[number]=numbers.get(number,0)+1
            if number not in pins:errors.append({'ref':ref,'pad':number,'error':'unexpected numbered pad'})
            elif pad.GetNetname()!=pins[number]:errors.append({'ref':ref,'pad':number,'expected':pins[number],'actual':pad.GetNetname()})
        for number in pins:
            if number not in numbers:errors.append({'ref':ref,'pad':number,'error':'missing physical pad'})
        if any(n>1 for n in numbers.values()):dupes[ref]={k:v for k,v in numbers.items() if v>1}
    for ref in set(expected)-seen:errors.append({'ref':ref,'error':'missing footprint'})
    traces={}
    for t in pcb.GetTracks():
        net=t.GetNetname();entry=traces.setdefault(net,{'length_mm_by_width':{},'vias':0})
        if isinstance(t,p.PCB_VIA):entry['vias']+=1
        else:
            width=str(round(p.ToMM(t.GetWidth()),4));entry['length_mm_by_width'][width]=round(entry['length_mm_by_width'].get(width,0)+p.ToMM(t.GetLength()),4)
    report={'board':board,'board_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'model_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'components':len(seen),'physical_numbered_pads':count,'duplicate_pad_numbers':dupes,'errors':errors,'tracks':traces,'scope':'Pin contract including DNP footprints; track inventory does not establish current capacity or connectivity.'}
    reports.append(report);print(board+': '+str(len(errors))+' mismatch(es), '+str(count)+' pads',flush=True)
(ROOT/'validation/pcb-pin-contract.json').write_text(json.dumps(reports,indent=2)+'\n')
if any(r['errors'] for r in reports):raise SystemExit(1)
