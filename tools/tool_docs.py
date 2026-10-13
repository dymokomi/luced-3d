#!/usr/bin/env python3
"""Write docs/TOOLS.md from the tool registry (src/tool_docs.luc)."""
from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

with tempfile.TemporaryDirectory(prefix="luced-3d-tool-docs-") as temporary:
    project = Path(temporary)
    shutil.copytree(ROOT / "src", project / "src")
    manifest = (ROOT / "package.prisma").read_text()
    manifest = re.sub(r'"\.\./([^"]+)"', lambda m: f'"{ROOT.parent / m.group(1)}"', manifest)
    (project / "package.prisma").write_text(manifest)
    shutil.copy2(ROOT / "tools/tool_docs.luc", project / "src/main.luc")
    binary = project / "tool_docs"
    subprocess.run([os.environ.get("LUCE", "luce"), "build", str(project / "src/main.luc"), "--native", "-o", str(binary)], check=True, timeout=480)
    text = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=60).stdout
    # print ends the page with one newline more.
    (ROOT / "docs/TOOLS.md").write_text(text[:-1] if text.endswith("\n\n") else text)
    print("wrote docs/TOOLS.md")
