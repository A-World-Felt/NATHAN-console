"""Prepare D1 pin-level designs and editable schematics, standard library only.

No pcbnew, application launch, rendering, installation, or fabrication exports.
Generated designs remain proposals; validation evidence lives in validation/native-current.
"""
from pathlib import Path
import csv
import json
import math
import uuid
import xml.etree.ElementTree as ET
import base_audio
import base_usb

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'electrical'
SOURCES={
 'DRV2604L':{'url':'https://www.ti.com/lit/ds/symlink/drv2604l.pdf','revision':'SLOS866F, March 2018','pages':'4,23-24'},
 'MCP3208':{'url':'https://ww1.microchip.com/downloads/en/DeviceDoc/21298e.pdf','revision':'DS21298E, 2008','pages':'1,15,17-18'},
 'MCP23017':{'url':'https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP23017-Data-Sheet-DS20001952.pdf','revision':'DS20001952D, June 2022','pages':'1,11'},
 'TCA9548A':{'url':'https://www.ti.com/lit/ds/symlink/tca9548a.pdf','revision':'SCPS207H, September 2024','pages':'3,19-24'},
 'TPS62080':{'url':'https://www.ti.com/lit/ds/symlink/tps62080.pdf','revision':'SLVSAE8F, November 2016','pages':'4,12-14,19'},
 'XAL4020':{'url':'https://www.coilcraft.com/getmedia/6adcb47d-8b55-416c-976e-1e22e0d2848c/xal4000.pdf','revision':'Coilcraft XAL40xx current datasheet; product page checked 2026-10-22','pages':'XAL4020-102MEC table and mechanical drawing'},
 'JST_PH':{'url':'https://www.jst-mfg.com/product/pdf/eng/ePH.pdf','revision':'PH manufacturer catalog','pages':'1-3'},
 'Pi_GPIO':{'url':'https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio','revision':'Official GPIO documentation','pages':'online; physical header map must also be verified against actual board'},
}
SOURCES.update(base_audio.SOURCES)
SOURCES.update(base_usb.SOURCES)
COMP=[]
FPR='Resistor_SMD:R_0603_1608Metric'
FPC='Capacitor_SMD:C_0603_1608Metric'


def add(board,sheet,ref,value,pins,nets,footprint='',source='design proposal',note='',dnp=False):
    # pins are (number, manufacturer pin name, ERC electrical type).
    COMP.append({'board':board,'sheet':sheet,'reference':ref,'value':value,
                 'pins':[{'number':str(n),'name':name,'type':kind,'net':nets.get(str(n))} for n,name,kind in pins],
                 'footprint':footprint,'source':source,'note':note,'dnp':dnp})


def passive(board,sheet,ref,value,a,b,footprint=None,note='',dnp=False):
    add(board,sheet,ref,value,[('1','1','passive'),('2','2','passive')],{'1':a,'2':b},
        footprint or (FPC if ref.startswith('C') else FPR),note=note,dnp=dnp)


def conn(board,sheet,ref,nets,names=None,footprint='',note='Pin contract only; mating hardware not qualified'):
    if not footprint and board=='controls' and ref!='J100':
        n=len(nets); footprint=f'Connector_JST:JST_PH_B{n}B-PH-K_1x{n:02d}_P2.00mm_Vertical'
        note += '; prototype PCB connector JST B'+str(n)+'B-PH-K-S, PHR-'+str(n)+' housing, SPH-002T-P0.5S contacts; confirm wire gauge and orientation'
    add(board,sheet,ref,ref+' interface',[(str(i),names[i-1] if names else 'Pin_'+str(i),'passive') for i in range(1,len(nets)+1)],
        {str(i):n for i,n in enumerate(nets,1)},footprint,note=note)


