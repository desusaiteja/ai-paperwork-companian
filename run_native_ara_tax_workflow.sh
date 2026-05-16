#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HELPER_SCRIPT="$SCRIPT_DIR/ara_tax_helper.py"

TAX_YEAR="${ARA_TAX_YEAR:-$(( $(date +%Y) - 1 ))}"
OUTPUT_ROOT="${ARA_OUTPUT_ROOT:-$HOME/Documents/Ara Paperwork}"
GMAIL_STAGING_DIR="${ARA_GMAIL_STAGING_DIR:-$HOME/Downloads/Ara Tax Inbox}"

SCAN_DOWNLOADS="${ARA_SCAN_DOWNLOADS:-1}"
SCAN_DOCUMENTS="${ARA_SCAN_DOCUMENTS:-1}"
SCAN_DESKTOP="${ARA_SCAN_DESKTOP:-1}"
OPEN_FOLDER="${ARA_OPEN_FOLDER:-1}"
SPEAK_SUMMARY="${ARA_SPEAK_SUMMARY:-1}"
VERBOSE="${ARA_VERBOSE:-1}"
MAX_DEPTH="${ARA_MAX_DEPTH:-4}"

sources=()

mkdir -p "$GMAIL_STAGING_DIR"

if [[ -d "$GMAIL_STAGING_DIR" ]]; then
  sources+=("$GMAIL_STAGING_DIR")
fi

if [[ "$SCAN_DOWNLOADS" == "1" ]]; then
  sources+=("$HOME/Downloads")
fi

if [[ "$SCAN_DOCUMENTS" == "1" ]]; then
  sources+=("$HOME/Documents")
fi

if [[ "$SCAN_DESKTOP" == "1" ]]; then
  sources+=("$HOME/Desktop")
fi

if [[ $# -gt 0 ]]; then
  for arg in "$@"; do
    if [[ -d "$arg" ]]; then
      sources+=("$arg")
    fi
  done
fi

if [[ ${#sources[@]} -eq 0 ]]; then
  echo "No valid source directories found for the Ara tax workflow." >&2
  echo "Expected at least one of:" >&2
  echo "  - $GMAIL_STAGING_DIR" >&2
  echo "  - $HOME/Downloads" >&2
  echo "  - $HOME/Documents" >&2
  echo "  - $HOME/Desktop" >&2
  exit 2
fi

deduped_sources=()
typeset -A seen
for source in "${sources[@]}"; do
  if [[ -z "${seen[$source]:-}" ]]; then
    seen[$source]=1
    deduped_sources+=("$source")
  fi
done

cmd=(
  python3
  "$HELPER_SCRIPT"
  --year "$TAX_YEAR"
  --output-root "$OUTPUT_ROOT"
  --max-depth "$MAX_DEPTH"
)

if [[ "$OPEN_FOLDER" == "1" ]]; then
  cmd+=(--open-folder)
fi

if [[ "$SPEAK_SUMMARY" == "1" ]]; then
  cmd+=(--speak-summary)
fi

if [[ "$VERBOSE" == "1" ]]; then
  cmd+=(--verbose)
fi

for source in "${deduped_sources[@]}"; do
  cmd+=(--source "$source")
done

exec "${cmd[@]}"
