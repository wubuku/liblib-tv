import sys
# 用例 23：上游给功能开放配置补上写入路由。
# 注入后 p_feature_availability_readonly 的 (a) 子判据失效 → 整条应失效。
# 这条用例守的是手册「只暴露了只读的 GET /features，没有写入接口」——
# 一旦上游补上 PATCH，读者就能自己开关，那句「本地部署下你多半遇不到」必须删。
s = sys.stdin.read()
old = """	r.GET("/features", func(c *gin.Context) {"""
assert old in s, "锚点未命中"
s = s.replace(old, """	r.PATCH("/features", func(c *gin.Context) {
		if _, err := currentUser(c, svc); err != nil {
			failService(c, err)
			return
		}
		ok(c, gin.H{"features": setting})
	})

	r.GET("/features", func(c *gin.Context) {""", 1)
sys.stdout.write(s)
