import re
import sys
# 方向十一反验用例 33：把对应关系表里的**一整行删掉**（少认领一个驱动）
# → 期望报出「驱动 `selftest-exclusions.py` 没有被对应关系表认领」。
#
# **这是本方向最重要的一条**：它对应 Batch 168 抓到的真实事故形态——
# **规约写着「每道闸都必须有反验」，而闸 1/2/6 三道一道都没有，账面看不出区别。**
# 删一行模拟的就是「新增一道闸（或删掉一道反验）却忘了登记」，
# 而**漏认领的东西看起来和已认领的东西长得一模一样**。
#
# **为什么删「闸 5」这一行**：它是唯一「认领内容与闸号完全解耦」的一行——
# 判据不靠名字猜对应关系，只看**这一行还在不在**，
# 所以换成任何一行都能触发，**用例不依赖具体哪道闸**。
s = sys.stdin.read()
lines = s.split("\n")

idx = [i for i, ln in enumerate(lines)
       if re.match(r"^\|\s*5\s", ln) and "selftest-" in ln]
assert len(idx) == 1, "锚点未命中：应恰好找到 1 行以「5 」开头且含 selftest- 的表行，实得 %d" % len(idx)
i = idx[0]
assert lines[i].strip().endswith("|"), "锚点未命中：不是表格行"

out = lines[:i] + lines[i + 1:]
text = "\n".join(out)
assert "selftest-exclusions.py" not in text, "空转：被删的行还在（或该驱动还被别处提到）"
sys.stdout.write(text)
