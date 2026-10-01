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
before = (cells[0], cells[1], cells[2])

# **只往最后一个单元格里追加文字，其余字节一律不动**。
# 第一版是拆开重排整行再拼回去——那会把 `| 3 端点双向 | …` 的空格也一起吃掉，
# 判据照样放行，但**这条用例就不再是「只改备注」了**。
# 「只改一处」这件事必须字面成立，否则用例证明的东西比它声称的少。
j = lines[i].rstrip().rfind("|")
assert j > 0, "锚点未命中：行尾不是表格收尾竖线"
lines[i] = lines[i][:j] + "（反验注入：只改备注，不动任何不变量）" + lines[i][j:]

out = "\n".join(lines)
row = next(ln for ln in out.split("\n") if re.match(r"^\|\s*3\s", ln) and "selftest-endpoints.py" in ln)
after_cells = [c.strip() for c in row.strip().strip("|").split("|")]
# 三个不变量必须**逐字未变**——否则这条用例就不是「只改备注」
assert (after_cells[0], after_cells[1], after_cells[2]) == before, "空转：动到了不变量"
assert "反验注入" in after_cells[-1], "空转：备注没改成功"
sys.stdout.write(out)
