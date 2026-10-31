#!/bin/bash
# Run the reduced LEBench binary three times on the kernel that is booted.
# Usage: run_reduced.sh <kernel-release> <output-directory>
set -u
REL="$1"
DEST="$2"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$DEST"

{
  echo "kernel: $(uname -r)"
  echo "cmdline: $(cat /proc/cmdline)"
  echo "date_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "gcc: $(gcc --version | head -n 1)"
  echo "cpu: $(grep -m1 'model name' /proc/cpuinfo | sed 's/.*: //')"
  echo "nproc: $(nproc)"
  if [ -r /sys/devices/system/cpu/vulnerabilities/meltdown ]; then
    echo "meltdown: $(cat /sys/devices/system/cpu/vulnerabilities/meltdown)"
  fi
  if [ -r /sys/devices/system/cpu/vulnerabilities/spectre_v2 ]; then
    echo "spectre_v2: $(cat /sys/devices/system/cpu/vulnerabilities/spectre_v2)"
  fi
} > "$DEST/environment.txt"

export LEBENCH_DIR="${ROOT}/"
cd "$ROOT"
# OS_Eval appends "/TEST_DIR/socket" to LEBENCH_DIR and binds a Unix socket there.
mkdir -p "${ROOT}/TEST_DIR"
for i in 1 2 3; do
  success=0
  for attempt in 1 2 3 4 5; do
    rm -f "$ROOT/output.${REL}.csv" "$ROOT/output_file.csv" "$ROOT/new_output_file.csv" "${ROOT}/TEST_DIR/socket"
    stdbuf -oL -eL "$ROOT/course/sweep_bench" 0 "$REL" > "$DEST/run${i}.stdout.txt" 2> "$DEST/run${i}.stderr.txt"
    status=$?
    echo "$status" > "$DEST/run${i}.exit_code.txt"
    if [ "$status" -eq 0 ] && [ -f "$ROOT/output.${REL}.csv" ]; then
      mv "$ROOT/output.${REL}.csv" "$DEST/run${i}.csv"
      success=1
      break
    fi
  done
  if [ "$success" -ne 1 ]; then
    echo "run $i failed after retries" >> "$DEST/run${i}.stderr.txt"
  fi
done
chmod -R a+rX "$DEST"
