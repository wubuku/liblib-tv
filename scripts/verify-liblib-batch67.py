#!/usr/bin/env python3

"""Run the Batch 67 Director project document contract verifier."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    subprocess.run(
        [
            "node",
            "--disable-warning=MODULE_TYPELESS_PACKAGE_JSON",
            "--experimental-strip-types",
            "scripts/verify-liblib-batch67.mjs",
        ],
        cwd=ROOT,
        check=True,
    )


if __name__ == "__main__":
    main()
