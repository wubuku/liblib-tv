import sys
# 方向六反验用例 20：把「站点首页豁免孤儿检测」这行**去掉**，期望闸门**立刻报出**
# 根 README.md 是孤儿页。
#
# **为什么反过来测豁免**：首页 README.md 的入链是由 vitepress 框架提供的
# （约定即 `/`），正文里从来就没有、也不该有指向它的 .md 链接。
# 现状就是「首页无入链且闸门放行」——**但这只证明基线是绿的，
# 不证明「是豁免让它绿的」**。去掉豁免后它若**不报**，说明孤儿检测对真实页面
# 根本不工作（用例 19 之外再加一道交叉验证）；它若**报**，才同时证明
# ①孤儿检测有效 ②豁免是真正承重的、不是恰好没触发。
s = sys.stdin.read()
old = 'orphans = [p for p in sorted(pages) if p not in inbound and p not in in_sidebar and p != home]'
assert old in s, "锚点未命中：没找到孤儿页判定那行"
new = 'orphans = [p for p in sorted(pages) if p not in inbound and p not in in_sidebar]  # 反验：去掉首页豁免'
out = s.replace(old, new, 1)
assert out != s, "空转：豁免未去掉"
sys.stdout.write(out)
