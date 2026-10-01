import sys
# 用例 31（不误伤）：注入的是**比较式**，不是写入。
#
# 背景：Batch 157 用例 29 判失败，暴露出 (b) 的正则只认等号
# `starterMode = "guided"`，而上游现有写法恰恰是冒号属性式
# （`project.tsx:2823` 的 `{ starterMode: "freeform" }`）——**最可能的修复路径判据照不到**。
# 修法：正则从 `starterMode[^\n]{0,40}=\s*\{?\s*"guided"` 放宽为
#       `starterMode\s*[:=]\s*\{?\s*"guided"`。
#
# **但放宽正则本身有风险**：若写成 `starterMode.{0,40}"guided"` 这种，
# 连 `starterMode === "guided"` 这种**纯比较**也会被当成写入 → 闸门永远失效。
# 所以必须有这条用例钉住「比较式不算写入」——
# **闸门要成对：能抓 + 不误伤，不误伤用例不是可选项。**
#
# 注入点选在 canvas-starter.ts 的类型定义下方：加一个**只在比较中出现**的辅助函数。
s = sys.stdin.read()
old = "    return starterMode === \"guided\" ? \"guided\" : \"freeform\";"
assert old in s, "锚点未命中：canvas-starter.ts 的判定行不在预期位置"
new = old + "\n// 反验注入：只比较、不写入（用于验证判据不把比较式误当成写入点）\nexport const isGuidedStarter = (starterMode?: CanvasStarterMode) => starterMode === \"guided\";"
out = s.replace(old, new, 1)
# 空转检查：脚本没报错但什么也没改，和报错一样不可信（Batch 154 的教训）
assert out != s, "空转：替换后内容与原文相同"
assert 'isGuidedStarter' in out, "空转：注入特征未出现在结果里"
sys.stdout.write(out)
