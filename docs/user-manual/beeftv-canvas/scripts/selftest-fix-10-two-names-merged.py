import sys
# 用例 10：上游把两处改名统一到同一个字段（canvasTitle 那个洞被填了）。
# 注入后 p_rename_two_names 的 (c) 不再成立：库内 saveTitle 也开始写 canvasTitle。
s = sys.stdin.read()
old = "            renameProject(project.id, editingTitle);"
assert old in s, "锚点未命中"
s = s.replace(old,
              "            useCanvasStore.getState().updateProject(project.id, { canvasTitle: editingTitle });\n"
              "            renameProject(project.id, editingTitle);", 1)
sys.stdout.write(s)
