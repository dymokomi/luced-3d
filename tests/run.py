#!/usr/bin/env python3
"""Build the editor's behavior tests in isolation using the installed, current
toolchain. CAD meshing and the file formats have their own runners in luce-cad,
luce-step, luce-obj and luce-fbx."""
import os
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def prepare(project):
    shutil.copytree(ROOT / "src", project / "src")
    shutil.copytree(ROOT / "tests/fixtures", project / "tests/fixtures")
    # A ~500k-face planar grid for worker request-size and Edit replay checks.
    n = 710
    points = "".join(f"v {x} 0 {z}\n" for z in range(n + 1) for x in range(n + 1))
    faces = "".join(f"f {z * (n + 1) + x + 1} {(z + 1) * (n + 1) + x + 1} {(z + 1) * (n + 1) + x + 2} {z * (n + 1) + x + 2}\n"
                    for z in range(n) for x in range(n))
    (project / "tests/fixtures/grid500k.obj").write_text(points + faces)
    manifest = (ROOT / "package.prisma").read_text()
    for name in ("luce-ui", "luce-geocore", "luce-3d", "luce-color", "luce-std", "luce-gpu", "luce-window", "luce-obj", "luce-cad", "luce-step", "luce-fbx", "luce-prism"):
        manifest = manifest.replace(f'"../{name}"', f'"{ROOT.parent / name}"')
    (project / "package.prisma").write_text(manifest)


def build(project, binary, optimization="0", backend="native"):
    cache = Path(os.environ.get("LUCE_TEST_CACHE", str(ROOT / "build/test-cache")))
    cache.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ, LUCE_CACHE=str(cache))
    flags = ["--native", "--opt", optimization] if backend == "native" else ["--backend=c"] + (["--release"] if int(optimization) >= 2 else [])
    subprocess.run([os.environ.get("LUCE", "luce"), "build", str(project / "src/main.luc"),
                    *flags, "-o", str(binary)],
                   check=True, env=environment, timeout=480)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opt", choices=["0", "1", "2", "3"], default="0")
    parser.add_argument("--backend", choices=["native", "c"], default="native")
    parser.add_argument("--case", choices=sorted(path.stem for path in (ROOT / "tests").glob("*_tests.luc")), help="Run one named regression module (default: the complete suite)")
    arguments = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="luced-3d-tests-") as temporary:
        project = Path(temporary)
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
