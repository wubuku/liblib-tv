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
#   5) 方向三抓「闸门清单漏登记」：加一道闸却没更新清单表
#   6) 方向三抓「标题数与表行数差 1」——这正是本闸上线当天在真实文档里
#      抓到的第三次同向遗漏（标题在数脚本数，表行数还要加内联那道）
#   7) 方向四抓「页面没进索引」：Batch 153 在真实仓库里抓到的——Batch 139/140/141
#      连续新建的三页都没登记，其中 /create 是产品第二大门户
#   8) 方向四抓「索引链接文字与页面标题对不上」
#   9) **不误伤**：保留原有的「标题（提示）」形态——索引在标题后补一句提示是
#      有意设计（「只读画布与画布副本（无入口，副本不上传）」）
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

# ── snapshot / restore：还原到「脚本启动时的状态」，不是 HEAD ─────────
#
# **第一版用 `git checkout -- <files>` 还原，当场把本批未提交的工作抹掉了**：
# AUDIT-RULES.md 刚改成「现有九道闸」，被一键退回 HEAD 的「七道闸」，
# 下一个用例的锚点就找不到，基线也跟着挂。
#
# 这比 Batch 143 第 25 条「前提不干净」**更严重**：那条是**结论不可信**，
# 这条是**工作被销毁**。本项目禁用 stash，故改用临时目录做快照。
#
# **还原的基准必须是「进来时什么样」，而不是「仓库里已提交什么样」**——
# 否则这个脚本就成了一个会吃掉未提交改动的工具，而它本该是被信任的检查工具。
SNAP="$(mktemp -d "${TMPDIR:-/tmp}/beef-meta-selftest.XXXXXX")"
SNAP_FILES=(README.md 10-tasks/README.md FINAL-REPORT.md AUDIT-RULES.md AUDIT.md PROGRESS.md 00-quickstart.md build-site.sh)

snapshot() {
  cd "$ROOT" || exit 1
  for f in "${SNAP_FILES[@]}"; do
    [ -f "$f" ] || continue
    mkdir -p "$SNAP/$(dirname "$f")"
    cp "$f" "$SNAP/$f"
  done
}

restore() {
  cd "$ROOT" || exit 1
  for f in "${SNAP_FILES[@]}"; do
    [ -f "$SNAP/$f" ] && cp "$SNAP/$f" "$f"
  done
}

# 每次用例前**全量还原**（Batch 143 第 25 条：只还原当次目标文件的话，
# 上一个用例注入的改动会留在原地，让本用例的输出对不上）。
snapshot
trap 'restore' EXIT

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

# 用例 5：方向三——加一道闸到 build-site.sh，但**忘了更新清单表**
# 守的是「清单表漏登记」。这在真实仓库里已经发生过两次（Batch 143 的第七道、
# Batch 146 的第八道），用例要保证它以后会被自动抓到。
run_fail_case "5) 加了闸但清单表没登记" "清单表却没有登记" \
  "python3 -c \"
p='build-site.sh'; s=open(p,encoding='utf-8').read()
s=s.replace('python3 scripts/verify-tables.py','python3 scripts/verify-foo.py',1)
open(p,'w',encoding='utf-8').write(s)
\""

# 用例 6：方向三——标题数与表行数差 1
# 这不是假设出来的场景：**本闸上线当天就在真实 AUDIT-RULES.md 上抓到过**
# （标题写「八道闸」而表里 9 行）。根因是标题数的是「verify 脚本数」，
# 而表行数还要加上「站内死链」那道内联的——差 1 每次都刚好逃过肉眼。
run_fail_case "6) 标题的闸数与表行数差 1" "标题写「8 道闸」，清单表却有 9 行" \
  "python3 -c \"
p='AUDIT-RULES.md'; s=open(p,encoding='utf-8').read()
s=s.replace('### 现有九道闸','### 现有八道闸',1)
open(p,'w',encoding='utf-8').write(s)
\""

# 用例 7：方向四——把一个任务页从索引里删掉（模拟「建了页面忘了登记」）
run_fail_case "7) 任务页没进索引" "不在 10-tasks/README.md 的索引里" \
  "python3 -c \"
p='10-tasks/README.md'; s=open(p,encoding='utf-8').read()
s=s.replace(' · [素材库（资产页）](asset-library.md)','',1)
open(p,'w',encoding='utf-8').write(s)
\""

# 用例 8：方向四——把索引里的链接文字改成一个与页面标题无关的名字
run_fail_case "8) 索引链接文字与页面标题对不上" "与页面标题" \
  "python3 -c \"
p='10-tasks/README.md'; s=open(p,encoding='utf-8').read()
s=s.replace('[创建各类节点](create-nodes.md)','[节点创建向导](create-nodes.md)',1)
open(p,'w',encoding='utf-8').write(s)
\""

# 用例 9：**不误伤**——「标题（提示）」是索引的有意形态，必须放行。
# 没有这一条，方向四一上线就会把两条真实存在的提示报成「不一致」。
run_pass_case "9) 索引里的「标题（提示）」形态（必须不报）" \
  "python3 -c \"
p='10-tasks/README.md'; s=open(p,encoding='utf-8').read()
s=s.replace('[创建各类节点](create-nodes.md)','[创建各类节点（新建入口在此）](create-nodes.md)',1)
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
# 与 **snapshot** 比对，而不是 `git status`。
# 用 git status 会把「本批本来就还没提交的改动」也算成残留 —— 那是正常状态，不是残留。
# 第一版就是这么写的，于是每次跑都报 1，看着像没还原干净。
leftover=0
for f in "${SNAP_FILES[@]}"; do
  [ -f "$SNAP/$f" ] || continue
  cmp -s "$SNAP/$f" "$f" || { echo "  ✗ 未还原：$f"; leftover=$((leftover+1)); }
done
echo "  与进入脚本时不一致的文件: $leftover （应为 0）"
[ "$FAIL" -eq 0 ] || exit 1
