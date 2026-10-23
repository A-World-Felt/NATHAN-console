"""Prototype audio pin model; sources are manufacturer datasheets, not measurements."""
SOURCES={
 'PCM5102A':{'url':'https://www.ti.com/lit/ds/symlink/pcm5102a.pdf','revision':'SLAS859C May 2015','pages':'5,9-10,25-26,28,41'},
 'TPA6132A2':{'url':'https://www.ti.com/lit/ds/symlink/tpa6132a2.pdf','revision':'SLOS597B July 2017','pages':'3,5-6,11-15'},
 'RT9193':{'url':'https://www.richtek.com/assets/product_file/RT9193/DS9193-18.pdf','revision':'DS9193-18 June 2022','pages':'1-4'},
}

def populate(add,passive,conn):
    b='base'
    add(b,'audio-power','U400','RT9193-33GB',[(1,'VIN','power_in'),(2,'GND','power_in'),(3,'EN','input'),(4,'BP','passive'),(5,'VOUT','power_out')],{'1':'5V_SYS','2':'GND','3':'5V_SYS','4':'AUDIO_BP','5':'3V3_AUDIO'},'Package_TO_SOT_SMD:SOT-23-5','RT9193','300 mA regulator, not 500 mA. Audio only; no motor current. Dissipation and effective capacitors to qualify.')
    for ref,value,a,c in [('C400','1uF 10V X7R','5V_SYS','GND'),('C401','1uF 10V X7R','3V3_AUDIO','GND'),('C402','22nF','AUDIO_BP','GND')]:passive(b,'audio-power',ref,value,a,c)
    pins=[(1,'CPVDD','power_in'),(2,'CAPP','passive'),(3,'CPGND','power_in'),(4,'CAPM','passive'),(5,'VNEG','power_out'),(6,'OUTL','output'),(7,'OUTR','output'),(8,'AVDD','power_in'),(9,'AGND','power_in'),(10,'DEMP','input'),(11,'FLT','input'),(12,'SCK','input'),(13,'BCK','input'),(14,'DIN','input'),(15,'LRCK','input'),(16,'FMT','input'),(17,'XSMT','input'),(18,'LDOO','power_out'),(19,'DGND','power_in'),(20,'DVDD','power_in')]
    nets={'1':'3V3_AUDIO','2':'DAC_CAPP','3':'GND','4':'DAC_CAPM','5':'DAC_VNEG','6':'DAC_L','7':'DAC_R','8':'3V3_AUDIO','9':'GND','10':'GND','11':'3V3_PI','12':'GND','13':'I2S_BCLK','14':'I2S_DOUT','15':'I2S_LRCLK','16':'GND','17':'AUDIO_ENABLE','18':'DAC_LDOO','19':'GND','20':'3V3_PI'}
    add(b,'audio-dac','U401','PCM5102APW',pins,nets,'Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm','PCM5102A','3-wire I2S PLL, 48 kHz/64 BCLK initial setting; low-latency filter; line output feeds a separate headphone amplifier.')
    caps=[('C403','2.2uF 10V X7R','DAC_CAPP','DAC_CAPM'),('C404','2.2uF 10V X7R','DAC_VNEG','GND'),('C405','100nF','DAC_LDOO','GND'),('C406','100nF','3V3_PI','GND'),('C407','10uF 6.3V X5R','3V3_PI','GND'),('C408','100nF','3V3_AUDIO','GND'),('C409','10uF 6.3V X5R','3V3_AUDIO','GND'),('C410','100nF','3V3_AUDIO','GND'),('C411','10uF 6.3V X5R','3V3_AUDIO','GND')]
    for ref,value,a,c in caps:passive(b,'audio-dac',ref,value,a,c)
    passive(b,'audio-dac','R400','100k','AUDIO_ENABLE','GND',note='Default mute at boot; software must sequence clocks and mute before shutdown')
    for ch,offset in [('L',0),('R',1)]:
        passive(b,'audio-filter','R'+str(401+offset),'470R','DAC_'+ch,'DAC_FILTER_'+ch)
        passive(b,'audio-filter','C'+str(412+offset),'2.2nF C0G','DAC_FILTER_'+ch,'GND')
        passive(b,'audio-filter','R'+str(403+offset),'10k 1%','DAC_FILTER_'+ch,'HP_ATT_'+ch)
        passive(b,'audio-filter','R'+str(405+offset),'10k 1%','HP_ATT_'+ch,'GND')
        passive(b,'audio-filter','C'+str(414+offset),'1uF 10V X7R','HP_ATT_'+ch,'HP_IN_'+ch)
    pins=[(1,'INL_MINUS','input'),(2,'INL_PLUS','input'),(3,'INR_PLUS','input'),(4,'INR_MINUS','input'),(5,'OUTR','output'),(6,'G0','input'),(7,'G1','input'),(8,'HPVSS','power_out'),(9,'CPN','passive'),(10,'PGND','power_in'),(11,'CPP','passive'),(12,'HPVDD','power_out'),(13,'EN','input'),(14,'VDD','power_in'),(15,'SGND','power_in'),(16,'OUTL','output'),(17,'EP','power_in')]
    nets={'1':'HP_IN_L','2':'GND','3':'GND','4':'HP_IN_R','5':'HEADPHONE_R','6':'GND','7':'GND','8':'HP_VSS','9':'HP_CPN','10':'GND','11':'HP_CPP','12':'HP_VDD','13':'AUDIO_ENABLE','14':'3V3_AUDIO','15':'GND','16':'HEADPHONE_L','17':'GND'}
    add(b,'audio-headphone','U402','TPA6132A2RTER',pins,nets,'Package_DFN_QFN:WQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm','TPA6132A2','G0=G1=0 gives -6 dB. HPVDD is an internal output, NOT tied to supply. Gain/input attenuation provisional; not a hearing-safety level guarantee.')
    for ref,value,a,c in [('C416','1uF 10V X7R','HP_CPP','HP_CPN'),('C417','1uF 10V X7R','HP_VSS','GND'),('C418','2.2uF 10V X7R','HP_VDD','GND'),('C419','1uF 10V X7R','3V3_AUDIO','GND')]:passive(b,'audio-headphone',ref,value,a,c)
    conn(b,'audio-headphone','J400',['HEADPHONE_L','HEADPHONE_R','GND'],['TIP_LEFT','RING_RIGHT','SLEEVE'],footprint='Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical',note='JST PH cable to a panel-mounted 3.5 mm stereo TRS jack. Jack mechanics not qualified; this is an explicit cable interface, not an assumed jack pinout.')
