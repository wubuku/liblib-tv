import sys
# 方向八反验用例 23：把一处 skip 路径的 `return 2` **改回 `return 0`**，
# 期望方向八报出「无法核对 ≠ 通过」被破坏。
#
# 背景（Batch 160 普查）：**6 个闸共 11 处**在数据不可用时打印 `[skip]`
# 然后 `return 0`，而 build-site.sh 只看退出码——**上游目录一改名，
# 9 道闸里有 5 道什么都没查却全绿**。
#
# 注入点选 `verify-endpoints.py` 的第一条 skip 路径，**注入形态与判据所查的
# 形态一致**（「打印 [skip] 的块之后紧跟的 return 0」），
# 否则用例会「通过」而什么都没验到（Batch 154/157/159 连续栽在同一类上）。
s = sys.stdin.read()
old = '''    if not src:
        print("[skip] 未找到 BeefTV 源码，跳过端点核对")
        return 2'''
assert old in s, "锚点未命中：没找到 endpoints 的第一条 skip 路径"
new = '''    if not src:
        print("[skip] 未找到 BeefTV 源码，跳过端点核对")
        return 0'''
out = s.replace(old, new, 1)
assert out != s, "空转：内容未变"
assert "return 0" in out, "空转：注入特征未出现"
# 确认**只动了一处**（多动会让用例失去单变量性质）
assert out.count("return 0") == s.count("return 0") + 1
sys.stdout.write(out)
