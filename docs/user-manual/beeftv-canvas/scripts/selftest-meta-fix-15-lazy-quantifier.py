import sys
# 方向五反验用例 15：注入**惰性量词** `{0,300}?`（PCRE 语法，POSIX ERE 不支持）。
#
# 这一类比用例 13 的 `\s` 更危险：`\s` 只是让模式匹配不到，
# 而 `{0,300}?` 与「重复数 > 255」会让 git **整条拒绝模式并返回 128**，
# stdout 为空 —— 而「空输出」在判据里与「零命中」完全等价，
# 于是**整条断言恒真、闸门永远绿、实际什么都没照到**。
# 本闸真实中过：`p_readonly_no_ui_entry` 两条都犯了，从上线起就是死代码。
#
# 注入点仍是 git grep 的模式行，形状与真实代码一致（用例 13 证明过：
# 若把模式写在调用行内，判据根本照不到，负向测试就成了假通过）。
s = sys.stdin.read()
old = """                        r'starterMode[[:space:]]*[:=][[:space:]]*\\{?[[:space:]]*\\"guided\\"',"""
assert old in s, "锚点未命中：没找到 starterMode 那条 git grep 的模式行"
new = """                        r'starterMode[^"\\x60]{0,300}?[?&][[:space:]]*=',"""
out = s.replace(old, new, 1)
assert out != s, "空转：替换后内容与原文相同"
assert "{0,300}?" in out, "空转：惰性量词未出现在结果里"
sys.stdout.write(out)
