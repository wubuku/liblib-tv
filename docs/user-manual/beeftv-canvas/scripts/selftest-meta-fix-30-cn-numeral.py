import re
import sys
# 方向三反验用例 30：把标题里的中文数字**换成另一个复合数**（当前 +10，形如「二十一」）
# → 期望方向三报出「标题写「N 道闸」，清单表却有 M 行」，而**不是**「找不到标题」。
#
# **它验的是 `_cn_int` 能解析复合中文数字**（十X 与 X十Y 两种形态）。
#
# ⚠️ **Batch 171 重写锚点（纪律 107 第三次应验）**：第一版把
# `anchor = "### 现有十道闸"` 写死，替换成「十一道闸」。本批新增闸 11 之后
# **真实标题自己变成了「现有十一道闸」**——于是
#   ① 锚点失配 → 用例作废（本批验收里**整整作废了两次**才发现）；
#   ② 更要命的是**它想验的那件事已经由真实仓库本身覆盖了**：
#      标题真的是「十一道闸」，`_cn_int` 必须能解析它，否则基线就会红。
# **一条用例的前提被别人做掉之后，它要么重复、要么作废——两条都没价值。**
#
# 现在改成**从现场推导**：抓出当前标题的数字，+10 后渲染成复合中文数
# （21 → 「二十一」，属 **X十Y**；而真实标题的「十一」是 **十X**——
# **两种形态现在各有一条覆盖**：真实基线覆盖十X，本条覆盖 X十Y）。
def cn(n):
    d = "零一二三四五六七八九"
    if n < 10:
        return d[n]
    if n == 10:
        return "十"
    if n < 20:
        return "十" + d[n - 10]
    if n % 10 == 0:
        return d[n // 10] + "十"
    return d[n // 10] + "十" + d[n % 10]


def parse(s):
    m = re.search(r"###\s*现有([零一二三四五六七八九十]+)道闸", s)
    if not m:
        raise AssertionError("锚点未命中：找不到「### 现有 N 道闸」标题")
    t = m.group(1)
    digits = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
              "六": 6, "七": 7, "八": 8, "九": 9}
    if "十" not in t:
        return digits[t]
    head, _, tail = t.partition("十")
    tens = digits.get(head, 1) if head else 1
    ones = digits.get(tail, 0) if tail else 0
    return tens * 10 + ones


s = sys.stdin.read()
cur = parse(s)
nxt = cn(cur + 10)
m = re.search(r"###\s*现有[零一二三四五六七八九十]+道闸", s)
out = s[:m.start()] + "### 现有%s道闸" % nxt + s[m.end():]
assert out != s, "空转：内容未变"
# 纪律（Batch 165）：断言**改完之后锚点真的不见了**，否则子串判断会照样命中
assert ("现有%s道闸" % nxt) in out and ("现有%s道闸" % s[m.start():m.end()][4:-3]) not in out, \
    "空转：原锚点没被替换掉"
sys.stdout.write(out)
