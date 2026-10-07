import sys
# 用例 37（Batch 296）：在后端**真的注册一组画布文件夹端点**。
#
# **守的是 Batch 294 给 `canvas-folders-local-only` 补的那条 (d)**：
# 原判据只靠「画布库页零处引用 AssetFolder」**间接**推出「服务端没有画布文件夹这个概念」，
# **而上游完全可以「页面照旧直调 store 的 createFolder、同时后端新增了端点」——
# 那种树���旧判据会报绿**（本批实测：同一棵合成 ref 上旧闸 成立 / 新闸 失效）。
#
# 注入点选 `r.GET("/assets"` 这一行之前：它在基线与 origin/main 上都在，
# 而 `/canvas-folders` 在基线两个目录合计 0 处（实测），所以这条注入**两侧都造得出来**。
s = sys.stdin.read()
ANCHOR = "\tr.GET(\"/assets\", func(c *gin.Context) {"
assert s.count(ANCHOR) == 1, "锚点数 = %d，注入作废" % s.count(ANCHOR)
INJECT = (
    "\t// Batch 296 鉴别力注入：服务端接上了画布文件夹\n"
    "\tr.GET(\"/canvas-folders\", func(c *gin.Context) { c.JSON(200, nil) })\n"
    "\tr.PUT(\"/canvas-folders/:id\", func(c *gin.Context) { c.JSON(200, nil) })\n"
)
sys.stdout.write(s.replace(ANCHOR, INJECT + ANCHOR, 1))
