#!/usr/bin/env bash
# 第二十六道闸（verify-link-labels.py）的反向验证。
#
# 一道只会「通过」的闸门等于没有闸门。这里用 7 个用例证明它**真能抓到**链接文字退化
# （3 个），也证明它**不会误伤**（4 个）——后者更要紧：
# 判据一旦把「本来正确的写法」报成问题，它会逼着人把好写法改成它能通过的写法，
# 那正是判据过宽的真正代价（Batch 139/141/142/226 的同一个教训）。
#
# 为什么这个闸的反验要「把闸脚本自己复制进临时树」：
# 本闸的根目录由 `__file__` 推导，**不接受路径参数、也不看 cwd**——
# 这是 Batch 166 实测出来的正确做法（从别的目录运行曾扫到「0 文件 → 判通过」）。
# 复制脚本进临时树，跑的就是**生产代码的那条路径**，不给闸开后门。
#
# 全程只在临时目录里操作手册副本，不碰真实文件；结束即清。
# **Batch 205：`$var` 一律写成 `${var}`。** macOS 自带的 bash 3.2 在 UTF-8 locale 下
# 会把 `$var` 后面紧跟的多字节字符（中文全角标点）算进变量名。
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/beef-linklabel-selftest.XXXXXX")"
PASS=0; FAIL=0; VOID=0

cleanup() { rm -rf "$WORK" 2>/dev/null || true; }
trap cleanup EXIT

# 复制闸脚本 + 全部正文页（10-tasks/ 下的任务页 + 根目录 4 个内容页）
mkdir -p "$WORK/10-tasks" "$WORK/scripts"
cp "$HERE/verify-link-labels.py" "$WORK/scripts/"
# **Batch 249：闸 26 开始 import `headingkey`。**
# 不搬它临时目录 import 失败、每一例都红，而 `build-site.sh` 仍然全绿。
cp "$HERE/headingkey.py" "$WORK/scripts/"
for f in 00-quickstart.md 20-reference.md 30-concepts.md 90-troubleshooting.md; do
  cp "$ROOT/$f" "$WORK/" 2>/dev/null
done
cp "$ROOT/10-tasks/"*.md "$WORK/10-tasks/" 2>/dev/null

reset_tree() {   # 每个用例都从**全部干净副本**重来
  cp "$ROOT/10-tasks/"*.md "$WORK/10-tasks/" 2>/dev/null
  for f in 00-quickstart.md 20-reference.md 30-concepts.md 90-troubleshooting.md; do
    cp "$ROOT/$f" "$WORK/" 2>/dev/null
  done
}

# ── 基线前提（Batch 276 新增）────────────────────────────────────
#
# **它治什么**：本脚本每例都 `reset_tree`——**而 `reset_tree` 是从真实手册树
# 逐个文件复制过去的**，所以**工作区里任何未提交的改动都会成为每一例的起点**。
# **实测（Batch 275）**：同事一处注入实验让 `asset-library.md` 的首行不再是 H1，
# 于是基线用例红、13 例里 7 例红，**而那 7 条报的是「闸门误报了」——
# 一个完全指错方向的诊断**（闸门没误报，它报的是同事那处改动）。
#
# **为什么不能靠「把工作区弄干净」来修**：同事正在改东西是正常状态，
# **丢弃或 stash 别人的改动是被明令禁止的**。
# **而「让它变绿」的最短路径恰好就是那件事——判据不能教人这么做。**
#
# **关键区分（本方向的价值全在这行区分上）**：
#   · 「期望闸门**保持沉默**」的用例**依赖基线干净**（基线脏 → 闸门本来就要说话）；
#   · 「期望闸门**报出某句**」的用例**不依赖**（断言查的是 `$want`，噪声再多也不影响）；
#   · 空树用例**完全不依赖**（它用 `$WORK/empty`）。
# **所以不是整份放弃**：能抓那一半照跑，依赖基线的那些记「作废」。
#
# **退出码取 2 而不是 1**：这一轮它**确实什么都没核**，
# 而 rc=1 的含义是「核过且核出不一致」——**拿环境的缺口冒充「反验坏了」
# 是反验文件头列为最坏的一种错**（纪律 156 / 204）。
BASE_RC=0
BASE_OUT="$WORK/baseline.out"
python3 "$HERE/verify-link-labels.py" > "$BASE_OUT" 2>&1 || BASE_RC=$?
if [ "$BASE_RC" -ne 0 ]; then
  echo "=== 基线前提不成立：真实手册自己就没过闸（退出码 ${BASE_RC}）==="
  echo "  下面这些用例本轮**无法评估**，一律记「作废」而不是「失败」："
  echo "    · 期望闸门保持沉默的那一半（不误伤）——基线脏时闸门本来就要说话；"
  echo "    · 行号准确性——它取闸门报出的第一行，基线多报一行就会取错。"
  echo "  能抓的那一半（期望报出某一句）**照跑**：断言查的是那一句，噪声不影响它。"
  echo "  ============================================================"
  echo "  **不要靠丢弃这些改动来让本脚本变绿。**"
  echo "  工作区脏不是缺陷——同事正在改东西是正常状态（闸 38 报的就是这个状态，rc=0）。"
  echo "  本轮退出码是 **2（未能核对）**，不是 1。"
  echo "  ============================================================"
  grep -E "✗" "$BASE_OUT" | head -5 | sed 's/^/    /'
