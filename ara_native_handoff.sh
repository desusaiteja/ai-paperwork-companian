#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKFLOW_SCRIPT="$SCRIPT_DIR/run_native_ara_tax_workflow.sh"

tax_year=""
transcript=""
sources=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --year)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --year" >&2
        exit 2
      fi
      tax_year="$2"
      shift 2
      ;;
    --transcript)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --transcript" >&2
        exit 2
      fi
      transcript="$2"
      shift 2
      ;;
    --source)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --source" >&2
        exit 2
      fi
      sources+=("$2")
      shift 2
      ;;
    --help|-h)
      cat <<'EOF'
Usage:
  ./ara_native_handoff.sh
  ./ara_native_handoff.sh --year 2024
  ./ara_native_handoff.sh --transcript "Ara, gather everything I need for my taxes."
  ./ara_native_handoff.sh --year 2024 --source "/path/to/folder"

This is the single native handoff command for Ara. It builds a canonical
tax-gathering transcript and routes the request into the local helper workflow.
EOF
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

extract_tax_year() {
  local raw_text="$1"
  local match
  match=$(printf '%s\n' "$raw_text" | grep -Eo '\b20[0-9]{2}\b' | head -n 1 || true)
  if [[ -n "$match" ]]; then
    printf '%s' "$match"
  fi
}

if [[ -n "$tax_year" ]]; then
  if [[ ! "$tax_year" =~ ^20[0-9][0-9]$ ]]; then
    echo "Invalid tax year: $tax_year" >&2
    exit 2
  fi
fi

if [[ -z "$tax_year" && -n "$transcript" ]]; then
  tax_year="$(extract_tax_year "$transcript")"
fi

if [[ -n "$tax_year" ]]; then
  export ARA_TAX_YEAR="$tax_year"
fi

if [[ -n "$transcript" ]]; then
  printf 'Ara transcript: %s\n' "$transcript" >&2
fi

if [[ -n "${ARA_TAX_YEAR:-}" ]]; then
  printf 'Using tax year: %s\n' "$ARA_TAX_YEAR" >&2
else
  printf 'Using default tax year from workflow.\n' >&2
fi

if [[ ${#sources[@]} -gt 0 ]]; then
  printf 'Including extra sources:\n' >&2
  for source in "${sources[@]}"; do
    printf '  - %s\n' "$source" >&2
  done
else
  printf 'Using standard source folders only.\n' >&2
fi

if [[ ! -x "$WORKFLOW_SCRIPT" ]]; then
  chmod +x "$WORKFLOW_SCRIPT"
fi

if [[ ${#sources[@]} -gt 0 ]]; then
  exec "$WORKFLOW_SCRIPT" "${sources[@]}"
else
  exec "$WORKFLOW_SCRIPT"
fi
