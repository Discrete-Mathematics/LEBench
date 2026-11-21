#!/usr/bin/env bash
# Rebuild the English and Chinese report PDFs from the .tex sources.
#
# Requires tectonic, a single-file LaTeX engine that fetches packages on demand:
#   https://tectonic-typesetting.github.io/en-US/install.html
# The PDFs are committed, so this is only needed after editing the .tex files.
set -euo pipefail

cd "$(dirname "$0")/../report"

if ! command -v tectonic >/dev/null 2>&1; then
  echo "error: tectonic not found on PATH (see https://tectonic-typesetting.github.io)" >&2
  exit 1
fi

tectonic report.tex
tectonic report_zh.tex
echo "rebuilt report.pdf and report_zh.pdf"
