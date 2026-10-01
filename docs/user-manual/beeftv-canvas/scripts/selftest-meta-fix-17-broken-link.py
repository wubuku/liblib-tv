import sys
# 方向六反验用例 17：把一条正文链接改成指向不存在的文件 → 必须报出。
#
# 注入形态刻意选**相对 .md 路径**（同目录），这是最常见的手误：
# 改文件名时忘了同步正文链接。第一版注入过 `../screenshots/nonexistent.png`
# 那种形态，而方向六对 md 与 img 两条路径是分开归类的，会掩盖问题。
s = sys.stdin.read()
old = "## 你将完成\n"
assert old in s, "锚点未命中：找不到「## 你将完成」小节"
new = ("## 你将完成\n\n"
       "见 [这个页面](../10-tasks/does-not-exist.md)。\n")
out = s.replace(old, new, 1)
assert out != s, "空转：替换后内容与原文相同"
assert "does-not-exist.md" in out, "空转：注入特征未出现"
sys.stdout.write(out)
