#!/usr/bin/env bash
# 按退出码逐个跑全部门禁并汇总（F140 的落地，M302 新增）。
#
# **为什么需要这个脚本**：
# M301 撞上一件很典型的事——我每批验收时临时拼的 shell 循环是
#
#     out=$(python3 "$f" 2>&1 | grep -E "^\[fail\]|FAIL" | head -2)
#
# ★ **而各门禁的失败文案格式并不统一**：`check-retractions.py` 输出 `[FAIL] …`，
# ★ `check-encoding.py` 输出的却是「编码校验未通过（…）」——★ **两个模式都匹配不上，
# ★ **于是那道门禁失败时被静默跳过**，★ **而整条循环仍打印「全部门禁跑完」。
# ★ **★ 那个输出与真的全绿一模一样。**（F140）
#
# 本脚本只认退出码。**任何格式的失败输出都会被如实计成失败。**
#
# 用法：
#     bash scripts/run-gates.sh [手册根目录]
#     bash scripts/run-gates.sh . --quiet     # 只在失败时输出

set -uo pipefail

ROOT="${1:-.}"
shift || true
QUIET=0
for a in "$@"; do
  [ "$a" = "--quiet" ] && QUIET=1
done

[ -d "$ROOT/scripts" ] || { echo "用法：bash scripts/run-gates.py <手册根目录>"; exit 2; }

fail_names=""
total=0
for f in "$ROOT"/scripts/check-*.py; do
  [ -f "$f" ] || continue
  total=$((total + 1))
  name="$(basename "$f")"
  out="$(cd "$ROOT" && python3 "scripts/$name" "$ROOT" 2>&1)"
  rc=$?
  # ★ **只认退出码**——不 grep 任何文案（F140）
  if [ $rc -ne 0 ]; then
    fail_names="$fail_names $name"
    echo "[FAIL exit=$rc] $name"
    printf '%s\n' "$out" | sed 's/^/    /'
  elif [ "$QUIET" -eq 0 ]; then
    printf '%s\n' "$out" | tail -1 | sed "s|^|  ok  $name  |"
  fi
done

echo "————————————————————————————————"
if [ -n "$fail_names" ]; then
  echo "门禁未通过：$(( $(echo $fail_names | wc -w) )) / $total 道失败 →$fail_names"
  exit 1
fi
echo "全部门禁通过：$total 道，退出码均为 0"
exit 0