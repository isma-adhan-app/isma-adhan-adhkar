"""PyInstaller entry shim.

The frozen exe runs its entry script as __main__ with NO package context, so
relative imports inside the entry script fail with "attempted relative import
with no known parent package". This shim sits OUTSIDE the package, uses only
absolute imports, and imports the real entry point as a proper package
module, which restores package context for everything below it.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Dev convenience only (python launcher.py from the repo root); the frozen
# build resolves isma_adhan from the spec's pathex instead.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from isma_adhan.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
