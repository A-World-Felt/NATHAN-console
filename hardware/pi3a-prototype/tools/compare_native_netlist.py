"""Compare KiCad's exported XML with the proposed pin model, without running CAD."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('board', choices=['controls', 'base'])
    args = parser.parse_args()
    model_path = ROOT / 'electrical/design-networks.json'
    native_path = ROOT / 'validation/native-current' / (args.board + '-native.net')
    model = json.loads(model_path.read_text(encoding='utf-8'))
    components = [c for c in model['components'] if c['board'] == args.board
                  and not c['reference'].startswith('#')]
    expected = {(c['reference'], str(p['number'])): p['net']
                for c in components for p in c['pins']}
    actual = {}
    duplicates = []
    tree = ET.parse(native_path)
    for net in tree.findall('./nets/net'):
        for node in net.findall('node'):
            key = (node.get('ref'), node.get('pin'))
            if key[0].startswith('#'):
                continue
            if key in actual:
                duplicates.append(key)
            name = net.get('name')
            actual[key] = None if name.startswith('unconnected-(') else name
    differences = [{'reference': ref, 'pin': pin,
                    'expected': expected.get((ref, pin), '<missing>'),
                    'actual': actual.get((ref, pin), '<missing>')}
                   for ref, pin in sorted(expected.keys() | actual.keys())
                   if expected.get((ref, pin), '<missing>') != actual.get((ref, pin), '<missing>')]
    report = {'board': args.board, 'physical_components': len(components),
              'pins_compared': len(expected), 'duplicate_nodes': duplicates,
              'differences': differences,
              'model_sha256': hashlib.sha256(model_path.read_bytes()).hexdigest(),
              'native_netlist_sha256': hashlib.sha256(native_path.read_bytes()).hexdigest(),
              'scope': 'Pin-to-net agreement only; no component, PCB or circuit qualification.'}
    dest = ROOT / 'validation/native-current' / (args.board + '-netlist-comparison.json')
    dest.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    if differences or duplicates:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
