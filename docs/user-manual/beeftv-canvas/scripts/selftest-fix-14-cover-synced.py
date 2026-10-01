import sys
# 用例 14：上游把画布封面从 localStorage 挪进画布内容。
# 注入后 p_canvas_cover_is_localstorage 应失效（localStorage 写入消失）。
s = sys.stdin.read()
old = "                try { localStorage.setItem(`beeftv-project-cover:${project.id}`, dataUrl); } catch { /* quota */ }"
assert old in s, "锚点未命中"
s = s.replace(old,
              "                useCanvasStore.getState().updateProject(project.id, { coverDataUrl: dataUrl });", 1)
sys.stdout.write(s)
