#!/usr/bin/env python3
"""
Patch only the <Maximizer> block in an Ozone 12 XML preset.
Keeps comma decimals and warns if Maximizer is not present in ElementChain.

Usage:
  python patch_ozone_maximizer.py input.xml output.xml --profile streaming-safe
  python patch_ozone_maximizer.py input.xml output.xml --gain 2.6 --margin -2.0 --target -12.0
"""
import argparse, base64, re, struct, sys, time
from pathlib import Path

PROFILES = {
    "streaming-safe": {
        "Mode": "3",
        "Margin": -2.0,
        "Prevent Intersample Clipping": "1",
        "Character": 2.5,
        "EnableLowLevelBoost": "1",
        "LowLevelBoostWetAmount": 0.8,
        "Gain": 2.5,
        "Stereo Link": 70.0,
        "Stereo Transient Link Amount": 70.0,
        "Target Loudness [dB]": -12.0,
        "Soft Clip Enable": "0",
        "Soft Clip Amount": 0.0,
    },
    "wow-pop": {
        "Mode": "3",
        "Margin": -2.0,
        "Prevent Intersample Clipping": "1",
        "Character": 2.2,
        "EnableLowLevelBoost": "1",
        "LowLevelBoostWetAmount": 1.1,
        "Gain": 2.6,
        "Stereo Link": 60.0,
        "Stereo Transient Link Amount": 60.0,
        "Target Loudness [dB]": -11.8,
        "Soft Clip Enable": "0",
        "Soft Clip Amount": 0.0,
    },
    "codec-safe": {
        "Mode": "3",
        "Margin": -2.5,
        "Prevent Intersample Clipping": "1",
        "Character": 2.5,
        "Gain": 1.8,
        "Target Loudness [dB]": -12.5,
        "Soft Clip Enable": "0",
        "Soft Clip Amount": 0.0,
    },
    "loud-probe": {
        "Mode": "3",
        "Margin": -1.5,
        "Prevent Intersample Clipping": "1",
        "Character": 2.5,
        "Gain": 4.0,
        "Target Loudness [dB]": -11.0,
        "Soft Clip Enable": "0",
        "Soft Clip Amount": 0.0,
    },
}

def fmt_value(v):
    if isinstance(v, str):
        return v
    return f"{float(v):.8f}".replace('.', ',')

def decode_element_chain(text):
    m = re.search(r'<ExtraBytes\s+ElementID="ElementChain"\s+Data="([^"]*)"\s*/>', text)
    if not m:
        return None
    data = base64.b64decode(m.group(1))
    pos, names = 0, []
    while pos < len(data):
        if data[pos] != 0:
            # Try to resync but warn by returning what was decoded.
            break
        pos += 1
        if pos + 4 > len(data):
            break
        ln = struct.unpack_from('<I', data, pos)[0]
        pos += 4
        raw = data[pos:pos+ln]
        pos += ln
        try:
            names.append(raw.decode('utf-8'))
        except UnicodeDecodeError:
            names.append(raw.decode('utf-8', 'replace'))
    return names

def patch_param(block, param_id, value):
    value = fmt_value(value)
    pattern = re.compile(r'(<Param\s+ElementID="Maximizer"\s+ParamID="' + re.escape(param_id) + r'"\s+Value=")([^"]*)("\s*/>)')
    if pattern.search(block):
        return pattern.sub(r'\g<1>' + value + r'\g<3>', block), True
    insert = f'        <Param ElementID="Maximizer" ParamID="{param_id}" Value="{value}" />\n'
    eb = re.search(r'\s*<ExtraBytes\s+ElementID="Maximizer"\s+Data="[^"]*"\s*/>', block)
    if eb:
        return block[:eb.start()] + insert + block[eb.start():], False
    return block + "\n" + insert, False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input_xml')
    ap.add_argument('output_xml')
    ap.add_argument('--profile', choices=sorted(PROFILES.keys()), default=None)
    ap.add_argument('--gain', type=float)
    ap.add_argument('--margin', type=float)
    ap.add_argument('--target', type=float)
    ap.add_argument('--character', type=float)
    ap.add_argument('--soft-clip-enable', choices=['0','1'])
    ap.add_argument('--comments-suffix', default=' MAX_PATCH')
    args = ap.parse_args()

    text = Path(args.input_xml).read_text(encoding='utf-8', errors='ignore')
    chain = decode_element_chain(text)
    if chain is None:
        print('WARN: ElementChain not found. Check visible chain in Ozone manually.', file=sys.stderr)
    else:
        print('ElementChain:', ' -> '.join(chain))
        if 'Maximizer' not in chain:
            print('WARN: Maximizer is not in ElementChain. Enabled=1 is not enough.', file=sys.stderr)
        elif chain[-1] != 'Maximizer':
            print('WARN: Maximizer is present but not last. True Peak/loudness may not be final.', file=sys.stderr)

    m = re.search(r'(<Maximizer\b[^>]*>)(.*?)(</Maximizer>)', text, re.S)
    if not m:
        print('ERROR: <Maximizer> block not found.', file=sys.stderr)
        sys.exit(2)

    settings = {}
    if args.profile:
        settings.update(PROFILES[args.profile])
    if args.gain is not None:
        settings['Gain'] = args.gain
    if args.margin is not None:
        settings['Margin'] = args.margin
    if args.target is not None:
        settings['Target Loudness [dB]'] = args.target
    if args.character is not None:
        settings['Character'] = args.character
    if args.soft_clip_enable is not None:
        settings['Soft Clip Enable'] = args.soft_clip_enable
        if args.soft_clip_enable == '0':
            settings['Soft Clip Amount'] = 0.0

    if not settings:
        print('ERROR: no settings supplied. Use --profile or explicit args.', file=sys.stderr)
        sys.exit(2)

    block = m.group(2)
    for k, v in settings.items():
        block, existed = patch_param(block, k, v)
        print(('set' if existed else 'insert'), k, '=', fmt_value(v))

    out = text[:m.start(2)] + block + text[m.end(2):]
    # Make preset unique enough to avoid Ozone cache confusion.
    out = re.sub(r'(Comments=")([^"]*)"', lambda mm: mm.group(1) + mm.group(2) + args.comments_suffix + ' ' + time.strftime('%Y%m%d_%H%M%S') + '"', out, count=1)
    Path(args.output_xml).write_text(out, encoding='utf-8')
    print('Wrote', args.output_xml)

if __name__ == '__main__':
    main()
