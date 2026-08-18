#!/usr/bin/env python3
"""Dump Ozone XML Param ElementID/ParamID/Value and ElementChain if possible."""
import argparse, base64, struct, xml.etree.ElementTree as ET
from pathlib import Path

def decode_chain(data):
    if not data:
        return []
    b=base64.b64decode(data)
    out=[]; i=0
    while i < len(b):
        if i>=len(b): break
        if b[i] != 0:
            raise ValueError(f"Expected 00 marker at {i}, got {b[i]:02x}")
        i += 1
        if i+4 > len(b): break
        n=struct.unpack('<I', b[i:i+4])[0]
        i += 4
        name=b[i:i+n].decode('utf-8')
        i += n
        out.append(name)
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('xml')
    args=ap.parse_args()
    root=ET.parse(args.xml).getroot()
    for eb in root.iter('ExtraBytes'):
        if eb.get('ElementID') == 'ElementChain':
            try:
                print('ElementChain:', ' -> '.join(decode_chain(eb.get('Data',''))))
            except Exception as e:
                print('ElementChain decode error:', e)
    for p in root.iter('Param'):
        print(f"{p.get('ElementID')}\t{p.get('ParamID')}\t{p.get('Value')}")
if __name__ == '__main__':
    main()
