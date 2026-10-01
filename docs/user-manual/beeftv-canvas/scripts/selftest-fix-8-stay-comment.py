import sys
# 用例 8：上游把 `?stay=1` 提升为正式功能（注释里的「验收脚本」字样消失），
# 判据 p_stay_acceptance_only 依赖这句自认注释，故注释一改断言即失效。
s = sys.stdin.read()
s = s.replace("// 允许浏览器验收脚本在项目库内保留新卡片，真实用户仍沿用 LibTV 的直接进入画布行为。",
              "// 允许在新卡片入库后停留在项目库，便于用户先确认再建。", 1)
sys.stdout.write(s)
