import sys
# 用例 6：给只读模式接上一个界面入口（导航里真的出现了 ?readonly=1）。
# 注入点选顶栏组件——模拟上游「在顶栏加一个只读分享按钮」这种最自然的修复。
#
# 两个要点：
#  ① 注入形态刻意用**数据对象里的字符串**（to: "..."）而不是 navigate(`...`)：
#     Batch 135 首次扫描正是漏掉了这种形态（首页能力卡 home-data.ts 就是这么写的），
#     闸门的写出点判据因此才改成保守口径。若这里换成 navigate() 也能被抓到，
#     说明判据同时覆盖了两种形态。
#  ② 锚点用本文件真实的导出名 CanvasTopBar（不是 CanvasProjectTopBar）——
#     Batch 135 首轮锚点写错，被反向验证的**前提校验**当场作废，这正是它的用途。
s = sys.stdin.read()
assert "export function CanvasTopBar" in s, "锚点未命中"
s = s.replace("export function CanvasTopBar",
              "const canvasSelftestReadonlyLink = { to: \"/canvas/demo?readonly=1\" };\n"
              "export function CanvasTopBar", 1)
sys.stdout.write(s)
