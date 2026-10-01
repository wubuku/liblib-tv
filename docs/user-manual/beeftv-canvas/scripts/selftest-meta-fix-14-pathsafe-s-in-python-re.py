import sys
# 方向五反验用例 14（**不误伤**）：把 `\\s` 加进一个 **Python re** 的模式里。
#
# 方向五只该盯 `git grep -E` 的模式——**Python 的 re 是支持 `\s` 的**，
# 手册脚本里大量用 `\s` 匹配「= 后面有没有空格」，那是完全正确的写法。
# 若方向五不分引擎地一律报错，它会把这几十处正当写法全报成违规，
# **第一次误报就会让人开始忽略这道闸，闸门就废了**
# （Batch 150 试建文案闸时判「不可建」用的正是同一条理由）。
#
# 注入点刻意选在 p_readonly_no_ui_entry 里那段 **Python re.search**：
# 它本来就含 `\s`，注入后再加一处 `\s`——判据必须**当没看见**。
s = sys.stdin.read()
old = """    judged = bool(re.search(
        r'searchParams\\.get\\("readonly"\\)\\s*===\\s*"1"\\s*\\|\\|\\s*'
        r'searchParams\\.get\\("mode"\\)\\s*===\\s*"readonly"', body))"""
assert old in s, "锚点未命中：没找到 p_readonly_no_ui_entry 的 Python re.search"
new = """    judged = bool(re.search(
        r'searchParams\\.get\\("readonly"\\)\\s*===\\s*"1"\\s*\\|\\|\\s*'
        r'searchParams\\.get\\("mode"\\)\\s*===\\s*"readonly"\\s*(?:$|\\n)',
        body))"""
out = s.replace(old, new, 1)
assert out != s, "空转：替换后内容与原文相同"
# 自证注入的确实是「Python re 里的 \s」：改动落在 re.search 调用内
assert out != s and 're.search' in out
sys.stdout.write(out)
