import re
import sys
# 方向九反验用例 31：把 A 类小节标题里手写的类数**改小 1**（表仍是 10 行）
# → 期望方向九报出「小节标题的计数与表内容脱节」。
#
# **这条验的是 Batch 168 实锤的真缺陷，不是假想**：
# `**A 类 · 有闸守着（9 类）**` 写着 9、表里已经 10 行 ——
# 因为 Batch 162 新增闸 10 时加了行、**没改标题**，之后**连过 6 个批次**。
# 方向九原先只管「表 vs 闸门清单」（两侧同步漂移时看不出来），**管不到标题里那个数**。
#
# **为什么这个数特别危险**：它长得像**结论**（「9 类风险有人管」），
# 读者会据此判断自己关心的那一类**有没有被覆盖**。它过期六个批次没人发现，
# 因为**没有任何判据在读它**——而判据的覆盖度表自己写着「本手册的判据是完备的」。
#
# **锚点仍按结构**（找 `**A 类 …` 标题行 → 改其中「（N 类）」），
# **不锚具体数字**：这样这条用例在类数将来变成 12 时依然成立。
s = sys.stdin.read()
lines = s.split("\n")

heads = [i for i, ln in enumerate(lines) if re.match(r"^\*\*A\s*类", ln.strip())]
assert len(heads) == 1, "锚点未命中：A 类小节标题应恰好 1 行，实得 %d 行" % len(heads)
i = heads[0]

m = re.search(r"（([0-9零一二三四五六七八九十]+)\s*类\s*）", lines[i])
assert m, "前提不成立：A 类标题里没有「（N 类）」计数（用例 32 才是验这个的）"

# 现值减 1：用「声明数 - 1」而不是写死 9，避免将来类数变化时用例自身失配
cur = lines[i]
nxt = m.group(0).replace(m.group(1), str(int(m.group(1)) - 1))
lines[i] = cur.replace(m.group(0), nxt, 1)
out = "\n".join(lines)
assert out != s, "空转：内容未变"
assert "类与表内容脱节" not in out, "空转：注入特征串 leaked"
sys.stdout.write(out)
