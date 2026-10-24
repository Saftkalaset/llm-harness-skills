#!/usr/bin/env python3
"""Check nozzle-centre deposition bounds, including XY arcs and coordinate modes.

No firmware macros, travel collision, strength or thermal behavior is simulated.
Unknown motion formats fail closed. Binary G-code must first be exported as text.
"""
import argparse
import collections
import json
import math
import re
from pathlib import Path

WORDS = re.compile(r'([A-Za-z])([-+]?(?:\d+(?:\.\d*)?|\.\d+))')
TAU = 2 * math.pi


def arc_points(start, end, words, clockwise, absolute_center=False, offset=(0, 0, 0), tolerance=.05):
    """Endpoints and all XY cardinal extrema, with interpolated Z for helical arcs."""
    if 'R' in words:
        if 'I' in words or 'J' in words:
            raise ValueError('Arc combines R and I/J')
        radius = abs(words['R'])
        dx, dy = end[0]-start[0], end[1]-start[1]
        chord = math.hypot(dx, dy)
        if chord < 1e-10 or chord > 2*radius + tolerance:
            raise ValueError('Invalid radius arc')
        h = math.sqrt(max(0., radius*radius-chord*chord/4))
        mid = [(start[0]+end[0])/2, (start[1]+end[1])/2]
        candidates = [(mid[0]+sign*h*(-dy/chord), mid[1]+sign*h*(dx/chord)) for sign in (-1, 1)]
        selected = None
        for cx, cy in candidates:
            a0 = math.atan2(start[1]-cy, start[0]-cx);a1 = math.atan2(end[1]-cy, end[0]-cx)
            sweep = ((a0-a1) if clockwise else (a1-a0)) % TAU
            if (words['R'] >= 0 and sweep <= math.pi+1e-9) or (words['R'] < 0 and sweep >= math.pi-1e-9):
                selected = (cx, cy);break
        if selected is None:
            raise ValueError('Cannot resolve radius arc')
        cx, cy = selected
    else:
        if not ('I' in words or 'J' in words) or 'K' in words:
            raise ValueError('Expected XY I/J or R arc')
        if absolute_center:
            if not all(k in words for k in ('I', 'J')):
                raise ValueError('Absolute arc centre requires I and J')
            cx, cy = words['I']+offset[0], words['J']+offset[1]
        else:
            cx, cy = start[0]+words.get('I', 0), start[1]+words.get('J', 0)
    r0, r1 = math.hypot(start[0]-cx, start[1]-cy), math.hypot(end[0]-cx, end[1]-cy)
    if min(r0, r1) < 1e-10 or abs(r0-r1) > tolerance:
        raise ValueError('Inconsistent arc radii')
    radius = max(r0, r1)  # Conservative under endpoint rounding.
    a0 = math.atan2(start[1]-cy, start[0]-cx);a1 = math.atan2(end[1]-cy, end[0]-cx)
    direction = -1 if clockwise else 1
    sweep = ((a1-a0)*direction) % TAU
    if math.hypot(end[0]-start[0], end[1]-start[1]) < 1e-9:
        sweep = TAU
    if sweep < 1e-12:
        raise ValueError('Degenerate arc')
    result = [start, end]
    for angle in (0, math.pi/2, math.pi, 3*math.pi/2):
        progress = ((angle-a0)*direction) % TAU
        if progress <= sweep+1e-10:
            result.append([cx+radius*math.cos(angle), cy+radius*math.sin(angle),
                           start[2]+(end[2]-start[2])*min(1, progress/sweep)])
    return result


