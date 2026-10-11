#!/usr/bin/env python3
"""The viewport's Render mode in a real window: frame intervals while a light is
dragged and the camera orbits, the time to a change's first whole image, and,
with --frames FOLDER, every frame of the drag as PNG (render_frames.luc)."""
from pathlib import Path
import argparse
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
os.environ["LUCE_CRASH_WINDOW"] = "0"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--frames", type=Path, help="Save the drag's frames here as PNG")
parser.add_argument("--project", type=Path, help="A project to render (its first light is dragged), e.g. examples/splats/splat_shadows.prisma")
parser.add_argument("--opt", choices=["0", "1", "2", "3"], default="2")
arguments = parser.parse_args()


def chunk(tag, payload):
    return struct.pack(">I", len(payload)) + tag + payload + struct.pack(">I", zlib.crc32(tag + payload) & 0xffffffff)


def png(ppm, output):
    header, dimensions, maximum, pixels = ppm.read_bytes().split(b"\n", 3)
    width, height = map(int, dimensions.split())
    rows = b"".join(b"\0" + pixels[y * width * 3:(y + 1) * width * 3] for y in range(height))
    output.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
                       + chunk(b"IDAT", zlib.compress(rows, 6)) + chunk(b"IEND", b""))


def prepare(project):
    """A copy of the package whose path dependencies point at the siblings."""
    shutil.copytree(ROOT / "src", project / "src")
    manifest = re.sub(r'"\.\./([^"]+)"', lambda m: f'"{ROOT.parent / m.group(1)}"', (ROOT / "package.prisma").read_text())
    (project / "package.prisma").write_text(manifest)


def build(project, binary, optimization):
    cache = Path(os.environ.get("LUCE_TEST_CACHE", str(ROOT / "build/test-cache")))
    cache.mkdir(parents=True, exist_ok=True)
    subprocess.run([os.environ.get("LUCE", "luce"), "build", str(project / "src/main.luc"), "--native", "--opt", optimization, "-o", str(binary)],
                   check=True, env=dict(os.environ, LUCE_CACHE=str(cache)), timeout=480)

with tempfile.TemporaryDirectory(prefix="luced-3d-render-frames-") as temporary:
    project = Path(temporary)
    prepare(project)
    shutil.copy2(ROOT / "tools/render_frames.luc", project / "src/main.luc")
    native = (ROOT.parent / "luce-gpu/tests/gpu/native.lucb").read_text() + "\n" + (ROOT / "tools/readback.lucb").read_text()
    (project / "src/probe.lucb").write_text(native)
    binary = project / "render_frames"
    build(project, binary, arguments.opt)
    folder = project / "frames"
    folder.mkdir()
    subprocess.run([str(binary), str(folder) if arguments.frames else "", str(arguments.project.resolve()) if arguments.project else ""], check=True, timeout=300)
    if arguments.frames:
        arguments.frames.mkdir(parents=True, exist_ok=True)
        for ppm in sorted(folder.glob("*.ppm")):
            png(ppm, arguments.frames / (ppm.stem + ".png"))
        print(f"{arguments.frames}: {len(list(folder.glob('*.ppm')))} frames")
