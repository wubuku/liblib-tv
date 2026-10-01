import re
import sys
# 方向九反验用例 32：把 A 类小节标题里的「（N 类）」**整个删掉**
# → 期望方向九报出「A 类标题没写「（N 类）」计数——删掉它就绕过了检查」。
#
# **这条不是凑数，是判据设计的必要一半**：
# 用例 31 证明「写错会被抓」，可**只要检查写成「有计数才校验」**，
# 那么**删掉计数**就是绕过它的最短路径 —— 而这恰恰是真实项目里最可能的动作：
# 有人重排表格、觉得标题里的数字碍事、手一删，检查从此静默失效，
# **而且比失效前更隐蔽**（它看起来像是「本来就没这个要求」）。
#
# **纪律 104 的延伸**：抑制规则与匹配规则互为镜像，**这里则是「缺省」与「存在」互为镜像**：
# 判据若只认「有」，就必须显式认「无」，否则**没写**比**写错**更安全。
# 这与 Batch 166「收窄抑制前先量误报」是同一个思路的另一面。
s = sys.stdin.read()
lines = s.split("\n")

heads = [i for i, ln in enumerate(lines) if re.match(r"^\*\*A\s*类", ln.strip())]
assert len(heads) == 1, "锚点未命中：A 类小节标题应恰好 1 行，实得 %d 行" % len(heads)
i = heads[0]

m = re.search(r"\s*（[0-9零一二三四五六七八九十]+\s*类\s*）", lines[i])
assert m, "前提不成立：A 类标题里本来就没有「（N 类）」计数"

lines[i] = lines[i][:m.start()] + lines[i][m.end():]
out = "\n".join(lines)
assert out != s, "空转：内容未变"
assert re.search(r"^\*\*A\s*类", lines[i]) and "类）" not in lines[i], "空转：标题没被改干净"
sys.stdout.write(out)
