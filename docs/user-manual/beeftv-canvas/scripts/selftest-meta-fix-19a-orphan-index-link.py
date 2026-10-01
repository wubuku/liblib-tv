import sys
# 方向六反验用例 19（第一步）：删掉 README.md 里指向任务索引的链接。
# 任务索引 10-tasks/README.md **不在侧栏**，它的入链只有两条
# （README.md 与 30-concepts.md），**两处都删才会真的成为孤儿页**。
s = sys.stdin.read()
old = "| 建节点、传素材、连参考 | [10-tasks/](10-tasks/README.md) |"
assert old in s, "锚点未命中：README.md 里找不到指向 10-tasks/ 索引的那一行"
out = s.replace(old, "| 建节点、传素材、连参考 | 先看上面那几项 |", 1)
assert out != s, "空转：内容未变"
sys.stdout.write(out)
