#!/usr/bin/env bash
# 第七道闸（verify-tables.py）的反向验证。
#
# 一道只会「通过」的闸门等于没有闸门。这里用三个用例证明它**真能抓到**表格损坏：
#   1) 在表格单元格里注入代码 `a || b`（Batch 122/124/135/136 的真实损坏形态）
#   2) 在表格单元格里注入一个含裸竖线的 URL（20-reference.md 的真实损坏形态）
#   3) 在**围栏代码块内**注入同样的 `||` —— 必须**不报**，
#      因为代码块里的竖线不是表格分隔符。这一条是防误报的对称验证。
#
# 全程只在临时目录里操作手册副本，不碰真实文件；结束即清。
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
      echo "  ✗ $desc：闸门**未**报出损坏（期望退出码 1）"; FAIL=$((FAIL+1)); return
    fi
    if echo "$out" | grep -qF "$want"; then
      echo "  ✓ $desc：闸门正确报出 [$want]（退出码 $rc）"; PASS=$((PASS+1))
    else
      echo "  ✗ $desc：报错了但不是 [$want]；实际："; echo "$out" | sed 's/^/      /'; FAIL=$((FAIL+1))
    fi
  else
    if [ "$rc" -eq 0 ]; then
      echo "  ✓ $desc：闸门**未误报**（退出码 0）"; PASS=$((PASS+1))
    else
      echo "  ✗ $desc：闸门误报了（期望退出码 0）；实际："; echo "$out" | sed 's/^/      /'; FAIL=$((FAIL+1))
    fi
  fi
}

run_case "1) 表格单元格里注入代码 a || b" PROGRESS.md \
  's = s.replace("| 142 | ", "| 142 | `x || y` ", 1)' PROGRESS.md yes

run_case "2) 表格单元格里注入含裸竖线的 URL" 20-reference.md \
  's = s.replace("| `/assets` |", "| `/api/x?a|b` |", 1)' 20-reference.md yes

run_case "3) 围栏代码块内注入同样的 ||（不得误报）" 30-concepts.md \
  's = s.replace("## 三层历史", "## 三层历史\n\n```ts\nconst x = a || b;\n```\n", 1)' "" no

echo "=== 基线：真实手册应当通过 ==="
if python3 "$GATE" "$ROOT" >/dev/null 2>&1; then echo "  ✓ 真实手册通过"; else echo "  ✗ 真实手册未通过"; FAIL=$((FAIL+1)); fi

echo "=== 结果：通过 $PASS / 失败 $FAIL ==="
echo "=== 清理后状态 ==="
echo "  临时目录已删除: $WORK"
[ "$FAIL" -eq 0 ] || exit 1
