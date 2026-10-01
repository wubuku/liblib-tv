import sys
# 用例 7：给「复制项目」补上后端同步——只修 duplicateCurrentProject 一处即可，
# 判据要求两条复制入口都不得出现 syncLocalCanvasProjectToBackend，
# 所以只补一条就足以让断言失效（对应手册里「三条路径里两条不上传」的说法）。
s = sys.stdin.read()
s = s.replace("        await flushCanvasStorePersistence();\n        navigate(`/canvas/${id}`);",
              "        await flushCanvasStorePersistence();\n"
              "        await syncLocalCanvasProjectToBackend(id);\n"
              "        navigate(`/canvas/${id}`);", 1)
sys.stdout.write(s)
