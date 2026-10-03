#!/usr/bin/env bash
# 第八道闸（verify-tables.py）的反向验证。**Batch 246 订正：原写「第七道闸」，
# 而 `AUDIT-RULES.md` 的对应关系表登记的是「8 表格结构」。**
#
# 一道只会「通过」的闸门等于没有闸门。这里用五个用例证明它**真能抓到**表格损坏
# （4/5 是 Batch 174 加的，盯的是「整张表不再渲染」这一类——它不报错、只是表格消失）：
#   1) 在表格单元格里注入代码 `a || b`（Batch 122/124/135/136 的真实损坏形态）
#   2) 在表格单元格里注入一个含裸竖线的 URL（20-reference.md 的真实损坏形态）
#   3) 在**围栏代码块内**注入同样的 `||` —— 必须**不报**，
#
# Batch 213 补 7/8：**第二行不是 GFM 分隔行**（删掉 / 少一列 / 写成 `| |`
# / 缺首尾竖线 —— 实测五种全部漏过去，而它们是同一个根因）。
#      因为代码块里的竖线不是表格分隔符。这一条是防误报的对称验证。
#
# Batch 206 的用例 6 换了含义：旧判据把它归给「行尾缺竖线」，实测**那个理由是假的**
# （行尾竖线在表头/分隔行/数据行上都可以省），真正多出来的是**一格**。
# 用例 6 保留，因为注入形态没变——但现在它证明的是**新判据**（比格数）接住了同一个缺陷。
#
# Batch 246 补 9–12：**判据从「数竖线」换成「数格」。**
#   这一步的依据是逐条量出来的（vitepress 1.6.4 真渲染器，见 verify-tables.py 文件头）：
#     · 表格行**首尾的竖线都是可选的**——行尾省掉，表照样渲染；
#     · 真正决定「是不是表格」的是**表头与分隔行的格数是否相等**。
#   **而这一处最要紧的发现不是「判据漏了什么」，是「旧的两条判据在互相抵消」**：
#   旧闸同时存在「比未转义竖线数」与「行尾必须有竖线」两条，而
#   **当每行都带行尾竖线时，竖线数 ≡ 格数，两条判据恰好互补**：
#   凡是一条会漏的形态，必定行尾缺竖线，于是被另一条抓住。
#   **实测反事实**：只删掉「行尾必须有竖线」、其余原样不动，闸 7 在一个
#   **分隔行比表头多一格**的真缺陷上 **rc=0 彻底静默**。
#   ——旧闸不是「判据偏松」，是**两条都站不住的判据凑成了一对能用的**。
#   用例 9 正是这个反事实用例：旧闸报是报了，但报的是「行尾没有竖线」，
#   **照着改会把一张好表改坏**。
#
# 全程只在临时目录里操作手册副本，不碰真实文件；结束即清。
# **Batch 205：`$var` 一律写成 `${var}`。** macOS 自带的 bash 3.2 在 UTF-8 locale 下
# 会把 `$var` 后面紧跟的多字节字符（中文全角标点）算进变量名，
# 于是报「`desc?: unbound variable`」——**而 `desc` 明明刚 `local` 过**。
# 实测：同一份脚本、同一台机器，`LC_CTYPE=C.UTF-8` 时 0/5 通过，不设时 5/5 通过。
# **`${var}` 是唯一可靠写法**，而「可靠」这件事在默认环境下看不出来。
# **Batch 246：macOS 的 `${TMPDIR}` 末尾自带斜杠，直接拼会得到 `T//beef-…`（双斜杠）。**
# 虽不影响功能，但它是**唯一一个会在输出里露出来的格式瑕疵**，一并修掉。
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"
GATE="$HERE/verify-tables.py"
WORK="$(mktemp -d "${TMPDIR:-/tmp}beef-table-selftest.XXXXXX")"
[ -d "$WORK" ] || WORK="$(mktemp -d "/tmp/beef-table-selftest.XXXXXX")"
PASS=0; FAIL=0

cleanup() { rm -rf "$WORK" 2>/dev/null || true; }
trap cleanup EXIT

# 只复制被改的三个文件 + 目录骨架，够闸门跑即可
mkdir -p "$WORK/10-tasks" "$WORK/screenshots" "$WORK/scripts"
cp "$ROOT/20-reference.md" "$WORK/" 2>/dev/null
cp "$ROOT/PROGRESS.md" "$WORK/" 2>/dev/null
cp "$ROOT/30-concepts.md" "$WORK/" 2>/dev/null
cp "$ROOT/90-troubleshooting.md" "$WORK/" 2>/dev/null

