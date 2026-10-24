#!/usr/bin/env python3
"""Discover and probe a PrusaSlicer-compatible CLI without opening its GUI."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def run_process(argv, cwd, log_path, timeout=120):
    """Run argv synchronously; keep logs off stdout and stop orphaned launchers.

    Never changes permissions, invokes a shell, installs software or retries with
    broader access. On POSIX a private process group also bounds child lifetime.
    """
    if not isinstance(argv, (list, tuple)) or not argv or not all(isinstance(a, str) for a in argv) or not argv[0]:
        raise ValueError('command must be a nonempty argv list of strings')
    if timeout <= 0:
        raise ValueError('timeout must be positive')
    log_path = Path(log_path)
    start = time.monotonic()
    result = {'command': argv, 'log': str(log_path), 'returncode': None}
    proc = None
    with log_path.open('wb') as log:
        try:
            proc = subprocess.Popen(argv, cwd=str(cwd), stdout=log,
                                    stderr=subprocess.STDOUT,
                                    start_new_session=os.name == 'posix')
            result['returncode'] = proc.wait(timeout=timeout)
            result['status'] = 'pass' if proc.returncode == 0 else 'fail'
        except subprocess.TimeoutExpired:
            result.update(status='timeout', error='command exceeded timeout')
            if os.name == 'posix':
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                proc.kill()
            proc.wait()
        except OSError as exc:
            result.update(status='fail', error=str(exc))
        finally:
            # A wrapper that backgrounds its child is not a synchronous CLI.
            # Do not leave it writing artifacts after its reported completion.
            if proc is not None and os.name == 'posix':
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
    result['elapsed_seconds'] = round(time.monotonic() - start, 3)
    return result


def discover_commands():
    """Return candidates; discovery never starts the slicer or changes defaults."""
    candidates = []
    seen = set()
    for name in ('prusa-slicer', 'PrusaSlicer', 'prusa-slicer-console',
                 'prusa-slicer-console.exe', 'prusa-slicer.exe'):
        executable = shutil.which(name)
        if executable and executable not in seen:
            seen.add(executable)
            candidates.append({'kind': 'native', 'command': [executable]})
    flatpak = shutil.which('flatpak')
    if flatpak:
        try:
            output = subprocess.run(
                [flatpak, 'list', '--app', '--columns=application,branch,arch'],
                capture_output=True, text=True, timeout=10, check=True).stdout
        except (OSError, subprocess.SubprocessError):
            output = ''
        for line in output.splitlines():
            fields = line.split()
            if len(fields) >= 3 and fields[0] == 'com.prusa3d.PrusaSlicer':
                app, branch, arch = fields[:3]
                candidates.append({'kind': 'flatpak', 'branch': branch,
                                   'command': [flatpak, 'run',
                                               '--command=prusa-slicer',
                                               f'{app}/{arch}/{branch}']})
    return sorted(candidates, key=lambda c: (c.get('branch', '') != 'stable',
                                             c.get('branch', '') == 'beta',
                                             c['command']))


def _write_probe(path):
    faces = [((0, 0, 0), (0, 10, 0), (10, 0, 0)),
             ((0, 0, 0), (10, 0, 0), (0, 0, 10)),
             ((0, 0, 0), (0, 0, 10), (0, 10, 0)),
             ((10, 0, 0), (0, 10, 0), (0, 0, 10))]
    lines = ['solid cli_probe']
    for face in faces:
        lines.extend(['facet normal 0 0 0', 'outer loop'])
        lines.extend('vertex %s %s %s' % vertex for vertex in face)
        lines.extend(['endloop', 'endfacet'])
    lines.append('endsolid cli_probe')
    Path(path).write_text('\n'.join(lines) + '\n')


def validate_stl(path):
    """Basic parseability check for a CLI probe, not a manifold certification."""
    import struct
    data = Path(path).read_bytes()
    if len(data) >= 84:
        count = struct.unpack('<I', data[80:84])[0]
        if count and len(data) == 84 + count * 50:
            for facet in struct.iter_unpack('<12fH', data[84:]):
                if not all(__import__('math').isfinite(x) for x in facet[:12]):
                    raise ValueError('STL contains non-finite coordinates')
            return {'triangles': count, 'format': 'binary'}
    text = data.decode('ascii')
    vertices = re.findall(r'\bvertex\s+([-+\deE.]+)\s+([-+\deE.]+)\s+([-+\deE.]+)', text)
    count = len(re.findall(r'\bendfacet\b', text))
    if not text.lstrip().startswith('solid') or count == 0 or len(vertices) != count * 3:
        raise ValueError('not a parseable nonempty STL')
    for vertex in vertices:
        if not all(__import__('math').isfinite(float(v)) for v in vertex):
            raise ValueError('STL contains non-finite coordinates')
    return {'triangles': count, 'format': 'ascii'}


def probe_command(command, work_dir=None, timeout=30, cache_path=None):
    """Verify help and an actual export in an isolated directory.

    Choose a work_dir visible to the CLI sandbox. Permission failures are
    reported; this function does not mount additional host paths automatically.
    An explicitly supplied cache reuses only a previously successful probe when
    the command, executable signature, help/version and working parent match.
    """
    if not isinstance(command, (list, tuple)) or not command or not all(isinstance(a, str) for a in command) or not command[0]:
        raise ValueError('command must be a nonempty argv list of strings')
    work_dir = Path(work_dir or Path.cwd()).resolve()
    report = {'command': list(command), 'status': 'fail', 'issues': []}
    with tempfile.TemporaryDirectory(prefix='slicer-probe-', dir=work_dir) as tmp:
        tmp = Path(tmp)
        help_result = run_process(list(command) + ['--help'], tmp, tmp / 'help.log', timeout)
        help_text = (tmp / 'help.log').read_text(errors='replace')
        report['help_returncode'] = help_result['returncode']
        if help_result['status'] != 'pass' or '--export-stl' not in help_text:
            report['issues'].append('CLI help failed or does not advertise --export-stl')
            report['diagnostic'] = help_text[-2000:]
            return report
        version = next((line.strip() for line in help_text.splitlines()
                        if re.search(r'PrusaSlicer[- ]?\d', line)), 'unidentified')
        report['version'] = version
        signature = []
        for item in [shutil.which(command[0]) or command[0], *command[1:]]:
            try:
                candidate = Path(item)
                if candidate.is_file():
                    stat = candidate.stat()
                    signature.append([str(candidate.resolve()), stat.st_size, stat.st_mtime_ns])
            except OSError:
                pass
        cache_key = hashlib.sha256(json.dumps(
            [command, signature, help_text, str(work_dir), sys.platform],
            sort_keys=True).encode()).hexdigest()
        if cache_path:
            try:
                cached = json.loads(Path(cache_path).read_text())
                if cached['key'] == cache_key and cached['report']['status'] == 'pass':
                    return dict(cached['report'], cached=True)
            except (OSError, ValueError, KeyError, TypeError):
                pass
        input_path, output_path = tmp / 'probe-input.stl', tmp / 'probe-output.stl'
        _write_probe(input_path)
        argv = list(command) + ['--datadir', str(tmp / 'state'), '--export-stl',
                                '--output', str(output_path), str(input_path)]
        process = run_process(argv, tmp, tmp / 'export.log', timeout)
        report['process_status'] = process['status']
        if process['status'] != 'pass':
            report['issues'].append('export process failed or timed out')
        elif not output_path.is_file() or output_path.stat().st_size == 0:
            report['issues'].append('CLI returned success without a nonempty output; check launcher behavior and path access')
        else:
            try:
                report['output'] = validate_stl(output_path)
                if report['output']['triangles'] != 4:
                    report['issues'].append('probe export did not preserve the four input triangles')
            except (ValueError, OSError, UnicodeError) as exc:
                report['issues'].append('unparseable probe output: ' + str(exc))
        if report['issues']:
            report['diagnostic'] = (tmp / 'export.log').read_text(errors='replace')[-2000:]
        else:
            report['status'] = 'pass'
            if cache_path:
                Path(cache_path).write_text(json.dumps({'key': cache_key, 'report': report}, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--command-json', help='Explicit CLI argv JSON array; otherwise discover installations')
    parser.add_argument('--probe', action='store_true', help='Run help and a small isolated STL export')
    parser.add_argument('--work-dir', type=Path, default=Path.cwd())
    parser.add_argument('--timeout', type=float, default=30)
    parser.add_argument('--cache', type=Path, help='Optional machine-local successful-probe cache')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    try:
        if args.command_json:
            command = json.loads(args.command_json)
            if not isinstance(command, list) or not command or not all(isinstance(a, str) for a in command) or not command[0]:
                raise ValueError('--command-json must be a nonempty argv JSON array of strings')
            commands = [{'kind': 'explicit', 'command': command}]
        else:
            commands = discover_commands()
        if args.cache and len(commands) != 1:
            parser.error('--cache requires one explicit command')
        report = {'candidates': commands}
        if args.probe:
            report['probes'] = [probe_command(c['command'], args.work_dir, args.timeout, args.cache)
                                for c in commands]
            report['status'] = 'pass' if any(p['status'] == 'pass' for p in report['probes']) else 'fail'
        else:
            report['status'] = 'discovered' if commands else 'unavailable'
        if args.report:
            args.report.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
        return 0 if report['status'] in ['pass', 'discovered'] else 1
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({'status': 'fail', 'issues': [str(exc)]}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
