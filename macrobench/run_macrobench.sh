#!/usr/bin/env bash
# Run the Claim 3 macrobenchmarks (Redis, Apache, Nginx) N times and record
# every observation in results/macro/<config>/results.csv.
#
# Usage:
#   bash macrobench/run_macrobench.sh --config default --runs 3
#   bash macrobench/run_macrobench.sh --config spectre-off --runs 3
set -euo pipefail

CONFIG="default"
RUNS=3
OUT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    --runs)   RUNS="$2"; shift 2 ;;
    --out)    OUT="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,9p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUT:-$ROOT/results/macro/$CONFIG}"
mkdir -p "$OUT/raw"

REDIS_PREFIX="/opt/redis-4.0.8"
REDIS_SERVER="$REDIS_PREFIX/src/redis-server"
REDIS_BENCH="$REDIS_PREFIX/src/redis-benchmark"
[[ -x "$REDIS_SERVER" ]] || REDIS_SERVER="$(command -v redis-server)"
[[ -x "$REDIS_BENCH" ]]  || REDIS_BENCH="$(command -v redis-benchmark)"

RESULTS="$OUT/results.csv"
[[ -f "$RESULTS" ]] || echo "config,run,app,test,metric,value,unit" > "$RESULTS"

append() {
  printf '%s,%s,%s,%s,%s,%s,%s\n' "$@" >> "$RESULTS"
}

record_env() {
  {
    echo "config: $CONFIG"
    echo "date_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "uname: $(uname -r)"
    echo "cmdline: $(cat /proc/cmdline)"
    echo "cpu: $(awk -F': ' '/model name/ {print $2; exit}' /proc/cpuinfo)"
    echo "nproc: $(nproc)"
    for f in /sys/devices/system/cpu/vulnerabilities/*; do
      if [[ -r "$f" ]]; then echo "$(basename "$f"): $(cat "$f")"; fi
    done
    echo "redis_server: $("$REDIS_SERVER" --version 2>/dev/null | head -1)"
    echo "redis_bench: $("$REDIS_BENCH" --version 2>/dev/null | head -1)"
    echo "apache: $(apache2 -v 2>/dev/null | head -1)"
    echo "nginx: $(nginx -v 2>&1 | head -1)"
    echo "ab: $(ab -V 2>&1 | head -1)"
  } > "$OUT/environment.txt"
}

wait_for() { # url label
  local i
  for i in $(seq 1 30); do
    if curl -fsS -o /dev/null "$1"; then return 0; fi
    sleep 1
  done
  echo "error: $2 is not answering at $1" >&2
  return 1
}

start_services() {
  if ! pgrep -f 'redis-server' >/dev/null; then
    "$REDIS_SERVER" --daemonize yes --save '' --appendonly no
    sleep 1
  fi
  systemctl is-active --quiet apache2 || sudo systemctl start apache2
  systemctl is-active --quiet nginx   || sudo systemctl start nginx
  wait_for "http://127.0.0.1/" apache
  wait_for "http://127.0.0.1:8080/" nginx
  "$REDIS_BENCH" -n 10 -c 1 -q >/dev/null
}

http_metrics() { # app baseurl run
  local app="$1" url="$2" run="$3" log="$OUT/raw/$1.run$3.log"
  ab -n 100000 -c 100 "$url" > "$log" 2>&1
  append "$CONFIG" "$run" "$app" index throughput \
    "$(awk '/^Requests per second:/ {print $4; exit}' "$log")" req_per_s
  append "$CONFIG" "$run" "$app" index latency_mean \
    "$(awk '/^Time per request:/ {print $4; exit}' "$log")" ms
  append "$CONFIG" "$run" "$app" index failed \
    "$(awk '/^Failed requests:/ {print $3; exit}' "$log")" count
}

echo "[macrobench] config=$CONFIG runs=$RUNS out=$OUT"
record_env
start_services

for r in $(seq 1 "$RUNS"); do
  echo "[macrobench] run $r/$RUNS"

  echo "[macrobench]   redis"
  "$REDIS_BENCH" -n 100000 -c 50 -q -t rpush,spop,rpop,get,lrange \
    > "$OUT/raw/redis.run$r.log" 2>&1
  while IFS= read -r line; do
    name="${line%%:*}"
    rest="${line#*: }"
    value="${rest%% *}"
    append "$CONFIG" "$r" redis "$name" throughput "$value" req_per_s
  done < <(grep -E '^[A-Za-z_]+: [0-9.]+ requests per second' "$OUT/raw/redis.run$r.log" || true)

  echo "[macrobench]   apache"
  http_metrics apache "http://127.0.0.1/" "$r"

  echo "[macrobench]   nginx"
  http_metrics nginx "http://127.0.0.1:8080/" "$r"

  sleep 5
done

echo "[macrobench] wrote $RESULTS"
echo "[macrobench] next: python3 macrobench/parse_macrobench.py $ROOT/results/macro"