run_case() {  # 说明 目标文件 注入命令 期望(文件名) 是否期望报错
  local desc="$1" file="$2" inject="$3" want="$4" expect_fail="$5" out rc
  # 每次从**全部**干净副本重来——只还原当次目标文件是不够的：
  # 上一个用例注入的破坏会留在工作目录里，让本用例的闸门输出对不上（Batch 142 实踩）。
  for f in 20-reference.md PROGRESS.md 30-concepts.md 90-troubleshooting.md; do
    cp "$ROOT/$f" "$WORK/$f"
  done
  python3 - "$WORK/$file" <<PYEOF
import io, sys
p = sys.argv[1]
s = io.open(p, encoding="utf-8").read()
$inject
io.open(p, "w", encoding="utf-8").write(s)
PYEOF
  out=$(python3 "$GATE" "$WORK" 2>&1); rc=$?
  if [ "$expect_fail" = "yes" ]; then
    if [ "$rc" -eq 0 ]; then
      echo "  ✗ ${desc}：闸门**未**报出损坏（期望退出码 1）"; FAIL=$((FAIL+1)); return
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

run_case "1) 表格单元格里注入代码 a || b" PROGRESS.md \
  's = s.replace("| 142 | ", "| 142 | `x || y` ", 1)' PROGRESS.md yes

run_case "2) 表格单元格里注入含裸竖线的 URL" 20-reference.md \
  's = s.replace("| `/assets` |", "| `/api/x?a|b` |", 1)' 20-reference.md yes

run_case "3) 围栏代码块内注入同样的 ||（不得误报）" 30-concepts.md \
  's = s.replace("## 三层历史", "## 三层历史\n\n```ts\nconst x = a || b;\n```\n", 1)' "" no

# 4/5 是 Batch 174 加的：畸形表**不会被渲染成表格**，而原判据只比列数、看不见它。
# 用例 4 复现本批自己写坏的那一处（表头与分隔行之间夹进引用块），
# 用例 5 复现 20-reference.md 里那处**历史遗留**（一行被空行隔在表外）。
# **这一类的危险在于它不报错**：表格直接不渲染，读者看到的是一行悬空的文字。
run_case "4) 表头与分隔行之间夹进引用块（整张表不再渲染，必须报）" 20-reference.md \
  's = s.replace("| 策略项 | 默认部署 | 本地部署（localMode） | 对读者意味着什么 |\n|---|---|---|---|",
                "| 策略项 | 默认部署 | 本地部署（localMode） | 对读者意味着什么 |\n\n> 夹在中间的引用块\n\n|---|---|---|---|", 1)' \
  20-reference.md yes

run_case "5) 表格里某一行被空行隔出去（那一行不再属于表格，必须报）" 20-reference.md \
  's = s.replace("\n\n**已退场、访问会被重定向回首页的路由**", "\n\n| `/injected` | 悬空的一行 |\n\n**已退场、访问会被重定向回首页的路由**", 1)' \
  20-reference.md yes

# 6 是 Batch 206 加的，**Batch 246 改了它的诊断归属**。
# 注入形态一个字没改（`| 参数 | 位置 | 作用 | 备注 |` → `... | 备注 | 尾巴`，
# **行尾竖线没了、同时多出一格**），但它到底是什么缺陷，本批量清楚了：
#   · 旧判据说它是「行尾没有竖线」——**那个理由是假的**（行尾竖线本来就可选）；
#   · 真渲染器实测：**整块不是表格**（表头 5 格 vs 分隔行 4 格）；
#   · 新判据的诊断：「解析出 4 格，表头是 5 格」——**说的是同一件事，且是真的**。
# **注入形态保留不换**，是因为它恰好是「少一个结构竖线 + 多一个字面竖线」互相抵消
# 那个真实历史形态：只注入「行尾缺竖线」的话，竖线数会从 5 掉到 4，
# 旧判据会报另一条，测不出「计数相等却仍然损坏」这件事。
run_case "6) 表头比分隔行多一格（整块不是表格，必须报）" 20-reference.md \
  'L = s.split("\n")
for i, l in enumerate(L):
    if l.startswith("|") and l.rstrip().endswith("|") and l.count("|") >= 4 and "---" not in l:
        cells = l[1:-1].split("|")
        last = cells[-1].strip()
        head, tail = (last.split(" ", 1) + [""])[:2] if " " in last else (last, "尾巴")
        L[i] = "|" + "|".join(cells[:-1]) + "| " + head + " | " + tail
        break
s = "\n".join(L)' 20-reference.md yes

# 7/8 是 Batch 213 加的：**块有两行以上时，第二行必须是 GFM 意义上的分隔行**。
# 7 是「能抓」，8 是「不误伤」——而 8 更要紧：
# **判据若把「本来正常的表」也报成缺分隔行，它会逼着人到处加空行**，
# 而那正是判据过宽的真正代价（Batch 139/141/142 的同一个教训）。
run_case "7) 删掉整条分隔行（整张表不再渲染，必须报）" 20-reference.md \
  'L = s.split("\n")
for i, l in enumerate(L):
    if l.startswith("|") and i + 1 < len(L) and set(L[i+1].strip()) <= set("|-: ") and "-" in L[i+1]:
        del L[i+1]
        break
else:
    raise SystemExit("锚点未命中：没找到「表头 + 分隔行」相邻的一处")
