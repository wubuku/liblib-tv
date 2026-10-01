import sys
# 方向七反验用例 21：把一处 `fail()` 换回**裸 print**（不经计数），期望方向七报出。
#
# 这条守着 Batch 159 的核心不变式：**闸门不能「只报错不失败」**。
# 方向五与方向六各漏过一次计数，闸门把问题打印出来了、退出码却是 0，
# 而 build-site.sh、反验脚本、CI **全都只看退出码**。
#
# 注入点选在方向一里一条**真实的、以 ✗ 开头的 fail() 调用**——
# 判据锚定的正是「被打印的字符串以 ✗ 开头」这个形态，
# **注入必须与判据所锚定的形态一致**，否则用例会「通过」而什么都没验到
# （Batch 154/157 连续栽在同一类上）。
s = sys.stdin.read()
import re
m = re.search(r'^(\s*)fail\("  ✗ ', s, re.M)
assert m, "锚点未命中：没找到以 ✗ 开头的 fail() 调用"
i = s.index(m.group(0))
j = s.index("\n", i)
indent = m.group(1)
out = (s[:i]
       + indent + 'print("  ✗ " + "注入演示：把 fail() 换回裸 print")'
       + s[j:])
assert out != s, "空转：内容未变"
assert 'print("  ✗ " + "注入演示' in out, "空转：注入特征未出现"
# 空转检查的加强：确认**只动了一处**（多动会让用例失去单变量性质）
assert out.count('print("  ✗ " + "注入演示') == 1
sys.stdout.write(out)
