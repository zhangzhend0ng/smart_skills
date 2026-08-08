#!/usr/bin/env bash
# gate.sh — 机械事实提交门禁(bookkeeping gate,非防漂移脚本)
#
# 只拦"有没有走框架"的机械事实,不判语义质量。检查:
#   G1 journal 覆盖:代码/内核改动(CODE ∪ KERNEL)必须伴随 journal 改动
#   G2 journal 完成标志:journal 已改则其(改动后)内容必须含合法 `Pattern Index 更新: (N/A|新增)` 行
#   G3 内核/bench 资产改动:必须通过 meta-bench `--verify` + `--demo`(只读)
#
# iter 119 边界(引自 Stratum loop-journal.md:5297 一手源):
#   "脚本只能防数字/路径漂移(且多源打架时查不准),防不了语义/方案级漂移——后者靠对抗式核实。"
# 本脚本只查"可由独立观察者复核的过程痕迹"(改动集、marker 行存在性、bench 退出码),
# 不解释内容真伪——请勿在此追加语义检查(check_drift.py 那一类已被 iter 119 证伪)。
# 已知宽松语义(对抗审查 M2 接受):G2 只要求 journal 文件(改动后状态)内含 ≥1 条合法 marker,
#   不校验"哪条 marker 对应哪次改动"——那是语义事实,超出机械边界。
#
# 配置(env 可覆盖):
#   GATE_CODE_PATTERNS   需 journal 的代码 glob(默认不含 yml/json/.github——配置/CI 属纯局部改动)
#   GATE_KERNEL_PATTERNS 内核 glob(改内核需 journal + bench)
#   GATE_BENCH_PATTERNS  meta-bench 资产 glob(改之需 bench;种子变更=bench 输入变了,信号最强)
#   GATE_JOURNAL         journal 文件(空格分隔;任一命中改动集即算"journal 已改")
#   GATE_META_BENCH_CMD  meta-bench 运行器路径
#
# 退出码:0 = 全过或无改动;1 = 任一 FAIL;2 = 环境错误(非 git 仓库/缺 python/缺 bench 运行器)
# 用法:bash gate.sh [--why]

# -f:关闭 glob 展开——模式变量(如 *.cpp)在 for 循环里必须保持字面,
#    否则会被 cwd 文件展开破坏(实测:nullglob+globstar 下 *.py 变成具体文件名,
#    case 永不匹配,门禁静默失效)。case 模式自身不需 pathname expansion。
set -fuo pipefail

cd "$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "GATE: not a git repository (exit 2)"; exit 2; }

CODE_PATTERNS="${GATE_CODE_PATTERNS:-*.cpp *.hpp *.h *.c *.py *.rs *.go *.js *.ts *.tsx *.jsx *.sh *.java *.cs *.rb *.php *.lua *.toml Makefile Dockerfile}"
KERNEL_PATTERNS="${GATE_KERNEL_PATTERNS:-skills/**/SKILL.md skills/**/references/framework-manual.md}"
BENCH_PATTERNS="${GATE_BENCH_PATTERNS:-skills/**/scripts/*.py skills/**/assets/meta-bench/**}"
JOURNAL_PATHS="${GATE_JOURNAL:-LOOP-JOURNAL.md docs/loop-journal.md}"
META_BENCH_CMD="${GATE_META_BENCH_CMD:-skills/adversarial-development-loop/scripts/run_meta_bench.py}"

if [ "${1:-}" = "--why" ]; then
  cat <<'EOF'
G1: 代码/内核改动必须伴随 journal 改动(每轮迭代落盘条目)
G2: journal 内容必须含合法 'Pattern Index 更新: (N/A|新增)' 行(机械完成标志)
G3: 内核/bench 资产改动必须通过 meta-bench --verify + --demo
边界(iter 119):只查过程痕迹存在性,不判语义真伪;勿加语义检查
EOF
  exit 0
fi

# 改动集 = diff HEAD(若有 HEAD)+ untracked(-uall 展开目录,防 M1 目录折叠漏拦)
# 剥离状态前缀(如 '?? '/' M '/'MM '),处理重命名 'R  old -> new' 取旧路径
changeset() {
  {
    if git rev-parse --verify HEAD >/dev/null 2>&1; then
      git diff --name-only HEAD
    fi
    git status --porcelain -uall
  } | sed -E 's/^.{0,2}[[:space:]]//; s/ -> .*$//' | sort -u
}