def controls():
    b='controls'
    link=['5V_SYS','5V_SYS','GND','GND','I2C_SDA','I2C_SCL','GND','INPUT_IRQ_N','SPI_SCLK','GND','SPI_MOSI','SPI_MISO','ADC_CS_N','GND','3V3_PI','CTRL_RESET_N']
    conn(b,'interface','J100',link,footprint='Connector_IDC:IDC-Header_2x08_P2.54mm_Vertical',note='Proposed keyed 16-way signal cable; 5 V supply contact/current and cable assembly qualification pending. Pins 15/16 change D0 reserved assignments.')
    # Native Pi pulls should be counted before populating any extra master pullups.
    for ref,net in [('R11','I2C_SDA'),('R12','I2C_SCL')]: passive(b,'interface',ref,'4.7k DNP',net,'3V3_PI',dnp=True,note='DNP until total Pi/PiSugar pullup network is measured')
    passive(b,'interface','R13','10k','CTRL_RESET_N','3V3_PI')
    passive(b,'interface','R14','10k','INPUT_IRQ_N','3V3_PI')
    passive(b,'interface','R15','10k','ADC_CS_N','3V3_PI')
    passive(b,'interface','C13','100nF','CTRL_RESET_N','GND')
    passive(b,'interface','C14','1uF','3V3_PI','GND')
    # Fourteen input pins only. GPA7/GPB7 deliberately not used as inputs.
    names=['FACE_L_UP','FACE_L_RIGHT','FACE_L_DOWN','FACE_L_LEFT','FACE_R_UP','FACE_R_RIGHT','FACE_R_DOWN','FACE_R_LEFT','CENTRAL_1','CENTRAL_2','STICK_L_CLICK','STICK_R_CLICK','SHOULDER_L1','SHOULDER_R1']
    gpio_pins=[21,22,23,24,25,26,27,1,2,3,4,5,6,7]
    u7pins=[(i,'GPB'+str(i-1),'bidirectional') for i in range(1,9)]
    u7pins += [(9,'VDD','power_in'),(10,'VSS','power_in'),(11,'NC','no_connect'),(12,'SCL','input'),(13,'SDA','bidirectional'),(14,'NC','no_connect'),(15,'A0','input'),(16,'A1','input'),(17,'A2','input'),(18,'RESET_N','input'),(19,'INTB','output'),(20,'INTA','output')]
    u7pins += [(21+i,'GPA'+str(i),'bidirectional') for i in range(8)]
    nets={str(n):name for n,name in zip(gpio_pins,names)}
    nets.update({'9':'3V3_PI','10':'GND','12':'I2C_SCL','13':'I2C_SDA','15':'GND','16':'GND','17':'GND','18':'CTRL_RESET_N','20':'INPUT_IRQ_N'})
    add(b,'digital','U7','MCP23017-E/SO',u7pins,nets,'Package_SO:SOIC-28W_7.5x17.9mm_P1.27mm','MCP23017','0x20. Configure GPA7/GPB7 outputs low; mirror both interrupt banks into INTA; INTB left open. Verify manufacturer land pattern before routing.')
    passive(b,'digital','C15','100nF','3V3_PI','GND')
    for i,name in enumerate(names):
        passive(b,'digital','R'+str(30+i),'10k',name,'3V3_PI')
        if i<10:
            add(b,'digital','SW'+str(i+2),'B3F-4055 candidate',[('1','contact_1','passive'),('2','contact_2','passive')],{'1':name,'2':'GND'},'Button_Switch_THT:SW_PUSH-12mm',note='Ten existing BOM buttons: 8 face + 2 central. Candidate footprint still to qualify.')
    # Analog model with externally defined physical joystick/trigger assemblies.
    adc=['LX','LY','RX','RY','L2','R2']
    adc_pins=[(i+1,'CH'+str(i),'input') for i in range(8)]+[(9,'DGND','power_in'),(10,'CS_N','input'),(11,'DIN','input'),(12,'DOUT','output'),(13,'CLK','input'),(14,'AGND','power_in'),(15,'VREF','input'),(16,'VDD','power_in')]
    anets={str(i+1):'ADC_'+name for i,name in enumerate(adc)}
    anets.update({'7':'GND','8':'GND','9':'GND','10':'ADC_CS_N','11':'SPI_MOSI','12':'SPI_MISO','13':'SPI_SCLK','14':'GND','15':'3V3_PI','16':'3V3_PI'})
    add(b,'analog','U6','MCP3208-CI/SL',adc_pins,anets,'Package_SO:SOIC-16_3.9x9.9mm_P1.27mm','MCP3208','Proposed 12-bit replacement for MCP3008. SPI command framing changes; not software drop-in. Six ratiometric channels.')
    passive(b,'analog','C16','100nF','3V3_PI','GND'); passive(b,'analog','C17','1uF','3V3_PI','GND')
    for i,name in enumerate(adc):
        passive(b,'analog','R'+str(50+i),'100R','RAW_'+name,'ADC_'+name)
        passive(b,'analog','C'+str(20+i),'1nF','ADC_'+name,'GND',note='Initial filter candidate; settle/error must be measured with actual sensor. Start SPI at 100 kHz, dummy conversion after channel change.')
    conn(b,'analog','J20',['3V3_PI','GND','RAW_LX','RAW_LY','STICK_L_CLICK'],note='Joystick left interface, not COM-09032 physical pin numbering')
    conn(b,'analog','J21',['3V3_PI','GND','RAW_RX','RAW_RY','STICK_R_CLICK'],note='Joystick right interface, not COM-09032 physical pin numbering')
    conn(b,'analog','J22',['3V3_PI','GND','RAW_L2'],note='Analog trigger left; sensor and pivot not selected')
    conn(b,'analog','J23',['3V3_PI','GND','RAW_R2'],note='Analog trigger right; sensor and pivot not selected')
    conn(b,'digital','J24',['SHOULDER_L1','GND'],note='Additional left shoulder switch beyond workbook quantities')
    conn(b,'digital','J25',['SHOULDER_R1','GND'],note='Additional right shoulder switch beyond workbook quantities')
    # Address mux and each independently named haptic channel.
    mpins=[(1,'A0','input'),(2,'A1','input'),(3,'RESET_N','input')]
    mpins += [(n,name,'bidirectional') for n,name in [(4,'SD0'),(5,'SC0'),(6,'SD1'),(7,'SC1'),(8,'SD2'),(9,'SC2'),(10,'SD3'),(11,'SC3'),(13,'SD4'),(14,'SC4'),(15,'SD5'),(16,'SC5'),(17,'SD6'),(18,'SC6'),(19,'SD7'),(20,'SC7')]]
    mpins += [(12,'GND','power_in'),(21,'A2','input'),(22,'SCL','input'),(23,'SDA','bidirectional'),(24,'VCC','power_in')]
    mnets={'1':'GND','2':'GND','3':'CTRL_RESET_N','12':'GND','21':'GND','22':'I2C_SCL','23':'I2C_SDA','24':'3V3_PI'}
    for i,(sd,sc) in enumerate([(4,5),(6,7),(8,9),(10,11),(13,14)],1): mnets.update({str(sd):'H'+str(i)+'_SDA',str(sc):'H'+str(i)+'_SCL'})
    add(b,'haptic-mux','U8','TCA9548APWR',sorted(mpins),mnets,'Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm','TCA9548A','Address 0x70; channels 0-4 used, 5-7 unconnected. Select one channel for each transaction with 0x5A devices.')
    passive(b,'haptic-mux','C18','100nF','3V3_PI','GND')
    dpins=[(1,'REG','power_out'),(2,'SCL','input'),(3,'SDA','bidirectional'),(4,'IN_TRIG','input'),(5,'EN','input'),(6,'VDD_NC','power_in'),(7,'OUT_PLUS','output'),(8,'GND','power_in'),(9,'OUT_MINUS','output'),(10,'VDD','power_in')]
    for i in range(1,6):
        prefix='H'+str(i); sheet='haptic-'+str(i)
        dn={'1':prefix+'_REG','2':prefix+'_SCL','3':prefix+'_SDA','4':'GND','5':'3V3_HAPTIC','6':'3V3_HAPTIC','7':prefix+'_PLUS','8':'GND','9':prefix+'_MINUS','10':'3V3_HAPTIC'}
        add(b,sheet,'U'+str(i),'DRV2604LDGSR',dpins,dn,'Package_SO:VSSOP-10_3x3mm_P0.5mm','DRV2604L','EN follows motor rail; I2C runtime/standby control. OUT_MINUS is a differential output, never ground. LRA rated voltage must be configured separately.')
        passive(b,sheet,'C'+str(i*2-1),'1uF',prefix+'_REG','GND')
        passive(b,sheet,'C'+str(i*2),'1uF','3V3_HAPTIC','GND')
        passive(b,sheet,'R'+str(i*2-1),'4.7k',prefix+'_SDA','3V3_HAPTIC')
        passive(b,sheet,'R'+str(i*2),'4.7k',prefix+'_SCL','3V3_HAPTIC')
        conn(b,sheet,'J'+str(i+1),[prefix+'_PLUS',prefix+'_MINUS'],note='VG0832013D cable interface; exact keyed connector/counterpart pending')
    # Buck retained from BOM. U9 is not put in series with this rail.
    ppins=[(1,'EN','input'),(2,'GND','power_in'),(3,'MODE','input'),(4,'FB','input'),(5,'VOS','input'),(6,'PG','open_collector'),(7,'SW','power_out'),(8,'VIN','power_in'),(9,'EP','power_in')]
    pn={'1':'5V_SYS','2':'GND','3':'GND','4':'HAPTIC_FB','5':'3V3_HAPTIC','7':'HAPTIC_SW','8':'5V_SYS','9':'GND'}
    add(b,'power','PS2','TPS62080DSGR',ppins,pn,'Package_SON:WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm','TPS62080','3.308 V nominal divider, MODE low disables snooze. PG unused. EP grounded; land pattern/thermal layout pending.')
    passive(b,'power','L1','1uH XAL4020-102MEC candidate','HAPTIC_SW','3V3_HAPTIC',footprint='Inductor_SMD:L_Coilcraft_XAL4020-XXX',note='Prototype alternative: XAL4020-102MEC; 8.7 A at 30% drop, 6.7 A reference current for 20 C rise, 14.6 mOhm max DCR; larger 4 mm package chosen for generous current/thermal margin; compare actual worst-case peak and thermal behavior')
    COMP[-1]['source']='XAL4020'
    passive(b,'power','C30','10uF 10V X5R','5V_SYS','GND',footprint='Capacitor_SMD:C_0805_2012Metric',note='Effective capacitance under bias to confirm')
    passive(b,'power','C31','22uF 6.3V X5R','3V3_HAPTIC','GND',footprint='Capacitor_SMD:C_0805_2012Metric',note='Candidate Murata GRM21BR60J226ME39L per TI example; derating to verify')
    passive(b,'power','R60','249k 1%','3V3_HAPTIC','HAPTIC_FB')
    passive(b,'power','R61','39.2k 1%','HAPTIC_FB','GND')
    # ERC declarations identify the external source/return and regulated node.
    # They do not assert measured rail quality, safety, or current capability.
    for i,(sheet,net) in enumerate([('interface','5V_SYS'),('interface','GND'),('interface','3V3_PI'),('power','3V3_HAPTIC')],1):
        add(b,sheet,'#FLG'+str(i),'PWR_FLAG',[(1,'pwr','power_out')],{'1':net},note='ERC source declaration only; physical supply qualification remains open')
        COMP[-1]['virtual']=True
    return link


