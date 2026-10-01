import sys
# 方向六反验用例 19（第二步）：删掉 30-concepts.md 里指向任务索引的最后一条链接。
s = sys.stdin.read()
old = "- 概念对应的操作页入口：[任务指南](10-tasks/README.md)"
assert old in s, "锚点未命中：30-concepts.md 里找不到指向任务索引的那一行"
out = s.replace(old, "- 概念对应的操作页入口：见站点侧栏", 1)
assert out != s, "空转：内容未变"
sys.stdout.write(out)
