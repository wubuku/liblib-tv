import sys
# 用例 24：上游把审美批改两层统一成「都取第一张」。
# 注入后 p_art_critique_two_layers 的 (b) 失效 → 整条应失效。
# 守的是手册「节点取第一张、弹窗要求恰好一张，**两层不一致**」这个**差异本身**：
# 上游哪天统一了，手册必须改写成「现在节点和面板一致取第一张」，
# 而不是继续拿一个已经不存在的不一致去提醒读者。
s = sys.stdin.read()
old = 'const input = useMemo(() => { const images = upstreamNodes.filter(isArtCritiqueImageInput); return images.length === 1 ? images[0] : undefined; }, [upstreamNodes]);'
assert old in s, "锚点未命中"
s = s.replace(old,
              'const input = useMemo(() => { const images = upstreamNodes.filter(isArtCritiqueImageInput); return images[0]; }, [upstreamNodes]);',
              1)
sys.stdout.write(s)
