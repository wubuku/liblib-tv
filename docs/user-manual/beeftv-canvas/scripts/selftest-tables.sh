#!/usr/bin/env bash
# 第七道闸（verify-tables.py）的反向验证。
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
# 全程只在临时目录里操作手册副本，不碰真实文件；结束即清。
# **Batch 205：`$var` 一律写成 `${var}`。** macOS 自带的 bash 3.2 在 UTF-8 locale 下
# 会把 `$var` 后面紧跟的多字节字符（中文全角标点）算进变量名，
# 于是报「`desc?: unbound variable`」——**而 `desc` 明明刚 `local` 过**。
# 实测：同一份脚本、同一台机器，`LC_CTYPE=C.UTF-8` 时 0/5 通过，不设时 5/5 通过。
# **`${var}` 是唯一可靠写法**，而「可靠」这件事在默认环境下看不出来。
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"
GATE="$HERE/verify-tables.py"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/beef-table-selftest.XXXXXX")"
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

# 6 是 Batch 206 加的：**行尾缺竖线**（而列数刚好相等）。
# **注入必须复现「少一个结构竖线 + 多一个字面竖线」这个互相抵消的形态**——
# 只注入「行尾缺竖线」的话，未转义竖线会从 4 掉到 3，**旧判据照样报绿**，
# 那样这条用例就测不出「计数相等却仍然损坏」这件事。
run_case "6) 行尾没有竖线、但列数与表头相等（计数抵消，必须报）" 20-reference.md \
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

echo "=== 基线：真实手册应当通过 ==="
if python3 "$GATE" "$ROOT" >/dev/null 2>&1; then echo "  ✓ 真实手册通过"; else echo "  ✗ 真实手册未通过"; FAIL=$((FAIL+1)); fi

echo "=== 结果：通过 $PASS / 失败 $FAIL ==="
echo "=== 清理后状态 ==="
echo "  临时目录已删除: $WORK"
[ "$FAIL" -eq 0 ] || exit 1
