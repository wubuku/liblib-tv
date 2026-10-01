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
#  10) 方向四之二抓「页面不在 vitepress 侧栏」——Batch 154 在真实仓库里抓到 4 个，
#      其中 readonly-canvas.md 从建页起就一直在侧栏外
#  11) 方向四之二**不误伤**：侧栏文字用短标题（「上传本地素材」vs 页面 h1）
#      是有意设计，必须放行——**该方向只查存在性，不比文字**
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
VOID=0

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
SNAP_FILES=(README.md 10-tasks/README.md FINAL-REPORT.md AUDIT-RULES.md AUDIT.md PROGRESS.md 00-quickstart.md 30-concepts.md build-site.sh .vitepress/config.mjs scripts/verify-unreachable.py scripts/verify-meta.py scripts/verify-endpoints.py scripts/verify-shortcuts.py scripts/verify-screenshots.py)

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
  find . -name "*.injected" -delete 2>/dev/null
  find . -name "*.injecterr" -delete 2>/dev/null
}

# 每次用例前**全量还原**（Batch 143 第 25 条：只还原当次目标文件的话，
# 上一个用例注入的改动会留在原地，让本用例的输出对不上）。
snapshot
trap 'restore' EXIT

# 注意：这里**不能用 grep -q**（Batch 160 当场踩到）。脚本开了 `set -o pipefail`，
# 而 `grep -q` 命中即退出 → 上游 `printf`/`echo` 收到 SIGPIPE 返回 141 →
# 整条管道被判失败 → **明明打印出了要匹配的那行，用例却判「报错了但不是它」**。
# 危害与假通过同级：它让**正确的闸门输出被当成错误**。
# 第二条命令 `grep -F ... >/dev/null` 会**读完整个输入**，不产生 SIGPIPE。

# ── 内联注入的空转检测（Batch 162） ────────────────────────────────────
# **为什么要加**：`run_fail_case` 的注入是内联 `python3 -c`，**没有锚点断言**。
# 本批把闸门数从 9 改成 10、标题从「现有九道闸」改成「现有十道闸」之后，
# 用例 6 的 `replace('### 现有九道闸', …)` **匹配不到、静默什么也没改**，
# 闸门当然通过 → 用例判「本应报错，却通过了」。
# **危险之处在于它不报错**：失败信息指向「闸门没报错」，会把人引向完全错误的方向，
# 而真实原因是「测试自己没注入成功」。
#
# **通用解法**：eval 前后各做一次快照，**内容没变即判作废**。
# 这样不必把每条内联注入都改写成带 assert 的注入脚本文件，
# 而**任何未来的锚点失配都会被立刻暴露**（Batch 135「锚点错就作废」的推广）。
run_fail_case() {
  local desc="$1"; shift
  local want="$1"; shift
  restore
  local before after
  before="$(cd "$ROOT" && for f in "${SNAP_FILES[@]}"; do [ -f "$f" ] && md5 -q "$f" 2>/dev/null; done | md5 -q)"
  eval "$@"                      # 注入破坏
  after="$(cd "$ROOT" && for f in "${SNAP_FILES[@]}"; do [ -f "$f" ] && md5 -q "$f" 2>/dev/null; done | md5 -q)"
  if [ "$before" = "$after" ]; then
    echo "  · 前提不成立：注入**空转**（所有目标文件内容都没变，多半是锚点失配）；作废该用例"
    VOID=$((VOID+1)); restore; return 0
  fi
  local out rc
  out="$(python3 "$GATE" 2>&1)"; rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "  ✗ $desc：闸门本应报错，却通过了"; echo "$out" | sed 's/^/      /'; FAIL=$((FAIL+1))
  elif echo "$out" | grep -F "$want" >/dev/null; then
    echo "  ✓ $desc：正确报出 [$want]（退出码 $rc）"; PASS=$((PASS+1))
  else
    echo "  ✗ $desc：报错了但不是 [$want]；实际："; echo "$out" | sed 's/^/      /'; FAIL=$((FAIL+1))
  fi
  restore
}

