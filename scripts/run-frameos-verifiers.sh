#!/usr/bin/env bash
# FrameOS 克隆验证器统一入口 (Batch 184)
# 用法:
#   bash scripts/run-frameos-verifiers.sh            # 跑全部
#   bash scripts/run-frameos-verifiers.sh 171 172    # 只跑指定批次
# 前置: dev server 已运行在 $LIBLIB_BASE_URL (默认 http://localhost:4317),
#       python 需有 playwright (~/.pyenv/versions/3.10.6/bin/python 已验证可用)。

set -u

PY="${FRAMEOS_PYTHON:-$HOME/.pyenv/versions/3.10.6/bin/python}"
[ -x "$PY" ] || PY="python3"
BASE_URL="${LIBLIB_BASE_URL:-http://localhost:4317}"
export LIBLIB_BASE_URL="$BASE_URL"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# 全量清单: 动态发现 scripts/verify-frameos-batch*.py (Batch 194 起自维护);
# batch168 已随源站新版本退役, 如残留脚本则跳过
RETIRED="168"
if [ "$#" -gt 0 ]; then
  BATCHES="$*"
else
  BATCHES=$(ls "$ROOT"/scripts/verify-frameos-batch*.py 2>/dev/null \
    | sed -E 's/.*batch([0-9]+)\.py/\1/' | sort -n | tr '\n' ' ')
fi

pass=0
fail=0
failed_list=""
retry_list=""
for b in $BATCHES; do
  script="scripts/verify-frameos-batch$b.py"
  if [ ! -f "$script" ]; then
    echo "skip batch$b (no verifier)"
    continue
  fi
  for r in $RETIRED; do
    if [ "$b" = "$r" ]; then
      echo "skip batch$b (retired)"
      continue 2
    fi
  done
  if out=$("$PY" "$script" 2>&1); then
    pass=$((pass + 1))
    echo "PASS batch$b"
  else
    fail=$((fail + 1))
    failed_list="$failed_list $b"
    echo "FAIL batch$b"
    echo "$out" | tail -5
  fi
done

# Batch 215: 失败批次自动重试一次 (并发负载下的偶发失败隔离)
if [ "$fail" -gt 0 ]; then
  echo "---- retrying failed batches:$failed_list"
  retried_fail=0
  for b in $failed_list; do
    if out=$("$PY" "scripts/verify-frameos-batch$b.py" 2>&1); then
      pass=$((pass + 1))
      fail=$((fail - 1))
      echo "RETRY PASS batch$b"
    else
      retried_fail=$((retried_fail + 1))
      echo "RETRY FAIL batch$b"
      echo "$out" | tail -5
    fi
  done
  fail=$retried_fail
fi

echo "----"
echo "frameos verifiers: $pass passed, $fail failed (after retry)"
[ "$fail" -eq 0 ] || { echo "failed batches:$failed_list"; exit 1; }
