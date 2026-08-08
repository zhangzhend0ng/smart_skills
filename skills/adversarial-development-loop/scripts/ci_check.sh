#!/usr/bin/env bash
# ci_check.sh — CI 侧 meta-bench 回归(不调 gate.sh:CI 快照无工作树改动,gate 恒绿空转,
#   见 framework-manual §6 对抗 M3)。全种子 --score 基准属本地回流工作流(需真实 REFUTE 报告),
#   CI 只跑 primitive:--verify + --demo(全种子 pass/fail 对)+ py_compile。
set -uo pipefail

cd "$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "CI: not a git repository (exit 2)"; exit 2; }
S=skills/adversarial-development-loop/scripts

PY=""
for c in python python3 py; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then echo "CI: no python interpreter (python/python3/py 均不可用)——exit 2"; exit 2; fi

fail=0
"$PY" "$S/run_meta_bench.py" --verify >/dev/null 2>&1 || { echo "CI FAIL: meta-bench --verify"; fail=1; }
"$PY" "$S/run_meta_bench.py" --demo >/dev/null 2>&1 || { echo "CI FAIL: meta-bench --demo"; fail=1; }
"$PY" -m py_compile "$S/run_meta_bench.py" "$S/new_seed.py" \
  skills/adversarial-development-loop/assets/meta-bench/seeds/*/*/fixture.py >/dev/null 2>&1 \
  || { echo "CI FAIL: py_compile"; fail=1; }

if [ "$fail" = 0 ]; then echo "CI PASS: verify + demo + py_compile"; exit 0; fi
exit 1
