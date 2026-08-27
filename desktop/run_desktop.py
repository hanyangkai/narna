"""PyInstaller entry — frozen NARNA Desktop."""

from __future__ import annotations

import sys

from uap.desktop_app import main

if __name__ == "__main__":
    raise SystemExit(main())
