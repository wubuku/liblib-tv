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
# Batch 225 新增方向六之二（页内相对指代不许悬空），加了 2 例，**成对**：
#  40) 能抓：把被引用的那句「运行时实证」改掉 → 下面那层证据声明悬空，必须报
#  41) 不误伤：同一处耦合，只把指代方式换成自指的「本节」→ 必须放行
#
#
# ── Batch 340 修一处**从写下那天就错着**的编号（纪律 376）──────────────────
# **上面这两条原先写的是 12) 与 13)**，而**它们的实现从一开始就是 40/41**
# （`git show 058c3b4b` 实测：那次提交同时加了这两行注释**和** 40/41 的实现，
# **而注释里的号是 12/13**——**实现与注释在同一次提交里就已经不一致了**）。
# **为什么一直没被发现**，两个原因叠在一起，**每一个单独都足以让它潜伏**：
#   ① **12 号在整份文件里只出现在那一行注释里**（实测），所以
#      `preflight` 的 `find_case` 判它 `missing`「只在注释行里出现过」——
#      **而闸 9 方向十一只核「例数是正整数」，核不到「这一例到底存不存在」**；
#   ② **13 号更隐蔽**：那个号**已经被 Batch 150 的一条真用例占了**
#      （第 364 行「git grep 模式里混入反向斜杠加 s」），**而 `find_case` 判它 `ok`
#      ——它借别人的实现「活着」**。
#      **一条从没写过的用例，靠一个同号的真用例通过了存在性检查。**
# **而这一对注释正是「成对」的两条，坏掉的时候也是一起坏**：
# **12 报 missing、13 报 ok，而「一对里恰好一个 ok」比「两个都 missing」更像没事**。
# **编号写错的后果不是「注释不好看」**：它让闸 18 方向十六的真跑名单里
# **少了一例**（那一对里 40 是能抓的），**而账面完全看不出来**。
# Batch 250 给方向四加了 4 条，钉的是**「页面 H1 是怎么取的」**：
#  43) 能抓：整行删掉 H1（页面真的没有 H1）→ 必须报，**不得静默跳过整页**
#  44) 能抓：H1 在第 2 行 + 索引链接写错 → 必须报，**证明那一页真的被比了**
#  45) 不误伤：H1 带 ATX 闭合序列、索引写渲染后的名字 → 必须放行
#  46) 不误伤：H1 之前有含 `# 注释` 的代码围栏 → 必须放行
#      （**46 钉的是新判据自己新引入的风险**，前 45 条一条都伤不到它）
#  47) 不误伤：H1 写成缩进形态 ` # 标题` → 必须放行
#
# **Batch 325 加的两条**（方向十四：版本标注只认版本号，不认那一行的说明文字）：
#  52) 能抓：版本标注写了一个上游不存在的 tag → 必须报
#  53) 不误伤：只改版本标注那一行的说明、版本号一个字不动 → 必须放行
#      （**本清单原先止于 47，而实跑早已到 53**——**执行形态是真的，
#      **而「清单」这一侧停了六个号**，于是闸 9 方向十一核的「例数」与
#      「头部清单列了几个」**根本不是同一个数**，**两处都自洽、互不参照**）。
#      （Batch 251 加：**真渲染器给标题**，而 first_h1 当时不认缩进 → 会误报
#        「全文没有任何 H1」，**把 46 号那条刚写好的守卫变成假警报**）
#      （**「本节」恒成立，方向刻意不查**；少了它，40 可能只是「逢那句话就报」）
#
# 第 4 条是本闸最关键的一条：Batch 145 之所以能撞见那批过期数字，
# 正是因为它们当时**没人扫**；但反过来，闸门也不能因此把
# `AUDIT-RULES.md:334` 那句「README 写着 25 篇」当成当前声明去报错。
# **能抓和不误伤在这里是同一件事的两面，缺了第 4 条，闸门会在第一次
# 有人记录自己的历史错误时就变成噪音。**
# **Batch 205：`$var` 一律写成 `${var}`。** macOS 自带的 bash 3.2 在 UTF-8 locale 下
# 会把 `$var` 后面紧跟的多字节字符（中文全角标点）算进变量名，
# 于是报「`desc?: unbound variable`」——**而 `desc` 明明刚 `local` 过**。
# 实测：同一份脚本、同一台机器，`LC_CTYPE=C.UTF-8` 时 0/5 通过，不设时 5/5 通过。
# **`${var}` 是唯一可靠写法**，而「可靠」这件事在默认环境下看不出来。

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
SNAP_FILES=(README.md 10-tasks/README.md 10-tasks/asset-library.md 10-tasks/timeline-editing.md FINAL-REPORT.md AUDIT-RULES.md AUDIT.md PROGRESS.md 00-quickstart.md 30-concepts.md build-site.sh .vitepress/config.mjs scripts/verify-unreachable.py scripts/verify-meta.py scripts/verify-endpoints.py scripts/verify-shortcuts.py scripts/verify-screenshots.py scripts/verify-tables.py 10-tasks/director-basics.md)

