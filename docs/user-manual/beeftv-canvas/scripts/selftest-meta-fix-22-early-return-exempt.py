import sys
# 方向七反验用例 22（**不误伤**）：给早退路径加一处**合法的**裸 ✗ 打印，必须放行。
#
# 方向七豁免两类形态：① 计数函数 `fail()` 自己的打印；② **报完立刻 `return 1`**
# 的早退路径——退出码由 return 决定，不经计数器，**是正确写法**。
# 本闸开头那段 `screenshots_match_disk` 前置检查就是第 ② 类。
#
# **若方向七不豁免它，它上线当天就会把这段正确代码报成违规**，
# 而要「修」它只能把早退改成累加器——**那是为让闸门闭嘴而改坏代码**。
# 这条用例把该豁免钉死。
s = sys.stdin.read()
old = '''        print("✗ screenshots/manifest.yml 与磁盘 png 不一致——")
        print("    截图数这个真值不可信，先跑 verify-screenshots.py 定位")'''
assert old in s, "锚点未命中：没找到截图前置检查的早退打印"
new = '''        print("✗ screenshots/manifest.yml 与磁盘 png 不一致——")
        print("    截图数这个真值不可信，先跑 verify-screenshots.py 定位")
        print("✗ （反验注入：同样属于「报完立刻 return 1」的早退形态，必须放行）")'''
out = s.replace(old, new, 1)
assert out != s, "空转：内容未变"
assert "反验注入：同样属于" in out, "空转：注入特征未出现"
sys.stdout.write(out)
