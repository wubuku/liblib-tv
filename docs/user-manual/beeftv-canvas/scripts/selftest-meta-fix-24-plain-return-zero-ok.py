import sys
# 方向八反验用例 24（**不误伤**）：新增一条**正常的** `return 0`（闸核对通过），
# 期望方向八**不报**。
#
# 方向八查的是「打印 [skip] 的块之后紧跟的 return 0」——**不是**「文件里有没有
# return 0」。若它退化成「见到 return 0 就报」，那每个正常通过的闸都会被误伤，
# **闸门立刻失去可用性**（Batch 150 判「文案逐字对账闸不可建」用的同一条理由：
# 会稳定误报的闸不如不建）。
#
# 注入方式：在 shortcuts 闸的成功分支上再加一句带 [skip] 字样的**说明文字**
# 之外的普通 return 0 —— 更直接的写法是：给一个**不含 [skip] 打印**的
# 正常早退路径加 return 0，验证它不会被算成违规。
s = sys.stdin.read()
old = '''def main():
    src = find_source()'''
if old not in s:
    # 不同版本的 main 头部形态不同，退一步找第一个不含 [skip] 的 return 0
    import re as _re
    m = _re.search(r"^def main\(\):", s, _re.M)
    assert m, "锚点未命中：找不到 main()"
    old = m.group(0)
    new = old + "\n    # 反验注入：这是一条**普通**的正常返回，不带 [skip]，方向八必须放行\n    if False:\n        return 0"
else:
    new = old + "\n    # 反验注入：这是一条**普通**的正常返回，不带 [skip]，方向八必须放行\n    if False:\n        return 0"
out = s.replace(old, new, 1)
assert out != s, "空转：内容未变"
assert "反验注入：这是一条**普通**的正常返回" in out, "空转：注入特征未出现"
sys.stdout.write(out)