s = "\n".join(L)' 20-reference.md yes

run_case "8) 不误伤：分隔行完全合规的表（必须不报）" 20-reference.md \
  'L = s.split("\n")
for i, l in enumerate(L):
    if l.startswith("|") and i + 1 < len(L) and set(L[i+1].strip()) <= set("|-: ") and "-" in L[i+1]:
        L[i+1] = L[i+1].replace("---", ":---", 1)   # 对齐标记：GFM 认，列数与形状都不变
        break
else:
    raise SystemExit("锚点未命中：没找到「表头 + 分隔行」相邻的一处")
s = "\n".join(L)' 20-reference.md no

# ── Batch 246：判据换成「数格」之后的四个用例 ──────────────────────────────────
# 9/12 是**能抓**，10/11 是**不误伤**，两两成对。
# **10/11 同时是鉴别力用例**：旧闸在这两个形态上 rc=1（误报一张好表），
#   而反事实闸（只删掉行尾方向）在用例 9 上 rc=0（漏报一个真缺陷）。
#   三条形态全部逐条过过 vitepress 1.6.4 真渲染器，不是推的。

# 9) 分隔行**多一格**、而裸竖线数与表头**恰好相等**（表头 5 竖线 / 4 格，
#    分隔行改成 5 竖线 / 5 格且没有行尾竖线）。
#    真渲染器：整块不是表格。这是「数竖线」和「数格」唯一会分道的地方，
#    **也正是反事实闸 rc=0 静默的那个形态**。
run_case "9) 分隔行比表头多一格、但竖线总数相同（整块不是表格，必须报）" 20-reference.md \
  'L = s.split("\n")
for i, l in enumerate(L):
    if l.strip() == "|---|---|---|---|" and L[i-1].startswith("|") and L[i-1].count("|") >= 5:
        L[i] = "|---|---|---|---|---"   # 多一格；竖线数仍是 5，与表头相同
        break
else:
    raise SystemExit("锚点未命中：没找到 4 列且分隔行正好是 |---|---|---|---| 的一处")
s = "\n".join(L)' "解析出 5 格，表头是 4 格" yes

# 10) 分隔行**省掉行尾竖线**、格数不变 —— 实测渲染成完全正常的表。
#     旧闸在这里 rc=1，且给出**两条都是假的**诊断（「它不是分隔行，整块不是表格」
#     与「行尾没有竖线」）——照着改会把一张好表改坏。
run_case "10) 不误伤：分隔行只省了行尾竖线、格数没变（真渲染器：正常表）" 20-reference.md \
  'L = s.split("\n")
for i, l in enumerate(L):
    if l.strip() == "|---|---|---|---|" and L[i-1].startswith("|") and L[i-1].count("|") >= 5:
        L[i] = l.rstrip()[:-1]          # 只去掉行尾竖线：竖线 5→4，格数仍是 4
        break
else:
    raise SystemExit("锚点未命中：没找到 4 列且分隔行正好是 |---|---|---|---| 的一处")
s = "\n".join(L)' 20-reference.md no

# 11) 数据行**省掉行尾竖线** —— 实测同样渲染成正常的表（GFM 补不出问题）。
run_case "11) 不误伤：数据行省掉行尾竖线（真渲染器：正常表）" 20-reference.md \
  'L = s.split("\n")
for i, l in enumerate(L):
    if (i >= 2 and l.startswith("|") and "---" not in l and L[i-1].startswith("|")
            and l.rstrip().endswith("|") and l.count("|") >= 4):
        L[i] = l.rstrip()[:-1]          # 数据行去掉行尾竖线
        break
else:
    raise SystemExit("锚点未命中：没找到一张表里的数据行")
s = "\n".join(L)' 20-reference.md no

# 12) 数据行**多一格** —— 实测渲染仍是表格，但**多出来的那格被静默丢弃**，
#     读者看不到那格内容。危害是真的，机制是「丢格」而不是「多出一列」。
run_case "12) 数据行多出一格（内容被静默丢弃，必须报）" 20-reference.md \
  'L = s.split("\n")
for i, l in enumerate(L):
    if (i >= 2 and l.startswith("|") and "---" not in l and L[i-1].startswith("|")
            and l.rstrip().endswith("|") and l.count("|") >= 4):
        L[i] = l.rstrip() + " 多出来的一格 |"
        break
else:
    raise SystemExit("锚点未命中：没找到一张表里的数据行")
s = "\n".join(L)' "解析出 5 格，表头是 4 格" yes

echo "=== 基线：真实手册应当通过 ==="
if python3 "$GATE" "$ROOT" >/dev/null 2>&1; then echo "  ✓ 真实手册通过"; else echo "  ✗ 真实手册未通过"; FAIL=$((FAIL+1)); fi

echo "=== 结果：通过 $PASS / 失败 $FAIL ==="
echo "=== 清理后状态 ==="
echo "  临时目录已删除: $WORK"
[ "$FAIL" -eq 0 ] || exit 1
