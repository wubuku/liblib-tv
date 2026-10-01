import re
import sys
# 方向十一反验用例 36（不误伤）：只改**备注列**的措辞，三个不变量一律不动
# → 期望**必须放行**。
#
# **「不误伤」这一半不是凑数**：判据扫的是这张表，而这张表的**备注列天生最爱改**
# （每批都要补一句「这批改了什么」）。如果判据把措辞也当成事实，
# 那么**每次记账都会被报成违规**，而人会开始改判据而不是改事实——
# **判据过宽的真正代价，是它逼着你把话说得越来越含糊。**
s = sys.stdin.read()
lines = s.split("\n")

idx = [i for i, ln in enumerate(lines)
       if re.match(r"^\|\s*3\s", ln) and "selftest-endpoints.py" in ln]
assert len(idx) == 1, "锚点未命中：应恰好找到 1 行以「3 」开头且认领 selftest-endpoints.py，实得 %d" % len(idx)
i = idx[0]
cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
assert len(cells) >= 4, "锚点未命中：列数不足，备注列不存在"
# **必须拿 strip 后的值当基准**：第一版存的是未 strip 的原值，
# 改完再拿 strip 后的值去比 → 两边永远不等 → 断言失败，
# 而**失败原因与真实问题毫无关系**。
before = (cells[0], cells[1], cells[2])
cells[-1] = cells[-1].rstrip() + "（反验注入：只改备注，不动任何不变量）"
lines[i] = "|" + "|".join(cells) + "|"

out = "\n".join(lines)
row = next(ln for ln in out.split("\n") if re.match(r"^\|\s*3\s", ln) and "selftest-endpoints.py" in ln)
after_cells = [c.strip() for c in row.strip().strip("|").split("|")]
# 三个不变量必须**逐字未变**——否则这条用例就不是「只改备注」
assert (after_cells[0], after_cells[1], after_cells[2]) == before, "空转：动到了不变量"
assert "反验注入" in after_cells[-1], "空转：备注没改成功"
sys.stdout.write(out)
