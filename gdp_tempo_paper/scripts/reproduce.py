"""Run the complete public-repository reproduction pipeline."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from validate_reproduction import required_artifacts

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "reproduction" / "logs"

ANALYSIS_STEPS = (
    ("verify_sources", "verify_source_data.py"),
    ("full_mobs_analysis", "run_full_analysis_mobs.py"),
    ("base_analysis", "run_paper_analyses.py"),
    ("manuscript_figures_1_9", "make_fig3_and_fig5.py"),
    ("solow_and_wealth", "solow_decomposition.py"),
    ("k_level_analysis", "k_level_analysis.py"),
)


def run_step(name: str, script: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"{name}.log"
    print(f"[{name}] {script}", flush=True)
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script)],
            cwd=ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )
    if process.returncode:
        tail = log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-30:]
        raise SystemExit(f"{name} failed; log: {log_path}\n" + "\n".join(tail))


def clear_required_artifacts() -> None:
    removed = 0
    for artifact in required_artifacts():
        if artifact.exists():
            artifact.unlink()
            removed += 1
    print(f"Removed {removed} previously generated validation artifacts.", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-documents",
        action="store_true",
        help="regenerate numerical results, figures, and tables but not DOCX/PPTX/PDF files",
    )
    args = parser.parse_args()

    clear_required_artifacts()
    for name, script in ANALYSIS_STEPS:
        run_step(name, script)
    if not args.skip_documents:
        run_step("submission_documents", "build_docx_pptx.py")
    run_step("validate", "validate_reproduction.py")
    print("Complete reproduction passed. See reproduction/reproduction_report.json")


if __name__ == "__main__":
    main()
