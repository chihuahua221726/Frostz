#!/usr/bin/env python3
"""Build the standalone FrostZ HTML and compressed SVG files."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent

from scripts.build_single_file import build


if __name__ == "__main__":
    build()
