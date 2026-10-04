#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第四十道闸：「取证基线」是一份**落点声明**——基线之后上游发了什么，手册必须逐个点名。

**为什么要有这道闸（Batch 272 的由来）**：本批顺着「手册停在哪个版本」查了一遍，发现一件事：

  · 手册的取证基线是 **v1.6.22**；
  · 而上游 `origin/main` 已经是 **v1.7.3**（`3b4c79a`），跨度 **34 个提交 / 1263 个文件**；
  · `CHANGELOG.md` 从 v1.6.23 到 v1.7.3 有 **4 个发布段落**，
    提取出 **124 条**条目，其中用户可见能力包括：
    **v1.6.23 画布助手**（起草场景、编辑节点、连接引用、逐轮撤销、跨重启恢复、
    可撤销的 CLI / MCP 接入）、**v1.7.1 消息框旁选模型 + Astra / Opus / DeepSeek / GLM 目录**、
    **v1.7.2 Windows MCP 与 Claude Desktop 设置、模型服务地址与 DNS 报错指引**、
    **v1.7.3 引导式模型服务接入（OpenAI / Gemini / 火山方舟 + 可搜索目录 + 手动录入）**、
    **本地凭据加密**。
  · **手册里这些词 0 命中**（`画布助手` / `canvas-assistant` / `引导式` / `MCP` / `Astra` /
    `凭据加密` / `本地模型服务` 全部搜不到；`目录` 有 8 处命中，但**那 8 处都是别的东西**——
    「目录」是本手册用得最多的普通词之一，**拿它当「引导式模型目录」的证据是纯误判**）。

**于是读者手上是 v1.7.3、翻的是一本核到 v1.6.22 的手册，
而手册从头到尾没有一处告诉他「本手册止于哪一版，之后变了什么」。**
`20-reference.md` 的「取证基线」小节确实写了「你如果跑的是更新版本，数字与文案可能已经变了」，
**但那句话没有说变了什么**——**而「可能变了」与「变了什么」对读者的用处差着一整个数量级**：
前者让他知道要留一手，后者告诉他该去哪里找。

**本闸判什么**：`CHANGELOG.md` 里**严格新于取证基线**的每一个发布版本，
必须在 `20-reference.md` 的「基线之后」小节里**有一条以该版本号开头的列表项，且带一句实质说明**。
**两个方向都判**（少了反向那一半，「版本地图」就成了可以随便写的地方）：

  · **正向（漏报）**：上游有、手册没点名 → rc=1。**读者撞得到、手册没提。**
  · **反向（幻觉）**：小节里点了名、上游没有这个版本 → rc=1。**读者按它去找会找不到。**

**为什么是新闸，而不是把闸 32 往上延伸一格——量过等价，不是假定（纪律 250）**：
闸 32 `verify-version-coverage.py` 问的是「**基线及更早**的版本里，改了 `web/src`
用户可见中文字面量的那些，是否列进了 README 的增量清单」。三条实测差异：

  1. **闸 32 的 tag 查询在跨大版本后结构上够不着**。它按 `series = "v%d.%d.*" % (base[0], base[1])`
     取 tag，基线是 v1.6.22 → 查 `v1.6.*`。实测 `git tag -l "v1.6.*"` 返回 24 个 tag
     （含 v1.6.23），`git tag -l "v1.7.*"` 返回 3 个（v1.7.1 / 7.2 / 7.3）——
     **`v1.7.*` 一个都不在闸 32 的候选集里**。而且闸 32 另有 `if _v(cur_t) > base: break`，
     连同系列的 v1.6.23 也会被跳过。**这不是「调一下参数」能接上的，是两个问题。**
  2. **代理量纲不同**。闸 32 的代理是「`web/src` 里中文**字符串字面量**的增减条数」，
     而基线之后的变更主体是**新增整块功能**（画布助手、引导式接入），
     **它们的字面量增减不集中在已核过的那几条线上**，拿老代理去量会既漏又误。
  3. **问题的方向不同**。闸 32 问「**我声称核过的部分**，有没有漏讲」；
     本闸问「**我没声称核过的部分**，有没有说清楚」。**前者默认读者停在基线上，
     后者默认读者在基线之后**——而基线声明里那句话恰恰假设了后者。

