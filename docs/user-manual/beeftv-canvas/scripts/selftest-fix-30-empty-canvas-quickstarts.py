import sys
# 用例 30：上游把空画布四个快捷入口放出来
# （showQuickStarts 改成受环境/配置控制，或直接置 true）。
# 注入后 p_empty_canvas_quickstarts_off 的 (a) 失效 → 整条应失效。
# 守的是手册 create-nodes.md「空画布上原本有四个快捷入口…被一个写死的开关关着，
# 所以你看到的空画布真的只有那一行字」——一旦上游放出，读者就会看到四个按钮，
# 而手册还在说「只有那一行字」，那是在给读者写假话。
#
# 注入点必须落在 (a) 逐字匹配的那一行常量上：
# 判据是 `const showQuickStarts = (true|false);` 的正则匹配，
# 注入到别处（比如只改 quickStarts 数组、或加一个 prop）都不会让它失效，
# 用例就成了假通过（Batch 154/155 连续栽在同一类上）。
#
# 这里改成**条件表达式**而不是 `= true;`：判据的 (a) 明确只认字面量
# （与 simple-mode 同口径——`cond ? false : true` 不算缺陷），
# 所以注入条件式之后断言仍应失效，这同时覆盖了 (a) 的另一半。
# 反过来若注入 `= true;`，判据同样会失效，但那是另一条路径；两者都失效才对。
s = sys.stdin.read()
old = "    const showQuickStarts = false;"
assert old in s, "锚点未命中：空画布快捷入口常量行不在预期位置"
new = "    const showQuickStarts = import.meta.env.DEV;"
out = s.replace(old, new, 1)
# 空转检查：脚本没报错但什么也没改，和报错一样不可信（Batch 154 的教训）
assert out != s, "空转：替换后内容与原文相同"
assert new in out, "空转：注入特征未出现在结果里"
sys.stdout.write(out)
