#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from cv_checker.batch_run import build_warnings, sort_results, write_csv
from cv_checker.main import analyze_pdf_bytes, load_keywords


INCOMING_DIR = PROJECT_ROOT / "data" / "cv" / "incoming"
PROCESSED_DIR = PROJECT_ROOT / "data" / "cv" / "processed"
FAILED_DIR = PROJECT_ROOT / "data" / "cv" / "failed"
RESULTS_DIR = PROJECT_ROOT / "outputs" / "batch_history"
LATEST_RESULTS_DIR = PROJECT_ROOT / "outputs" / "latest"
RUN_TS_FMT = "%Y%m%d_%H%M%S"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Traite les CV deposes dans le dossier de reception puis les deplace vers traite ou erreur."
    )
    parser.add_argument("--incoming-dir", default=str(INCOMING_DIR), help="Dossier de reception des CV a traiter.")
    parser.add_argument("--processed-dir", default=str(PROCESSED_DIR), help="Dossier final des CV traites.")
    parser.add_argument("--failed-dir", default=str(FAILED_DIR), help="Dossier des CV en erreur.")
    parser.add_argument("--results-dir", default=str(RESULTS_DIR), help="Dossier des resultats batch horodates.")
    parser.add_argument("--run-name", default=None, help="Nom du run. Par defaut: horodatage.")
    parser.add_argument(
        "--sync-latest",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Copie aussi les derniers resultats vers outputs/latest.",
    )
    return parser.parse_args()


def unique_destination(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    i = 1
    while True:
        candidate = parent / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def move_preserve_relative(source: Path, root: Path, target_root: Path) -> Path:
    rel = source.relative_to(root)
    dst = target_root / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst = unique_destination(dst)
    shutil.move(str(source), str(dst))
    return dst


def main() -> None:
    args = parse_args()
    run_name = args.run_name or datetime.now().strftime(RUN_TS_FMT)

    incoming_dir = Path(args.incoming_dir)
    processed_root = Path(args.processed_dir) / run_name
    failed_root = Path(args.failed_dir) / run_name
    results_dir = Path(args.results_dir)
    out_json = results_dir / f"batch_results_{run_name}.json"
    out_csv = results_dir / f"batch_results_{run_name}.csv"

    incoming_dir.mkdir(parents=True, exist_ok=True)
    processed_root.parent.mkdir(parents=True, exist_ok=True)
    failed_root.parent.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    pdfs = sorted([p for p in incoming_dir.rglob("*.pdf") if p.is_file()])
    if not pdfs:
        print(f"Aucun PDF trouve dans: {incoming_dir.resolve()}")
        print("Depose des CV dans ce dossier puis relance le script.")
        return

    keywords = load_keywords()
    all_results: list[dict] = []
    errors: list[dict] = []
    moved_ok = 0
    moved_failed = 0

    print(f"PDFs trouves: {len(pdfs)}")
    for i, pdf_path in enumerate(pdfs, start=1):
        try:
            analysis = analyze_pdf_bytes(pdf_path.read_bytes(), pdf_path.name, keywords=keywords)
            result = analysis["result"]
            warnings = build_warnings(result)
            all_results.append({"file": str(pdf_path), "result": result, "warnings": warnings})

            move_preserve_relative(pdf_path, incoming_dir, processed_root)
            moved_ok += 1
            print(f"[{i}/{len(pdfs)}] OK {pdf_path.name} warnings={len(warnings)}")
        except Exception as exc:
            errors.append({"file": str(pdf_path), "error": str(exc)})
            try:
                move_preserve_relative(pdf_path, incoming_dir, failed_root)
                moved_failed += 1
            except Exception:
                pass
            print(f"[{i}/{len(pdfs)}] EXCEPTION {pdf_path.name} -> {exc}")

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "run_name": run_name,
                "mode": "direct:analyze_pdf_bytes",
                "incoming_dir": str(incoming_dir.resolve()),
                "processed_dir": str(processed_root.resolve()),
                "failed_dir": str(failed_root.resolve()),
                "count": len(all_results),
                "results": all_results,
                "errors": errors,
                "moved_ok": moved_ok,
                "moved_failed": moved_failed,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    sorted_results = sort_results(all_results)
    write_csv(sorted_results, out_csv)

    latest_csv = None
    latest_json = None
    if args.sync_latest:
        LATEST_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        latest_csv = LATEST_RESULTS_DIR / "batch_results.csv"
        latest_json = LATEST_RESULTS_DIR / "batch_results.json"
        shutil.copy2(out_csv, latest_csv)
        shutil.copy2(out_json, latest_json)

    print("\nTermine.")
    print(f"- JSON: {out_json.resolve()}")
    print(f"- CSV : {out_csv.resolve()}")
    if latest_csv and latest_json:
        print(f"- Latest CSV: {latest_csv.resolve()}")
        print(f"- Latest JSON: {latest_json.resolve()}")
    print(f"- CV traites deplaces: {moved_ok}")
    print(f"- CV en erreur deplaces: {moved_failed}")
    print(f"- Erreurs: {len(errors)}")


if __name__ == "__main__":
    main()