**为什么用 `CHANGELOG.md` 当事实源，而不是 tag 之间的 diff**：
  · CHANGELOG 是**上游自己对「什么变了」的陈述**，一份带结构的文档，
    读它不需要在 1263 个文件里猜哪些是用户可见的；
  · 而闸 32 那条 diff 路**已经证明过它的代价**：v1.6.18 / v1.6.20 的字面量增减是 0，
    闸 32 只能推出「读者不必知道」——**而读者无从分辨「这版没什么」和「没人查过」**
    （闸 32 自己的文件头就这么写着）。**那个问题在基线之后更严重**：
    4 个发布段落、124 条条目，逐个 diff 分类既慢又要人判断；
  · CHANGELOG 顺带修掉闸 32 那个「tag 序列有缺口」的问题：
    上游**没有 v1.6.12 这个 tag**，闸 32 得靠 `cv[2] - pv[2] > 1` 点出归属偏移，
    **而 CHANGELOG 里 `## v1.6.12` 是一个独立段落，没有偏移这回事**。

**`## Unreleased` 为什么不判**：它还没发布，**读者跑不到**——
手册没法写一个读者遇不上的版本的行为。**但它必须被看见**：
本闸每次都数出它有几条并打印，理由是「上游正在攒的东西，你迟早要撞上」。
**判成失败会让这道闸变成一个无法满足的订阅**（上游每个开发日都有 Unreleased）。

**rc=0 在「无事可判」时的含义要说清楚**：如果上游所有发布段落都不新于基线
（将来手册追上去了就是这个局面），本闸打印「上游没有比基线更晚的发布版本」并 rc=0。
**这不是「读空了也算通过」**：源码读到了、版本集合非空、结论就是那个空集。
**两种「空」必须分开**（纪律 101）：
「**读不到** CHANGELOG」是 rc=2，「**读到 CHANGELOG 且基线之后为空**」是 rc=0。

**覆盖不到什么，必须说在前面**：
  · **只要求「点名 + 一句说明」，不核那句说明对不对。**
    判据读得到 CHANGELOG 的原文，但**把中文条目译回「手册该写什么」需要判断**，
    那不是机械判据能干的。**本闸过的是「读者有机会顺着版本号找到这次改了什么」，
    不是「手册讲对了」**——与闸 32 同一口径，那道闸也只过前者；
  · **不要求写进正文任务页**。基线之后的那些能力（画布助手、引导式接入）**在本手册里
    确实一个章节都没有**，而这是**有意为之**：
    手册正文是逐条核到 v1.6.22 的，往里塞没做过运行时取证的内容，
    就是把「已实现」当成「已验证」（纪律 60）。**本闸只要求手册说清这个边界在哪**，
    不要求它假装覆盖了边界之外；
  · **只认 `origin/main` 上的 CHANGELOG**。本地克隆没 fetch 过就是 rc=2，
    **绝不静悄悄退回 `HEAD`**（`baseline.py` 对基线提交也是这个口径）——
    拿一份旧的 CHANGELOG 算出「上游没有新版本」并报绿，
    **是本闸最坏的一种失败形态**：它会让手册的落点声明看起来比实际更完整。

退出码：0 基线之后的每个发布版本都已被点名并说明；1 有版本漏点名，或点名了一个上游没有的版本；2 未能核对。
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from headingkey import atx_level                                    # noqa: E402
from baseline import declared_baseline, BaselineError, baseline_guard   # noqa: E402
from baseline import announce_fallback                             # noqa: E402
from baseline import SRC as _BEEFSRC                                # noqa: E402

ROOT = os.path.dirname(HERE)
REFERENCE = os.path.join(ROOT, "20-reference.md")

