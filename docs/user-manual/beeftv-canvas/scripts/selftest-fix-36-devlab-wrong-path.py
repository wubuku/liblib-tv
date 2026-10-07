import sys
# 用例 36（Batch 296）：把 dev 复现台隔离判断里比对的路径改错。
#
# **守的是 Batch 294 那处「认事实」的改法没有把牙齿一起磨掉**：
# 原判据写死 `'pathname === "/dev/director-repro"'`，origin/main 把
# `window.location.pathname` 换成了 `appPathname()` 就判不到了；
# 新判据改成「isolateDevRepro 的定义里有没有比对那个路径」——
# **判据放宽了，可它必须还能抓住「比对的目标本身错了」这种真失效**。
#
# 必须在基线 bcc3b05 上造（理由同用例 35）。
s = sys.stdin.read()
OLD = '=== "/dev/director-repro"'
assert s.count(OLD) == 1, "锚点数 = %d，注入作废" % s.count(OLD)
sys.stdout.write(s.replace(OLD, '=== "/dev/somewhere-else"'))
