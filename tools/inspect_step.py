#!/usr/bin/env python3
"""Read-only STEP fixture inventory for development, not the runtime importer."""
import collections
import re
import sys
from pathlib import Path


def args(text):
    result, depth, quoted, start = [], 0, False, 0
    for at, char in enumerate(text):
        if char == "'":
            quoted = not quoted
        elif not quoted:
            depth += (char == "(") - (char == ")")
            if char == "," and depth == 0:
                result.append(text[start:at].strip())
                start = at + 1
    result.append(text[start:].strip())
    return result


def inventory(path):
    source = re.sub(r"/\*.*?\*/", "", Path(path).read_text(), flags=re.S)
    records = {}
    # Include complex rational entities; do not terminate at quoted semicolons.
    pattern = r"#(\d+)\s*=\s*((?:'(?:''|[^'])*'|[^;'])+);"
    for match in re.finditer(pattern, source, re.S):
        body = match[2].strip()
        split = body.index("(")
        kind = body[:split].strip() or "COMPLEX"
        records[int(match[1])] = (kind, args(body[split + 1:-1]))
    return records


def inspect(path):
    records = inventory(path)
    def record(ref):
        return records[int(ref[1:])]
    def refs(value):
        return args(value[1:-1])
    def point(vertex):
        return record(record(vertex)[1][1])[1][1]
    print(collections.Counter(kind for kind, _ in records.values()))
    for key, (kind, data) in records.items():
        if kind != "ADVANCED_FACE":
            continue
        surface_kind, surface = record(data[2])
        print(f"Face #{key} {surface_kind} {data[2]} sense={data[3]}")
        if surface_kind == "B_SPLINE_SURFACE_WITH_KNOTS":
            rows = refs(surface[3])
            for row in [rows[0], rows[-1]]:
                print("  control row", [record(p)[1][1] for p in refs(row)])
        for bound in refs(data[1]):
            bound_kind, bound_data = record(bound)
            loop = record(bound_data[1])[1]
            print(" ", bound_kind, bound_data[2])
            for oriented_ref in refs(loop[1]):
                oriented = record(oriented_ref)[1]
                edge = record(oriented[3])[1]
                curve_kind, curve = record(edge[3])
                print("   ", oriented[3], curve_kind, edge[3], "edge sense", edge[4], "loop sense", oriented[4], point(edge[1]), point(edge[2]))


if __name__ == "__main__":
    inspect(sys.argv[1])