#: **闸门真正读的那一份上游检出**，由 `baseline.py` 统一解析（纪律 274：一份事实一份实现）。
#: 本模块自己**不查 `BEEFTV_SRC`、不建候选表**——`[兜底]` 提示由 `announce_fallback()` /
#: `@baseline_guard` 负责打，本闸一个字都不重复。
SRC = _BEEFSRC

#: 落点小节的锚点。**按标题文字认，不写死级别也不写死位置**——
#: 闸 32 的 `declared_screenshot_version()` 早就踩过「写死 `### 取证基线` 让一次纯结构修正
#: 打挂所有读基线的闸」（Batch 232），而 `baseline.py` 里那份实现连注释都写着
#: 「按标题文字定位，不认死级别」是那次的结论。**同一份事实不许出现第二种认法**（纪律 274）。
LANDMARK_KEY = "基线之后"

#: 版本号的完整形态。
#:
#: **Batch 272 订正**：这一行原先带着一句「**带负向前瞻是必须的**：`v1.6.2` 是 `v1.6.22`
#: 的前缀，而基线恰好就是 v1.6.22——**一个没加边界的匹配会让基线版本自己满足所有要求**」。
#: **那句话是错的**，而且它是照着「一处下标错可以被讲成一个完整的机制」那个形态写的
#: （纪律 306 推论五、纪律 307 推论一）：**一个听起来完整、实际上站不住的解释，
#: 比一处 plainly 的 bug 更贵**——它会让人去改别的东西。
#:
#: **实测（Batch 272，写完判据后当场量的）**：把 `(?![\d.])` 摘掉之后，
#: 在**真树落点小节枚举出的 5 个版本号**上，以及在
#: `v1.6.22` / `v1.6.2` / `v1.6.23` / `v1.7.1` / `v1.7.10` / `v1.7.1beta` 六种输入上，
#: **两条正则的枚举结果逐字相同**。原因有两条，**都不是边界**：
#:   ① **`\d+` 是贪婪的**——在 `v1.6.22` 上它吃掉的是 `22` 而不是 `2`，
#:      **截断压根不会发生**；
#:   ② **本闸从不做「拿版本号当字面子串去搜一个长字符串」**——
#:      那是**只有前缀才会咬人**的用法，而这里一律是 `finditer` 枚举 + 元组比大小。
#: 所以前瞻留着，但**它的身份要写对：它是一条防御，而今天量不到它起作用**。
#: **「判据里有一段今天不起作用的代码」本身不是缺陷，
#: 把它写成「必需」才是缺陷**（纪律 307 推论一）。
VER_RE = re.compile(r"v?(\d+\.\d+\.\d+)(?![\d.])", re.I)

#: 列表项：`- **v1.7.3** 说明文字`。**要求它是列表项**，而不是正文里顺口提到一次版本号——
#: 后者正是纪律 166 点名的那个形态（「某处提到过这个版本」≠「读者能顺着找到这次改了什么」）。
ENTRY_RE = re.compile(
    r"^[ \t]*[-*+][ \t]+\**[ \t]*(v?\d+\.\d+\.\d+)\**[ \t]*[：:]?[ \t]*(.*)$", re.I)

#: 说明里不算内容的字符。**去掉的全是排版件**（强调、反引号、括号、连字符、竖线），
#: **不碰汉字**——否则「画布助手」会被算成 2 个字。
_DESC_STRIP = re.compile(r"[\s*`\[\]()（）「」『』“”\"'，。、：；？！…—–·\-_/\\|~^+<>]")

#: 说明至少要有这么多**非排版字符**。**6 是量出来的**：本批写的四条真说明里
#: 最短的一条是 6 个字（「本地凭据加密」那类），
#: 而占位形态实测都 ≤ 4（`—` / `同上` / `TBD` / `待补` / `N/A` / `TODO`）。
MIN_DESC_CHARS = 6
#: 且至少要有这么多汉字。**光数字符拦不住 `MCP setup` 与 `TBD`**——
#: 前者 8 个字符却零汉字，后者只有 3 个却全是 ASCII。**两个下界量的是两件事。**
MIN_DESC_CJK = 4

