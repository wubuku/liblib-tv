import sys
# 用例 12：上游把 title / canvasTitle 加进自动保存的监视字段。
# 这正是 Batch 135/136 三个缺陷的共同根因，所以它的反向验证要盯住「字段集合」，
# 而不只是某一个具体函数。注入后 p_content_watcher_excludes_title 应失效。
s = sys.stdin.read()
old = "        const patch = { nodes, connections, chatSessions, activeChatId, appearance: canvasAppearance, backgroundMode, showImageInfo };"
assert old in s, "锚点未命中"
s = s.replace(old,
              "        const patch = { nodes, connections, chatSessions, activeChatId,"
              " appearance: canvasAppearance, backgroundMode, showImageInfo,"
              " title: currentProject?.title, canvasTitle: currentProject?.canvasTitle };", 1)
sys.stdout.write(s)