# **Batch 320 往 SNAP_FILES 里补了 `scripts/verify-tables.py`**——
# 方向十三那两条用例要改它的 docstring，而它原本不在快照里。
# **后果有两层，第二层严重**：`run_file_case` 的「注入空转」判定靠 SNAP_FILES 的 md5，
# 文件不在其中则锚点失配也检测不出来（**锚点失配的用例会伪装成一次真实通过**）；
# 而 `restore()` 只还原 SNAP_FILES 里的文件——**用例跑完那份被改坏的闸脚本就留在树上了**。
# **这与 Batch 250 加 `asset-library.md` 时是同一条纪律，一个批次之后它又触发了一次。**

# **Batch 250 往 SNAP_FILES 里加了一行，而加它的理由本身就是一条纪律。**
# 方向四的 4 条新用例都要改 `10-tasks/asset-library.md`，而它**原本不在快照里**。
# 后果有两层，第二层比第一层严重：
#   ① `run_fail_case` 的「注入空转」判定靠 SNAP_FILES 的 md5 —— 文件不在其中，
#      注入失配也检测不出来，**锚点失配的用例会伪装成一次真实通过**；
#   ② `restore()` 只还原 SNAP_FILES 里的文件，**没登记的文件还原不了**——
#      而每条用例前都 `restore`、脚本退出还有 `trap 'restore' EXIT`，
#      也就是说**用例跑完，那份被改坏的页面就留在真树上了**。
# **写一条注入之前，先问「它要改的文件在不在快照里」。**
# 这一条本该在 Batch 168 建 SNAP_FILES 时就想到——**它当时按「已有的用例要改哪些」列的表，
# 而表是跟着用例长的，所以每加一批用例都要重问一次。**

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
    echo "  ✗ ${desc}：闸门本应报错，却通过了"; echo "$out" | sed 's/^/      /'; FAIL=$((FAIL+1))
  elif echo "$out" | grep -F "$want" >/dev/null; then
    echo "  ✓ ${desc}：正确报出 [$want]（退出码 ${rc}）"; PASS=$((PASS+1))
  else
    echo "  ✗ ${desc}：报错了但不是 [$want]；实际："; echo "$out" | sed 's/^/      /'; FAIL=$((FAIL+1))
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
    echo "  ✗ ${desc}：闸门本应报错，却通过了"; echo "$out" | sed 's/^/      /'; FAIL=$((FAIL+1))
  elif printf '%s' "$out" | grep -F "$want" >/dev/null; then
    echo "  ✓ ${desc}：正确报出 [$want]（退出码 ${rc}）"; PASS=$((PASS+1))
  else
    echo "  ✗ ${desc}：报错了但不是 [$want]；实际："; echo "$out" | sed 's/^/      /'; FAIL=$((FAIL+1))
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
    echo "  ✓ ${desc}：闸门正确放行"; PASS=$((PASS+1))
  else
    echo "  ✗ ${desc}：本应放行却报错（误伤）；实际："; echo "$out" | sed 's/^/      /'; FAIL=$((FAIL+1))
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
    # **Batch 225 修**：这里原本漏了 `VOID=$((VOID+1))`——同函数的下一个分支有。
    # 后果不是「用例失败」，是**它静默消失**：既不进 PASS 也不进 VOID，直接 return 0。
    # 脚本头自己写着「作废的用例既没验到、也没被算失败，是最容易骗过人的一种绿灯」，
    # **而这行代码正是那句话的一个实例**。而它是 Batch 225 的用例 41 依赖的那个函数——
    # 夹具一旦哪天锚点失配，用例 41 就会变成一盏假绿灯。
    restore; VOID=$((VOID+1)); return 0
  fi
  if cmp -s "$target" "$target.injected"; then
    echo "  · 前提不成立：注入脚本空转（内容未变）；作废该用例"
    restore; VOID=$((VOID+1)); return 0
  fi
  mv "$target.injected" "$target"
  if python3 "$GATE" >/dev/null 2>&1; then
    echo "  ✓ ${desc}：闸门正确放行"; PASS=$((PASS+1))
  else
    echo "  ✗ ${desc}：本应放行却报错（误伤）；实际："; python3 "$GATE" 2>&1 | sed 's/^/      /'; FAIL=$((FAIL+1))
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
# ⚠️ Batch 171 改写锚点：原来写死 `'### 现有十道闸'`，而本批新增闸 11 之后标题成了
# **「现有十一道闸」**——锚点失配 → 注入被跳过 → 通用空转检测判作废 →
# **这条用例连同 fix-30 一起，在本批的验收里整整作废了两次才发现**。
# 第三次栽在纪律 107 上：**字面量锚点必然随每次正常编辑漂移**。
# 现在改成**从现场推导**：用正则抓出当前标题里的中文数字，一律换成「九」。
# **闸数将来是 9 时这条会退化成空转**——所以下面 assert 的是「标题真的变了」。
run_fail_case "6) 标题的闸数与表行数差 1" "道闸」，清单表却有" \
  "python3 -c \"