def base(link):
    b='base'
    conn(b,'interfaces','J100',link,footprint='Connector_IDC:IDC-Header_2x08_P2.54mm_Vertical',note='Same 1:1 pin contract as controls; cable keyed polarity/current pending')
    pn={1:'3V3_PI',2:'5V_SYS',3:'I2C_SDA',4:'5V_SYS',5:'I2C_SCL',11:'AUDIO_ENABLE',12:'I2S_BCLK',13:'CTRL_RESET_N',19:'SPI_MOSI',21:'SPI_MISO',22:'INPUT_IRQ_N',23:'SPI_SCLK',24:'ADC_CS_N',35:'I2S_LRCLK',40:'I2S_DOUT'}
    pn.update({i:'GND' for i in [6,9,14,20,25,30,34,39]})
    pn.update(base_usb.PI_PHYSICAL_PINS)
    conn(b,'interfaces','J1',[pn.get(i) for i in range(1,41)],footprint='Connector_IDC:IDC-Header_2x20_P2.54mm_Vertical',note='Proposed cable to actual Pi GPIO, not an assumed socket below Pi. Pin assignments need actual orientation/connector verification; no power import qualification.')
    COMP[-1]['source']='Pi_GPIO'
    conn(b,'interfaces','J101',['5V_SYS','GND'],footprint='NATHAN_USB:Power_Pigtail_2Pad',note='PiSugar 5 V OUTPUT cable, separate from charging INPUT. 20/22AWG soldered wire candidate with strain relief; pad counterpart and load/temperature qualification pending. Avoid a 2A JST PH contact on the full system supply.')
    conn(b,'interfaces','J102',['I2C_SDA','I2C_SCL','GND'],footprint='Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical',note='PiSugar management cable interface; exact module solder contacts need revision verification')
    base_audio.populate(add,passive,conn)
    base_usb.populate(add,passive,conn)
    for i,net in enumerate(['5V_SYS','3V3_PI','GND','USB_PC_VBUS'],1):
        add(b,'interfaces','#FLG'+str(i),'PWR_FLAG',[(1,'pwr','power_out')],{'1':net},note='External power declaration only; not supply qualification')
        COMP[-1]['virtual']=True


