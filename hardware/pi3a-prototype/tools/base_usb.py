"""NATHAN USB-C candidate, Codex/OpenAI. Not qualified for fabrication.

Populate the same pin contract as prepare_electronics.py. The high-current
Type-C path works without Linux. Legacy PC charge requires a fresh software
grant after USB configuration. Battery charging remains entirely in PiSugar.
"""
SOURCES = {
    key: {'url': url, 'revision': revision, 'pages': pages}
    for key, url, revision, pages in [
        ('USB4105', 'https://gct.co/files/drawings/usb4105.pdf', 'B4, 18 December 2023', '1'),
        ('BQ24392', 'https://www.ti.com/lit/ds/slis146d/slis146d.pdf', 'SLIS146D', '3-5,8-10'),
        ('TUSB320LAI', 'https://www.ti.com/lit/ds/symlink/tusb320lai.pdf', 'SLLSEQ8D', '3,11-14,28'),
        ('TPS709', 'https://www.ti.com/lit/ds/symlink/tps709.pdf', 'SBVS186H', '3-6,15'),
        ('TPS2553', 'https://www.ti.com/lit/ds/symlink/tps2553.pdf', 'SLVS841F', '3,7,14-19'),
        ('LM66100', 'https://www.ti.com/lit/ds/symlink/lm66100.pdf', 'SLVSEZ8A', '3-5,11'),
        ('TPS25947', 'https://www.ti.com/lit/ds/symlink/tps25947.pdf', 'SLVSFC9C May 2026', '4-10,29-32,73'),
        ('TS3USB30E', 'https://www.ti.com/lit/ds/symlink/ts3usb30e.pdf', 'SCDS255G', '4-7'),
        ('TPD2E2U06', 'https://www.ti.com/lit/ds/symlink/tpd2e2u06.pdf', 'SLLSEG9C', '3-4'),
        ('LVC2G04', 'https://www.ti.com/lit/ds/symlink/sn74lvc2g04.pdf', 'SCES195N', '3-6'),
        ('LVC2G08', 'https://www.ti.com/lit/ds/symlink/sn74lvc2g08.pdf', 'SCES198N', '3-6'),
        ('LVC1G32', 'https://www.ti.com/lit/ds/symlink/sn74lvc1g32.pdf', 'SCES219W', 'pin functions'),
        ('LVC1G74', 'https://www.ti.com/lit/ds/symlink/sn74lvc1g74.pdf', 'SCES794G', '3-6'),
        ('2N7002', 'https://assets.nexperia.com/documents/data-sheet/2N7002.pdf', 'Rev 7', '1'),
    ]
}
PI_PHYSICAL_PINS = {29: 'USB_CHARGE_RUN', 31: 'USB_CHARGE_CLOCK'}
LOCAL_LIBRARY = 'NATHAN_USB'