# 按**注入脚本文件**运行一个用例：把目标文件喂给注入脚本，再跑闸门。
#
# **前提 = 注入脚本的 anchor 断言命中**。注入脚本里写着 `assert old in s, "锚点未命中"`，
# 锚点不对时它非零退出 —— 这时**作废该用例，不算通过**。
#
# 第一版把「闸门输出里含注入标识」当前提，**结果用例 10 被永久作废**：
# 闸门**通过时根本不打印被检页面清单**，所以前提永远不成立。
# 第二次踩同一个坑：用例 11 的内联注入被多层转义弄出 SyntaxError，
# 而它是 run_pass_case（期望放行）——**注入失败 = 没注入 = 基线状态 = 放行 = 通过**，
# 属于**假通过**。**注入失败必须作废，不能算通过。**（Batch 135「锚点错就作废」的规矩，
# 当时只用在第六道闸，这里证明它对所有反向验证脚本都成立。）
run_file_case() {
  local desc="$1"; shift
  local target="$1"; shift
  local fixer="$1"; shift
  local want="$1"; shift
  restore
  [ -f "$target" ] || { echo "  · 前提不成立：目标文件 $target 不存在；作废"; VOID=$((VOID+1)); return 0; }
  if ! python3 "$fixer" < "$target" > "$target.injected" 2>"$target.injecterr"; then
    echo "  · 前提不成立：注入脚本未命中锚点（$(head -1 "$target.injecterr" 2>/dev/null)）；作废该用例"
    restore; VOID=$((VOID+1)); return 0
  fi
  # 注入后必须与注入前不同，否则说明注入脚本空转（也是前提不成立）
  if cmp -s "$target" "$target.injected"; then
    echo "  · 前提不成立：注入脚本空转（内容未变）；作废该用例"
    restore; VOID=$((VOID+1)); return 0
  fi
  mv "$target.injected" "$target"
  local out rc
  out="$(python3 "$GATE" 2>&1)"; rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "  ✗ $desc：闸门本应报错，却通过了"; echo "$out" | sed 's/^/      /'; FAIL=$((FAIL+1))
  elif printf '%s' "$out" | grep -F "$want" >/dev/null; then
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

# 对称的**放行**用例：注入成功后闸门**必须仍然通过**。
# 与 run_file_case 共用同一套前提校验（注入脚本 anchor 必须命中且内容真的变了），
# **所以「注入失败」在这里同样作废，而不是算通过**。
run_file_pass_case() {
  local desc="$1"; shift
  local target="$1"; shift
  local fixer="$1"; shift
  restore
  [ -f "$target" ] || { echo "  · 前提不成立：目标文件 $target 不存在；作废"; VOID=$((VOID+1)); return 0; }
  if ! python3 "$fixer" < "$target" > "$target.injected" 2>"$target.injecterr"; then
    echo "  · 前提不成立：注入脚本未命中锚点（$(head -1 "$target.injecterr" 2>/dev/null)）；作废该用例"
    restore; return 0
  fi
  if cmp -s "$target" "$target.injected"; then
    echo "  · 前提不成立：注入脚本空转（内容未变）；作废该用例"
    restore; VOID=$((VOID+1)); return 0
  fi
  mv "$target.injected" "$target"
  if python3 "$GATE" >/dev/null 2>&1; then
    echo "  ✓ $desc：闸门正确放行"; PASS=$((PASS+1))
  else
    echo "  ✗ $desc：本应放行却报错（误伤）；实际："; python3 "$GATE" 2>&1 | sed 's/^/      /'; FAIL=$((FAIL+1))
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
run_fail_case "6) 标题的闸数与表行数差 1" "标题写「9 道闸」，清单表却有 10 行" \
  "python3 -c \"
p='AUDIT-RULES.md'; s=open(p,encoding='utf-8').read()
assert '### 现有十道闸' in s, '锚点未命中'
s=s.replace('### 现有十道闸','### 现有九道闸',1)
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

# 用例 10：方向四之二——把一个任务页从侧栏里删掉。
# **用独立注入脚本而不是内联 python**：第一版内联写法在 heredoc + 转义里被拆坏
# （`\\"` 变成裸 `"` 破坏 Python 源码，SyntaxError）。第六道闸的 26 个用例全用独立
# `.py` 注入脚本，正是这个原因。**嵌套转义不是可靠机制，能用文件就别用字符串。**
run_file_case "10) 任务页不在 vitepress 侧栏" \
  ".vitepress/config.mjs" "$HERE/selftest-meta-fix-10-sidebar-missing.py" \
  "不在 vitepress 侧栏里"

# 用例 11：**不误伤**——侧栏文字用短标题是设计
# （侧栏「上传本地素材」vs 页面 h1「上传本地图片、视频、音频」），
# 方向四之二**只查存在性、不比文字**，必须放行。
# 第一版用内联 python，被 heredoc 多层转义弄出 SyntaxError；而它是 run_pass_case，
# **注入失败 = 没注入 = 基线状态 = 放行 = 通过**——**那是假通过**。改用注入脚本文件。
run_file_pass_case "11) 侧栏用短标题（必须不报）" \
  ".vitepress/config.mjs" "$HERE/selftest-meta-fix-11-sidebar-short-title.py"

# ── 方向五（Batch 157 新增）：git grep 正则的引擎兼容性 ──
#
# **这两条是本批最重要的一对**：方向五守的是「闸门的正则会不会静默失效」，
# 而它自己最可能的失效方式恰恰是**永远通过**。所以必须先证明它抓得到。
#
# 用例 14 尤其不能省：方向五只看 `git grep -E` 的模式，
# **Python 的 re 支持 `\s`**，手册脚本里大量这么用是**完全正确的**。
# 若不分引擎一律报错，它会一次报出几十处正当写法——
# **第一次误报就会让人开始忽略这道闸，闸门就废了**
# （Batch 150 判「文案逐字对账闸不可建」用的正是同一条理由）。
run_file_case "13) git grep 模式里混入 \\s（必须报）" \
  "scripts/verify-unreachable.py" "$HERE/selftest-meta-fix-13-bad-escape-in-gitgrep.py" \
  "git grep -E 模式含"
run_file_pass_case "14) Python re 里用 \\s（必须不报）" \
  "scripts/verify-unreachable.py" "$HERE/selftest-meta-fix-14-pathsafe-s-in-python-re.py"
# 用例 15：比 13 更危险的一类——惰性量词 `{0,n}?` 与「重复数 > 255」会让 git
# **整条拒绝模式并返回 128**，stdout 为空；而空输出在判据里等于「零命中」，
# **整条断言随之恒真**。本闸真实中过（p_readonly_no_ui_entry 从上线起是死代码）。
run_file_case "15) git grep 模式里混入惰性量词 {0,300}?（必须报）" \
  "scripts/verify-unreachable.py" "$HERE/selftest-meta-fix-15-lazy-quantifier.py" \
  "git grep -E 模式含"

# ── 用例 16：闸门自身的「工具失败必须可区分」运行时行为 ──
#
# 方向五（静态）能挡住**新的**非法模式，但 `_git_grep_run()` 那个运行时兜底
# 属于「改回去也不会有任何静态检查发现」的那类——所以必须单独验它一次。
#
# **这条用例也说明为什么它不在 selftest-unreachable.sh 里**：
# 那个框架靠 git plumbing 往 **BeefTV 源码**注入并重建临时 ref，
# 而这里要改的是**闸门脚本自己**（scripts/verify-unreachable.py），
# 它根本不在 BeefTV 仓里——用错框架会直接锚点失配。
echo "=== 用例 16：git grep 模式非法时，闸门须报「判据执行异常」而非「仍成立」 ==="
restore
G6=scripts/verify-unreachable.py
if [ ! -f "$G6" ]; then
  echo "  · 前提不成立：$G6 不存在；作废该用例"; VOID=$((VOID+1))
elif ! python3 "$HERE/selftest-meta-fix-15-lazy-quantifier.py" < "$G6" > "$G6.injected" 2>/dev/null; then
  echo "  · 前提不成立：注入脚本未命中锚点；作废该用例"; VOID=$((VOID+1))
elif cmp -s "$G6" "$G6.injected"; then
  echo "  · 前提不成立：注入脚本空转；作废该用例"; VOID=$((VOID+1))
else
  mv "$G6.injected" "$G6"
  out6="$(python3 "$G6" 2>&1)"; rc6=$?
  if [ "$rc6" -eq 0 ]; then
    echo "  ✗ 16) 模式非法却报「全部通过」——工具失败被当成了干净的否定结果"
    FAIL=$((FAIL+1))
  elif printf '%s' "$out6" | grep -F "判据执行异常" >/dev/null; then
    echo "  ✓ 16) 模式非法：闸门正确报出 [判据执行异常]（退出码 $rc6）"; PASS=$((PASS+1))
  else
    echo "  ✗ 16) 报错了但不是「判据执行异常」；实际："; printf '%s' "$out6" | tail -5 | sed 's/^/      /'
    FAIL=$((FAIL+1))
  fi
  restore
fi

# ── 方向六（Batch 158 新增）：内链完整性 ──
#
# **必须成对**：能抓（17/18/19）+ 不误伤（20）。
# **20 最要紧**——它反过来把「首页豁免」去掉，证明孤儿检测对真实页面确实在工作。
# 若去掉豁免后闸门**不报**，那说明孤儿检测形同虚设，19 那条也只是在测一个空壳。
run_file_case "17) 正文链接指向不存在的文件（必须报）" \
  "00-quickstart.md" "$HERE/selftest-meta-fix-17-broken-link.py" \
  "链接指向不存在的文件"
run_file_case "18) 正文链接带 #fragment（必须报）" \
  "00-quickstart.md" "$HERE/selftest-meta-fix-18-link-fragment.py" \
  "链接带 #fragment"

# 用例 19 需要**两处同时改**：任务索引不在侧栏，入链只有两条，
# 删一处它仍被另一处链着。写成一段自定义流程而不是 run_file_case。
echo "  → 用例 19: 摘掉任务索引的全部入链（两处），期望报出孤儿页"
restore
ok19=1
for pair in "README.md:$HERE/selftest-meta-fix-19a-orphan-index-link.py" \
            "30-concepts.md:$HERE/selftest-meta-fix-19b-orphan-index-link2.py"; do
  tgt="${pair%%:*}"; fix="${pair##*:}"
  if [ ! -f "$tgt" ]; then echo "  · 前提不成立：$tgt 不存在"; ok19=0; break; fi
  if ! python3 "$fix" < "$tgt" > "$tgt.injected" 2>/dev/null; then
    echo "  · 前提不成立：$tgt 的注入脚本未命中锚点"; ok19=0; break
  fi
  if cmp -s "$tgt" "$tgt.injected"; then
    echo "  · 前提不成立：$tgt 的注入脚本空转"; ok19=0; break
  fi
  mv "$tgt.injected" "$tgt"
done
if [ "$ok19" -eq 1 ]; then
  out19="$(python3 "$GATE" 2>&1)"; rc19=$?
  if [ "$rc19" -eq 0 ]; then
    echo "  ✗ 19) 索引已无入链却报通过——孤儿检测没在工作"; FAIL=$((FAIL+1))
  elif printf '%s' "$out19" | grep -F "10-tasks/README.md 没有任何入链" >/dev/null; then
    echo "  ✓ 19) 正确报出 [10-tasks/README.md 没有任何入链]（退出码 $rc19）"; PASS=$((PASS+1))
  else
    echo "  ✗ 19) 报错了但不是孤儿页；实际："; printf '%s' "$out19" | grep '✗' | head -3 | sed 's/^/      /'
    FAIL=$((FAIL+1))
  fi
fi
restore

# 用例 20：去掉首页豁免，期望闸门**立刻**报出根 README.md 是孤儿页。
# 注入的是**闸门脚本自己**（scripts/verify-meta.py），故它必须在 SNAP_FILES 里。
echo "  → 用例 20: 去掉首页豁免，期望立刻报出根 README.md 是孤儿页"
restore
G7=scripts/verify-meta.py
if [ ! -f "$G7" ]; then
  echo "  · 前提不成立：$G7 不存在；作废该用例"; VOID=$((VOID+1))
elif ! python3 "$HERE/selftest-meta-fix-20-drop-home-exemption.py" < "$G7" > "$G7.injected" 2>/dev/null; then
  echo "  · 前提不成立：注入脚本未命中锚点；作废该用例"; VOID=$((VOID+1))
elif cmp -s "$G7" "$G7.injected"; then
  echo "  · 前提不成立：注入脚本空转；作废该用例"; VOID=$((VOID+1))
else
  mv "$G7.injected" "$G7"
  out20="$(python3 "$GATE" 2>&1)"; rc20=$?
  if [ "$rc20" -eq 0 ]; then
    echo "  ✗ 20) 去掉首页豁免后仍报通过——孤儿检测对真实页面不工作，19 只是空壳"
    FAIL=$((FAIL+1))
  elif printf '%s' "$out20" | grep -F "README.md 没有任何入链" >/dev/null; then
    echo "  ✓ 20) 去掉豁免后正确报出 [README.md 没有任何入链]（退出码 $rc20）——"
    echo "      证明孤儿检测有效，且豁免是真正承重的"
    PASS=$((PASS+1))
  else
    echo "  ✗ 20) 报错了但不是首页孤儿；实际："; printf '%s' "$out20" | grep '✗' | head -3 | sed 's/^/      /'
    FAIL=$((FAIL+1))
  fi
  restore
fi

# ── 方向七（Batch 159 新增）：闸门不得「只报错不失败」 ──
#
# **这条不变式来自两次真实事故**：方向五与方向六**各漏过一次 `fails += 1`**，
# 闸门把问题打印出来了、**退出码却是 0**，而 build-site.sh / 反验 / CI 只看退出码。
# 修法不是「再加一道记得检查的闸」（同一个错误已经犯两次，第三次还会犯），
# 而是让 `print("✗ …")` **在结构上无法与计数分开**。
#
# 用例 22 尤其不能省：早退 `return 1` 是**正确写法**，
# 若方向七不豁免它，就得把早退改成累加器——**为让闸门闭嘴而改坏代码**。
run_file_case "21) 把 fail() 换回裸 print（必须报）" \
  "scripts/verify-meta.py" "$HERE/selftest-meta-fix-21-bare-error-print.py" \
  "退出码会仍是 0"
run_file_pass_case "22) 早退路径上的裸 ✗ 打印（必须不报）" \
  "scripts/verify-meta.py" "$HERE/selftest-meta-fix-22-early-return-exempt.py"

# ── 方向八（Batch 160 新增）：闸门不得在「无法核对」时返回 0 ──
#
# **为什么它是 Batch 157 的续集**：那批治的是「工具失败被当成零命中」，
# 这批治的是它的**反面**——「工具/数据不可用被当成通过」。
# 普查发现 **6 个闸共 11 处** `[skip]` 之后 `return 0`，
# 而 build-site.sh 只看退出码：**上游目录一改名，5 个闸空转而绿。**
run_file_case "23) skip 路径退回 return 0（必须报）" \
  "scripts/verify-endpoints.py" "$HERE/selftest-meta-fix-23-skip-returns-zero.py" \
  "打印 [skip] 之后却 return 0"
run_file_pass_case "24) 普通 return 0（必须不报）" \
  "scripts/verify-shortcuts.py" "$HERE/selftest-meta-fix-24-plain-return-zero-ok.py"

# ── 方向九（Batch 161 新增）：风险类别覆盖度表的自洽性 ──
#
# **用例 26 是本方向的核心**：它保证**表不会悄悄落后于现实**。
# 项目里已栽过两次同型（Batch 147「加了闸忘了改清单表」、153/154「补了索引忘查侧栏」），
# 有了这一条，下次新增闸而忘更新 A 类会被当场抓住。
run_file_case "25) 覆盖度表某格依据留空（必须报）" \
  "AUDIT-RULES.md" "$HERE/selftest-meta-fix-25-coverage-empty-cell.py" \
  "有空格"
run_file_case "26) A 类行数比闸门清单多 1（必须报）" \
  "AUDIT-RULES.md" "$HERE/selftest-meta-fix-26-coverage-drift.py" \
  "与闸门清单脱节"
# 锚的是**失败语**而不是成功语——第一版锚了「输入范围自声明」（那是 ✓ 的话术），
# 于是闸门**明明报出了违规**、用例却判失败。
# **反验锚的必须是「失败时会出现的那句话」**，锚成功语等于锚错。
run_file_case "27) 闸门用裸相对 glob 定位正文（必须报）" \
  "scripts/verify-screenshots.py" "$HERE/selftest-meta-fix-27-cwd-glob.py" \
  "输入范围由 cwd 决定"
run_file_case "28) 闸门用无根目录常量拼路径（必须报）" \
  "scripts/verify-screenshots.py" "$HERE/selftest-meta-fix-28-rootless-dir.py" \
  "输入范围由 cwd 决定"
run_file_pass_case "29) 不误伤：同样的字面量只出现在注释里（必须放行）" \
  "scripts/verify-screenshots.py" "$HERE/selftest-meta-fix-29-docstring-glob.py"
run_file_case "30) 中文数字写成「十一」必须能解析（必须报行数不符而非找不到标题）" \
  "AUDIT-RULES.md" "$HERE/selftest-meta-fix-30-cn-numeral.py" \
  "标题写「11 道闸」"
# 31/32 是 Batch 168 方向九 ④ 的两条：**写错计数**与**删掉计数**都必须被抓。
# 32 尤其不能省——**只认「有计数才校验」的话，删掉计数就成了绕过的最短路径**。
run_file_case "31) A 类标题写的类数比表内行数少 1（必须报）" \
  "AUDIT-RULES.md" "$HERE/selftest-meta-fix-31-title-count.py" \
  "小节标题的计数与表内容脱节"
run_file_case "32) 把 A 类标题的计数整个删掉（必须报，不给绕过留后门）" \
  "AUDIT-RULES.md" "$HERE/selftest-meta-fix-32-drop-title-count.py" \
  "删掉它就绕过了检查"
# 33–36 是 Batch 168 方向十一的反验：对应关系表必须与现场**双向**一致。
# 33 与 34 是两个方向（漏认领 / 认领了不存在的），**单边判据的绿灯毫无意义**；
# 36 是「不误伤」那一半——备注列天生每批都要改，判据若把措辞当事实，
# **它逼着你把话说得越来越含糊**，那才是判据过宽的真正代价。
run_file_case "33) 对应关系表删掉一行（必须报：驱动没人认领）" \
  "AUDIT-RULES.md" "$HERE/selftest-meta-fix-33-unclaimed-driver.py" \
  "没有被对应关系表认领"
run_file_case "34) 对应关系表认领了不存在的反验（必须报）" \
  "AUDIT-RULES.md" "$HERE/selftest-meta-fix-34-missing-selftest.py" \
  "并不存在"
run_file_case "35) 对应关系表某行例数写成 0（必须报）" \
  "AUDIT-RULES.md" "$HERE/selftest-meta-fix-35-zero-case-count.py" \
  "必须是正整数"
run_file_pass_case "36) 不误伤：只改对应关系表的备注文字（必须放行）" \
  "AUDIT-RULES.md" "$HERE/selftest-meta-fix-36-remark-only.py"

echo "=== 基线：真实仓库应当通过 ==="
restore
if python3 "$GATE" >/dev/null 2>&1; then
  echo "  ✓ 真实仓库通过"; PASS=$((PASS+1))
else
  echo "  ✗ 真实仓库未通过"; FAIL=$((FAIL+1))
fi

# **作废数必须出现在汇总里**（Batch 157 实测踩到）：用例 13 的锚点写着
# `subprocess.run(`，而本批把 git grep 调用点换成了 `_git_grep_run(`，
# 锚点失配 → 该用例被作废 → **而汇总只打「通过/失败」，14 条里少的 1 条
# 静静消失，整体还报「失败 0」**。作废的用例既没验到、也没被算失败，
# 是最容易骗过人的一种绿灯。**宁可少认几条 ✓，不可让作废隐身。**
echo "=== 结果：通过 $PASS / 失败 $FAIL / 作废 $VOID ==="
if [ "$VOID" -gt 0 ]; then
  echo "=== ⚠ 有 $VOID 条用例作废（前提不成立），它们**没有验到任何东西**，不算通过 ==="
fi
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
[ "$VOID" -eq 0 ] || exit 1
