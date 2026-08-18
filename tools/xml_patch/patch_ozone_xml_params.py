#!/usr/bin/env python3
"""Patch known Ozone XML Param values from a JSON map.
JSON shape:
{
  "Maximizer": {"Gain": "2,60000000", "Margin": "-2,00001144"},
  "Stereo Imager": {"Enable Stereoizer": "0"}
}
"""
import argparse, json, shutil, time, xml.etree.ElementTree as ET
from pathlib import Path

def patch(xml_in, json_patch, xml_out):
    tree=ET.parse(xml_in)
    root=tree.getroot()
    patch=json.load(open(json_patch, encoding='utf-8'))
    changed=[]; missing=[]
    for eid, params in patch.items():
        for pid, newval in params.items():
            found=False
            for p in root.iter('Param'):
                if p.get('ElementID') == eid and p.get('ParamID') == pid:
                    old=p.get('Value')
                    p.set('Value', str(newval))
                    changed.append((eid,pid,old,str(newval)))
                    found=True
            if not found:
                missing.append((eid,pid))
    root.set('LastModified', str(int(time.time())))
    tree.write(xml_out, encoding='utf-8', xml_declaration=True)
    return changed, missing

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--in', dest='xml_in', required=True)
    ap.add_argument('--patch', required=True)
    ap.add_argument('--out', dest='xml_out', required=True)
    args=ap.parse_args()
    changed, missing=patch(args.xml_in,args.patch,args.xml_out)
    print('Changed:')
    for r in changed:
        print('\t'.join(r))
    if missing:
        print('Missing:')
        for r in missing:
            print('\t'.join(r))
if __name__ == '__main__':
    main()
