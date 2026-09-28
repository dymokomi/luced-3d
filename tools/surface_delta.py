"""Compare STEP/OBJ surfaces through the native triangle BVH, not an O(N*M) scan."""
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
    binary = project / "probe"
    build(project, binary, "2")
    subprocess.run([str(binary), *sys.argv[1:]], check=True, timeout=180)