fi

# ── 注入护栏（Batch 277 新增，从 `run_case` 里提出来给三条路径共用）────
#
# **它治什么（实测的假通过，干净副本树）**：把用例 11 的注入整块换成
# 「两个都不存在的锚点、无 assert」——**语法合法、不抛异常、文件一个字节没动**——
# 于是它报「✓ 闸门未误报」，**整份报告是「通过 13 / 失败 0 / 作废 0」、rc=0**。
# **读者看的是那个总数，而「13 例全过」与「其中一条什么都没验」在报告上完全一样。**
#
# **根因不是「少写了一个 assert」，是「护栏只加在了一条路径上」**：
# `run_case` 有 cksum 前后比对（Batch 249 加的），
# **而 `run_two_file_case` 与内联的那两条没有**——
# 挡住它们的是「那几条注入恰好都手写了 `assert`」**这个巧合**，
# **而 `assert` 恰恰是最容易被下一次编辑删掉的东西**
# （它不在函数签名里、不在任何清单上，删掉之后脚本照常跑绿）。
#
# **为什么护栏不写成「assert 命中」**：`assert` 要人记得写，
# **而 cksum 比对是「跑完自然会发生的事」**——
# **护栏应该落在被测性质上（文件真的变了），而不是落在某个具体的失败形态上**
# （「抛异常」只是空转的其中一种，而且不是唯一一种）。
#: **两个数组按顺序存，而不是拼动态变量名**——
#: **`INJ_BEFORE_$k=$(cksum < …)` 在 bash 里行不通，而且失败方式极具误导性**：
#: **`INJ_BEFORE_$k` 在「解析期」不是合法赋值名**（名字里有个 `$`），
#: 于是 bash 把它当**命令词**，展开后去找一个叫
#: `INJ_BEFORE_10_tasks_asset_library_md=…` 的命令——
#: **实测报 `command not found`，而变量从头到尾没被赋值**，
#: 紧接着 `set -u` 让下一处读它时报 `unbound variable`、**整份脚本一条用例都没跑**。
#: **而 `before=$(cksum < …)` 是没问题的**（那是合法名字，走赋值路径，
#: 且赋值的右边不做词分割，所以 cksum 的两段不会被拆开）——
#: **同一个文件里两个看起来一样的写法，一个能用一个不能，而差别只在名字是不是字面量。**
snapshot_injection() {         # $@ = 相对 $WORK 的文件；把 cksum 按顺序存进 INJ_SNAP
  local f
  INJ_SNAP=()
  for f in "$@"; do
    [ -f "$WORK/$f" ] || { echo "文件不在场：$f"; return 1; }
    INJ_SNAP+=("$(cksum < "$WORK/$f")")
  done
  return 0
}
set_after_injection() {        # $@ = 与 snapshot_injection 同一批文件
  local f
  INJ_AFTERS=()
  for f in "$@"; do INJ_AFTERS+=("$(cksum < "$WORK/$f")"); done
}
assert_injection_changed() {   # $@ = 与 snapshot_injection 同一批文件
  local f i n
  n=${#INJ_SNAP[@]}
  if [ "$n" -eq 0 ]; then echo "护栏自己没拿到注入前的快照（前提失配）"; return 1; fi
  i=0
  for f in "$@"; do
    if [ "${INJ_SNAP[$i]}" = "${INJ_AFTERS[$i]}" ]; then
      echo "**$f 的内容一个字节都没变**"
      return 1
    fi
    i=$((i + 1))
  done
  [ "$i" -eq "$n" ] || { echo "护栏的文件数对不上（$i vs ${n}）——**别让「比的不是同一批」变成永远通过**"; return 1; }
  return 0
}

run_case() {  # 说明 目标文件 注入命令 期望出现在输出里的字串 期望退出码(1=须报,0=须放行)
  local desc="$1" file="$2" inject="$3" want="$4" expect_fail="$5" out rc inj_out before after
  reset_tree
  # **依赖基线的那一半：基线不成立时先判作废，别把环境的缺口记成「误报」。**
  if [ "$expect_fail" = "no" ] && [ "$BASE_RC" -ne 0 ]; then
    echo "  — ${desc}：**作废（基线前提不成立）**——本轮无法评估它是否误报"
    VOID=$((VOID+1)); return
  fi
  snapshot_injection "$file"
  inj_out=$(python3 - "$WORK/$file" <<PYEOF 2>&1
import io, sys
p = sys.argv[1]
s = io.open(p, encoding="utf-8").read()
$inject
io.open(p, "w", encoding="utf-8").write(s)
PYEOF
)
  rc=$?
  set_after_injection "$file"
  # **注入失败必须算用例失败**（Batch 225 实测过同一个坑：`selftest-meta.sh` 的
  # `run_file_pass_case()` 在「注入未命中锚点」分支漏了 `VOID++`，
  # 后果是用例静默消失、闸门在干净树上跑绿、报告上却写着 ✓）。
  # 本脚本第一版没有这道护栏，用例 7 的锚点因为「同一段文字出现两次」而 assert 失败，
  # **它照样报 ✓**——「用例没跑起来」和「用例通过」在输出上一模一样。
  if [ "$rc" -ne 0 ] || echo "$inj_out" | grep -q 'Error\|Traceback\|SystemExit'; then
    echo "  ✗ ${desc}：**注入失败，用例根本没跑起来**（不能算通过）"; echo "$inj_out" | sed 's/^/      /'; FAIL=$((FAIL+1)); return
  fi
  # 崩溃只是注入失败的一种。**更隐蔽的是它不崩也不改**：`str.replace` 锚点不中时
  #   静默返回原串，文件一个字节都没动，于是闸门在干净树上跑绿、用例照样 ✓。
  #   实测：把用例 2 的锚点改成一个不存在的串，护栏没响，用例改判「闸门未报出」——
  #   报出来的是**症状**，不是**原因**。所以必须独立断言「文件确实变了」。
  if ! assert_injection_changed "$file"; then
    echo "  ✗ ${desc}：**注入没有改变文件**（锚点很可能没命中），用例没跑起来（不能算通过）"
    FAIL=$((FAIL+1)); return
  fi
  out=$(python3 "$WORK/scripts/verify-link-labels.py" 2>&1); rc=$?
  if [ "$expect_fail" = "yes" ]; then
    if [ "$rc" -eq 0 ]; then
      echo "  ✗ ${desc}：闸门**未**报出（期望退出码 1）"; FAIL=$((FAIL+1)); return
    fi
    if echo "$out" | grep -qF "$want"; then
      echo "  ✓ ${desc}：闸门正确报出 [$want]（退出码 ${rc}）"; PASS=$((PASS+1))
    else
      echo "  ✗ ${desc}：报错了但不是 [$want]；实际："; echo "$out" | sed 's/^/      /'; FAIL=$((FAIL+1))
    fi
  else
    if [ "$rc" -eq 0 ]; then
      echo "  ✓ ${desc}：闸门**未误报**（退出码 0）"; PASS=$((PASS+1))
    else
      echo "  ✗ ${desc}：闸门误报了（期望退出码 0）；实际："; echo "$out" | sed 's/^/      /'; FAIL=$((FAIL+1))
    fi
  fi
}

# ── 能抓的 3 个 ──────────────────────────────────────────────
# 1 复现本批 147 处里的原始形态：链接文字退回裸文件名。读者在渲染后看到的就是
#   `storage-quota.md` 这一串路径，而同一本书的索引里同一页叫「账号存储、容量与配额」。
run_case "1) 链接文字退回裸文件名（本批 147 处的原始形态）" 10-tasks/asset-library.md \
  's = s.replace("[账号存储、容量与配额](storage-quota.md)", "[storage-quota.md](storage-quota.md)", 1)' \
  "storage-quota.md" yes

# 2 占位词：链接能跳转，但读者点之前不知道点过去是什么。
run_case "2) 链接文字写成占位词「点击这里」" 10-tasks/asset-library.md \
  's = s.replace("[账号存储、容量与配额](storage-quota.md)", "[点击这里](storage-quota.md)", 1)' \
  "点击这里" yes

# 3 指错页：文字是**另一页**的名字，而链接仍然指向原来那一页。
#   这条最阴——链接是通的、文字也是手册里真存在的名字，只是它属于别的页。
#   判据按**目标页**算名字集合，正好能分辨。
#   ⚠️ 第一版把整个链接连目标一起换了，于是文字与新目标恰好匹配，闸门当然不报——
#   **用例自己写错时，闸门越正确越显得像有 bug**。必须只换文字、不动 href。
run_case "3) 链接文字写成另一页的名字（指错页）" 10-tasks/asset-library.md \
  's = s.replace("[账号存储、容量与配额](storage-quota.md)", "[故障排查](storage-quota.md)", 1)' \
  "不是 storage-quota.md 的真名" yes

# ── 不误伤的 4 个 ────────────────────────────────────────────
# 4 围栏代码块里的链接是**示例**，不是导航。判据声明了排除它，就得证明真排除了。
run_case "4) 围栏代码块内的裸文件名链接（不得误报）" 10-tasks/asset-library.md \
  's = s.replace("## ", "## ", 1)
s = "```md\n参见 [storage-quota.md](storage-quota.md)\n```\n\n" + s' "" no

# 5 「H1（提示）」形态：verify-meta 的 index_check 早就认可它。
#   **本闸第一版漏了它，上线首跑把两条本来正确的索引链接报成了问题**——
#   漏判合法形态和误判有问题一样，都会让人不信任这道闸。用例 5 钉住它。
run_case "5) 「标题（提示）」形态（不得误报）" 10-tasks/asset-library.md \
  's = s.replace("[账号存储、容量与配额](storage-quota.md)", "[账号存储、容量与配额（副本不上传）](storage-quota.md)", 1)' "" no

# 6 H1 冒号前的简称：行文里放 23 字的完整 H1 会把句子撑散，简称是必要的。
#   **必须挑一个 H1 里真有「：」的页**（`generate-images`：发起图片生成：任务状态、批量与重试）。
#   第一版挑了 `storage-quota`（H1「账号存储、容量与配额」**没有冒号**），
#   于是什么都没冒号可截，闸门把「账号存储」判成非法是**完全正确**的——
#   而用例看起来像是「判据过严」。**用例挑错样本，测的就不是它想测的东西。**
run_case "6) H1 冒号前的简称（不得误报）" 10-tasks/director-basics.md \
  's = s.replace("[连线引用：拖线、吸附、快速创建与批量连线](connect-references.md)", "[连线引用](connect-references.md)", 1)' "" no

# 7 目标页某个小节的名字（不是页名）。这条要**在目标页新造一个小节**再从别处链过去，
#   它证明判据认的是「这个名字在目标页上确实存在」，
#   而不是「碰巧和现有内容对上了」——这两者的区别在将来加新页时才显出来。
#   ⚠️ 第一版把小节建在了**链接所在页**，闸门照实报了——建错页的节当然不在目标页上。
#   **而这类「用例自己写错」和「闸门有 bug」在输出上长得一模一样**（Batch 225 记过）。
echo "=== 用例 7 需要同时改两个文件（小节建在目标页、链接建在别处）==="
reset_tree
# **Batch 276：这一条是内联的，既不走 `run_case` 也不走 `run_two_file_case`，
# **所以前两处守卫都够不着它**——实测它正是脏树上第 3 条红。
if [ "$BASE_RC" -ne 0 ]; then
  echo "  — 7) 链向目标页新造的小节标题：**作废（基线前提不成立）**——本轮无法评估它是否误报"
  VOID=$((VOID+1))
elif ! INJ7=$(python3 - "$WORK/10-tasks/storage-quota.md" "$WORK/10-tasks/asset-library.md" <<'PYEOF' 2>&1
import io, sys
tgt, src = sys.argv[1], sys.argv[2]
# 目标页：加一个小节
s = io.open(tgt, encoding="utf-8").read()
assert s.count("## 侧栏的容量条") == 1, "锚点不唯一"
s = s.replace("## 侧栏的容量条", "## 副本清理时间线\n\n副本删除后 30 天内可恢复。\n\n## 侧栏的容量条", 1)
io.open(tgt, "w", encoding="utf-8").write(s)
# 别处：链向这个小节
# 锚点文字在本文件出现**两次**（一次行内、一次「相关页面」列表），
# 故只断言「至少存在」再替换第一处——写成 ==1 会让整个用例静默消失。
t = io.open(src, encoding="utf-8").read()
old = "[账号存储、容量与配额](storage-quota.md)"
assert old in t, f"锚点未命中: {old}"
t = t.replace(old, "[副本清理时间线](storage-quota.md)", 1)
io.open(src, "w", encoding="utf-8").write(t)
PYEOF
); then
  echo "  ✗ 7) 链向目标页新造的小节标题：**注入失败，用例根本没跑起来**（不能算通过）"
  echo "$INJ7" | sed 's/^/      /'; FAIL=$((FAIL+1))
else
  OUT=$(python3 "$WORK/scripts/verify-link-labels.py" 2>&1); RC=$?
  if [ "$RC" -eq 0 ]; then
    echo "  ✓ 7) 链向目标页新造的小节标题（未误报，退出码 0）"; PASS=$((PASS+1))
  else
    echo "  ✗ 7) 链向目标页新造的小节标题（期望退出码 0）；实际："; echo "$OUT" | sed 's/^/      /'; FAIL=$((FAIL+1))
  fi
fi

# ── Batch 249：链接文字与目标页名字**必须同一个口径** ──────────────────────
# 11/12 是**不误伤**（改前误报），13 是**能抓**（改前漏报）。
# **11/12 尤其要紧**：它们会让判据逼着人把一条「读者看到的就是页面上那个标题」的
# 正确链接，改成判据才认的写法——**而改完读者看到的东西一模一样，白改。**
run_two_file_case() {  # 说明 目标页 链接所在页 注入命令 期望退出码(1=须报,0=须放行)
  local desc="$1" tgt="$2" src="$3" inject="$4" expect_fail="$5" out rc inj
  reset_tree
  # **Batch 276：同一条守卫。`run_case` 那一份覆盖不到这里——
  # 而「我给公共路径加了守卫」不等于「所有用例都被守住了」，
  # **漏掉的那几条输出与「守卫根本没写」一模一样。**
  if [ "$expect_fail" = "no" ] && [ "$BASE_RC" -ne 0 ]; then
    echo "  — ${desc}：**作废（基线前提不成立）**——本轮无法评估它是否误报"
    VOID=$((VOID+1)); return
  fi
  # **Batch 277：这一条路径此前没有「文件真的变了」的检查**，
  # **挡住它的是那三条注入恰好都手写了 `assert`——巧合，不是机制**（详见助手上方）。
  snapshot_injection "10-tasks/$tgt" "10-tasks/$src"
  inj=$(python3 - "$WORK/10-tasks/$tgt" "$WORK/10-tasks/$src" <<INJEOF 2>&1
import io, sys
tgt, src = sys.argv[1], sys.argv[2]
t = io.open(tgt, encoding="utf-8").read()
u = io.open(src, encoding="utf-8").read()
$inject
io.open(tgt, "w", encoding="utf-8").write(t)
io.open(src, "w", encoding="utf-8").write(u)
INJEOF
)
  rc=$?
  if [ "$rc" -ne 0 ] || echo "$inj" | grep -q 'Error\|Traceback\|SystemExit'; then
    echo "  ✗ ${desc}：**注入失败，用例根本没跑起来**（不能算通过）"
    echo "$inj" | sed 's/^/      /'; FAIL=$((FAIL+1)); return
  fi
  # **两个文件都要比**：只比其中一个的话，**「改了一个没改另一个」会静默通过**——
  # **而这一族用例的意义恰恰是同时改两处**（小节建在目标页、链接建在别处）。
  set_after_injection "10-tasks/$tgt" "10-tasks/$src"
  if ! assert_injection_changed "10-tasks/$tgt" "10-tasks/$src"; then
    echo "  ✗ ${desc}：**注入没有改变文件**（锚点很可能没命中），用例没跑起来（不能算通过）"
    FAIL=$((FAIL+1)); return
  fi
  out=$(python3 "$WORK/scripts/verify-link-labels.py" 2>&1); rc=$?
  if [ "$expect_fail" = "yes" ]; then
    if [ "$rc" -eq 0 ]; then
      echo "  ✗ ${desc}：闸门**未**报出（期望退出码 1）；实际："; echo "$out" | sed 's/^/      /'; FAIL=$((FAIL+1))
    else
      echo "  ✓ ${desc}：闸门正确报出（退出码 ${rc}）"; PASS=$((PASS+1))
    fi
  else
    if [ "$rc" -eq 0 ]; then
      echo "  ✓ ${desc}：闸门**未误报**（退出码 0）"; PASS=$((PASS+1))
    else
      echo "  ✗ ${desc}：闸门误报了（期望退出码 0）；实际："; echo "$out" | sed 's/^/      /'; FAIL=$((FAIL+1))
    fi
  fi
}

# 11 ATX 的可选闭合序列：`## 侧栏的容量条 ##` 渲染出来就是「侧栏的容量条」，
#    而原判据把结尾的 `##` 也算进名字，于是链向它的正确链接被判成非法。
run_two_file_case "11) 目标页标题带 ATX 闭合井号、链接写渲染后的名字（不得误报）" \
  storage-quota.md asset-library.md 'assert t.count("## 侧栏的容量条") == 1, "目标页锚点不唯一"
t = t.replace("## 侧栏的容量条", "## 侧栏的容量条 ##", 1)
old = "[账号存储、容量与配额](storage-quota.md)"
assert old in u, "链接锚点未命中: " + old
u = u.replace(old, "[侧栏的容量条](storage-quota.md)", 1)' no

# 12 「：」前的简称必须从**渲染后**的文字上切。
#    **反引号必须放在冒号【前面】**——第一版写成 `侧栏的容量条：\`localMode\``，
#    那样切出来的简称本来就是干净的，**用例测不到它想测的东西**
#    （实测：改前的闸对第一版也放行，而这条例子的意义正是「改前的闸会误报」）。
#    改成 `\`localMode\`：侧栏的容量条`：渲染出来是「localMode：侧栏的容量条」，
#    简称是「localMode」，而原判据切出的是带反引号的那个。
run_two_file_case "12) 标题含行内代码、链接写渲染后的简称（不得误报）" \
  storage-quota.md asset-library.md 'assert t.count("## 侧栏的容量条") == 1, "目标页锚点不唯一"
t = t.replace("## 侧栏的容量条", "## `localMode`：侧栏的容量条", 1)
old = "[账号存储、容量与配额](storage-quota.md)"
assert old in u, "链接锚点未命中: " + old
u = u.replace(old, "[localMode](storage-quota.md)", 1)' no

# 13 井号后是全角空格时**那一行根本不是标题**，它不该给页面贡献任何名字；
#    而原判据认它，于是链向一个页面上不存在的名字反而被放行。
run_two_file_case "13) 目标页有一个全角空格伪标题、链向它（必须报）" \
  storage-quota.md asset-library.md 'assert t.count("## 侧栏的容量条") == 1, "目标页锚点不唯一"
t = t.replace("## 侧栏的容量条", "#　侧栏的容量条", 1)
old = "[账号存储、容量与配额](storage-quota.md)"
assert old in u, "链接锚点未命中: " + old
u = u.replace(old, "[侧栏的容量条](storage-quota.md)", 1)' yes

echo "=== 基线：真实手册应当通过 ==="
# **Batch 276：基线不成立时记「作废」而不是「失败」**——
# **工作区脏不是反验的缺陷**（闸 38 的立场），而把环境的缺口记成
# 「反验坏了」只会把人引去改一份不属于他的文件。
if [ "$BASE_RC" -eq 0 ]; then
  echo "  ✓ 真实手册通过"; PASS=$((PASS+1))
else
  echo "  — 真实手册未通过：**作废（工作区状态，不是反验缺陷）**"
  echo "    **不要靠丢弃同事的未提交改动来让这一行变绿。**"
  VOID=$((VOID+1))
fi

echo "=== 行号准确性：代码块之后的注入，报出的行号必须对得上原文 ==="
if [ "$BASE_RC" -ne 0 ]; then
  echo "  — 行号准确性：**作废（基线前提不成立）**——闸门多报的行会让它取错第一行"
  VOID=$((VOID+1))
else
reset_tree
python3 - "$WORK/10-tasks/asset-library.md" <<'PYEOF'
import io, sys
p = sys.argv[1]
s = io.open(p, encoding="utf-8").read()
s = "```\nx = 1\n```\n\n" + s          # 在文件最前面插一个 4 行的代码块
lines = s.split("\n")
for i, l in enumerate(lines):
    if "[账号存储、容量与配额](storage-quota.md)" in l:
        lines[i] = l.replace("[账号存储、容量与配额](storage-quota.md)",
                             "[storage-quota.md](storage-quota.md)")
        want = i + 1
        break
else:
    raise SystemExit("锚点未命中")
io.open(p, "w", encoding="utf-8").write("\n".join(lines))
print(f"__WANT__{want}")
PYEOF
OUT=$(python3 "$WORK/scripts/verify-link-labels.py" 2>&1); RC=$?
GOT=$(echo "$OUT" | grep -oE 'asset-library\.md:[0-9]+' | head -1 | grep -oE '[0-9]+$')
if [ "$RC" -eq 1 ] && [ "${GOT:-}" = "$(python3 - "$WORK/10-tasks/asset-library.md" <<'PYEOF'
import io, sys
for i, l in enumerate(io.open(sys.argv[1], encoding="utf-8").read().split("\n"), 1):
    if "[storage-quota.md](storage-quota.md)" in l:
        print(i); break
PYEOF
)" ]; then
  echo "  ✓ 报出的行号 ${GOT} 与原文一致（前面隔着 4 行代码块）"; PASS=$((PASS+1))
else
  echo "  ✗ 行号不符：闸门报的是「${GOT:-无}」，退出码 ${RC}"; echo "$OUT" | sed 's/^/      /'; FAIL=$((FAIL+1))
fi

fi
echo "=== 零输入不许报绿：空手册树必须返回 2（Batch 191/192 纪律 156）==="
EMPTY="$WORK/empty"; mkdir -p "$EMPTY/scripts"
cp "$HERE/verify-link-labels.py" "$EMPTY/scripts/"
cp "$HERE/headingkey.py" "$EMPTY/scripts/"
EO=$(python3 "$EMPTY/scripts/verify-link-labels.py" 2>&1); ERC=$?
if [ "$ERC" -eq 2 ]; then
  echo "  ✓ 空树返回 2「未能核对」，没有冒充「全部合规」"; PASS=$((PASS+1))
else
  echo "  ✗ 空树返回 ${ERC}，应为 2；实际：${EO}"; FAIL=$((FAIL+1))
fi

# **Batch 276：汇总行带上「作废」**。**口径与表里那一行一致**
# （合计 = 通过 + 失败 + 作废，Batch 209 写进 AUDIT-RULES.md 的那一条），
# **而 `TALLY_PATS` 的第一条正好认这个形态**——干净树上跑出
# `通过 13 / 失败 0 / 作废 0`，合计仍是 **13**，**表里那一行不用改**。
echo "=== 结果：通过 $PASS / 失败 $FAIL / 作废 $VOID ==="
echo "=== 清理后状态 ==="
echo "  临时目录已删除: $WORK"
# **退出码三段**：`0` 全部通过 / `1` 核出不一致 / **`2` 本轮未能核对**。
# **基线不成立时给 2 而不是 1**——这一轮它什么都没核，
# 而 rc=1 会被方向十六读成「反验坏了」，**那正是 Batch 275 记下的那个误诊**。
if [ "$BASE_RC" -ne 0 ]; then
  exit 2
fi
[ "$FAIL" -eq 0 ] || exit 1
