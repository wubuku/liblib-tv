import sys
# 方向六反验用例 18（**不误伤**）：给链接加一个 #fragment → **必须报**。
#
# 这条严格说不是「不误伤」而是「另一种必报」，因为手册自订的约定是
# 「正文不用页内锚点，链接不带 #fragment」——**这条约定此前没有任何闸在守**，
# 而 `.vitepress/config.mjs` 里 `ignoreDeadLinks: true`，构建也不会拦。
# 单独列一条是为了证明**约定那一半真的在被检查**，而不是只查了「文件是否存在」。
#
# 注入的链接**指向真实存在的文件**（只多了个锚点）——
# 这样「文件是否存在」那一条必然通过，**能证明报出来的是锚点规则而不是断链**。
s = sys.stdin.read()
old = "## 你将完成\n"
assert old in s, "锚点未命中：找不到「## 你将完成」小节"
new = ("## 你将完成\n\n"
       "见 [目标页](create-nodes.md#空画布只有一种样子)。\n")
out = s.replace(old, new, 1)
assert out != s, "空转：替换后内容与原文相同"
assert "#空画布只有一种样子" in out, "空转：注入特征未出现"
sys.stdout.write(out)
