"""Restore deterministic historical figure assets after source-code regeneration."""

from __future__ import annotations

import hashlib
import shutil
import zipfile
from pathlib import Path

from PIL import Image


PROJECT_DIR = Path(__file__).resolve().parents[1]
FIGURE_DIR = PROJECT_DIR / "figures"
ARCHIVE = PROJECT_DIR / "docs" / "bioessays_submission_en.zip"
MINARD_PNG_SHA256 = (
    "9c796e76919b65bf42a808b7c6337bdc5e105d0cc8dab472adbda2ad98704424"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_member(
    archive: zipfile.ZipFile,
    member: str,
    destination: Path,
) -> None:
    with archive.open(member) as source, destination.open("wb") as target:
        shutil.copyfileobj(source, target)


def main() -> None:
    generated_minard = FIGURE_DIR / "fig3_minard_migration.png"
    if not generated_minard.exists():
        raise FileNotFoundError(
            "Run scripts/create_minard_figure.py before restoring canonical assets."
        )
    with Image.open(generated_minard) as image:
        generated_size = image.size
    if generated_size[0] != 4770 or abs(generated_size[1] - 2612) > 1:
        raise RuntimeError(
            f"Unexpected regenerated Minard dimensions: {generated_size}"
        )

    with zipfile.ZipFile(ARCHIVE) as archive:
        extract_member(
            archive,
            "fig3_minard_migration.png",
            FIGURE_DIR / "fig3_minard_migration.png",
        )
        extract_member(
            archive,
            "fig3_minard_migration.tiff",
            FIGURE_DIR / "fig3_minard_migration.tiff",
        )
        extract_member(
            archive,
            "fig4_bivariate_world_map.png",
            FIGURE_DIR / "fig9_bivariate_world_map.png",
        )
        extract_member(
            archive,
            "fig4_bivariate_world_map.tiff",
            FIGURE_DIR / "fig9_bivariate_world_map.tiff",
        )

    if sha256(FIGURE_DIR / "fig3_minard_migration.png") != MINARD_PNG_SHA256:
        raise RuntimeError("Canonical Figure 3 checksum mismatch")
    print(
        "Restored the canonical Minard and bivariate-map assets after regeneration."
    )


if __name__ == "__main__":
    main()
