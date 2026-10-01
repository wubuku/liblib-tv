import sys
# 方向五反验用例 13：往 git grep 的模式里塞回一个引擎不支持的 \s。
#
# 背景：Batch 157 用例 29 判失败，顺藤摸出**一类系统性缺陷**——
# `git grep -E` 走 POSIX ERE，把 `\s` 当**字面字母 s**，
# 于是一条断言的正则永远匹配不上、闸门永远绿，**而它什么都照不到**。
# 方向五就是为盯住这类「静默失效」而建的，所以它自己必须先被验过。
#
# 注入点必须是**真的 git grep 调用**附近：
# 判据只看传给 git grep -E 的模式，注入到 Python `re` 里不算数
# （Python 的 re 支持 \s，那里用 \s 是对的）——用例 14 正是钉这一条。
s = sys.stdin.read()
# 锚点写成**当前的**调用形态 `_git_grep_run(`。
# **本批踩过一次**：锚点写的是 `subprocess.run(`，而我随后把所有 git grep
# 调用点换成了薄包装 `_git_grep_run(`，锚点失配 → 用例被作废 →
# 而汇总行当时只打「通过/失败」，**14 条里少的 1 条静静消失，整体还报「失败 0」**。
# **教训：改判据脚本的调用形态时，反验脚本的锚点必须同步更新**，
# 且**作废数必须出现在汇总里**，否则作废就是伪装成绿灯的漏洞。
old = """                        r'starterMode[[:space:]]*[:=][[:space:]]*\\{?[[:space:]]*\\"guided\\"',"""
assert old in s, "锚点未命中：没找到 starterMode 那条 git grep 的模式行"
new = """                        r'starterMode\\s*[:=]\\s*\\{?\\s*\\"guided\\"',"""
out = s.replace(old, new, 1)
assert out != s, "空转：替换后内容与原文相同"
assert "\\s" in out, "空转：注入特征未出现在结果里"
sys.stdout.write(out)
