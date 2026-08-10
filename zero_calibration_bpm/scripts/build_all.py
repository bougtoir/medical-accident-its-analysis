#!/usr/bin/env python3
"""
One-command reproduction of the whole project.

Runs, in order: simulate -> analyze -> figures (EN + JA) -> manuscripts
(EN + JA) -> tables docx -> figure deck (PPTX) -> cover letter.

Every number, table and figure is regenerated from the seeded simulation, so
a clean clone plus `python scripts/build_all.py` reproduces all outputs.
"""

import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "src")


def run_module(path, label):
    print(f"\n=== {label} ===")
    runpy.run_path(path, run_name="__main__")


def main():
    sys.path.insert(0, SRC)
    sys.path.insert(0, HERE)
    run_module(os.path.join(SRC, "simulate.py"), "1/9 simulate")
    run_module(os.path.join(SRC, "real_waveforms.py"), "2/9 real waveforms")
    run_module(os.path.join(SRC, "analyze.py"), "3/9 analyze")
    run_module(os.path.join(SRC, "figures.py"), "4/9 figures (EN + JA)")
    run_module(os.path.join(HERE, "create_bpm_docx_en.py"), "5/9 manuscript EN")
    run_module(os.path.join(HERE, "create_bpm_docx_ja.py"), "6/9 manuscript JA")
    run_module(os.path.join(HERE, "create_tables_docx_en.py"), "7/9 tables docx")
    run_module(os.path.join(HERE, "create_figures_pptx_en.py"), "8/9 figures pptx")
    run_module(os.path.join(HERE, "create_tim_cover_letter.py"), "9/9 cover letter")
    print("\nAll outputs regenerated.")


if __name__ == "__main__":
    main()
