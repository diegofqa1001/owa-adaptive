#!/usr/bin/env python
"""Demo de un comando: genera figuras + reporte HTML reproducibles.

Funciona sin instalar el paquete (añade ``src/`` al path). Salidas en
``<repo>/outputs``.
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(_HERE, "..", "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from owa_adaptive.demo import run  # noqa: E402

if __name__ == "__main__":
    out = os.path.join(_HERE, "..", "outputs")
    run(output_dir=out)
