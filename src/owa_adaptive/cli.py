"""Punto de entrada de consola: ``owa-demo``."""
from __future__ import annotations

import argparse

from .config import SEED
from .demo import run


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="owa-demo",
        description="Demo reproducible del motor de recomendación adaptativo OWA.",
    )
    parser.add_argument("-o", "--output-dir", default="outputs",
                        help="Carpeta de salida (figuras + reporte HTML).")
    parser.add_argument("--n-assets", type=int, default=30)
    parser.add_argument("--n-days", type=int, default=1500)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--no-figures", action="store_true",
                        help="No generar figuras (solo tablas/HTML).")
    args = parser.parse_args(argv)

    run(output_dir=args.output_dir, n_assets=args.n_assets, n_days=args.n_days,
        seed=args.seed, make_figures=not args.no_figures)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
