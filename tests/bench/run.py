#!/usr/bin/env python3
"""Build and run the headless editor benchmark: the 700k-face grid as an OBJ, and
a STEP file (default ~/Desktop/camera.step) through Tessellate, each into an Edit
node, timing import, first display, selecting 1k faces and a Move round trip.

Report-only; single runs of a --native --opt 2 build.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))
from run import prepare  # noqa: E402

TARGETS = {
    "Move 1k faces round trip": "< 10 ms",
    "Move 1k adjacent faces round trip": "< 10 ms",
    "select 1k faces (1000 clicks)": "< 2 ms per click",
    "first display": "< 30 ms",
    "CV drag frame, mean of 5": "< 50 ms",
}


def grid(path, n=837):
    with open(path, "w") as out:
        for z in range(n + 1):
            out.write("".join(f"v {x / n - 0.5} 0 {z / n - 0.5}\n" for x in range(n + 1)))
        for z in range(n):
            out.write("".join(f"f {z * (n + 1) + x + 1} {(z + 1) * (n + 1) + x + 1} {(z + 1) * (n + 1) + x + 2} {z * (n + 1) + x + 2}\n"
                              for x in range(n)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", type=Path, default=Path.home() / "Desktop/camera.step")
    parser.add_argument("--opt", choices=["0", "1", "2", "3"], default="2")
    parser.add_argument("--only", choices=["drag"], help="Run one case only (drag: the STEP file's CV drag)")
    arguments = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="luced-3d-bench-") as temporary:
        project = Path(temporary)
        prepare(project)
        shutil.copy2(ROOT / "tests/bench/bench.luc", project / "src/main.luc")
        shutil.copy2(ROOT / "tests/bench/offscreen.lucb", project / "src/offscreen.lucb")
        mesh = project / "grid700k.obj"
        grid(mesh)
        binary = project / "bench"
        environment = dict(os.environ, LUCE_CACHE=str(project / "cache"))
        subprocess.run([os.environ.get("LUCE", "luce"), "build", str(project / "src/main.luc"), "--native", "--opt", arguments.opt,
                        "-o", str(binary)], check=True, env=environment, timeout=600)
        step = str(arguments.step) if arguments.step.exists() else ""
        if not step:
            print(f"# {arguments.step} is missing; the STEP case is skipped")
        result = subprocess.run([str(binary), str(mesh), step] + ([arguments.only] if arguments.only else []), capture_output=True, text=True, timeout=3600, cwd=project)
        if result.returncode != 0:
            sys.exit(f"bench failed ({result.returncode}):\n{result.stdout}\n{result.stderr}")
        output = result.stdout
    lines = output.splitlines()
    for line in lines:
        if line.startswith("#"):
            print(line)
    print("| Operation | Measured | Target |")
    print("|---|---:|---|")
    for line in lines:
        if line.startswith("#"):
            continue
        name, _, value = line.partition("\t")
        target = next((goal for key, goal in TARGETS.items() if name.endswith(key)), "")
        print(f"| {name} | {float(value):.3f} ms | {target} |")


if __name__ == "__main__":
    main()