import re
p='AUDIT-RULES.md'; s=open(p,encoding='utf-8').read()
m=re.search(r'### 现有[零一二三四五六七八九十]+道闸', s)
assert m, '锚点未命中：找不到「### 现有 N 道闸」标题'
s2=s[:m.start()]+'### 现有九道闸'+s[m.end():]
assert s2!=s, '空转：当前标题已经是「九道闸」'
open(p,'w',encoding='utf-8').write(s2)
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
    echo "  ✓ 16) 模式非法：闸门正确报出 [判据执行异常]（退出码 ${rc6}）"; PASS=$((PASS+1))
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
    echo "  ✓ 19) 正确报出 [10-tasks/README.md 没有任何入链]（退出码 ${rc19}）"; PASS=$((PASS+1))
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
    echo "  ✓ 20) 去掉豁免后正确报出 [README.md 没有任何入链]（退出码 ${rc20}）——"
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
# `want` 锚的是「**标题被成功解析**」这个形态（「N 道闸」，清单表却有 M 行），
# 而不是某个具体数字——**注入的数是现场推导出来的**（当前 +10），
# 锚死数字就会在闸数变化时再次失配（这正是本条自己栽过的坑）。
run_file_case "30) 中文数字写成复合形「二十一」必须能解析（必须报行数不符而非找不到标题）" \
  "AUDIT-RULES.md" "$HERE/selftest-meta-fix-30-cn-numeral.py" \
  "道闸」，清单表却有"
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

# ── 37-39（Batch 218）：发布范围的真值必须被**读**，不能被**抄** ────────
#
# 闸 9 原来在脚本里抄了一份 srcExclude，注释写着「与 config.mjs 保持一致——
# **改了那边就要改这里**，这是有意的耦合」。**那句话是一次已经发生过的失败承诺**：
# 把 20-reference.md 加进 config.mjs 之后，闸 9 照旧打印「✓ 内容页数 = 35」
# （真值已是 34），**而同一时刻闸 16 立刻改口**。
#
# **这三例验的是「修法生效了」，不是「判据还能抓那个已知缺陷」**（纪律 225）：
# 改法写了但没接上，判据照样能抓已知缺陷、看起来一切正常。
# `.vitepress/config.mjs` **本来就在 SNAP_FILES 里**，所以这三例的还原与空转检测都覆盖它——
# **注入一个不在快照里的文件，会把它永久留在损坏状态**（那比用例失败严重得多）。
run_file_case "37) 发布配置里多排一个发布页（本闸的正向数必须跟着变）" \
  ".vitepress/config.mjs" "$HERE/selftest-meta-fix-37-scope-drops-page.py" \
  "实际 34"
run_file_case "38) config.mjs 里没有 srcExclude（必须 rc=2 未能核对）" \
  ".vitepress/config.mjs" "$HERE/selftest-meta-fix-38-scope-exclude-gone.py" \
  "未能核对"
run_file_case "39) srcExclude 解析出 0 项（必须 rc=2：零输入不许报绿）" \
  ".vitepress/config.mjs" "$HERE/selftest-meta-fix-39-scope-exclude-empty.py" \
  "不得当成"
# **方向六之二（Batch 225 新增）：页内相对指代不许悬空。40/41 成对。**
# 40 钉「能抓」：把被引用的那句「运行时实证」改掉，分层声明就悬空了。
# 41 钉「不误伤」：同一处耦合，只把指代方式换成自指的「本节」，必须放行——
#    **「本节」在这张手册里恒成立，方向刻意不查它**（查了就是稳定误报）。
run_file_case "40) 被引用的原句被改写 → 页内指代悬空（必须报）" \
  "10-tasks/timeline-editing.md" "$HERE/selftest-meta-fix-40-relative-ref-dangling.py" \
  "指代悬空"
