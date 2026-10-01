import sys
# 用例 10：把一个任务页从 vitepress 侧栏里删掉（模拟「建了页面忘了加侧栏」）。
# 注入后方向四之二应报出「不在 vitepress 侧栏里」。
# Batch 154 在真实仓库里一次抓到 4 个，其中 readonly-canvas.md 从 Batch 135
# 建页起就一直不在侧栏——**侧栏比 README 索引漏得更久**。
s = sys.stdin.read()
old = "          { text: '素材库（资产页）', link: '/10-tasks/asset-library' },\n"
assert old in s, "锚点未命中"
s = s.replace(old, "", 1)
sys.stdout.write(s)
