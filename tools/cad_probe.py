#!/usr/bin/env python3
"""Run the real Luce Base STEP/CAD pipeline; audit its mesh against a reference OBJ."""
import argparse
from collections import Counter
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from cad_distance import sampled_distance

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from run import prepare, build


def audit(text):
    points, faces = [], []
    rendered = None
    for line in text.splitlines():
        fields = line.split()
        if fields[:1] == ["v"]:
            points.append(tuple(map(float, fields[1:4])))
        elif fields[:1] == ["f"]:
            faces.append([int(f.split("/")[0]) - 1 for f in fields[1:]])
        elif line.startswith("# renderer_area="):
            rendered = tuple(float(field.split("=")[1]) for field in fields[1:])
    edges, orientation = Counter(), Counter()
    volume = area = 0.0
    for face in faces:
        for a, b in zip(face, face[1:] + face[:1]):
            key = tuple(sorted((a, b)))
            edges[key] += 1
            orientation[key] += 1 if a < b else -1
        a = points[face[0]]
        for i in range(1, len(face) - 1):
            b, c = points[face[i]], points[face[i + 1]]
            u, v = [b[j] - a[j] for j in range(3)], [c[j] - a[j] for j in range(3)]
            cross = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
            area += math.sqrt(sum(x*x for x in cross)) / 2
            volume += sum(a[j] * cross[j] for j in range(3)) / 6
    # A triangle fan is not a valid area/volume measurement for arbitrary
    # nonplanar or concave n-gons. Prefer the native renderer's triangulation.
    if rendered:
        area, volume = rendered
    elif any(len(face) != 3 for face in faces):
        area = volume = None
    return dict(points=len(points), faces=len(faces), face_sizes=dict(Counter(map(len, faces))),
                boundary_edges=sum(v == 1 for v in edges.values()),
                nonmanifold_edges=sum(v > 2 for v in edges.values()),
                inconsistent_edges=sum(edges[k] == 2 and v != 0 for k, v in orientation.items()),
                euler=len(points)-len(edges)+len(faces), area=area, volume=volume,
                bounds=[tuple(f(p[j] for p in points) for j in range(3)) for f in (min, max)])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step", type=Path)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--divisions", choices=["4", "8", "16", "64"], default="16")
    parser.add_argument("--opt", choices=["0", "1", "2"], default="0")
    parser.add_argument("--backend", choices=["native", "c"], default="native")
    parser.add_argument("--edge-size", type=float, default=0.0)
    parser.add_argument("--tolerance", type=float, default=0.0, help="STEP import tolerance in source units; 0 uses the file uncertainty")
    parser.add_argument("--timeout", type=float, default=120.0, help="Maximum native import/meshing runtime in seconds")
    parser.add_argument("--preview", action="store_true", help="Audit per-patch display meshing, without converting the whole CAD model")
    parser.add_argument("--stats", action="store_true", help="Report triangle/quad counts per original CAD face")
    parser.add_argument("--topology", action="store_true", help="Inspect one patch's support type and shared CAD edges without meshing")
    parser.add_argument("--patch", type=int, default=-1, help="Extract a zero-based patch after the full production cook (or isolate preview with --preview)")
    parser.add_argument("--planned", action="store_true", help="Mesh --patch with the full model's shared-edge/layout plan, skipping other final face jobs; NOT proof of whole-model success")
    parser.add_argument("--output", type=Path, help="Optional generated OBJ (never the reference file)")
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("timeout must be finite and positive")
    if args.topology and args.patch < 0:
        parser.error("--topology requires --patch")
    if args.planned and (args.patch < 0 or args.preview or args.topology):
        parser.error("--planned requires --patch and cannot be combined with --preview or --topology")
    if args.output and args.reference and args.output.resolve() == args.reference.resolve():
        parser.error("output must not overwrite the reference")
    with tempfile.TemporaryDirectory(prefix="luced-cad-probe-") as temporary:
        project = Path(temporary)
        prepare(project)
        shutil.copy2(ROOT / "tools/cad_probe.luc", project / "src/main.luc")
        shutil.copy2(ROOT / "tools/cad_probe_output.lucb", project / "src/cad_probe_output.lucb")
        shutil.copy2(ROOT / "tools/cad_probe_quality.lucb", project / "src/cad_probe_quality.lucb")
        binary = project / "cad-probe"
        build(project, binary, args.opt, args.backend)
        result = subprocess.run([str(binary), str(args.step.resolve()), args.divisions, str(args.edge_size), "topology" if args.topology else ("stats" if args.stats else ("preview" if args.preview else "mesh")), str(args.patch), str(args.tolerance), "planned" if args.planned else "full"],
                                capture_output=True, text=True, timeout=args.timeout)
        if result.returncode:
            sys.stderr.write(result.stdout + result.stderr)
            result.check_returncode()
        print(result.stdout.splitlines()[0])
        if args.topology:
            print("\n".join(result.stdout.splitlines()[1:]))
            if args.output: args.output.write_text(result.stdout)
            sys.exit(0)
        if args.stats:
            print(result.stdout.splitlines()[-1])
            lines = [line for line in result.stdout.splitlines() if line.startswith("patch ")]
            print("worst non-quad counts (triangles and cut-cell n-gons):")
            print("\n".join(sorted(lines, key=lambda line: int(line.split()[4]), reverse=True)[:30]))
            print("groups:", sorted({line.split(" ", 5)[5] for line in lines}))
            quality = [line for line in result.stdout.splitlines() if line.startswith("quality ")]
            print("worst quad skew counts (corner sine below 0.1):")
            print("\n".join(sorted(quality, key=lambda line: int(line.split()[7]), reverse=True)[:20]))
            if args.output: args.output.write_text(result.stdout)
            sys.exit(0)
        if args.preview:
            failures = [line for line in result.stdout.splitlines() if line.startswith("failure ")]
            print("failed patches", len(failures), Counter(line.split(" ", 2)[2] for line in failures))
            print("first failures", failures[:12])
            timings = [(int(line.split()[2]), int(line.split()[1])) for line in result.stdout.splitlines() if line.startswith("timing ")]
            print("slowest patches (ns, index)", sorted(timings, reverse=True)[:12])
            print(result.stdout.splitlines()[-1])
            if args.output:
                args.output.write_text(result.stdout)
            sys.exit(0)
        generated = audit(result.stdout)
        print("STEP", generated)
        assert generated["nonmanifold_edges"] == generated["inconsistent_edges"] == 0
        if args.patch < 0: assert generated["boundary_edges"] == 0
        if args.reference:
            reference_text = args.reference.read_text()
            reference = audit(reference_text)
            print("OBJ ", reference)
            if generated["volume"] is not None and reference["volume"]:
                print("relative volume difference", abs(generated["volume"] / reference["volume"] - 1))
                print("relative area difference", abs(generated["area"] / reference["area"] - 1))
            if set(generated["face_sizes"]) == set(reference["face_sizes"]) == {3}:
                print("sampled STEP mesh -> OBJ distance", sampled_distance(result.stdout, reference_text))
                print("sampled OBJ -> STEP mesh distance", sampled_distance(reference_text, result.stdout))
            else:
                print("Use tools/surface_delta.py for n-gon-aware native surface distances.")
        if args.output:
            args.output.write_text(result.stdout)