run_file_pass_case "41) 不误伤：指代改写成自指的「本节」（必须放行）" \
  "10-tasks/timeline-editing.md" "$HERE/selftest-meta-fix-41-relative-ref-self.py"

# ── 42（Batch 237）：方向十一之二的反验——**它此前被记成「关不掉」，而那个理由是错的** ──
#
# 方向十一之二（Batch 212 新增）**在写下时就明确记了「这条没有自动反验用例」**，
# 理由是「验这个洞需要**两处**改动（新建一份被引用的反验 + 不登记它），
# 而本脚本的注入机制只能改**一个**文件」。
#
# **那个理由错在一个具体的地方：它只想到了一种验法。**
# 方向十一之二要抓的是「**非夹具**反验没有被认领」，而**驱动只是非夹具的一个子集**。
# 现场恰好有 7 份反验「被别的反验在字符串里提到过、因而不是驱动、但仍是真入口」
# ——**它们全都被登记了**，所以**只要删掉其中一行的认领，就是一个单文件注入**。
#
# **为什么这一条值得写**：一条被记成「关不掉」的覆盖缺口，会一直留在那里，
# 而**下一个人看到它只会接受现状**——缺口一旦被当成事实，就再也没人去问
# 「真的关不掉吗」。**问一次的成本是一次注入，答案是能关。**
run_file_case "42) 删掉一份「被引用但不是驱动」的反验的认领行（必须报：方向十一之二）" \
  "AUDIT-RULES.md" "$HERE/selftest-meta-fix-42-unclaimed-nondriver.py" \
  "非夹具反验"

# ── 方向四（Batch 250 重做）：任务页的 H1 是怎么取的 ──────────────────
#
# 旧判据的形状是 `open(path).readline()` 之后判 `startswith("# ")`，
# **读不到就 `continue`**。本组 4 条用例量的就是这一行的三个后果，
# 全部在改前的判据上实测过（rc 是同一个注入在改前/改后两个版本上的实测值）：
#
#   用例 | 注入形态                       | 改前 | 改后 | 钉的是什么
#   -----+--------------------------------+------+------+-------------------------------
#    43  | 整行删掉 H1（页面真的没有 H1） |  0   |  1   | 不再静默
#    44  | H1 在第 2 行 + 索引链接写错   |  0   |  1   | **真的跨过首行去比了**
#    45  | H1 带 ATX 闭合序列            |  1   |  0   | 不拿读者看不见的字当标题
#    46  | H1 之前有含 `# 注释` 的围栏   |  0   |  0   | 新判据自己新引入的风险
#
# **43 与 44 不是同一条，缺一不可**：
# 43 注入之后页面**真的没有 H1**，新判据报「全文没有任何 H1」——
# 而**只读首行的旧判据在同一个注入上走的也是「读不到 H1」那条分支**。
# 只钉 43，「全篇扫」这件事其实没被验过。
# 44 注入之后页面**有 H1，只是不在首行**，旧判据会整页跳过，
# 索引里那个写错的链接**永远比不到**——**它才是「不再只读首行」的直接证据**。
#
# **45 的诊断最坏的地方**：改前报的是「页面标题『素材库（资产页） ##』」，
# 而**那串字在页面上不存在**（渲染器丢掉 ATX 闭合序列）——
# 照着它去改的人会把好端端的索引链接改成带 `##` 的形态。
#
# **46 钉的不是旧缺陷，是新判据自己带来的风险**：前 45 条没有一条能伤到它
# （旧判据只读首行、看不见页面中段），**而全篇扫一旦不剥围栏，
# 「代码块里的井号」就成了页面标题**。本树围栏内 0 处形似标题，
# **所以真树回归跑不出这个洞——「现场没有」不能当护栏**。
run_file_case "43) 任务页整行没有 H1（必须报：不得静默跳过整页）" \
  "10-tasks/asset-library.md" "$HERE/selftest-meta-fix-43-page-no-h1.py" \
  "全文没有任何 H1"

# 44 改**两个**文件（页面 + 索引），走 `run_fail_case` 直接执行注入脚本。
# 那条路径的「注入空转」判定看 SNAP_FILES 的 md5，
# 而 `10-tasks/asset-library.md` 是本批才加进 SNAP_FILES 的（见上面的注释）。
run_fail_case "44) H1 不在首行时索引链接写错（必须报：那一页真的被比了）" "与页面标题" \
  "python3 $HERE/selftest-meta-fix-44-h1-not-first.py"

