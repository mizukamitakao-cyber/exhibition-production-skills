#!/usr/bin/env python3
"""Claude Code 環境へのデプロイエントリポイント。scripts/deploy.py に委譲する。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.deploy import main

if __name__ == "__main__":
    main()
