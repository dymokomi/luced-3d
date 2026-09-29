#!/usr/bin/env python3
"""Build behavior tests in isolation using the installed, current toolchain."""
import os
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile
from fbx_fixtures import write_fixtures

ROOT = Path(__file__).resolve().parents[1]


def prepare(project):
    shutil.copytree(ROOT / "src", project / "src")
    shutil.copytree(ROOT / "tests/fixtures", project / "tests/fixtures")
    write_fixtures(project / "tests/fixtures")
    # Regression for the historical 65,536-corner OBJ buffer overrun.
    (project / "tests/fixtures/large.obj").write_text(
        "v 0 0 0\nv 1 0 0\nv 0 1 0\nvt 0 0\nvn 0 0 1\n" +
        "f 1/1/1 2/1/1 3/1/1\n" * 22000)
    # A ~500k-face planar grid for worker request-size and Edit replay checks.
    n = 710
    points = "".join(f"v {x} 0 {z}\n" for z in range(n + 1) for x in range(n + 1))
    faces = "".join(f"f {z * (n + 1) + x + 1} {(z + 1) * (n + 1) + x + 1} {(z + 1) * (n + 1) + x + 2} {z * (n + 1) + x + 2}\n"
                    for z in range(n) for x in range(n))
    (project / "tests/fixtures/grid500k.obj").write_text(points + faces)
    manifest = (ROOT / "package.prisma").read_text()
    for name in ("luce-ui", "luce-3d", "luce-color", "luce-std", "luce-gpu", "luce-window", "luce-obj", "luce-tesselator", "luce-cad", "luce-step", "luce-fbx", "luce-prism"):
        manifest = manifest.replace(f'"../{name}"', f'"{ROOT.parent / name}"')
    (project / "package.prisma").write_text(manifest)


def build(project, binary, optimization="0", backend="native"):
    cache = Path(os.environ.get("LUCE_TEST_CACHE", str(ROOT / "build/test-cache")))
    cache.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ, LUCE_CACHE=str(cache))
    flags = ["--native", "--opt", optimization] if backend == "native" else ["--backend=c"] + (["--release"] if int(optimization) >= 2 else [])
    subprocess.run([os.environ.get("LUCE", "luce"), "build", str(project / "src/main.luc"),
                    *flags, "-o", str(binary)],
                   check=True, env=environment, timeout=240)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opt", choices=["0", "1", "2", "3"], default="0")
    parser.add_argument("--backend", choices=["native", "c"], default="native")
    parser.add_argument("--case", choices=sorted(path.stem for path in (ROOT / "tests").glob("*_tests.luc")), help="Run one named regression module (default: the complete suite)")
    arguments = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="luced-3d-tests-") as temporary:
        project = Path(temporary)
        # Run internal layout contracts in the CAD package's own module scope.
        # They must not become exports of the public application-facing API.
        cad_binary = project / "cad-layout-tests"
        cad_flags = ["--native", "--opt", arguments.opt] if arguments.backend == "native" else ["--backend=c"] + (["--release"] if int(arguments.opt) >= 2 else [])
        subprocess.run([os.environ.get("LUCE_BASE", "luce-base"), "build",
                        str(ROOT.parent / "luce-cad/src/luce_cad/tests/layout_contract.lucb"), *cad_flags,
                        "-o", str(cad_binary)], check=True, timeout=240)
        subprocess.run([str(cad_binary)], check=True, timeout=60)
        print("PASS spline endpoint roundoff, periodic crossings, diagonal curvature and fixed-trim interior spacing", flush=True)
        trim_binary = project / "trim-predicate-tests"
        subprocess.run([os.environ.get("LUCE_BASE", "luce-base"), "build",
                        str(ROOT.parent / "luce-tesselator/src/luce_tesselator/tests/trim_predicates_contract.lucb"), *cad_flags,
                        "-o", str(trim_binary)], check=True, timeout=240)
        subprocess.run([str(trim_binary)], check=True, timeout=60)
        print("PASS filtered/exact trim predicates, close boundary vertices, disjoint holes and true crossing rejection", flush=True)
        prepare(project)
        if arguments.case:
            (project / "src/main.luc").write_text(
                f"from {arguments.case} import {arguments.case}\n"
                f"pub func main(arguments: list[str]) -> int!:\n    {arguments.case}()\n    return 0\n")
        else:
            shutil.copy2(ROOT / "tests/main.luc", project / "src/main.luc")
        for module in (ROOT / "tests").glob("*_tests.luc"):
            shutil.copy2(module, project / "src" / module.name)
        binary = project / "test-runner"
        build(project, binary, arguments.opt, arguments.backend)
        subprocess.run([str(binary)], check=True, timeout=300, cwd=project)