run_file_pass_case "45) H1 带 ATX 闭合序列、索引写渲染后的名字（必须不报）" \
  "10-tasks/asset-library.md" "$HERE/selftest-meta-fix-45-closing-atx.py"

run_file_pass_case "46) H1 之前有含井号注释的代码围栏（必须不报）" \
  "10-tasks/asset-library.md" "$HERE/selftest-meta-fix-46-fenced-hash.py"

# 47 是 Batch 251 加的，钉的是**上一个批次刚写好的那条守卫**。
run_file_pass_case "47) H1 写成缩进形态（真渲染器给标题，必须不报）" \
  "10-tasks/asset-library.md" "$HERE/selftest-meta-fix-47-indented-h1.py"

# 48/49 是 Batch 319 加的方向十二那对，**成对**：
#   48) 能抓：把闸清单表的第 9、10 两行**对调**（= 本批实测到的那 10 行错位的真实形态）。
#       **必须是对调而不是改数字**——改数字会被方向十一之③抓到（编号集合缺一多一），
#       而对调后编号集合一个不少，**这正是它能活到今天的原因**。
#       对照实验 D 臂实测：同一份对调，44 道闸新增报红 **0 道**。
#   49) 不误伤：**只改**闸清单表某一行末尾的说明文字 → 必须放行。
#       它钉的是方向十二自己的风险：第三格是自由散文，每道闸上线都要补来历，
#       **判据若去比第三格，任何人补一句来历都会被报红**（误伤比漏报更坏，纪律 248）。
#       而**前 47 条用例一条都伤不到它**（它们改的是 README / 索引 / 侧栏 / H1 / 例数，
#       方向十二的输入只有两列：行位置 ↔ 脚本）。
run_file_case "48) 闸清单表第 9、10 两行对调（方向十二必须报：两份抄本说的不是同一道闸）" \
  "AUDIT-RULES.md" "$HERE/selftest-meta-fix-48-inventory-row-swap.py" \
  "两份抄本说的不是同一道闸"

run_file_pass_case "49) 只改闸清单表一行的说明文字（方向十二只读行位置↔脚本，必须放行）" \
  "AUDIT-RULES.md" "$HERE/selftest-meta-fix-49-inventory-text-only.py"

# 50/51 是 Batch 320 加的方向十三那对，**成对**：
#   50) 能抓：把 `verify-tables.py` docstring 自称的「第八道闸」改成「第七道闸」
#       → 方向十三必须报。**这就是 Batch 319 对照实验的 C 臂**，
#          而那一臂实测「44 道闸新增报红 0 道」——**这一族当时无人守**。
#       **注入必须改「那一行」而不是全局替换**：`verify-tables.py` 的 docstring 里
#       还留着「本文原先自称『第七道闸』」这句 Batch 246 的订正说明，
#       全局替换会把订正一起改掉，**而输出看起来一模一样**。
#   51) 不误伤：**同一行、只改冒号之后的说明，闸号一个字不动**。
#       它比「改 docstring 别的行」更强一档——**改的就是方向十三读的那一行**。
#       **方向十三必须只认那个 N，不能认整行也不能认首行长度**。
#       而**前 49 例一条都碰不到 docstring**（它们改 README / 索引 / 侧栏 / H1 /
#       例数 / 表格行序），**所以方向十三自己引入的误伤风险此前无人验过**。
run_file_case "50) 闸脚本 docstring 自称的闸号被改错（方向十三必须报）" \
  "scripts/verify-tables.py" "$HERE/selftest-meta-fix-50-gate-selfname-wrong.py" \
  "它自己的 docstring 自称"

run_file_pass_case "51) 只改 docstring 首行的说明、闸号不动（方向十三只认 N，必须放行）" \
  "scripts/verify-tables.py" "$HERE/selftest-meta-fix-51-gate-selfname-text.py"

run_file_case "52) 版本标注用了一个上游不存在的 tag（方向十四必须报）" \
  "10-tasks/director-basics.md" "$HERE/selftest-meta-fix-52-bogus-version-annot.py" \
  "上游"

run_file_pass_case "53) 只改版本标注那一行的说明、版本号一个字不动（方向十四只认版本号，必须放行）" \
  "10-tasks/director-basics.md" "$HERE/selftest-meta-fix-53-version-annot-text-only.py"

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
