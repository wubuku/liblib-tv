import sys
# 用例 21：上游把「复制提示词 / 反推提示词」那个 more 分组接上渲染。
# 注入后 p_image_toolbar_omits_tools 的 (c) 失效。
# 守的是手册那句「复制/反推提示词目前任何界面都点不到」——
# 这两个功能不是「被条件隐藏」，而是整组从未被渲染，接上就立刻能用。
s = sys.stdin.read()
anchor = "    const panoramaTools ="
assert anchor in s, "锚点未命中"
s = s.replace(anchor,
              '    const moreTools = inGroup("more");\n' + anchor, 1)
sys.stdout.write(s)
