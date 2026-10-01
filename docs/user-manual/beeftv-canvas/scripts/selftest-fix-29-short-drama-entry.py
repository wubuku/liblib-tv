import sys
# 用例 29：上游补上把 starterMode 设成 "guided" 的入口
# （例如新建画布时按来源决定引导形态）。
# 注入后 p_short_drama_empty_state_unreachable 的 (b) 失效 → 整条应失效。
# 守的是手册 create-nodes.md「短剧引导那套进不去、没有任何入口能到达」——
# 一旦上游补了入口，这段必须改写成「新建画布时可以选择进入短剧引导」。
# 注入点选在 use-canvas-store.ts（真正做字段写入的地方），不是类型定义处：
# **判据查的是写入点，注入也必须落在写入点**，否则用例会「通过」而什么都没验到
# （Batch 155 的同类教训）。
s = sys.stdin.read()
old = "    createProject: (title?: string, projectId?: string, workspaceProjectId?: string) => string;"
assert old in s, "锚点未命中"
new = old + "\n    enterGuidedStarter: (id: string) => set((state) => ({ projects: state.projects.map((project) => project.id === id ? { ...project, starterMode: \"guided\" } : project) })),"
s = s.replace(old, new, 1)
sys.stdout.write(s)
