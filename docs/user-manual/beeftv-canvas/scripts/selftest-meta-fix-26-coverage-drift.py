import re
import sys
# 方向九反验用例 26：给覆盖度表**新增一道闸的 A 类行**（A 类比闸门清单多 1 行）
# → 期望方向九报出「覆盖度表与闸门清单脱节」。
#
# **这条是方向九最核心的一条**：它保证**表不会悄悄落后于现实**。
# 实际项目里已经栽过两次同型（Batch 147「加了闸忘了改清单表」、
# Batch 153/154「补了索引忘了查侧栏」）——**都是新增了东西没更新汇总处**。
# 有了这一条，**下次新增闸而忘更新 A 类会被当场抓住**，而不是等下一批考古。
#
# 注入形态刻意是「**A 类多一行**」而不是「少一行」：
# 少一行在现实中不可能发生（闸不会自己消失），
# 而多一行正是「加了闸忘了登记」的真实形态。
#
# ⚠️ **Batch 168 重写锚点**：第一版把**整行 A 类闸 9 的文本**誊抄进来当锚
# （`| 元数据计数 / …（8 个方向） | 闸 9 `verify-meta.py`（9 个方向） |`），
# 结果 **Batch 162 把「8 个方向」改成「9 个」、Batch 167 改成「10 个方向」**，
# 锚点两次失配 —— 而**失配的后果是用例被作废、不算通过也不算失败**，
# 连续两个批次里这条「最核心」的用例**什么都没验**。
#
# **这正是纪律 95/100 的教科书案例**：判据锚的必须是**事实**
# （「A 类这张表有几个数据行」），**不是「某一份文件此刻长什么样」**——
# 后者是誊抄副本，**一定会漂移，而且没有任何机制会告诉你它漂了**。
# 现在改为**按结构定位**：找到 `**A 类 …` 小节标题 → 取其下连续表格行 →
# 在表格末尾追加一行。表的措辞怎么改都不会失配；而真把表删了仍会 assert 失败。
s = sys.stdin.read()
lines = s.split("\n")

heads = [i for i, ln in enumerate(lines) if re.match(r"^\*\*A\s*类", ln.strip())]
assert len(heads) == 1, "锚点未命中：A 类小节标题应恰好 1 行，实得 %d 行" % len(heads)

end = None
started = False
for i in range(heads[0] + 1, len(lines)):
    ln = lines[i]
    if not ln.strip():
        # 标题与表格之间本来就空一行；**但表开始之后就不再跳过空行**，
        # 否则会把下一小节（B 类）也当成同一张表的延续。
        if started:
            break
        continue
    if not ln.startswith("|"):
        break
    started = True
    end = i
assert end is not None, "锚点未命中：A 类标题下面没有表格"
table = lines[heads[0] + 1:end + 1]
# 去掉表头（「风险类别 | 守护者」）与分隔行（|---|---|），剩下的才是数据行
rows = [ln for ln in table
        if not re.match(r"\|\s*:?-", ln)
        and ln.strip().strip("|").split("|")[0].strip() != "风险类别"]
assert rows, "锚点未命中：A 类表里没找到任何数据行"

new_row = "| 反验注入：假装新增的第十一道闸 | `scripts/verify-injected.py`（并不存在） |"
assert new_row not in s, "前提不成立：注入行已存在（上一轮没还原干净）"
out = lines[:end + 1] + [new_row] + lines[end + 1:]
assert "\n".join(out) != s, "空转：内容未变"
sys.stdout.write("\n".join(out))
