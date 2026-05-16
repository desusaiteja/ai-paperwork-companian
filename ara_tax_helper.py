#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".csv", ".txt"}
TEXT_EXTENSIONS = {".csv", ".txt"}
SKIP_DIR_NAMES = {
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    "node_modules",
    "Library",
    "Applications",
    "Ara Paperwork",
}
DEFAULT_OUTPUT_ROOT = Path.home() / "Documents" / "Ara Paperwork"
DEFAULT_MAX_DEPTH = 4
TEXT_SAMPLE_BYTES = 120_000

DOCUMENT_RULES = [
    {
        "doc_type": "W2",
        "category": "Income",
        "keywords": ["w-2", "w2", "wage and tax", "withholding"],
    },
    {
        "doc_type": "1099",
        "category": "Income",
        "keywords": ["1099", "1099-nec", "1099-misc", "1099-k", "contractor"],
    },
    {
        "doc_type": "BankInterest",
        "category": "Income",
        "keywords": ["1099-int", "interest statement", "bank interest", "savings interest"],
    },
    {
        "doc_type": "InvestmentTaxForm",
        "category": "Investments",
        "keywords": [
            "1099-div",
            "1099-b",
            "brokerage",
            "dividend",
            "capital gains",
            "investment",
            "consolidated 1099",
        ],
    },
    {
        "doc_type": "DonationReceipt",
        "category": "Donations",
        "keywords": ["donation", "charity", "charitable", "donor", "receipt", "red cross"],
    },
    {
        "doc_type": "MedicalReceipt",
        "category": "Medical",
        "keywords": ["medical", "dental", "hospital", "clinic", "hsa", "copay", "pharmacy"],
    },
    {
        "doc_type": "MortgageInterest",
        "category": "Other",
        "keywords": ["1098", "mortgage interest", "mortgage statement"],
    },
]

KNOWN_ISSUERS = {
    "bank of america": "BankOfAmerica",
    "vanguard": "Vanguard",
    "fidelity": "Fidelity",
    "charles schwab": "CharlesSchwab",
    "schwab": "CharlesSchwab",
    "red cross": "RedCross",
    "community food bank": "CommunityFoodBank",
    "food bank": "CommunityFoodBank",
    "chase": "Chase",
    "hsa": "ChaseHSA",
    "smile dental": "SmileDental",
    "hospital": "Hospital",
    "sunrise credit union": "SunriseCreditUnion",
}

IGNORED_ISSUER_TOKENS = {
    "tax",
    "form",
    "statement",
    "receipt",
    "document",
    "copy",
    "w2",
    "w",
    "2",
    "1099",
    "1098",
    "int",
    "div",
    "nec",
    "misc",
    "medical",
    "donation",
    "mortgage",
    "interest",
}


def expand_path(raw_path: str) -> Path:
    return Path(raw_path).expanduser().resolve()


def path_is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def read_text_sample(path: Path) -> str:
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return ""

    try:
        with path.open("rb") as handle:
            data = handle.read(TEXT_SAMPLE_BYTES)
    except OSError:
        return ""
    return data.decode("utf-8", errors="ignore").lower()


def detect_issuer(path: Path, combined_text: str) -> str:
    for keyword, issuer in KNOWN_ISSUERS.items():
        if keyword in combined_text:
            return issuer

    cleaned = re.sub(r"[^a-z0-9]+", " ", path.stem.lower()).strip()
    parts = [
        part
        for part in cleaned.split()
        if part not in IGNORED_ISSUER_TOKENS and not part.isdigit()
    ]
    if not parts:
        return "UnknownIssuer"

    return "".join(part.capitalize() for part in parts[:3])


def normalize_search_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def has_pattern(text: str, pattern: str) -> bool:
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def has_conflicting_year(text: str, tax_year: int) -> bool:
    years = {int(match) for match in re.findall(r"\b20[0-9]{2}\b", text)}
    return bool(years and tax_year not in years)


