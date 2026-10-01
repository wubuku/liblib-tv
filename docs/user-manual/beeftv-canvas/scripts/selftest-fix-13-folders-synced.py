import sys
# 用例 13：上游给画布文件夹接上了服务端（画布库开始用素材那套接口）。
# 注入后 p_canvas_folders_are_local 的 (c) 不再成立：画布库页面出现了
# AssetFolder / asset-folders 引用。
#
# 锚点用本文件真实的默认导出名 CanvasPage（Batch 138 首轮写成了
# CanvasIndexPage，被反向验证的**前提校验**当场作废——这正是它的用途）。
s = sys.stdin.read()
old = "export default function CanvasPage() {"
assert old in s, "锚点未命中"
s = s.replace(old,
              "const canvasSelftestAssetFolders = () => createAssetFolder(\"selftest\");\n"
              "export default function CanvasPage() {", 1)
sys.stdout.write(s)
