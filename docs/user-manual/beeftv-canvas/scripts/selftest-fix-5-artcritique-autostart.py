import sys
# **Batch 272 换锚点**：上游把审美批改的启动请求从组件内的
# `useState<{ …; restart: boolean } | null>(null)` 搬进了 `useCanvasProjectDialogs()`，
# **本文件的旧锚点在 v1.7.3 上已经不存在**——
# 实测 `git show origin/main:web/src/pages/canvas/project.tsx | grep restart` 只剩**一处使用**，
# **声明那行没有了**，而 `str.replace` 对不上的锚点**静默空转**，
# 于是「变换结果里找不到修复特征」，闸 18 报这条用例作废。
# **修法**：锚点跟着上游的新形状走——解构块的收尾行
# `    } = useCanvasProjectDialogs();`（实测在第 324 行），
# **它后面紧跟一条新语句，注入点合法**（旧锚点也是语句级的 `useState` 声明）。
# **两条 assert 是这一批补的**（纪律 229）：旧版一个都没有，
# **而这正是「锚点失效」能一路安静到闸 18 才被发现的直接原因**。
s = sys.stdin.read()
anchor = "    } = useCanvasProjectDialogs();\n"
assert anchor in s, "锚点未命中：上游的 useCanvasProjectDialogs 解构块收尾行已改名或挪位"
FEATURE = "    void setArtCritiqueStartRequest;\n"
s = s.replace(anchor, anchor + FEATURE, 1)
assert FEATURE.strip() in s, "注入空转：str.replace 没有真的改到东西"
sys.stdout.write(s)
