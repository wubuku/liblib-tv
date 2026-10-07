import sys
# 用例 35（Batch 296）：给「复制项目」补上后端同步——**但调的是另一个符号**。
#
# **这条用例守的是一个假绿**：Batch 294 实测 origin/main 上同一个文件里并存两个
# 同义 sync 符号（旧的 syncLocalCanvasProjectToBackend 仍有 7 处、仍被别处使用；
# 新的 syncLocalCanvasProject(id, includeGeneratedAssets, scope) 由
# createLocalCanvasProject 调用）。**而 Batch 294 之前的判据只查旧名**——
# **若上游把复制路径改成调新符号，闸会照旧报「仍成立」，而副本其实已经会上传。**
#
# **必须在基线 bcc3b05 上造**：旧闸在 origin/main 上本来就是红的（那正是要修的误报），
# **在它已经红的树上注入，量不出假绿**（纪律 330 ⑧）。
s = sys.stdin.read()
OLD = "        await flushCanvasStorePersistence();\n        navigate(`/canvas/${id}`);"
assert s.count(OLD) == 1, "锚点数 = %d，注入作废" % s.count(OLD)
NEW = ("        void syncLocalCanvasProject(id, false, expectedScope);\n"
       + OLD)
sys.stdout.write(s.replace(OLD, NEW, 1))
