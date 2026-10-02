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

# **Batch 198 改锚点**：原来硬编码删「闸 5」那一行（认领 `selftest-exclusions.py`），
# **而 Batch 198 修好 `verify-meta` 的驱动判定之后，它已经不再是驱动了**
# （它被别的 .py 反验引用，是注入夹具）——于是删掉它并不会报「没被认领」，
# **用例从「作废」变成了「失败」**。**这两种都不是好结果：作废是没人看，失败是看不懂。**
# 改成**现场算**：从 `verify-meta` 问出当前的驱动集合，
# 再挑一行**确实认领了某个驱动**的表行删掉。
# **这样用例才真正做到它注释里声称的「不依赖具体哪道闸」**——
# 之前那句声称是假的：它依赖某个具体文件，而那个文件是驱动这件事会变。
import importlib.util
_spec = importlib.util.spec_from_file_location("vm", "scripts/verify-meta.py")
_vm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_vm)
_drivers = set(_vm.selftest_drivers(".")[0])

idx = [i for i, ln in enumerate(lines)
       if ln.startswith("|") and re.match(r"^\|\s*\d", ln)
       and any(("%s" % d) in ln for d in _drivers)]
assert idx, ("锚点未命中：表里没有一行认领了当前的驱动（驱动共 %d 份，"
             "而表里认领的名字应包含其中之一）" % len(_drivers))
i = idx[0]
assert lines[i].strip().endswith("|"), "锚点未命中：不是表格行"

out = lines[:i] + lines[i + 1:]
text = "\n".join(out)
# **Batch 198 修**：原断言是 `"selftest-exclusions.py" not in text`——
# **要求这个名字在整个文件里都不许再出现**。而「慢反验实测耗时」那段散文里
# 早就写着它的名字（HEAD 版本里就有 2 处），于是**这条用例早就作废了**，
# 而作废的输出是「前提不成立：没有验到任何东西」——**方向十一最要紧的两条
# 实际上有一段时间什么都没验**。
# 它的真实意图是「**表里没有行再认领这个驱动**」，那就只核表行。
_dropped = [d for d in _drivers if ("%s" % d) in lines[i]]
assert len(_dropped) == 1, "被删的那一行应恰好认领 1 份驱动，实得 %d" % len(_dropped)
_name = _dropped[0]


def _claims(rows, name):
    return [r for r in rows if r.startswith("|") and name in r and
            re.match(r"^\|\s*\d", r)]
assert not _claims(out, _name), "空转：表里还有行认领这个驱动"
sys.stdout.write(text)
