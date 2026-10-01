import sys
# 用例 11：把侧栏的文字改成一个**更短的标题**。
# 这是**有意设计**（侧栏用短标题，页面 h1 用完整标题），方向四之二只查存在性，
# 所以必须放行。若这条报错，说明方向四之二的判据退化成「比对文字」——
# 那会误报 29 条里的绝大多数（侧栏本来就有 20+ 条短标题与 h1 不同）。
s = sys.stdin.read()
old = "{ text: '上传本地素材', link: '/10-tasks/upload-materials' }"
assert old in s, "锚点未命中"
s = s.replace(old, "{ text: '上传素材', link: '/10-tasks/upload-materials' }", 1)
sys.stdout.write(s)