def uid(text): return str(uuid.uuid5(uuid.NAMESPACE_URL,'nathan-electrical-D1/'+text))
def q(s): return json.dumps(str(s),ensure_ascii=False)
def fmt(x): return ('%.4f'%x).rstrip('0').rstrip('.') if x else '0'
def effect(size=1.0,hide=False): return '(effects (font (size '+str(size)+' '+str(size)+'))'+(' hide' if hide else '')+')'


def model(c):
    pins=c['pins']; count=math.ceil(len(pins)/2); top=(count-1)*1.27; height=max(3.81,top+2.54)
    points=[]; geometry=[]
    for i,p in enumerate(pins):
        side=0 if i<count else 1; row=i if side==0 else i-count
        x=-17.78 if side==0 else 17.78; y=top-row*2.54; angle=0 if side==0 else 180
        points.append((p,x,y,side))
        kind='passive' if p['type']=='no_connect' else p['type']
        geometry.append(f'(pin {kind} line (at {fmt(x)} {fmt(y)} {angle}) (length 5.08) (name {q(p["name"])} {effect(.9)}) (number {q(p["number"])} {effect(.9)}))')
    name='NATHAN:'+c['reference']; simple=c['reference']
    populated='no' if c.get('virtual') else 'yes'
    lib=f'(symbol {q(name)} (pin_names (offset 0.508)) (in_bom {populated}) (on_board {populated}) (property "Reference" "U" (at 0 {fmt(height+2.54)} 0) {effect()}) (property "Value" {q(c["value"])} (at 0 {fmt(-height-2.54)} 0) {effect()}) (symbol {q(simple+"_0_1")} (rectangle (start -12.7 {fmt(height)}) (end 12.7 {fmt(-height)}) (stroke (width 0.254) (type default)) (fill (type background)))) (symbol {q(simple+"_1_1")} '+''.join(geometry)+'))'
    return lib,points,height


