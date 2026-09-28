"""Run all requested local fixtures through the production Base importers."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from run import prepare, build

with tempfile.TemporaryDirectory(prefix="luced-corpus-") as temporary:
    project = Path(temporary)
    prepare(project)
    shutil.copy2(ROOT / "tools/corpus_probe.luc", project / "src/main.luc")
    binary = project / "probe"
    build(project, binary, "2")
    # One child per file bounds retained compiler/runtime heaps and isolates failures.
    for path in sys.argv[1:]:
        try:
            result = subprocess.run([str(binary), path], timeout=180, text=True, capture_output=True)
            print(result.stdout + result.stderr, end="", flush=True)
            if result.returncode: print(f"PROCESS FAILURE {path}: {result.returncode}", flush=True)
        except subprocess.TimeoutExpired:
            print(f"TIMEOUT {path}: 180s", flush=True)
