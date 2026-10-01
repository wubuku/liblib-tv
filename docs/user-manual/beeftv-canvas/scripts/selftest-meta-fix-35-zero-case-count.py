import re
import sys
# 方向十一反验用例 35：把某行的**例数写成 0**
# → 期望报出「必须是正整数」。
#
# **为什么 0 和空格都要报**（Batch 161 的原话：空格看起来像有人管，其实没有）：
# 一行「认领了某个反验、例数 0」的记录，读起来像「这个闸的反验跑过了但没发现东西」，
# 实际上是**一条反验都没有**。**它比整行缺失更危险，因为整行缺失一眼看得见。**
s = sys.stdin.read()
lines = s.split("\n")

idx = [i for i, ln in enumerate(lines)
       if re.match(r"^\|\s*8\s", ln) and "selftest-tables.sh" in ln]
assert len(idx) == 1, "锚点未命中：应恰好找到 1 行以「8 」开头且认领 selftest-tables.sh，实得 %d" % len(idx)
i = idx[0]
# **列序：cells[0]=闸、cells[1]=反验、cells[2]=例数**。
# 第一版写成 cells[1]（反验列），结果把反验文件名换成了 0 ——
# 闸门报的是「认领了不存在的」，而用例锚的是「必须是正整数」，
# **用例失败会把我引向完全错误的方向**（与 Batch 156「先怀疑注入」的同一课）。
cells = lines[i].strip().strip("|").split("|")
assert len(cells) >= 3, "锚点未命中：列数不足"
assert "selftest-tables.sh" in cells[1], "锚点未命中：cells[1] 不是反验列"
old = cells[2].strip()
cells[2] = " 0 "
lines[i] = "|" + "|".join(cells) + "|"

out = "\n".join(lines)
# 断言**例数那格真的变成了 0**（而不是别处还留着原值）
row = next(ln for ln in out.split("\n") if re.match(r"^\|\s*8\s", ln) and "selftest-tables.sh" in ln)
new_cells = [c.strip() for c in row.strip().strip("|").split("|")]
assert new_cells[2] == "0", "空转：例数那格没变成 0（现在是 %r）" % new_cells[2]
assert old not in new_cells, "空转：原例数还留在这一行"
sys.stdout.write(out)
