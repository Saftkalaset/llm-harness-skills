#!/usr/bin/env python3
"""Inspect 3MF geometry/configuration or package a verified slicer configuration.

Uses the standard library. No printer connection or application settings are changed.
"""
import argparse
import collections
import hashlib
import io
import json
import math
import os
import posixpath
import re
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

CONFIG_PART = 'Metadata/Slic3r_PE.config'
CORE = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
NS = {'m': CORE}
UNITS = {'micron': .001, 'millimeter': 1., 'centimeter': 10., 'inch': 25.4,
         'foot': 304.8, 'meter': 1000.}


def sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _parse_config(lines, serialized=False):
    result = {}
    for line in lines:
        line = line.strip()
        if serialized and line.startswith(';'):
            line = line[1:].strip()
        elif line.startswith(('#', ';')):
            continue
        if not line:
            continue
        if line.startswith('['):
            raise ValueError('Expected one resolved configuration, not a preset bundle with sections')
        if '=' not in line:
            if serialized:
                continue  # Slicer version header.
            raise ValueError('Invalid configuration line: ' + line[:80])
        key, value = (s.strip() for s in line.split('=', 1))
        if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', key):
            raise ValueError('Invalid configuration key: ' + key)
        if key in result and result[key] != value:
            raise ValueError('Conflicting configuration values: ' + key)
        result[key] = value
    if not result:
        raise ValueError('Configuration is empty')
    if result.get('inherits', '').strip():
        raise ValueError('Unresolved preset inheritance; provide a flattened configuration')
    return result


def config_from_gcode(path):
    """Extract the complete serialized PrusaSlicer configuration, without loading toolpaths."""
    block, active, complete = [], False, False
    with open(path, encoding='utf-8-sig') as stream:
        for line in stream:
            if line.strip() == '; prusaslicer_config = begin':
                if active or complete:
                    raise ValueError('Multiple configuration blocks')
                active = True
            elif line.strip() == '; prusaslicer_config = end':
                if not active:
                    raise ValueError('Configuration end without begin')
                active, complete = False, True
            elif active:
                block.append(line)
    if active or not complete:
        raise ValueError('Missing or incomplete serialized G-code configuration')
    return _parse_config(block, serialized=True)


def load_config(path):
    path = Path(path)
    if path.suffix.lower() in ('.gcode', '.gco'):
        return config_from_gcode(path)
    lines = path.read_text(encoding='utf-8-sig').splitlines()
    raw = any('=' in s and not s.lstrip().startswith(('#', ';')) for s in lines)
    return _parse_config(lines, serialized=not raw)


