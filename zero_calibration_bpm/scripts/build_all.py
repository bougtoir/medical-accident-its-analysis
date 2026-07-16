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
    run_module(os.path.join(SRC, "simulate.py"), "1/8 simulate")
    run_module(os.path.join(SRC, "analyze.py"), "2/8 analyze")
    run_module(os.path.join(SRC, "figures.py"), "3/8 figures (EN + JA)")
    run_module(os.path.join(HERE, "create_bpm_docx_en.py"), "4/8 manuscript EN")
    run_module(os.path.join(HERE, "create_bpm_docx_ja.py"), "5/8 manuscript JA")
    run_module(os.path.join(HERE, "create_tables_docx_en.py"), "6/8 tables docx")
    run_module(os.path.join(HERE, "create_figures_pptx_en.py"), "7/8 figures pptx")
    run_module(os.path.join(HERE, "create_bpm_cover_letter.py"), "8/8 cover letter")
    print("\nAll outputs regenerated.")


if __name__ == "__main__":
    main()