CJK_RE = re.compile("[一-鿿]")


def _v(text):
    m = VER_RE.search(text)
    return tuple(int(x) for x in m.group(1).split(".")) if m else None


def _fmt(v):
    return "v%d.%d.%d" % v


def changelog_ref():
    """本闸读哪一份 CHANGELOG。**拿不到就返回 None，调用方报 rc=2。**

    **只认 `origin/main`，不退回 `HEAD`**：闸问的是「**读者现在能撞到什么**」，
    而 `HEAD` 是一份可能停在几个月前的检出——
    拿它算出「上游没有新版本」会让落点声明显得比实际更完整，
    **而这正是本闸要防的那件事本身**。
    """
    if SRC is None:
        return None
    r = subprocess.run(["git", "-C", SRC, "rev-parse", "--verify", "--quiet",
                        "origin/main^{commit}"], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return r.stdout.strip()


def read_changelog(src, ref):
    """返回 (CHANGELOG 全文, 是否拿到)。"""
    r = subprocess.run(["git", "-C", src, "show", f"{ref}:CHANGELOG.md"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None, False
    return r.stdout, True


def changelog_sections(text):
    """把 CHANGELOG 拆成「版本 → 该段落全文」与「Unreleased 的条目数」。

    **锚在 `^## ` 行首而不是全文搜版本号**——理由与 `baseline.py` 相同：
    条目正文里也会出现版本号（实测 v1.6.22 那段里就有），
    全文搜会把「正文提到 v1.6.12」当成「存在 v1.6.12 这个发布段落」。
    **Unreleased 必须整段收完再数，而不能像第一版那样在遇到标题的那一行就地数**——
    第一版数的是**标题之前**那份缓冲区（实测是文件头那 4 行说明文字），
    于是 `unreleased` 恒为 0、**那条提示一次都没打印过**。
    **它不会让本闸变红**（Unreleased 本来就不参与判定），
    **所以这一段坏掉是彻底安静的**——「一个不参与判定的东西坏了」没有任何症状可循，
    只能靠一条把它钉住的探针（见 `main` 里的自检三）。
    """
    bodies, cur = [], ("other", None, [])
    for line in text.split("\n"):
        m = re.match(r"^##[ \t]+(v?\d+\.\d+\.\d+)[ \t]*$", line, re.I)
        m_un = re.match(r"^##[ \t]+Unreleased[ \t]*$", line)
        if m:
            bodies.append(cur)
            cur = ("version", m.group(1), [])
            continue
        if m_un:
            bodies.append(cur)
            cur = ("unreleased", None, [])
            continue
        if re.match(r"^##[ \t]", line):
            # 别的 `## ` 段（例如 `## [1.0.0] - ...` 那种别的格式）——结束当前段落，不硬认。
            bodies.append(cur)
            cur = ("other", None, [])
            continue
        cur[2].append(line)
    bodies.append(cur)

    versions, unreleased = [], 0
    for kind, raw, lines in bodies:
        joined = "\n".join(lines)
        if kind == "version":
            v = _v(raw)
            if v is not None:
                versions.append((v, joined))
        elif kind == "unreleased":
            unreleased = len(re.findall(r"^[ \t]*[-*+][ \t]+\S", joined, re.M))
    return versions, unreleased


def landmark_section(text):
    """`20-reference.md` 里第一个标题文字含「基线之后」的小节正文。返回 (正文, 报错)。

    **用 `headingkey.atx_level` 逐行走**（纪律 274 推论一：「是不是标题」只有一份实现），
    **小节到下一个标题为止，不管它是什么级别**——
    这里刻意与 `baseline.py` 的「到同级或更浅的标题为止」不同：
    落点小节是 `###`，而它下面**本来就不该再有同级或更浅的标题**，
    一旦有，那是结构问题，归闸 26 管，**不该让本闸顺手把它截短再得出「某版本没提到」的结论**。
    """
    off = 0
    for line in text.split("\n"):
        lv = atx_level(line)
        if lv is not None and LANDMARK_KEY in line:
            body, off2 = [], off + len(line) + 1
            for nxt in text[off2:].split("\n"):
                if atx_level(nxt) is not None:
                    break
                body.append(nxt)
                off2 += len(nxt) + 1
            return "\n".join(body), None
        off += len(line) + 1
    return None, "20-reference.md 里找不到标题含「%s」的小节" % LANDMARK_KEY


def parse_entries(body):
    """落点小节里的列表项。返回 [(版本元组, 原始版本串, 说明原文)]。"""
    out = []
    for line in body.split("\n"):
        m = ENTRY_RE.match(line)
        if m:
            out.append((_v(m.group(1)), m.group(1), m.group(2)))
    return out


def desc_ok(desc):
    """一句说明是不是「实质的」。返回 (是否够, 汉字数, 非排版字符数)。"""
    flat = _DESC_STRIP.sub("", desc)
    n_cjk = len(CJK_RE.findall(flat))
    return len(flat) >= MIN_DESC_CHARS and n_cjk >= MIN_DESC_CJK, n_cjk, len(flat)


def named_versions(body):
    """小节里出现过的**全部**版本号（不限于列表项）——反向那一半要的是这个。"""
    return [(m.group(1), m.group(0)) for m in VER_RE.finditer(body)]


@baseline_guard
def main():
    #: **Batch 274 补上的一行**——`selftest-zero-input.py` 方向三之三报出来的：
    #: **本闸 import 了 `baseline`/`beefsrc` 去解析上游，于是 `BEEFTV_SRC` 指向非仓时
    #: 它会静悄悄回落到候选表里的真仓、然后照常报绿。**
    #: **而「静默降级比直接失败更坏，因为它还报绿」正是纪律 172 整条在说的**。
    #: **它是 Batch 272 建的闸、而这个缺陷躺了两个批次**——
    #: **因为报出它的那份反验在 SLOW 里，构建从不跑它**（纪律 309）。
    #: **「本闸读的是哪一份上游」必须留在它的输出里**，
    #: 否则「核过」与「核的是你指定的那一份」在结果里长得一模一样。
    announce_fallback()
    if SRC is None:
        print("[skip] 未找到 BeefTV 源码 %s，落点声明核对本轮未能进行" % SRC)
        return 2
    try:
        base_ver, _commit = declared_baseline()
    except BaselineError as exc:
        print("[skip] %s，落点声明核对本轮未能进行" % exc)
        return 2
    base = _v(base_ver)
    if base is None:
        print("[skip] 取证基线 %r 解析不出主.次.修订，本轮未能核对" % base_ver)
        return 2

    ref = changelog_ref()
    if ref is None:
        print("[skip] 在 %s 拿不到 origin/main——本地克隆可能没 fetch 过，"
              "**本轮未能核对，不是「上游没有新版本」**" % SRC)
        return 2
    text, ok = read_changelog(SRC, ref)
    if not ok:
        print("[skip] 在 %s 读不到 origin/main 的 CHANGELOG.md，本轮未能核对" % SRC)
        return 2
    sections, unreleased = changelog_sections(text)
    if not sections:
        print("[skip] CHANGELOG.md 里一个 `## vX.Y.Z` 段落都没解析到——"
              "**判据的段落正则可能已失效**，本轮未能核对")
        return 2

    # ---- 自检一：判据的两个下界必须真的能分开「实质说明」与「占位」，否则本闸恒真
    for stub, why in (("- **v1.7.3**", "只有版本号"),
                      ("- **v1.7.3** —", "一个破折号"),
                      ("- **v1.7.3** TBD", "ASCII 占位"),
                      ("- **v1.7.3** 同上", "两个字的中文占位"),
                      ("- **v1.7.3** MCP setup", "8 个字符却零汉字")):
        if desc_ok(ENTRY_RE.match(stub).group(2))[0]:
            print("[skip] 自检探针「%s」被当成实质说明（%s）——**判据的说明下界已失效**，"
                  "本轮未能核对" % (stub, why))
            return 2
    if not desc_ok(ENTRY_RE.match("- **v1.7.3** 本地凭据加密与设置备份").group(2))[0]:
        print("[skip] 自检探针「本地凭据加密」那一句被当成占位——**判据的说明下界过严**，"
              "本轮未能核对")
        return 2
    # ---- 自检二：一个版本号必须被枚举成**一个** token，不能被拆开。
    # **这一条量得到它起作用**：真树落点小节里同时有 v1.6.22 / v1.6.23 / v1.7.1 / v1.7.2 /
    # v1.7.3 五个，而 `v1.6.2` 是 `v1.6.22` 与 `v1.6.23` 两者的**共同前缀**——
    # 一旦枚举被拆开，反向判据（幻觉那一支）拿到的就不是版本元组。
    # **原先这里还有一条「基线是 v1.6.22、而 v1.6.2 是它的前缀，所以边界必需」的探针，
    # 本批已按实测删掉**——那一条今天恒不成立（见 `VER_RE` 上方的订正），
    # **留着一条恒不成立的探针比没有探针更坏**：它给人「这一层被守着」的感觉。
    if [m.group(0) for m in VER_RE.finditer("v1.6.22")] != ["v1.6.22"]:
        print("[skip] 自检探针「v1.6.22」被拆成了多个版本号——**版本号枚举已失效**，"
              "本轮未能核对")
        return 2
    if [m.group(0) for m in VER_RE.finditer("v1.6.22 与 v1.6.23")] != ["v1.6.22", "v1.6.23"]:
        print("[skip] 自检探针：两个相邻版本号被合并或漏数——**版本号枚举已失效**，"
              "本轮未能核对")
        return 2
    # ---- 自检三：`## Unreleased` 那一段必须真的被数到条目。
    # **Batch 272 实测踩到的**：第一版在遇到标题的那一行就地数缓冲区，
    # 数到的是**文件头那 4 行说明文字**，`unreleased` 恒为 0、**那条提示一次都没打印过**。
    # **它坏掉时本闸不可能变红**（Unreleased 压根不参与判定），
    # **所以一个不参与判定的东西坏了，没有任何症状可循**——只能靠探针。
    _pv, _pu = changelog_sections(
        "# Changelog\n\n说明文字。\n\n## Unreleased\n\n- 一条\n- 两条\n\n## v1.0.0\n\n- 别的\n")
    if _pu != 2 or sorted(v for v, _ in _pv) != [(1, 0, 0)]:
        print("[skip] 自检探针：CHANGELOG 的段落解析或 Unreleased 计数已失效，"
              "本轮未能核对（**探针读到 %d 条 Unreleased、%d 个版本段落**）"
              % (_pu, len(_pv)))
        return 2
    # ---- 自检四：正文里顺口提到一次版本号**不算数**（纪律 166）。
    # 那是闸 32 第一版判据的形态：「某处提到过这个版本」不等于「读者能顺着找到这次改了什么」。
    if ENTRY_RE.match("本手册的截图也适用于 v1.7.3 那一版的界面。"):
        print("[skip] 自检探针：一句正文里的版本号被当成了列表项——"
              "**判据已经退回「某处提到过就算覆盖」那一版**，本轮未能核对")
        return 2

    if _v(base_ver) not in {v for v, _ in sections}:
        print("[skip] CHANGELOG 里没有基线版本 %s 这一段——"
              "**基线声明与上游自己的发布记录对不上**，本轮未能核对" % base_ver)
        return 2

    after = sorted(v for v, _ in sections if v > base)
    if unreleased:
        print("提示：上游的 `## Unreleased` 段里还有 %d 条，**本闸不判它**——"
              "它还没发布、读者跑不到，而判成失败会让这道闸变成一个无法满足的订阅；"
              "**但你迟早会撞上其中一部分**" % unreleased)

    try:
        with open(REFERENCE, encoding="utf-8") as fh:
            ref_text = fh.read()
    except OSError as exc:
        print("[skip] 读不到 20-reference.md：%s，本轮未能核对" % exc)
        return 2
    body, sec_err = landmark_section(ref_text)
    if body is None:
        # **小节整个不在场**：不报 rc=2。**「没有落点声明」是一个可以判定的事实**
        # （漏报全部），不是「核不了」——rc=2 是留给「读不到」的（纪律 101）。
        # 下面那句会把每个基线之后的版本逐个报成 missing，**不需要在这里提前返回**。
        print("提示：%s——**本闸不因此返回 rc=2**，"
              "「没有落点声明」是可以判定的事实（下面的报告里会把它算成逐个漏报）" % sec_err)
        body = ""

    entries = parse_entries(body)
    covered = {}
    for v, raw, desc in entries:
        if v in after and v not in covered:
            covered[v] = (raw, desc)

    missing, thin = [], []
    for v in after:
        if v not in covered:
            missing.append(v)
        elif not desc_ok(covered[v][1])[0]:
            thin.append((v, covered[v][1]))

    known = {v for v, _ in sections}
    phantom = sorted({_v(raw) for raw, _ in named_versions(body or "")
                      if _v(raw) is not None and _v(raw) not in known})

    # **「无事可判」这一支必须排在 phantom 之后**——
    # **初版把它写在这条判断之前，于是 `after` 为空时直接 return 0、反向检查整个被跳过**。
    # 实测触发条件：把基线改成上游最新的 v1.7.3（`after` 变空），
    # **而小节里留着一条上游没有的版本号 → 闸会报 rc=0 通过**。
    # **今天触发不了**（真树还有 4 个基线之后的版本），
    # **而「今天触发不了」正是潜伏的假阴性最常见的形态**：
    # 它会在手册追平上游的那一天才开始发作，而那一天没人会去测它（纪律 307 推论一）。
    if not after and not phantom:
        print("落点声明核对通过：上游 %s 之后的 CHANGELOG 里**没有比基线 %s 更晚的发布版本**"
              "（已读到 %d 个发布段落）——**这是「读到且结论为空」，不是「读空了也算通过」**"
              % (ref[:8], base_ver, len(sections)))
        return 0

    if missing or thin or phantom:
        if not after:
            print("落点声明核对：基线 %s **已经是上游最新的发布版本**（已读到 %d 个段落），"
                  "本闸本无漏报可查——**但下面这条反向诊断是独立的**" % (base_ver, len(sections)))
        else:
            print("落点声明核对：基线 %s 之后有 %d 个发布版本，%d 个已被点名"
                  % (base_ver, len(after), len(after) - len(missing)))
        for v in missing:
            print("  · %s 在上游 CHANGELOG 里，**而「基线之后」小节没点名它**"
                  "——读者跑得到、手册没提" % _fmt(v))
        for v, d in thin:
            print("  · %s 点名了，但那句说明不足以让读者知道它改了什么：%r"
                  "（要 ≥%d 个非排版字符且 ≥%d 个汉字）"
                  % (_fmt(v), d.strip(), MIN_DESC_CHARS, MIN_DESC_CJK))
        for v in phantom:
            print("  · 「基线之后」小节点了名 %s，**而上游 CHANGELOG 里没有这个版本**"
                  "——读者按它去找会找不到" % _fmt(v))
        print("→ 在 `20-reference.md` 的「基线之后」小节里，一条一行补上："
              "`- **vX.Y.Z** 这一版改了什么、对读者意味着什么`；"
              "**如果读者确实不需要知道，也要写一句说明**——"
              "**读者分不清「这版没什么」和「没人查过」**")
        return 1

    print("落点声明核对通过：基线 %s 之后的 %d 个发布版本（%s）在「基线之后」小节里"
          "逐个被点名并带实质说明，**且小节里没有上游不存在的版本号**"
          % (base_ver, len(after),
             "、".join(_fmt(v) for v in after)))
    print("  **本闸只过「读者有机会顺着版本号找到这次改了什么」，不过「手册讲对了」**"
          "——那句说明的内容不在机械判据的射程内")
    return 0


if __name__ == "__main__":
    sys.exit(main())