def config_mismatches(config, expected):
    def normalized(value):
        text = str(value).strip().strip('"')
        if re.fullmatch(r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?%?', text):
            number = text.rstrip('%')
            return (float(number), text.endswith('%'))
        return text
    return {k: {'expected': str(v), 'actual': config.get(k)}
            for k, v in (expected or {}).items()
            if k not in config or normalized(config[k]) != normalized(v)}


def _transform(text, scale=1.):
    values = [float(x) for x in text.split()] if text else [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]
    if len(values) != 12 or not all(math.isfinite(x) for x in values):
        raise ValueError('Invalid instance transform')
    determinant = (values[0]*(values[4]*values[8]-values[7]*values[5])
                   -values[3]*(values[1]*values[8]-values[7]*values[2])
                   +values[6]*(values[1]*values[5]-values[4]*values[2]))
    if determinant == 0 or not math.isfinite(determinant):
        raise ValueError('Singular instance transform')
    return [[values[0], values[3], values[6], values[9] * scale],
            [values[1], values[4], values[7], values[10] * scale],
            [values[2], values[5], values[8], values[11] * scale], [0, 0, 0, 1]]


def _multiply(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def _point(matrix, point):
    return [sum(matrix[i][j] * point[j] for j in range(3)) + matrix[i][3] for i in range(3)]


def inspect_3mf(path, require_config=False, expected=None):
    """Check core meshes, component graph, printable instances, units and print metadata.

    Edge incidence is a mesh-integrity check, not self-intersection or mechanical validation.
    External component parts inside the package are supported; mixed-unit components fail closed.
    """
    report = {'path': str(path), 'sha256': sha256(path), 'pass': False,
              'status': 'fail', 'issues': [], 'meshes': [], 'instances': [], 'config': {}}
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise ValueError('Duplicate archive members')
            models = {}
            for name in names:
                if name.endswith('.model'):
                    content = archive.read(name)
                    namespaces = {}
                    for event, binding in ET.iterparse(io.BytesIO(content), events=('start-ns','start')):
                        if event == 'start':break
                        namespaces[binding[0]] = binding[1]
                    root = ET.fromstring(content)
                    if root.tag != '{' + CORE + '}model':
                        raise ValueError('Unsupported model namespace')
                    supported = {CORE, 'http://schemas.microsoft.com/3dmanufacturing/production/2015/06'}
                    for prefix in root.get('requiredextensions', '').split():
                        if namespaces.get(prefix) not in supported:
                            raise ValueError('Unsupported required 3MF extension: '+prefix)
                    unit = root.get('unit', 'millimeter')
                    if unit not in UNITS:
                        raise ValueError('Unsupported unit: ' + unit)
                    objects = root.findall('m:resources/m:object', NS)
                    identifiers = [o.get('id') for o in objects]
                    if None in identifiers or len(identifiers) != len(set(identifiers)):
                        raise ValueError('Missing or duplicate object IDs')
                    models[name] = (root, UNITS[unit], dict(zip(identifiers, objects)))
            root_path = None
            if '_rels/.rels' in names:
                rels = ET.fromstring(archive.read('_rels/.rels'))
                for rel in rels:
                    if rel.get('Type', '').endswith('/3dmodel'):
                        root_path = posixpath.normpath(rel.get('Target', '').lstrip('/'))
                        break
            if root_path is None:
                raise ValueError('Missing 3MF root model relationship')
            if root_path not in models:
                raise ValueError('Root model part is missing')
            if CONFIG_PART in names:
                report['config'] = _parse_config(archive.read(CONFIG_PART).decode('utf-8-sig').splitlines(), True)
            if require_config and not report['config']:
                report['issues'].append('Missing embedded print configuration')
            mismatches = config_mismatches(report['config'], expected)
            if mismatches:
                report['issues'].append({'configuration_mismatches': mismatches})
            mesh_data = {}
            all_points = []

            def visit(part, ident, transform, stack):
                key = (part, ident)
                if key in stack:
                    raise ValueError('Cyclic component references')
                if part not in models or ident not in models[part][2]:
                    raise ValueError('Missing component: ' + repr(key))
                _, scale, objects = models[part]
                obj = objects[ident]
                mesh = obj.find('m:mesh', NS)
                if mesh is not None:
                    if key not in mesh_data:
                        vertices = [tuple(float(v.get(k)) * scale for k in ('x', 'y', 'z'))
                                    for v in mesh.findall('m:vertices/m:vertex', NS)]
                        triangles = [tuple(int(t.get(k)) for k in ('v1', 'v2', 'v3'))
                                     for t in mesh.findall('m:triangles/m:triangle', NS)]
                        if not vertices or not triangles or not all(math.isfinite(q) for v in vertices for q in v):
                            raise ValueError('Empty or non-finite mesh')
                        edges, directed, adjacency = collections.Counter(), collections.Counter(), collections.defaultdict(set)
                        zero_area = 0
                        for tri in triangles:
                            if min(tri) < 0 or max(tri) >= len(vertices):
                                raise ValueError('Triangle index out of range')
                            a, b, c = (vertices[i] for i in tri)
                            u = [b[i] - a[i] for i in range(3)]; v = [c[i] - a[i] for i in range(3)]
                            cross = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
                            zero_area += sum(x*x for x in cross) <= 1e-20
                            for i, j in zip(tri, tri[1:] + tri[:1]):
                                edges[tuple(sorted((i, j)))] += 1; directed[i, j] += 1
                                adjacency[i].add(j); adjacency[j].add(i)
                        bad_edges = sum(n != 2 for n in edges.values())
                        bad_winding = sum(directed[i, j] != directed[j, i] for i, j in edges)
                        remaining = set(adjacency); shells = 0
                        while remaining:
                            todo = [remaining.pop()]; shells += 1
                            while todo:
                                for v in adjacency[todo.pop()]:
                                    if v in remaining:remaining.remove(v);todo.append(v)
                        summary = {'part': part, 'id': ident, 'vertices': len(vertices),
                                   'triangles': len(triangles), 'shells': shells, 'bad_edges': bad_edges,
                                   'bad_winding_edges': bad_winding, 'zero_area_triangles': zero_area}
                        report['meshes'].append(summary)
                        if bad_edges or bad_winding or zero_area:
                            report['issues'].append({'mesh_integrity': summary})
                        mesh_data[key] = vertices
                    all_points.extend(_point(transform, p) for p in mesh_data[key])
                    report['instances'].append({'part': part, 'id': ident})
                components = obj.findall('m:components/m:component', NS)
                if mesh is None and not components:
                    raise ValueError('Object has neither mesh nor components')
                for component in components:
                    child = part
                    path_attr = next((v for k, v in component.attrib.items() if k.endswith('}path')), None)
                    if path_attr:
                        child = posixpath.normpath(path_attr.lstrip('/') if path_attr.startswith('/') else
                                                  posixpath.join(posixpath.dirname(part), path_attr))
                    if child not in models or models[child][1] != scale:
                        raise ValueError('Missing or mixed-unit component model')
                    visit(child, component.get('objectid'), _multiply(transform, _transform(component.get('transform'), scale)), stack | {key})

            root, scale, _ = models[root_path]
            for item in root.findall('m:build/m:item', NS):
                if item.get('printable', '1') == '1':
                    part = root_path
                    path_attr = next((v for k,v in item.attrib.items() if k.endswith('}path')), None)
                    if path_attr:
                        part = posixpath.normpath(path_attr.lstrip('/') if path_attr.startswith('/') else
                                                 posixpath.join(posixpath.dirname(root_path), path_attr))
                    if part not in models or models[part][1] != scale:
                        raise ValueError('Missing or mixed-unit build model')
                    visit(part, item.get('objectid'), _transform(item.get('transform'), scale), set())
            if not all_points:
                raise ValueError('No printable instances')
            report['bounds_mm'] = [[min(p[i] for p in all_points), max(p[i] for p in all_points)] for i in range(3)]
            report['scope'] = 'Core mesh edges/winding and instance graph; no self-intersection, fit or strength proof'
    except (ValueError, KeyError, TypeError, OverflowError, ET.ParseError, zipfile.BadZipFile, OSError) as exc:
        report['issues'].append(str(exc))
    report['pass'] = not report['issues']
    report['status'] = 'pass' if report['pass'] else 'fail'
    return report


def package_project(source, config_path, destination):
    """Create a separate configured project from intact 3MF geometry and resolved settings."""
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve() or destination.exists():
        raise ValueError('Use a new destination; never overwrite the frozen input')
    geometry = inspect_3mf(source)
    if not geometry['pass']:
        raise ValueError('Source geometry failed inspection: ' + repr(geometry['issues']))
    config = load_config(config_path)
    # A project contains print settings, not connection credentials.
    private = {'printhost_apikey', 'printhost_password', 'printhost_user', 'print_host'}
    config = {k: v for k, v in config.items() if k not in private and k != 'compatible_printers'}
    content = '; generated by PrusaSlicer-compatible project packager\n\n' + ''.join('; '+k+' = '+v+'\n' for k,v in sorted(config.items()))
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=destination.parent, suffix='.3mf');os.close(fd)
    try:
        with zipfile.ZipFile(source) as original, zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as output:
            for member in original.namelist():
                if member not in (CONFIG_PART, 'Metadata/project_settings.config'):
                    output.writestr(member, original.read(member))
            output.writestr(CONFIG_PART, content)
        report = inspect_3mf(temporary, require_config=True, expected=config)
        if not report['pass']:
            raise ValueError('Packaged project failed inspection: ' + repr(report['issues']))
        if sha256(source) != geometry['sha256']:
            raise ValueError('Frozen source changed during packaging')
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)
    return inspect_3mf(destination, require_config=True, expected=config)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    inspect = sub.add_parser('inspect');inspect.add_argument('path');inspect.add_argument('--require-config', action='store_true')
    inspect.add_argument('--expect', action='append', default=[], metavar='KEY=VALUE')
    package = sub.add_parser('package');package.add_argument('source');package.add_argument('--config', required=True);package.add_argument('--output', required=True)
    args = parser.parse_args()
    try:
        if args.action == 'inspect':
            expected = dict(s.split('=', 1) for s in args.expect)
            report = inspect_3mf(args.path, args.require_config, expected)
        else:
            report = package_project(args.source, args.config, args.output)
    except (ValueError, OSError) as exc:
        report = {'status': 'fail', 'pass': False, 'issues': [str(exc)]}
    # Full profile values remain in the artifact; avoid dumping G-code/macros into context.
    summary = {k: v for k, v in report.items() if k != 'config'}
    print(json.dumps(summary, indent=2))
    return 0 if report['pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
