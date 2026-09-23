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

# 全量清单 (与 BEHAVIORS/验证器基线一致; batch168 已随源站新版本退役)
ALL_BATCHES="133 134 157 158 159 160 161 162 163 164 165 166 167 168 169 170 171 172 173 174 175 176 177 178 179 180"
# batch168: 源站新版本已移除双击空白菜单, 验证器已退役 — 除非清单中则跳过
if [ "$#" -gt 0 ]; then
  BATCHES="$*"
else
  BATCHES=$(echo "$ALL_BATCHES" | tr ' ' '\n' | grep -vx 168 | tr '\n' ' ')
fi

pass=0
fail=0
failed_list=""
for b in $BATCHES; do
  script="scripts/verify-frameos-batch$b.py"
  if [ ! -f "$script" ]; then
    echo "skip batch$b (no verifier)"
    continue
  fi
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

echo "----"
echo "frameos verifiers: $pass passed, $fail failed"
[ "$fail" -eq 0 ] || { echo "failed batches:$failed_list"; exit 1; }
