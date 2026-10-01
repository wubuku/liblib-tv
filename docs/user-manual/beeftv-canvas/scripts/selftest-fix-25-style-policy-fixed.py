import sys
# 用例 25：上游把画风执行策略改回单一硬编码（取消 strict-assets 分支）。
# 注入后 p_style_execution_policy_two_branches 的 (a)/(b) 失效 → 整条应失效。
# 守的是手册「默认兼容降级、可以切成严格阻止」这个**可切换性**：
# 一旦上游取消第二个取值，手册必须改回「恒被挡住」那种单一结论。
s = sys.stdin.read()
old = '    executionPolicy?: "compatible-fallback" | "strict-assets";'
assert old in s, "锚点未命中"
s = s.replace(old, '    executionPolicy?: "compatible-fallback";', 1)
sys.stdout.write(s)