def classify_file(path: Path, tax_year: int) -> dict[str, str] | None:
    stem_text = normalize_search_text(path.stem)
    path_context = normalize_search_text(str(path.parent))
    text_sample = normalize_search_text(read_text_sample(path))
    combined_text = f"{stem_text} {text_sample}".strip()

    if has_conflicting_year(f"{path_context} {combined_text}", tax_year):
        return None

    def match(doc_type: str, category: str) -> dict[str, str]:
        return {
            "docType": doc_type,
            "category": category,
            "issuer": detect_issuer(path, combined_text),
        }

    has_year = str(tax_year) in combined_text
    has_tax_context = has_year or has_pattern(
        combined_text,
        r"\b(tax|form|statement|receipt|year end|yearend)\b",
    )

    # Keep these rules deliberately strict. Earlier binary text sampling caused
    # unrelated PDFs/images to look like W-2s or 1099s.
    if has_pattern(combined_text, r"\bw\s*2\b|\bwage\s+and\s+tax\b"):
        if has_tax_context:
            return match("W2", "Income")

    if has_pattern(combined_text, r"\b1099\s*int\b|\binterest\s+statement\b|\bbank\s+interest\b"):
        return match("BankInterest", "Income")

    if has_pattern(
        combined_text,
        r"\b1099\s*(div|b)\b|\bconsolidated\s+1099\b|\b(brokerage|dividend|capital\s+gains)\b",
    ):
        if has_tax_context or has_pattern(combined_text, r"\b1099\b"):
            return match("InvestmentTaxForm", "Investments")

    if has_pattern(combined_text, r"\b1098\b|\bmortgage\s+interest\b"):
        return match("MortgageInterest", "Other")

    if has_pattern(
        combined_text,
        r"\b(donation|charitable|charity|donor|red\s+cross|goodwill|united\s+way|food\s+bank)\b",
    ):
        if has_tax_context or has_pattern(combined_text, r"\breceipt\b"):
            return match("DonationReceipt", "Donations")

    if has_pattern(
        combined_text,
        r"\b(medical|dental|hospital|clinic|pharmacy|hsa|fsa|copay|deductible)\b",
    ):
        if has_tax_context or has_pattern(combined_text, r"\breceipt\b"):
            return match("MedicalReceipt", "Medical")

    if has_pattern(combined_text, r"\b1099\s*(nec|misc|k)?\b|\bcontractor\b"):
        return match("1099", "Income")

    return None


def sanitize_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_") or "document"


def build_filename(tax_year: int, doc_type: str, issuer: str, original: Path) -> str:
    return sanitize_filename(f"{tax_year}_{doc_type}_{issuer}{original.suffix.lower()}")


