#!/usr/bin/env python3
"""Thin cross-platform launcher for the core Claude migration planner."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    core = Path(__file__).resolve().parents[2] / "ai-game-studio" / "scripts" / "ai_game_studio.py"
    if not core.is_file():
        print("Core plugin runtime not found; install ai-game-studio first.", file=sys.stderr)
        return 2
    return subprocess.run([sys.executable, str(core), "migrate", "claude", *sys.argv[1:]], check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
