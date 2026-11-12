#!/usr/bin/env python3
"""Run from the extracted package root: python run_baselines.py --help."""
import os
for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[key] = "1"
from signal_origin.cli import main
if __name__ == "__main__":
    raise SystemExit(main())