def populate(add, passive, conn):
    b = 'base'
    sot = 'Package_TO_SOT_SMD:'
    so = 'Package_SO:'
    qfn = 'Package_DFN_QFN:'

    def chip(sheet, ref, value, pins, nets, footprint, source, note=''):
        add(b, sheet, ref, value, pins, {str(k): v for k, v in nets.items()}, footprint, source, note)

    def r(sheet, ref, value, a, z, note=''):
        passive(b, sheet, ref, value, a, z, note=note)

    def cap(sheet, ref, value, net, footprint=None, note=''):
        passive(b, sheet, ref, value, net, 'GND', footprint=footprint, note=note)

    # GCT footprint has overlapping same-net A/B power contacts and four S1 pads.
    mapping = {'A1': 'GND', 'A4': 'USB_PC_VBUS', 'A5': 'USB_CC1',
               'A6': 'USB_PC_DP', 'A7': 'USB_PC_DM', 'A8': None,
               'A9': 'USB_PC_VBUS', 'A12': 'GND', 'B1': 'GND',
               'B4': 'USB_PC_VBUS', 'B5': 'USB_CC2', 'B6': 'USB_PC_DP',
               'B7': 'USB_PC_DM', 'B8': None, 'B9': 'USB_PC_VBUS',
               'B12': 'GND', 'S1': 'GND'}
    chip('usb-port', 'J120', 'USB4105-GF-A',
         [(n, n, 'passive') for n in mapping], mapping,
         'Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal',
         'USB4105', 'USB2 sink only, 5 V only. Both plug orientations. Shell to local ground; EMC validation pending. No PD voltage request.')
    for ref, nets in [('D200', ('USB_PC_DP', 'USB_PC_DM')), ('D201', ('USB_CC1', 'USB_CC2'))]:
        chip('usb-port', ref, 'TPD2E2U06DRLR',
             [(1, 'NC', 'no_connect'), (2, 'NC', 'no_connect'), (3, 'IO1', 'passive'),
              (4, 'GND', 'power_in'), (5, 'IO2', 'passive')],
             {3: nets[0], 4: 'GND', 5: nets[1]}, sot+'SOT-553', 'TPD2E2U06',
             'Short ESD return at connector. Protection response and USB eye require measurements; no CC-to-VBUS short protection claimed.')

    chip('usb-detect', 'U200', 'TPS70933DBVR',
         [(1, 'IN', 'power_in'), (2, 'GND', 'power_in'), (3, 'EN', 'input'),
          (4, 'NC', 'no_connect'), (5, 'OUT', 'power_out')],
         {1: 'USB_PC_VBUS', 2: 'GND', 3: 'USB_PC_VBUS', 5: '3V3_USB'},
         sot+'SOT-23-5', 'TPS709', 'USB-domain supply only; TPS70933 pinout differs from TPS709A/B.')
    cap('usb-detect', 'C200', '1uF 10V X7R', 'USB_PC_VBUS')
    cap('usb-detect', 'C201', '4.7uF 10V X7R', '3V3_USB',
        'Capacitor_SMD:C_0805_2012Metric', 'Verify >=2.2uF effective at bias.')
    chip('usb-detect', 'U201', 'TUSB320LAIRWBR',
         [(1, 'CC1', 'bidirectional'), (2, 'CC2', 'bidirectional'), (3, 'PORT', 'input'),
          (4, 'VBUS_DET', 'input'), (5, 'ADDR', 'input'), (6, 'OUT3', 'open_collector'),
          (7, 'OUT1', 'open_collector'), (8, 'OUT2', 'open_collector'),
          (9, 'ID', 'open_collector'), (10, 'GND', 'power_in'),
          (11, 'EN_N', 'input'), (12, 'VDD', 'power_in')],
         {1: 'USB_CC1', 2: 'USB_CC2', 3: 'GND', 4: 'CC_VBUS_SENSE',
          7: 'CC_OUT1', 8: 'CC_OUT2', 10: 'GND', 11: 'GND', 12: '3V3_USB'},
         qfn+'Texas_X2QFN-12_1.6x1.6mm_P0.4mm', 'TUSB320LAI',
         'UFP fixed, ADDR floating selects GPIO. Internal Rd in dead battery; do NOT add parallel external Rd. Autonomous 1.5A/3A detection.')
    r('usb-detect', 'R200', '887k 1%', 'USB_PC_VBUS', 'CC_VBUS_SENSE', 'Within specified 855..920k range.')
    r('usb-detect', 'R201', '10k', 'CC_OUT1', '3V3_USB')
    r('usb-detect', 'R202', '10k', 'CC_OUT2', '3V3_USB')
    cap('usb-detect', 'C202', '100nF', '3V3_USB')
    chip('usb-detect', 'U202', 'BQ24392RSER',
         [(1, 'SW_OPEN', 'open_collector'), (2, 'DM_HOST', 'bidirectional'),
          (3, 'DP_HOST', 'bidirectional'), (4, 'CHG_AL_N', 'open_collector'),
          (5, 'GOOD_BAT', 'input'), (6, 'GND', 'power_in'),
          (7, 'DP_CON', 'bidirectional'), (8, 'DM_CON', 'bidirectional'),
          (9, 'VBUS', 'power_in'), (10, 'CHG_DET', 'output')],
         {1: 'USB_SW_OPEN_N', 2: 'USB_MID_DM', 3: 'USB_MID_DP',
          4: 'USB_CHG_AL_N', 5: 'USB_GOOD_BAT', 6: 'GND', 7: 'USB_PC_DP',
          8: 'USB_PC_DM', 9: 'USB_PC_VBUS', 10: 'USB_CHG_DET'},
         qfn+'Texas_UQFN-10_1.5x2mm_P0.5mm', 'BQ24392',
         'GOOD_BAT follows cable supply to avoid dead-battery timer interrupting wall charge. CHG_DET is a 5V-domain output, never a Pi GPIO.')
    r('usb-detect', 'R203', '47k', 'USB_PC_VBUS', 'USB_GOOD_BAT')
    r('usb-detect', 'R204', '10k', 'USB_SW_OPEN_N', '3V3_USB')
    r('usb-detect', 'R205', '10k', 'USB_CHG_AL_N', '3V3_USB')
    cap('usb-detect', 'C203', '100nF', 'USB_PC_VBUS')

    chip('usb-data', 'U203', 'TS3USB30EDGSR',
         [(1, 'S', 'input'), (2, 'D1_PLUS', 'bidirectional'), (3, 'D2_PLUS', 'bidirectional'),
          (4, 'D_PLUS', 'bidirectional'), (5, 'GND', 'power_in'), (6, 'D_MINUS', 'bidirectional'),
          (7, 'D2_MINUS', 'bidirectional'), (8, 'D1_MINUS', 'bidirectional'),
          (9, 'OE_N', 'input'), (10, 'VCC', 'power_in')],
         {1: 'GND', 2: 'USB_PI_DP', 4: 'USB_MID_DP', 5: 'GND', 6: 'USB_MID_DM',
          8: 'USB_PI_DM', 9: 'USB_SW_OPEN_N', 10: '3V3_PI'},
         so+'VSSOP-10_3x3mm_P0.5mm', 'TS3USB30E',
         'Pi-side Ioff isolation when Pi is off. Two series switches: 480Mbps signal integrity is NOT qualified.')
    cap('usb-data', 'C204', '100nF', '3V3_PI')
    conn(b, 'usb-data', 'J122', ['GND', 'USB_PI_DM', 'USB_PI_DP', 'GND'],
         ['GND', 'D_MINUS', 'D_PLUS', 'SHIELD'],
         footprint=LOCAL_LIBRARY+':USB_Data_Pigtail_4Pad',
         note='Internal short shielded USB cable to actual Pi USB-A data pins. Pi VBUS wire MUST terminate insulated and unconnected. Footprint is solder pads, not a certified high-speed connector. Cable continuity and eye tests required.')

    inv_pins = [(1, '1A', 'input'), (2, 'GND', 'power_in'), (3, '2A', 'input'),
                (4, '2Y', 'output'), (5, 'VCC', 'power_in'), (6, '1Y', 'output')]
    and_pins = [(1, '1A', 'input'), (2, '1B', 'input'), (3, '2Y', 'output'),
                (4, 'GND', 'power_in'), (5, '2A', 'input'), (6, '2B', 'input'),
                (7, '1Y', 'output'), (8, 'VCC', 'power_in')]
    chip('usb-policy', 'U206', 'SN74LVC2G04DBVR', inv_pins,
         {1: 'USB_SW_OPEN_N', 2: 'GND', 3: 'USB_CHG_AL_N', 4: 'USB_CHARGE_ALLOWED',
          5: '3V3_USB', 6: 'USB_DATA_ACTIVE'}, sot+'SOT-23-6', 'LVC2G04')
    chip('usb-policy', 'U207', 'SN74LVC2G08DCUR', and_pins,
         {1: 'USB_DATA_ACTIVE', 2: 'USB_RUN_IN', 3: 'USB_LEGACY_REQUEST', 4: 'GND',
          5: 'USB_REQUEST', 6: 'USB_CHARGE_ALLOWED', 7: 'USB_GRANT_CLEAR_N', 8: '3V3_USB'},
         so+'VSSOP-8_2.3x2mm_P0.5mm', 'LVC2G08')
    chip('usb-policy', 'U208', 'SN74LVC1G74DCUR',
         [(1, 'CLK', 'input'), (2, 'D', 'input'), (3, 'Q_N', 'output'), (4, 'GND', 'power_in'),
          (5, 'Q', 'output'), (6, 'CLR_N', 'input'), (7, 'PRE_N', 'input'), (8, 'VCC', 'power_in')],
         {1: 'USB_CLOCK_IN', 2: '3V3_USB', 4: 'GND', 5: 'USB_SDP_GRANT',
          6: 'USB_GRANT_CLEAR_N', 7: '3V3_USB', 8: '3V3_USB'},
         so+'VSSOP-8_2.3x2mm_P0.5mm', 'LVC1G74',
         'Fresh rising pulse only after USB configured >=500mA. RUN low clears on suspend/deconfigure; BQ data detach also clears. A stale GPIO high does not restore grant after reconnect. Q is pin5.')
    chip('usb-policy', 'U209', 'SN74LVC1G32DBVR',
         [(1, 'A', 'input'), (2, 'B', 'input'), (3, 'GND', 'power_in'), (4, 'Y', 'output'), (5, 'VCC', 'power_in')],
         {1: 'USB_CHG_DET', 2: 'USB_SDP_GRANT', 3: 'GND', 4: 'USB_REQUEST', 5: '3V3_USB'},
         sot+'SOT-23-5', 'LVC1G32', 'Input accepts BQ 5V output; output is USB-domain 3.3V.')
    chip('usb-policy', 'U210', 'SN74LVC2G04DBVR', inv_pins,
         {1: 'CC_OUT1', 2: 'GND', 3: 'CC_OUT2', 4: 'CC_OUT2_LOW', 5: '3V3_USB', 6: 'USB_CC_POWER'},
         sot+'SOT-23-6', 'LVC2G04')
    chip('usb-policy', 'U211', 'SN74LVC2G08DCUR', and_pins,
         {1: 'USB_LEGACY_REQUEST', 2: 'CC_OUT1', 3: 'USB_CC_3A', 4: 'GND',
          5: 'USB_CC_POWER', 6: 'CC_OUT2_LOW', 7: 'USB_LEGACY_EN', 8: '3V3_USB'},
         so+'VSSOP-8_2.3x2mm_P0.5mm', 'LVC2G08')
    for i in range(6): cap('usb-policy', 'C'+str(206+i), '100nF', '3V3_USB')
    for ref, a, z in [('R206', 'USB_CHARGE_RUN', 'USB_RUN_IN'), ('R207', 'USB_CHARGE_CLOCK', 'USB_CLOCK_IN')]:
        r('usb-policy', ref, '1k', a, z)
    r('usb-policy', 'R208', '4.7k', 'USB_RUN_IN', 'GND')
    r('usb-policy', 'R209', '4.7k', 'USB_CLOCK_IN', 'GND')
    r('usb-policy', 'R210', '10k', 'USB_LEGACY_EN', 'GND')
    r('usb-policy', 'R211', '10k', 'USB_CC_POWER', 'GND')

    chip('usb-power-legacy', 'U204', 'TPS2553DBVR',
         [(1, 'IN', 'power_in'), (2, 'GND', 'power_in'), (3, 'EN', 'input'),
          (4, 'FAULT', 'open_collector'), (5, 'ILIM', 'passive'), (6, 'OUT', 'power_out')],
         {1: 'USB_PC_VBUS', 2: 'GND', 3: 'USB_LEGACY_EN', 5: 'USB_LEGACY_ILIM', 6: 'USB_LEGACY_LIMITED'},
         sot+'SOT-23-6', 'TPS2553', '62k 1%: calculated DC bounds 377..479mA, plus detector/logic supply. Current and voltage sag with PiSugar require measurement.')
    r('usb-power-legacy', 'R212', '62k 1%', 'USB_LEGACY_ILIM', 'GND')
    cap('usb-power-legacy', 'C212', '100nF', 'USB_PC_VBUS')
    cap('usb-power-legacy', 'C213', '1uF 10V X7R', 'USB_LEGACY_LIMITED')
    chip('usb-power-legacy', 'U205', 'LM66100DCKR',
         [(1, 'VIN', 'power_in'), (2, 'GND', 'power_in'), (3, 'CE', 'input'),
          (4, 'NC', 'no_connect'), (5, 'ST_UNUSED_GND', 'passive'), (6, 'VOUT', 'passive')],
         {1: 'USB_LEGACY_LIMITED', 2: 'GND', 3: 'USB_CHARGE_LIMITED', 5: 'GND', 6: 'USB_CHARGE_LIMITED'},
         sot+'SOT-363_SC-70-6', 'LM66100', 'CE=VOUT reverse protection on legacy path only (<0.5A). Does not imply zero reverse transient. ST is physically open-drain; modeled passive ONLY for the manufacturer-prescribed unused GND strap, avoiding a generic ERC open-drain/power-flag false conflict.')
    chip('usb-power-typec', 'U212', 'TPS259470ARPWR',
         [(1, 'EN_UVLO', 'input'), (2, 'OVLO', 'input'), (3, 'AUXOFF', 'open_collector'),
          (4, 'FLT', 'open_collector'), (5, 'IN', 'power_in'), (6, 'OUT', 'power_out'),
          (7, 'DVDT', 'passive'), (8, 'GND', 'power_in'), (9, 'ILM', 'passive'), (10, 'ITIMER', 'passive')],
         {1: 'USB_CC_POWER', 2: 'USB_OVLO', 5: 'USB_PC_VBUS', 6: 'USB_CHARGE_LIMITED',
          7: 'USB_DVDT', 8: 'GND', 9: 'USB_TYPEC_ILIM'},
         LOCAL_LIBRARY+':TI_RPW0010A', 'TPS25947',
         'Autonomous path only for CC>=1.5A. 2.80k -> nominal1.191A; parallel2.80k on CC3A ->2.381A. ITIMER open gives fastest current-limit response. True reverse blocking. Not a USB compliance guarantee.')
    r('usb-power-typec', 'R213', '2.80k 1%', 'USB_TYPEC_ILIM', 'GND')
    r('usb-power-typec', 'R214', '2.80k 1%', 'USB_TYPEC_ILIM', 'USB_ILIM_EXTRA')
    chip('usb-power-typec', 'Q200', '2N7002', [(1, 'G', 'input'), (2, 'S', 'passive'), (3, 'D', 'passive')],
         {1: 'USB_CC_3A', 2: 'GND', 3: 'USB_ILIM_EXTRA'}, sot+'SOT-23', '2N7002',
         'Low-current ILIM resistor selection. Finite Rds(on) reduces requested current; qualification at 3.3V gate and temperature required.')
    r('usb-power-typec', 'R215', '100k', 'USB_CC_3A', 'GND')
    r('usb-power-typec', 'R216', '348k 1%', 'USB_PC_VBUS', 'USB_OVLO')
    r('usb-power-typec', 'R217', '100k 1%', 'USB_OVLO', 'GND',
      'OVLO nominal5.376V; this is NOT proof that PiSugar 5.2V maximum input is protected. Source/module voltage tolerance remains a qualification gate.')
    cap('usb-power-typec', 'C214', '3.3nF C0G', 'USB_DVDT')
    cap('usb-power-typec', 'C215', '100nF', 'USB_PC_VBUS')
    cap('usb-power-typec', 'C216', '1uF 10V X7R', 'USB_CHARGE_LIMITED')
    conn(b, 'usb-power-typec', 'J121', ['USB_CHARGE_LIMITED', 'GND'], ['PISUGAR_INPUT_5V', 'GND'],
         footprint=LOCAL_LIBRARY+':Power_Pigtail_2Pad',
         note='Soldered 20/22AWG candidate wire pair to identified PiSugar INPUT pads, not BAT or 5V output. Confirm module pad polarity, wire strain relief, thermal rise and voltage drop. No parallel 5V_SYS connection.')
