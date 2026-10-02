import re
import sys
# 方向十一反验用例 34：把某行认领的反验**改成一个不存在的文件名**
# → 期望报出「认领了不存在的」。
#
# **它与用例 33 是两个方向**：33 查「该认领的没认领」，34 查「认领了没有的」。
# **只做其中一个，判据就是单边的**——而单边判据的绿灯毫无意义：
# 一张表可以既不漏行、又整张都在认领不存在的文件，看上去完全自洽。
#
# **这个形态不是假想**：手写登记最常见的错就是**文件名拼错、或者文件被改名/删除后
# 登记没跟着改**，而表格看上去仍然是满的。
s = sys.stdin.read()
lines = s.split("\n")

idx = [i for i, ln in enumerate(lines)
       if re.match(r"^\|\s*6\s", ln) and "selftest-label-drift.py" in ln]
assert len(idx) == 1, "锚点未命中：应恰好找到 1 行以「6 」开头且认领 selftest-label-drift.py，实得 %d" % len(idx)
i = idx[0]

lines[i] = lines[i].replace("selftest-label-drift.py", "selftest-label-drift-v2.py", 1)
out = "\n".join(lines)
# 纪律：断言**改完之后锚点真的不见了**——`assert 原文里有 X` 只证明改之前在
# **Batch 198 修**：同样把判定限定在**表行**上（原式是全文匹配，
# 而散文里出现过这个反验名，于是这条用例同样早就作废了）。
_rows = out.split("\n")
def _claims(name):
    return [r for r in _rows if r.startswith("|") and name in r and
            re.match(r"^\|\s*\d", r)]
assert not _claims("selftest-label-drift.py"), "空转：原锚点那行没被换掉"
assert _claims("selftest-label-drift-v2.py"), "空转：注入特征未出现在表行里"
sys.stdout.write(out)