def draw_sheet(board,sheet,items,root_id,sheet_id):
    path=OUT/board/(sheet+'.kicad_sch'); project='nathan-'+board
    header=f'(kicad_sch (version 20231120) (generator "eeschema") (uuid "{uid(board+sheet)}") (paper "A1") (title_block (title {q("NATHAN D1 proposal / "+board+" / "+sheet)}) (rev "D1-proposal") (company "Codex/OpenAI nathan_bom") (comment 1 "Pin-level proposal; see versioned validation reports; physical qualification pending"))'
    models=[model(c) for c in items]; content=[header,'(lib_symbols '+''.join(x[0] for x in models)+')']
    for i,(c,(_,points,height)) in enumerate(zip(items,models)):
        x=101.6+(i%4)*193.04; y=60.96+(i//4)*66.04
        if y+height>575: raise ValueError('Too many components on '+sheet)
        ref=c['reference']; key=board+'/'+ref; symbol_id=uid(key)
        properties=f'(property "Reference" {q(ref)} (at {fmt(x)} {fmt(y-height-4)} 0) {effect(1.2)}) (property "Value" {q(c["value"])} (at {fmt(x)} {fmt(y+height+4)} 0) {effect(1)}) (property "Footprint" {q(c["footprint"])} (at {fmt(x)} {fmt(y)} 0) {effect(1,True)})'
        if c['source'] in SOURCES: properties+=f'(property "Datasheet" {q(SOURCES[c["source"]]["url"])} (at {fmt(x)} {fmt(y)} 0) {effect(1,True)})'
        pin_instances=''.join('(pin '+q(p['number'])+' (uuid "'+uid(key+'/pin/'+p['number'])+'"))' for p in c['pins'])
        populated='no' if c.get('virtual') else 'yes'
        content.append(f'(symbol (lib_id {q("NATHAN:"+ref)}) (at {fmt(x)} {fmt(y)} 0) (unit 1) (in_bom {populated}) (on_board {populated}) (dnp {"yes" if c["dnp"] else "no"}) (uuid "{symbol_id}") {properties} {pin_instances} (instances (project {q(project)} (path "/{root_id}/{sheet_id}" (reference {q(ref)}) (unit 1)))))')
        for p,px,py,side in points:
            ax=x+px; ay=y-py; net=p['net']; pkey=key+'/'+p['number']
            if net is None:
                content.append(f'(no_connect (at {fmt(ax)} {fmt(ay)}) (uuid "{uid(pkey+"/nc")}"))'); continue
            ex=ax+(-7.62 if side==0 else 7.62)
            content.append(f'(wire (pts (xy {fmt(ax)} {fmt(ay)}) (xy {fmt(ex)} {fmt(ay)})) (stroke (width 0) (type default)) (uuid "{uid(pkey+"/wire")}"))')
            angle=0 if side==0 else 180
            # Local labels are sheet-scoped; global labels carry the cross-sheet net.
            content.append(f'(global_label {q(net)} (shape bidirectional) (at {fmt(ex)} {fmt(ay)} {angle}) {effect(.9)} (uuid "{uid(pkey+"/label")}") (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {fmt(ex)} {fmt(ay)} {angle}) {effect(.9,True)}))')
    path.write_text('\n'.join(content)+'\n)\n',encoding='utf-8')


def schematic(board):
    folder=OUT/board; folder.mkdir(parents=True,exist_ok=True)
    # Explicit local library resolution for native ERC. Cached symbols alone are
    # sufficient for netlist export, but ERC also resolves the library nickname.
    local=[]; libs=set()
    for c in COMP:
        if c['board']!=board: continue
        raw=model(c)[0].replace('(symbol '+q('NATHAN:'+c['reference']), '(symbol '+q(c['reference']),1)
        local.append(raw)
        if c['footprint']: libs.add(c['footprint'].split(':')[0])
    (folder/'NATHAN.kicad_sym').write_text('(kicad_symbol_lib (version 20231120) (generator "kicad_symbol_editor")\n'+'\n'.join(local)+'\n)\n',encoding='utf-8')
    (folder/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "NATHAN")(type "KiCad")(uri "${KIPRJMOD}/NATHAN.kicad_sym")(options "")(descr "Project-local generated pin models; source references in design-networks.json")))\n',encoding='utf-8')
    (folder/'fp-lib-table').write_text('(fp_lib_table (version 7)\n'+'\n'.join('(lib (name '+q(name)+')(type "KiCad")(uri '+q(('${KIPRJMOD}/../' if name=='NATHAN_USB' else '${KICAD8_FOOTPRINT_DIR}/')+name+'.pretty')+')(options "")(descr "Candidate library; qualification pending"))' for name in sorted(libs))+'\n)\n',encoding='utf-8')
    root_id=uid(board+'/root'); project='nathan-'+board
    contents=[f'(kicad_sch (version 20231120) (generator "eeschema") (uuid "{root_id}") (paper "A3") (title_block (title {q("NATHAN "+board+" D1 electrical proposal")}) (rev "D1") (company "Codex/OpenAI nathan_bom")) (lib_symbols)']
    groups=sorted({c['sheet'] for c in COMP if c['board']==board})
    for i,sheet in enumerate(groups):
        sid=uid(board+'/sheet/'+sheet); x=25+(i%3)*125; y=35+(i//3)*55
        contents.append(f'(sheet (at {x} {y}) (size 100 35) (stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0)) (uuid "{sid}") (property "Sheetname" {q(sheet)} (at {x} {y-2} 0) {effect(1.27)}) (property "Sheetfile" {q(sheet+".kicad_sch")} (at {x} {y+37} 0) {effect(1.27)}) (instances (project {q(project)} (path "/{root_id}" (page "{i+2}")))))')
        draw_sheet(board,sheet,[c for c in COMP if c['board']==board and c['sheet']==sheet],root_id,sid)
    contents.append('(text "D1 proposal: see validation/native-current for revision-specific evidence. Component and manufacturing qualification pending." (at 25 275 0) (effects (font (size 1.27 1.27)) (justify left)) (uuid "'+uid(board+'/warning')+'"))')
    contents.append('(sheet_instances (path "/" (page "1")))')
    (folder/(project+'.kicad_sch')).write_text('\n'.join(contents)+'\n)\n',encoding='utf-8')
    pro=folder/(project+'.kicad_pro')
    config=json.loads(pro.read_text()) if pro.exists() else {}
    config.setdefault('meta',{'filename':project+'.kicad_pro','version':1})
    config.setdefault('text_variables',{})['DESIGN_STATUS']='D1 electrical proposal; see validation/native-current for revision-specific evidence'
    pro.write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')


def netlist(board):
    root=ET.Element('export',version='E'); design=ET.SubElement(root,'design')
    ET.SubElement(design,'source').text='nathan-'+board+'.kicad_sch'; ET.SubElement(design,'tool').text='Codex standard-library generator: NOT native KiCad export'
    components=ET.SubElement(root,'components'); nets={}
    for c in COMP:
        if c['board']!=board: continue
        node=ET.SubElement(components,'comp',ref=c['reference']); ET.SubElement(node,'value').text=c['value']; ET.SubElement(node,'footprint').text=c['footprint']
        for p in c['pins']:
            if p['net'] is not None: nets.setdefault(p['net'],[]).append((c['reference'],p))
    parent=ET.SubElement(root,'nets')
    for code,name in enumerate(sorted(nets),1):
        node=ET.SubElement(parent,'net',code=str(code),name=name)
        for ref,p in nets[name]: ET.SubElement(node,'node',ref=ref,pin=p['number'],pinfunction=p['name'],pintype=p['type'])
    ET.indent(root); ET.ElementTree(root).write(OUT/board/('nathan-'+board+'.net'),encoding='utf-8',xml_declaration=True)


def main():
    OUT.mkdir(exist_ok=True); link=controls(); base(link)
    (OUT/'design-networks.json').write_text(json.dumps({'status':'D1 proposals; see validation/native-current for revision-specific native checks; original D0 boards not synchronized yet','sources':SOURCES,'components':COMP},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    with (OUT/'pin-map.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f); w.writerow(['board','sheet','reference','value','pin','name','type','net','dnp'])
        for c in COMP:
            for p in c['pins']: w.writerow([c['board'],c['sheet'],c['reference'],c['value'],p['number'],p['name'],p['type'],p['net'] or 'NC',c['dnp']])
    with (OUT/'bom-proposal.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f); w.writerow(['board','reference','value','footprint','dnp','source','qualification_note'])
        for c in COMP:
            if not c.get('virtual'): w.writerow([c['board'],c['reference'],c['value'],c['footprint'],c['dnp'],c['source'],c['note']])
    for b in ['controls','base']: schematic(b); netlist(b)
    print(json.dumps({'components':len(COMP),'boards':{b:sum(c['board']==b for c in COMP) for b in ['controls','base']},'status':'text generation; consult validation/native-current for checks; routing separate'}))


if __name__=='__main__': main()
