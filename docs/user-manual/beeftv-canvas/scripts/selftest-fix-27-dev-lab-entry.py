import sys
# 用例 27：上游给 /dev/folders 接上一个界面入口（比如塞进命令面板）。
# 注入后 p_dev_lab_routes_no_entry 的 (b) 失效 → 整条应失效。
# 守的是手册「这两个调试台界面上零入口，只能手敲网址」——
# 一旦上游补了导航入口，手册必须改写成「可以从 X 进入」。
# 注意注入点是**侧栏**（一个 components/ 下的文件），正是 (b) 里显式排除的形态，
# 所以它会真的打断子判据，而不是被 (b) 的宽松条件放过。
s = sys.stdin.read()
old = "                { id: \"settings:channels\", title: \"模型配置\", icon: Settings2, to: \"/settings?section=channels\" },"
assert old in s, "锚点未命中"
s = s.replace(old,
              old + "\n                { id: \"dev:folders\", title: \"文件夹样式台\", icon: Settings2, to: \"/dev/folders\" },",
              1)
sys.stdout.write(s)
