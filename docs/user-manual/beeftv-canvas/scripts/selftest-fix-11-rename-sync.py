import sys
# 用例 11：顶栏改名补上后端同步 —— p_rename_not_synced 应当失效。
# 只改顶栏这一处即可：判据要求两处改名都不得出现 syncLocalCanvasProjectToBackend。
s = sys.stdin.read()
old = "        updateProject(canvasId, { canvasTitle });\n        await flushCanvasStorePersistence();"
assert old in s, "锚点未命中"
s = s.replace(old,
              "        updateProject(canvasId, { canvasTitle });\n"
              "        await flushCanvasStorePersistence();\n"
              "        await syncLocalCanvasProjectToBackend(canvasId);", 1)
sys.stdout.write(s)
