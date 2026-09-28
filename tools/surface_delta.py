"""Native BVH comparison: STEP OBJ [STEP-tolerance] [OBJ-to-STEP-unit-scale].

The optional positive scale is explicit; no shape registration is performed.
Distances are reported in STEP source units. Input files remain untouched.
"""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from run import prepare, build
with tempfile.TemporaryDirectory(prefix="luced-delta-") as temporary:
    project = Path(temporary)
    prepare(project)
    shutil.copy2(ROOT / "tools/surface_delta.luc", project / "src/main.luc")
    shutil.copy2(ROOT / "tools/cad_probe_output.lucb", project / "src/cad_probe_output.lucb")
    binary = project / "probe"
    build(project, binary, "2")
    subprocess.run([str(binary), *sys.argv[1:]], check=True, timeout=180)
