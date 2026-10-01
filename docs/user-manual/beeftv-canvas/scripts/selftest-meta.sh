#!/usr/bin/env bash
# 第八道闸（verify-meta.py）的反向验证。
#
# Batch 143 立了「闸门要成对：能抓 + 不误伤，缺一不可」，
# 本脚本是这个纪律在第八道闸上的应用。四条用例覆盖三类失效：
#
#   1) 方向一抓「数字写错」：把 README 的任务页数改回 Batch 145 之前的旧值
#   2) 方向一抓「登记项失效」：把手册改成闸门登记的正则扫不到的写法
#   3) 方向二抓「登记表漏项」：在参与发布的页面里塞一个未登记的元数据表述
#   4) **不误伤**：把「过期数字」写进台账（AUDIT-RULES.md）——它本就是
#      「记录曾经错了什么」的正当用途，闸门必须**当没看见**
#
# 第 4 条是本闸最关键的一条：Batch 145 之所以能撞见那批过期数字，
# 正是因为它们当时**没人扫**；但反过来，闸门也不能因此把
# `AUDIT-RULES.md:334` 那句「README 写着 25 篇」当成当前声明去报错。
# **能抓和不误伤在这里是同一件事的两面，缺了第 4 条，闸门会在第一次
# 有人记录自己的历史错误时就变成噪音。**

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"
GATE="$HERE/verify-meta.py"

PASS=0
FAIL=0

# 每次用例前**全量还原**——Batch 143 第 25 条：只还原当次目标文件的话，
# 上一个用例注入的改动会留在原地，让本用例的输出对不上。
restore() {
  cd "$ROOT" || exit 1
  git checkout -- README.md 10-tasks/README.md FINAL-REPORT.md AUDIT-RULES.md AUDIT.md PROGRESS.md 00-quickstart.md 2>/dev/null
  find . -name "*.png.new" -delete 2>/dev/null
}

run_fail_case() {
  local desc="$1"; shift
  local want="$1"; shift
  restore
  eval "$@"                      # 注入破坏
  local out rc
  out="$(python3 "$GATE" 2>&1)"; rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "  ✗ $desc：闸门本应报错，却通过了"; echo "$out" | sed 's/^/      /'; FAIL=$((FAIL+1))
  elif echo "$out" | grep -qF "$want"; then
    echo "  ✓ $desc：正确报出 [$want]（退出码 $rc）"; PASS=$((PASS+1))
  else
    echo "  ✗ $desc：报错了但不是 [$want]；实际："; echo "$out" | sed 's/^/      /'; FAIL=$((FAIL+1))
  fi
  restore
}

run_pass_case() {
  local desc="$1"; shift
  restore
  eval "$@"
  local out rc
  out="$(python3 "$GATE" 2>&1)"; rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "  ✓ $desc：闸门正确放行"; PASS=$((PASS+1))
  else
    echo "  ✗ $desc：本应放行却报错（误伤）；实际："; echo "$out" | sed 's/^/      /'; FAIL=$((FAIL+1))
  fi
  restore
}

echo "=== 第八道闸反向验证（verify-meta.py）==="

# 用例 1：把任务页数改回 Batch 145 修复前的旧值 25
run_fail_case "1) README 任务页数退回 25" "任务指南页数 写 [25]，实际 29" \
  "python3 -c \"
import re,io
p='README.md'; s=open(p,encoding='utf-8').read()
s=re.sub(r'\*\*29 篇任务指南\*\*','**25 篇任务指南**',s,1)
open(p,'w',encoding='utf-8').write(s)
\""

# 用例 2：把手册改成登记正则扫不到的写法（去掉粗体标记并换措辞）
# ——守的是「登记表与手册写法**双向**绑定」：手册改了排版而登记表没跟上必须报，
#    而不是静默地「这条不存在了」。
run_fail_case "2) README 改了写法使登记正则扫不到" "登记正则扫不到" \
  "python3 -c \"
p='README.md'; s=open(p,encoding='utf-8').read()
s=s.replace('**29 篇任务指南**','任务指南 29 篇',1)
open(p,'w',encoding='utf-8').write(s)
\""

# 用例 3：方向二——在参与发布的页面里塞一个**未登记**的元数据表述。
# 守的是反向扫描：没有登记表约束时，漏登记就等于没检查。
run_fail_case "3) 00-quickstart 塞入未登记的「N 张截图」表述" "但未登记为 截图数" \
  "python3 -c \"
p='00-quickstart.md'; s=open(p,encoding='utf-8').read()
s=s.rstrip()+chr(10)+chr(10)+'本手册共 88 张截图。'+chr(10)
open(p,'w',encoding='utf-8').write(s)
\""

# 用例 4：**不误伤**——把过期数字写进台账。台账不在 srcExclude 的发布范围内，
# 它记录「曾经错成什么样」是正当用途，闸门必须当没看见。
run_pass_case "4) 台账里记录历史过期数字（必须不报）" \
  "python3 -c \"
p='AUDIT-RULES.md'; s=open(p,encoding='utf-8').read()
s=s.rstrip()+chr(10)+'> 历史上 README 曾写「25 篇任务指南 / 账本共 32 项 / 33 页 HTML」，均已过期。'+chr(10)
open(p,'w',encoding='utf-8').write(s)
\""

echo "=== 基线：真实仓库应当通过 ==="
restore
if python3 "$GATE" >/dev/null 2>&1; then
  echo "  ✓ 真实仓库通过"; PASS=$((PASS+1))
else
  echo "  ✗ 真实仓库未通过"; FAIL=$((FAIL+1))
fi

echo "=== 结果：通过 $PASS / 失败 $FAIL ==="
echo "=== 清理后状态 ==="
echo "  未还原的手册改动: $(git status --porcelain -- README.md 10-tasks/README.md FINAL-REPORT.md AUDIT-RULES.md 00-quickstart.md 2>/dev/null | wc -l | tr -d ' ') （应为 0）"
[ "$FAIL" -eq 0 ] || exit 1
