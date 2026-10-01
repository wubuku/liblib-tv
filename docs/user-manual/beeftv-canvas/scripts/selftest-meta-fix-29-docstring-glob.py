import sys
# **不误伤用例**：同样的字面量只出现在**注释/说明文字**里，必须放行。
#
# 这正是方向十第一版判据栽的地方：它用正则扫原文，
# 于是把闸 4 **文档字符串里的示例写法**也匹配上了——判据太宽。
# 改用 AST 后，注释与文档字符串里出现什么写法都无关。
s = sys.stdin.read()
anchor = 'import glob'
assert anchor in s, "锚点未命中：找不到 import glob"
note = ("\n# 说明（仅注释，非代码）：本闸早前用 glob.glob("
        + repr("**/*.md") + ", recursive=True) 定位正文，Batch 167 已改为自定位")
sys.stdout.write(s.replace(anchor, anchor + note, 1))