def unique_destination(path: Path) -> Path:
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    counter = 2
    while True:
        candidate = path.with_name(f"{stem}_{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def collect_files(source: Path, output_root: Path, max_depth: int) -> list[Path]:
    files: list[Path] = []
    if not source.exists() or not source.is_dir():
        return files

    for current_root, dirs, filenames in os.walk(source):
        current_path = Path(current_root)
        try:
            depth = len(current_path.relative_to(source).parts)
        except ValueError:
            depth = 0

        dirs[:] = [
            name
            for name in dirs
            if not name.startswith(".")
            and name not in SKIP_DIR_NAMES
            and depth < max_depth
            and not path_is_within(current_path / name, output_root)
        ]

        if path_is_within(current_path, output_root):
            continue

        for filename in filenames:
            if filename.startswith("."):
                continue
            if filename.lower() in {"summary.txt", "summary.json"}:
                continue
            path = current_path / filename
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            files.append(path)

    return files


def infer_missing(found: list[dict[str, Any]]) -> list[str]:
    doc_types = {item["docType"] for item in found}
    categories = {item["category"] for item in found}
    missing: list[str] = []

    if "W2" not in doc_types:
        missing.append("W-2 from an employer")
    if "1099" not in doc_types:
        missing.append("1099 income forms")
    if "BankInterest" not in doc_types:
        missing.append("Bank interest statements")
    if "InvestmentTaxForm" not in doc_types:
        missing.append("Investment tax forms")
    if "DonationReceipt" not in doc_types:
        missing.append("Donation receipts")
    if "MedicalReceipt" not in doc_types:
        missing.append("Medical expense receipts")
    if "MortgageInterest" not in doc_types:
        missing.append("Mortgage interest form")
    if "Income" not in categories:
        missing.append("Income documents")

    return missing


def write_summary(output_root: Path, summary: dict[str, Any]) -> None:
    (output_root / "summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    lines = [
        f"Ara Paperwork Companion summary for tax year {summary['taxYear']}",
        "",
        f"Documents gathered: {summary['documentsFound']}",
        f"Output folder: {summary['outputFolder']}",
        "",
        "Likely missing documents:",
    ]
    lines.extend(f"- {entry}" for entry in summary["missingLikely"])
    lines.append("")
    lines.append("Copied files:")
    lines.extend(
        f"- {entry['category']}: {entry['fileName']}"
        for entry in summary["copiedFiles"]
    )
    (output_root / "SUMMARY.txt").write_text("\n".join(lines), encoding="utf-8")


def build_spoken_summary(summary: dict[str, Any]) -> str:
    documents_found = summary["documentsFound"]
    missing = summary["missingLikely"]

    if missing:
        missing_line = f"You may still be missing {missing[0]}."
    else:
        missing_line = "I did not detect any obvious missing documents."

    return (
        f"I gathered {documents_found} tax related documents and organized them "
        f"in your {summary['taxYear']} tax folder. {missing_line}"
    )


def speak_summary(summary: dict[str, Any], log: callable) -> None:
    message = build_spoken_summary(summary)
    try:
        subprocess.run(["say", message], check=False)
        log("Spoke the final summary out loud.")
    except OSError as error:
        log(f"Could not speak the summary automatically: {error}")


def organize_documents(
    *,
    tax_year: int,
    source_dirs: list[Path],
    explicit_files: list[Path],
    output_root_base: Path,
    max_depth: int,
    open_folder: bool,
    speak_result: bool,
    verbose: bool,
) -> dict[str, Any]:
    output_root = output_root_base / str(tax_year)
    output_root.mkdir(parents=True, exist_ok=True)

    logs: list[str] = []

    def log(message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}"
        logs.append(line)
        if verbose:
            print(line, file=sys.stderr)

    log(f"Target year: {tax_year}")
    log(f"Output folder: {output_root}")

    candidate_files: list[Path] = []
    for source_dir in source_dirs:
        if source_dir.exists():
            log(f"Scanning source: {source_dir}")
            candidate_files.extend(collect_files(source_dir, output_root, max_depth))
        else:
            log(f"Skipping missing source: {source_dir}")

    for explicit_file in explicit_files:
        if explicit_file.exists() and explicit_file.is_file():
            candidate_files.append(explicit_file.resolve())
        else:
            log(f"Skipping missing file: {explicit_file}")

    deduped_candidates: list[Path] = []
    seen_paths: set[str] = set()
    for path in candidate_files:
        resolved = str(path.resolve())
        if resolved not in seen_paths:
            seen_paths.add(resolved)
            deduped_candidates.append(path.resolve())

    log(f"Found {len(deduped_candidates)} candidate files to inspect.")

    matches: list[dict[str, Any]] = []
    copied_files: list[dict[str, str]] = []

    for path in deduped_candidates:
        classification = classify_file(path, tax_year)
        if not classification:
            continue
        match = {
            "sourcePath": str(path),
            "docType": classification["docType"],
            "category": classification["category"],
            "issuer": classification["issuer"],
        }
        matches.append(match)
        log(f"Matched {path.name} -> {match['category']} / {match['docType']}")

    if not matches:
        log("No tax-related documents matched the current rules.")

    for match in matches:
        source_path = Path(match["sourcePath"])
        category_root = output_root / match["category"]
        category_root.mkdir(parents=True, exist_ok=True)

        destination_name = build_filename(
            tax_year,
            match["docType"],
            match["issuer"],
            source_path,
        )
        destination_path = unique_destination(category_root / destination_name)
        shutil.copy2(source_path, destination_path)
        copied_files.append(
            {
                "category": match["category"],
                "fileName": destination_path.name,
                "sourcePath": str(source_path),
            }
        )
        log(f"Copied {source_path.name} -> {match['category']}/{destination_path.name}")

    missing_likely = infer_missing(matches)
    summary = {
        "taxYear": tax_year,
        "outputFolder": str(output_root),
        "documentsFound": len(copied_files),
        "copiedFiles": copied_files,
        "missingLikely": missing_likely,
        "logs": logs,
    }
    write_summary(output_root, summary)
    log("Wrote summary.json and SUMMARY.txt.")

    if open_folder:
        try:
            subprocess.run(["open", str(output_root)], check=False)
            log("Opened the output folder in Finder.")
        except OSError as error:
            log(f"Could not open Finder automatically: {error}")

    if speak_result:
        speak_summary(summary, log)

    summary["logs"] = logs
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Helper script for Ara to classify, rename, and organize tax documents.",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=datetime.now().year - 1,
        help="Tax year to organize into. Defaults to last year.",
    )
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="Source directory to scan recursively. May be provided multiple times.",
    )
    parser.add_argument(
        "--file",
        action="append",
        default=[],
        help="Explicit file to organize. May be provided multiple times.",
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="Base output directory. Final output will go into <output-root>/<year>.",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=DEFAULT_MAX_DEPTH,
        help="Maximum folder depth to scan inside each source directory.",
    )
    parser.add_argument(
        "--open-folder",
        action="store_true",
        help="Open the resulting folder in Finder after organizing files.",
    )
    parser.add_argument(
        "--speak-summary",
        action="store_true",
        help="Speak the final summary out loud using the macOS say command.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress logs to stderr while running.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_dirs = [expand_path(entry) for entry in args.source]
    explicit_files = [expand_path(entry) for entry in args.file]

    if not source_dirs and not explicit_files:
        print(
            "Provide at least one --source directory or --file path.",
            file=sys.stderr,
        )
        return 2

    summary = organize_documents(
        tax_year=args.year,
        source_dirs=source_dirs,
        explicit_files=explicit_files,
        output_root_base=expand_path(args.output_root),
        max_depth=args.max_depth,
        open_folder=args.open_folder,
        speak_result=args.speak_summary,
        verbose=args.verbose,
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
