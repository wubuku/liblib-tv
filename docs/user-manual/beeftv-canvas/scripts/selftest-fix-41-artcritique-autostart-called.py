import sys
# 用例 41（Batch 295 的鉴别力）：给 setArtCritiqueStartRequest 补一个**真实调用点**。
#
# **守的是新加的「全库零调用复核」只认零调用**——
# 若被判成「复核成立」，那处修复就把原来的误报换成了一处**更贵的漏报**：
# 上游真的接上了这条路，而闸说「声明唯一、无任何调用点 → 断言仍成立」。
#
# 注入点选 `const clearDeletedNodeIds = useCallback(`：它在 origin/main 上存在，
# 而本用例跑的正是 origin/main 树（用例 38–41 那一族）。
s = sys.stdin.read()
ANCHOR = "    const clearDeletedNodeIds = useCallback((removedIds: Set<string>) => {"
assert s.count(ANCHOR) == 1, "锚点数 = %d，注入作废" % s.count(ANCHOR)
INJECT = (
    "    // Batch 296 鉴别力注入：一个真实调用点\n"
    "    function __b295_probe() {\n"
    "        return setArtCritiqueStartRequest({ nodeId: \"n\", id: \"i\", restart: false });\n"
    "    }\n"
)
sys.stdout.write(s.replace(ANCHOR, INJECT + ANCHOR, 1))