# journal 文件在改动集中?
journal_changed() {
  local p j
  while IFS= read -r p; do
    [ -z "$p" ] && continue
    for j in $JOURNAL_PATHS; do
      [ "$p" = "$j" ] && return 0
    done
  done <<< "$1"
  return 1
}

# journal(改动后状态)内含 ≥1 条合法 marker 行?(untracked 直查文件内容,M2 宽松语义)
journal_has_valid_marker() {
  local j
  for j in $JOURNAL_PATHS; do
    [ -f "$j" ] || continue
    if grep -qE '^#+[[:space:]]*Pattern Index 更新:[[:space:]]*(N/A|新增)' "$j"; then
      return 0
    fi
  done
  return 1
}

# 跑 meta-bench(只读)。返回:0=通过 / 1=bench FAIL / 2=环境错误
run_meta_bench() {
  local py=""
  for c in py python python3; do
    if command -v "$c" >/dev/null 2>&1; then py="$c"; break; fi
  done
  if [ -z "$py" ]; then
    echo "GATE G3: no python interpreter (py/python/python3 均不可用)——环境错误(exit 2)"
    return 2
  fi
  if [ ! -f "$META_BENCH_CMD" ]; then
    echo "GATE G3: meta-bench runner not found: $META_BENCH_CMD (exit 2)"
    return 2
  fi
  "$py" "$META_BENCH_CMD" --verify >/dev/null 2>&1 || { echo "GATE G3: meta-bench --verify 未通过"; return 1; }
  "$py" "$META_BENCH_CMD" --demo >/dev/null 2>&1 || { echo "GATE G3: meta-bench --demo 未通过"; return 1; }
  return 0
}

main() {
  local changes code_changed=0 kernel_changed=0 bench_changed=0 journal_hit=0 fail=0 env_err=0 p pat j

  changes="$(changeset)"
  if [ -z "$changes" ]; then
    echo "GATE: no changes (exit 0)"
    return 0
  fi

  while IFS= read -r p; do
    [ -z "$p" ] && continue
    for j in $JOURNAL_PATHS; do [ "$p" = "$j" ] && journal_hit=1; done
    for pat in $CODE_PATTERNS; do case "$p" in $pat) code_changed=1;; esac; done
    for pat in $KERNEL_PATTERNS; do case "$p" in $pat) kernel_changed=1;; esac; done
    for pat in $BENCH_PATTERNS; do case "$p" in $pat) bench_changed=1;; esac; done
  done <<< "$changes"

  # G1
  if [ "$code_changed" = 1 ] || [ "$kernel_changed" = 1 ]; then
    if [ "$journal_hit" != 1 ]; then
      echo "G1 FAIL: 代码/内核改动但 journal 未在改动集($JOURNAL_PATHS)——每轮迭代必须落盘 journal 条目"
      fail=1
    else
      echo "G1 PASS: journal 覆盖代码/内核改动"
    fi
  else
    echo "G1 PASS: 无代码/内核改动(journal 非必需)"
  fi

  # G2
  if [ "$journal_hit" = 1 ]; then
    if journal_has_valid_marker; then
      echo "G2 PASS: journal 含合法 'Pattern Index 更新: (N/A|新增)' 行"
    else
      echo "G2 FAIL: journal 已改但缺合法 'Pattern Index 更新:' 行(值域 N/A|新增)"
      fail=1
    fi
  else
    echo "G2 PASS: journal 未改"
  fi

  # G3
  if [ "$kernel_changed" = 1 ] || [ "$bench_changed" = 1 ]; then
    run_meta_bench
    local rc=$?
    if [ "$rc" = 2 ]; then
      env_err=1
    elif [ "$rc" != 0 ]; then
      echo "G3 FAIL: meta-bench --verify/--demo 未通过(exit $rc)"
      fail=1
    else
      echo "G3 PASS: meta-bench --verify + --demo 通过"
    fi
  else
    echo "G3 PASS: 无内核/bench 改动"
  fi

  [ "$env_err" = 1 ] && return 2
  [ "$fail" = 1 ] && return 1
  return 0
}

main "$@"