def validate_gcode(path, bed=(250, 220, 270), margin=0., bead_radius=0., startup_exceptions=None):
    """Return scoped pass/fail/unsupported with bounded diagnostics.

    startup_exceptions are explicit [xmin,xmax,ymin,ymax,zmin,zmax] boxes.
    They apply only to unclassified/Custom extrusion before the first layer or model
    deposition. There is no blanket exemption for Custom G-code.
    """
    bed = tuple(float(v) for v in bed)
    if len(bed) != 3 or any(not math.isfinite(v) or v <= 0 for v in bed):
        raise ValueError('bed must have three finite positive dimensions')
    if not math.isfinite(margin) or not math.isfinite(bead_radius) or min(margin, bead_radius) < 0:
        raise ValueError('margin and bead_radius must be finite and nonnegative')
    exceptions = startup_exceptions or []
    for box in exceptions:
        if len(box) != 6 or not all(math.isfinite(v) for v in box) or any(box[i]>box[i+1] for i in (0, 2, 4)):
            raise ValueError('Invalid startup exception box')
    report = {'status': 'fail', 'pass': False, 'issues': [], 'issue_counts': {}, 'bounds_mm': {},
              'deposition_commands': {}, 'statistics': {}, 'startup_exemptions': 0,
              'scope': 'Nozzle deposition paths plus optional XY bead radius; no travel/firmware/thermal/strength simulation',
              'assumptions': ['Initial units are millimetres; initial arc plane is XY; initial I/J centres are relative'],
              'bed_mm': bed, 'margin_mm': margin, 'bead_radius_mm': bead_radius}
    pos, offset, known = [0., 0., 0.], [0., 0., 0.], [False]*3
    e, absolute, relative_e, scale, center_absolute = 0., None, None, 1., False
    role, startup = '', True
    counts, issues = collections.Counter(), collections.Counter()

    def issue(kind, line, detail):
        issues[kind] += 1
        if len(report['issues']) < 20:
            report['issues'].append({'kind': kind, 'line': line, 'detail': detail})

    def include(points, number, command):
        key = role or 'unclassified'
        bounds = report['bounds_mm'].setdefault(key, [[float('inf'), -float('inf')] for _ in range(3)])
        exempt_path = startup and role in ('', 'Custom') and any(
            all(all(box[2*i]-1e-6 <= point[i] <= box[2*i+1]+1e-6 for i in range(3))
                for point in points) for box in exceptions)
        for point in points:
            for i, value in enumerate(point):
                bounds[i][0] = min(bounds[i][0], value);bounds[i][1] = max(bounds[i][1], value)
            extension = [bead_radius, bead_radius, 0.]
            # Z=first layer height need not clear the same XY placement margin.
            bad = any(point[i]-extension[i] < margin-1e-6 or point[i]+extension[i] > bed[i]-margin+1e-6 for i in (0,1)) or point[2]<-1e-6 or point[2]>bed[2]+1e-6
            if bad:
                if exempt_path:report['startup_exemptions'] += 1
                else:issue('out_of_volume', number, {'command': command, 'point_mm': point, 'role': key})

    try:
        with open(path, encoding='utf-8-sig') as stream:
            for number, line in enumerate(stream, 1):
                stripped = line.strip()
                if stripped.startswith(';TYPE:'):
                    role = stripped[6:]
                if stripped == ';LAYER_CHANGE':startup = False
                if stripped.startswith(('; estimated printing time', '; filament used')) and '=' in stripped:
                    key, val = stripped[2:].split('=', 1);report['statistics'][key.strip()] = val.strip()
                raw = re.sub(r'\([^)]*\)', '', line.split(';', 1)[0]).split('*', 1)[0].strip()
                if not raw:continue
                tokens = [(k.upper(), float(v)) for k,v in WORDS.findall(raw)]
                commands = [(k,v) for k,v in tokens if k in ('G','M')]
                if not commands and tokens and tokens[0][0] == 'T':
                    commands = [tokens[0]]
                if not commands:
                    issue('unsupported', number, 'Unrecognized executable line');continue
                if len(commands) > 1:
                    issue('unsupported', number, 'Multiple commands on one line');continue
                letter, value = commands[0];cmd = letter+format(value, 'g')
                words = {k:v for k,v in tokens if k not in ('G','M','N')}
                if not all(math.isfinite(v) for v in words.values()):
                    issue('unsupported', number, 'Non-finite coordinate');continue
                if cmd == 'G90':absolute = True;continue
                if cmd == 'G91':absolute = False;continue
                if cmd == 'M83':relative_e = True;continue
                if cmd == 'M82':relative_e = False;continue
                if cmd == 'G20':scale = 25.4;continue
                if cmd == 'G21':scale = 1.;continue
                if cmd == 'G90.1':center_absolute = True;continue
                if cmd == 'G91.1':center_absolute = False;continue
                if cmd == 'G17':continue
                if cmd in ('G18','G19'):
                    issue('unsupported', number, 'Non-XY arc plane');continue
                if cmd in ('G28','G29','G30'):
                    known = [False]*3;continue
                if cmd == 'G92':
                    if set(words) - set('XYZE'):
                        issue('unsupported', number, 'Unsupported coordinate reset parameter');continue
                    for i,k in enumerate('XYZ'):
                        if k in words:
                            if not known[i]:issue('unsupported', number, 'G92 axis reset without a known machine position')
                            offset[i] = pos[i]-words[k]*scale
                    if 'E' in words:e = words['E']*scale
                    continue
                if cmd not in ('G0','G1','G2','G3'):
                    if letter == 'G' and cmd not in ('G4','G10','G11','G80'):
                        issue('unsupported', number, 'Unsupported coordinate/motion command '+cmd)
                    continue
                allowed = set('XYZEFIJR') if cmd in ('G2','G3') else set('XYZEF')
                if set(words) - allowed:
                    issue('unsupported', number, 'Unsupported motion parameters: '+','.join(sorted(set(words)-allowed)));continue
                if WORDS.sub('', raw).strip():
                    issue('unsupported', number, 'Unparsed motion syntax');continue
                letters = [k for k,v in tokens if k in 'XYZEFIJKR']
                if len(letters) != len(set(letters)):
                    issue('unsupported', number, 'Duplicate motion parameter');continue
                if absolute is None:
                    issue('unsupported', number, 'Missing G90/G91 positioning mode');continue
                previous_known = known[:];start = pos[:];end = pos[:]
                for i,k in enumerate('XYZ'):
                    if k in words:
                        end[i] = words[k]*scale+offset[i] if absolute else pos[i]+words[k]*scale
                        known[i] = absolute or known[i]
                de = 0.
                if 'E' in words:
                    if relative_e is None:
                        issue('unsupported', number, 'Missing M82/M83 extrusion mode')
                    else:
                        de = words['E']*scale if relative_e else words['E']*scale-e
                        e = e+words['E']*scale if relative_e else words['E']*scale
                spatial = any(abs(end[i]-start[i])>1e-10 for i in range(3)) or cmd in ('G2','G3')
                if de > 0 and spatial:
                    if role not in ('', 'Custom'):startup = False
                    if not all(previous_known) or not all(known):
                        issue('unsupported', number, 'Deposition starts at unknown machine coordinates')
                    else:
                        try:
                            points = arc_points(start, end, {k:v*scale for k,v in words.items()}, cmd=='G2', center_absolute, offset) if cmd in ('G2','G3') else [start,end]
                            include(points, number, cmd);counts[cmd] += 1
                        except ValueError as exc:issue('unsupported', number, str(exc))
                pos = end
    except (OSError, UnicodeError) as exc:
        issue('unsupported', 0, str(exc))
    if not counts:issue('unsupported', 0, 'No verified deposition paths')
    report['deposition_commands'] = dict(counts);report['issue_counts'] = dict(issues)
    report['pass'] = not issues
    report['status'] = 'pass' if report['pass'] else ('unsupported' if issues['unsupported'] else 'fail')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path');parser.add_argument('--bed', nargs=3, type=float, required=True)
    parser.add_argument('--margin', type=float, default=0);parser.add_argument('--bead-radius', type=float, default=0)
    parser.add_argument('--startup-exception', action='append', default=[], metavar='XMIN,XMAX,YMIN,YMAX,ZMIN,ZMAX')
    parser.add_argument('--report')
    args = parser.parse_args()
    try:
        report = validate_gcode(args.path, args.bed, args.margin, args.bead_radius,
                                [[float(v) for v in b.split(',')] for b in args.startup_exception])
    except ValueError as exc:
        report = {'status': 'unsupported', 'pass': False, 'issues': [str(exc)]}
    encoded = json.dumps(report, indent=2)
    if args.report:Path(args.report).write_text(encoded+'\n')
    print(encoded)
    return 0 if report['pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
