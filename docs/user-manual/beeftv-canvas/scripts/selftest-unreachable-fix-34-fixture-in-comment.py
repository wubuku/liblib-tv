import sys
# 反验用例 34（**不误伤那一半**）：只往**注释**里加一句 `?fixture=…`
# → 期望闸门**照旧通过**（`fixture` 仍是零写出参数）。
#
# **它是用例 33 的另一面，也是这次改动最需要钉住的行为**：
# 「注释里写了 `?fixture=`」**不是**「界面上有个按钮会产出它」。
# 改之前注释**确实**被当成写出点，于是这两个参数永远脱零写；改之后不是。
# **如果这条用例不写，「剥注释」这个改动就只有一个方向被验证**——
# 而单向的改动最容易变成「判据变弱了也没人知道」：比如哪天有人图省事
# 直接不剥了，或者把整个文件当注释丢掉，**闸门会变得更宽松、只会少报、不会报错**。
#
# 注入位置刻意选**不含 `?fixture=` 的那个文件**（assets/index.tsx），
# 免得与上游已有的那处注释混在一起、说不清是谁的功劳。
src = sys.stdin.read()
anchor = 'onSelectPersonal={() => navigate("/assets?tab=personal")}'
assert anchor in src, "锚点未命中：assets/index.tsx 里找不到 onSelectPersonal 那一行"
inject = ('        // 演示用深链：?fixture=libtv-storyboard（仅注释，不是界面入口）\n'
          + src)
assert inject != src, "空转：注入未改变内容"
sys.stdout.write(inject)
