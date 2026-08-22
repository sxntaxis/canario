from __future__ import annotations

import argparse
import hashlib
import json
import random
import subprocess
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def render_page(pdf: Path, out_prefix: Path, page: int, dpi: int) -> Path:
    run([
        "pdftoppm",
        "-f", str(page),
        "-l", str(page),
        "-r", str(dpi),
        "-singlefile",
        "-png",
        str(pdf),
        str(out_prefix),
    ])
    return out_prefix.with_suffix(".png")


def save_image_pdf(image_path: Path, pdf_path: Path, dpi: int) -> None:
    with Image.open(image_path) as image:
        image = image.convert("RGB")
        image.save(pdf_path, "PDF", resolution=float(dpi))


def skew_noise(source: Path, target: Path) -> None:
    random.seed(20260821)
    with Image.open(source) as image:
        gray = image.convert("L")
        gray = gray.filter(ImageFilter.GaussianBlur(radius=0.35))
        gray = ImageEnhance.Contrast(gray).enhance(0.82)
        noise = Image.effect_noise(gray.size, 10.0).convert("L")
        mixed = Image.blend(gray, noise, 0.075)
        rotated = mixed.rotate(2.2, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=255)
        rotated.save(target, "PNG", optimize=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--page", type=int, default=2)
    parser.add_argument("--work-dir", type=Path, required=True)
    args = parser.parse_args()

    if sha256(args.source) != args.source_sha256:
        raise SystemExit("source PDF hash mismatch; refusing to generate benchmark variants")

    args.work_dir.mkdir(parents=True, exist_ok=True)
    base300 = render_page(args.source, args.work_dir / "tse-p2-native-300", args.page, 300)
    low110 = render_page(args.source, args.work_dir / "tse-p2-lowdpi-110", args.page, 110)

    clean_scan = args.work_dir / "tse-p2-clean-scan-300.png"
    with Image.open(base300) as image:
        image.convert("L").save(clean_scan, "PNG", optimize=True)

    degraded = args.work_dir / "tse-p2-skew-noise-300.png"
    skew_noise(clean_scan, degraded)

    # Isolate the original native-text page so mixed native/scan coverage can be measured.
    native_page = args.work_dir / "tse-p2-native.pdf"
    run(["pdfseparate", "-f", str(args.page), "-l", str(args.page), str(args.source), str(args.work_dir / "native-%d.pdf")])
    generated_native = args.work_dir / f"native-{args.page}.pdf"
    generated_native.replace(native_page)

    variants = {
        "native_page_pdf": native_page,
        "native_300_png": base300,
        "clean_scan_300_png": clean_scan,
        "lowdpi_110_png": low110,
        "skew_noise_300_png": degraded,
    }
    for key, image_path in list(variants.items()):
        if key == "native_page_pdf" or key == "native_300_png":
            continue
        pdf_path = image_path.with_suffix(".pdf")
        dpi = 110 if "110" in key else 300
        save_image_pdf(image_path, pdf_path, dpi)
        variants[key.removesuffix("_png") + "_pdf"] = pdf_path

    # Build a two-page mixed document: native text first, image-only scan second.
    mixed_pdf = args.work_dir / "tse-p2-mixed-native-scan.pdf"
    run(["pdfunite", str(native_page), str(variants["clean_scan_300_pdf"]), str(mixed_pdf)])
    variants["mixed_native_scan_pdf"] = mixed_pdf

    # Deliberately corrupt a copy for failure-isolation checks.
    malformed_pdf = args.work_dir / "tse-p2-truncated.pdf"
    source_bytes = native_page.read_bytes()
    malformed_pdf.write_bytes(source_bytes[: max(256, len(source_bytes) // 2)])
    variants["malformed_truncated_pdf"] = malformed_pdf

    manifest = {
        "generator": "generate_controlled_variants.py",
        "source": str(args.source),
        "source_sha256": args.source_sha256,
        "page_ordinal": args.page,
        "variants": {
            key: {"path": str(path), "sha256": sha256(path), "bytes": path.stat().st_size}
            for key, path in variants.items()
        },
    }
    (args.work_dir / "controlled-variants.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
