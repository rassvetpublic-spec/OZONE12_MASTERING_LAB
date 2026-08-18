#!/usr/bin/env python3
"""Patch Ozone 12 Stereo Imager Transient/Sustain XML params.
Usage:
  python patch_ozone_imager_ts.py input.xml output.xml --preset strong
  python patch_ozone_imager_ts.py input.xml output.xml --module-amount 58 --t -20 0 8 5 --s -5 22 72 52 --recover-transient 0 --recover-sustain 1.2
Notes:
  - Patches existing Param nodes only; it does not rebuild ElementChain.
  - Check in Ozone UI after import.
"""
from __future__ import annotations
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

PRESETS = {
    'safe': dict(module_amount=45, t=[-15,0,5,5], s=[-5,12,45,35], rt=0.0, rs=0.6, c=[165,3000,12000]),
    'strong': dict(module_amount=58, t=[-20,0,8,5], s=[-5,22,72,52], rt=0.0, rs=1.2, c=[165.70428467,3484.03076172,11999.37695312]),
    'extreme': dict(module_amount=68, t=[-25,-5,0,0], s=[0,30,90,70], rt=0.0, rs=1.8, c=[165.70428467,3484.03076172,11999.37695312]),
}

def fmt(x):
    if isinstance(x, str): return x
    return f"{float(x):.8f}".replace('.', ',')

def set_param(root, eid, pid, value, add_if_missing=False):
    found=False
    for p in root.iter():
        if p.attrib.get('ElementID') == eid and p.attrib.get('ParamID') == pid:
            p.set('Value', fmt(value)); found=True
    if not found and add_if_missing:
        # Add near first Param if possible. This may not be accepted by every Ozone XML; prefer source templates with existing params.
        root.append(ET.Element('Param', {'ElementID': eid, 'ParamID': pid, 'Value': fmt(value)}))
    if not found:
        print(f"WARN: missing Param ElementID={eid!r} ParamID={pid!r}; not added")
    return found

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('input_xml')
    ap.add_argument('output_xml')
    ap.add_argument('--preset', choices=PRESETS.keys(), default=None)
    ap.add_argument('--module-amount', type=float, default=None)
    ap.add_argument('--t', type=float, nargs=4, metavar=('B1','B2','B3','B4'))
    ap.add_argument('--s', type=float, nargs=4, metavar=('B1','B2','B3','B4'))
    ap.add_argument('--recover-transient', type=float, default=None)
    ap.add_argument('--recover-sustain', type=float, default=None)
    ap.add_argument('--stereoize', choices=['off','on'], default='off')
    args=ap.parse_args()
    cfg = PRESETS.get(args.preset, {}).copy()
    if args.module_amount is not None: cfg['module_amount']=args.module_amount
    if args.t is not None: cfg['t']=args.t
    if args.s is not None: cfg['s']=args.s
    if args.recover_transient is not None: cfg['rt']=args.recover_transient
    if args.recover_sustain is not None: cfg['rs']=args.recover_sustain
    if 't' not in cfg or 's' not in cfg:
        raise SystemExit('Need --preset or both --t and --s')

    tree=ET.parse(args.input_xml)
    root=tree.getroot()
    E='Stereo Imager'
    set_param(root,E,'Processing Mode',1)
    set_param(root,E,'Transient/Sustain Selection',1)
    if 'module_amount' in cfg: set_param(root,E,'Module Amount',cfg['module_amount'])
    if 'c' in cfg:
        for i,v in enumerate(cfg['c'],1): set_param(root,E,f'Crossover Cutoff {i}',v)
    for i,v in enumerate(cfg['t'],1): set_param(root,E,f'Band {i} Width Percent',v)
    for i,v in enumerate(cfg['s'],1): set_param(root,E,f'Aux: Band {i} Width Percent',v)
    set_param(root,E,'Recover Sides Enabled',1)
    set_param(root,E,'Recover Sides Gain Offset (dB)',cfg.get('rt',0.0))
    set_param(root,E,'Aux: Recover Sides Enabled',1)
    set_param(root,E,'Aux: Recover Sides Gain Offset (dB)',cfg.get('rs',0.8))
    set_param(root,E,'Enable Stereoizer', 1 if args.stereoize=='on' else 0)
    tree.write(args.output_xml, encoding='utf-8', xml_declaration=True)
    print(f'Wrote {args.output_xml}')
    print('Check in Ozone UI: ElementChain, Stereo Imager visible, T/S mode, Stereoize off, Recover Sides values.')
if __name__ == '__main__': main()
