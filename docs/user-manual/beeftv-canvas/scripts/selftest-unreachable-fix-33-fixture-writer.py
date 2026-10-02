import sys
# 反验用例 33：往**代码**里加一个真实的界面写出点 `navigate("/x?fixture=…")`
# → 期望闸门报出「名单里的参数 `fixture` 本轮**已被扫到写出点**」。
#
# **它验的是 Batch 170 扩出来的那半个覆盖面**：`fixture` 原先因为源码注释里有一句
# `?fixture=` 而永远脱零写、闸门从不跟踪它；现在只看代码，它才真正进入看守范围。
# 而「进入看守范围」的**实质**就是：**上游哪天加一个真的按钮来产出它，闸门必须报**。
# 只测「它现在被算成零写出」是不够的——那证明不了它脱零写之后还能被抓住。
#
# 注入位置选 `web/src/pages/assets/index.tsx`：它是**真实文件**，
# 而 `?fixture=` 所在的注释在 `web/src/lib/canvas/canvas-libtv-fixture.ts`，
# 两者不是同一处，所以这条注入不会被原注释干扰。
src = sys.stdin.read()
anchor = 'onSelectPersonal={() => navigate("/assets?tab=personal")}'
assert anchor in src, "锚点未命中：assets/index.tsx 里找不到 onSelectPersonal 那一行"
# 加在**真实代码**里（不是注释），且与原注释分处不同文件
inject = ('        const __fixtureEntry = () => navigate("/canvas?fixture=libtv-text");\n'
          + src)
assert inject != src, "空转：注入未改变内容"
sys.stdout.write(inject)
