#!/usr/bin/env python3
"""Repeatable CPU timing, not GPU execution or input-to-photon latency."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from run import prepare, build
with tempfile.TemporaryDirectory(prefix="luced-3d-profile-") as temporary:
    project = Path(temporary)
    prepare(project)
    shutil.copy2(ROOT / "tools/profile.luc", project / "src/main.luc")
    shutil.copy2(ROOT / "tools/timing.lucb", project / "src/timing.lucb")
    binary = project / "profile"
    build(project, binary, os.environ.get("LUCE_PROFILE_OPT", "0"))
    subprocess.run([str(binary)] + sys.argv[1:], check=True, timeout=90)
