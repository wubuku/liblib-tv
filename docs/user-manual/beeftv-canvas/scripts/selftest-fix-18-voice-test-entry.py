import sys
# 用例 18：上游给语音录制测试页补一个界面入口（侧栏导航里加一项）。
# 注入后 p_test_voice_page_no_ui_entry 的 (c) 子判据失效——
# 因为除了 router.tsx 与页面自身，web/src 里出现了第三处指向该路径的字符串。
# 守的是手册路由表里那句「侧栏没有任何入口，只能手敲网址」：
# 一旦补上入口，那行必须删掉，否则手册会继续让用户去手敲网址。
s = sys.stdin.read()
anchor = "function toolItem(slug: NavigationToolSlug, to: string): WorkspaceNavItem {"
assert anchor in s, "锚点未命中"
s = s.replace(anchor,
              'const voiceTestEntry = { to: "/test-voice-recording", title: "语音录制测试" };\nvoid voiceTestEntry;\n\n'
              + anchor,
              1)
sys.stdout.write(s)
