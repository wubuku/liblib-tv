#!/usr/bin/env python3
"""探针契约一致性校验（第十八道门禁，M144 新增）。

**背景（M144 查的是一次真实的漂移，不是一次假想故障）**：

同一批探针教训在项目里被写进了**四个地方**——`SOURCE_OBSERVATIONS.md` 账本、
两个 `scripts/probe-*.js` 的文件头、`PUBLISH.md` 的「跑探针前必读」小节。
实测每条纪律散布在 3 到 5 个文件里（`elementFromPoint` 在 `AUDIT.md` 里出现 13 次）。
**副本一多就必然漂移**，而 M143 已经查出一处**读者实际查不到内容**的漂移：
`PUBLISH.md` 的纪律表只写「白名单四项」，**却没列出是哪四项**——
维护者在这张表里查不到具体清单，必须去翻 `.js` 源码才看得见。

**判据要放在「会被读到的地方」，而不只是「被写下的地方」**（M143）。
但光靠人记必然再漂，所以本门禁把**能被机械判定的那部分**钉住。

**本门禁只做一件事，且只做能机械判定的部分**：读源码里的 `DESTRUCTIVE` 集合，
断言 `PUBLISH.md` 的纪律表里**逐项列出了同样的名字**。反过来不查——
文档可以写得比源码细（多写背景、少写实现），但**不能漏项**。

**为什么不做双向全等**：文档的职责是「让人看懂」，源码的职责是「让机器跑」，
两者本就该有详略。全等会把文档逼成源码的复述，反而更难读。
**只守住「文档不能漏掉源码里的硬约束」这一条**，漏了就是读者拿不到。

**它的边界（必须如实说清）**：只校验「不可逆按钮白名单」这一项常量。
其余纪律是自然语言，**无法机械判定**，本门禁不碰——
把它们也算进来只会做出一个「全绿但什么都没查」的假门禁，
而那正是 M140 刚查出的那类害处。

用法：

    python3 scripts/check-probe-contracts.py .
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

DESTRUCTIVE_RE = re.compile(
    r"const\s+DESTRUCTIVE\s*=\s*new Set\(\[(?P<body>.*?)\]\)", re.S
)
STRING_RE = re.compile(r"'([^']+)'|\"([^\"]+)\"")
HEADING = "八条判据纪律"

# M178：第九条纪律的锚点小节，以及标记表的两个方向。
MARKER_HEADING = "第九条：定位靠"
MARKER_RE = re.compile(r"data-[a-z][a-z0-9-]*")

# 与 check-ledger-pin.py 同一处应用仓副本。**本机没有就跳过**——
# 手册仓会被 clone 到别的机器，那台机器上不会有一份应用源码，
# 要求「必须查到应用源码」会让门禁在别的机器上直接失败。
# 「跳过」与「缺失」必须分清（M151 已订正过这条）。
APP_REPO = Path("/Users/yangjiefeng/Documents/AICoderTudou/TDCanvas")


def strip_js_comments(text: str) -> str:
    """去掉 /* */ 块注释与「整行以 // 开头」的注释。

    **只去整行 // 注释、不做行内截断**，是因为探针里常有 `http://…` 这样的
    字符串，按 `//` 截到行尾会把 URL 砍成 `http:`。判据只找按钮文案的真前缀，
    残留的 URL 片段不影响结论。

    ★ **M242：这段原先是 `main()` 里的闭包**，新判据要用它，必须提到模块级。
    **「剥注释」不是可选步骤**——`probe-toolbar-states.js` 的文件头就有一段
    注释在讲 `DESTRUCTIVE` 是一道硬闸，**不剥就会把注释里的字样当成真代码**
    （M194 同族：不剥注释就扫源码，判据必然出假阳性）。
    """
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("//")
    )


# ★★ **M242 新增：不可逆按钮白名单的「运行时改写」判据。**
#
# 上面 `destructive_items()` 是**用正则读源码文本里的 `new Set([...])` 字面量**，
# 而「白名单」是本仓库最要命的一份名单——**它是探针唯一的硬闸**，
# 命中就跳过那个按钮；白名单空了，探针就会去点真正的删除。
#
# ★ **阳性对照（M242 实测，两个独立读数当场对不上）**：
#   在 `probe-toolbar-states.js` 声明之后加一行 `DESTRUCTIVE.clear();`
#   - 门禁的读数（正则读源码）：仍是 6 项 → **报「白名单 6 项与文档一致」**；
#   - `node` 真跑一遍算出来的：**`[]`（空）**。
#   **而 `check-probe-contracts.py` 全程 exit=0。**
#   同理 `DESTRUCTIVE.delete('删除全部')` 会让硬闸少一道、`.add(...)` 会多一道，
#   **三个读数两两不一致，而门禁只看得见其中一个。**
#
# ★ **所以加两条判据**：
#   ① **静态**：剥掉注释后，`DESTRUCTIVE` 不许作为 `.add/.delete/.clear/...`
#      的接收者出现，也不许被重新赋值。**这条不依赖任何外部工具。**
#   ② **真跑**：把「声明 + 随后的 Set 方法调用」原样交给 `node` 求值，
#      **与正则读数对账**。①只能拦住已知写法，②能拦住任何写法
#      （包括 `for` 循环里 `.add`、`.filter` 后重建等）。
MUTATOR_RE = re.compile(r"\bDESTRUCTIVE\s*\.\s*\w+\s*\(")
# ★ **裸赋值也算**（`DESTRUCTIVE = new Set([...])`，没有 const/let/var）：
#   第一版只认带声明关键字的，于是裸赋值**两条判据都看不见**——
#   而那正是最直接的「把白名单换掉」的手法。
REASSIGN_RE = re.compile(r"^\s*(?:(?:const|let|var)\s+)?DESTRUCTIVE\s*=(?!=)", re.M)


def destructive_mutations(script: Path) -> list[str]:
    """返回「声明之后对 DESTRUCTIVE 的运行时改写」清单（判据 ①）。"""
    body = strip_js_comments(script.read_text(encoding="utf-8"))
    decl = DESTRUCTIVE_RE.search(body)
    if not decl:
        return []
    after = body[decl.end():]
    hits = [f"第 {i} 行 `{m.group(0).strip()}`"
            for i, line in enumerate(after.splitlines(), 1)
            for m in [MUTATOR_RE.search(line)] if m]
    # 重新赋值只认「声明之后」的；第一处是合法的初始声明
    for m in REASSIGN_RE.finditer(after):
        hits.append(f"声明之后又出现 `{m.group(0).strip()}`")
    return hits


def destructive_runtime_items(script: Path) -> tuple[list[str] | None, str]:
    """用 `node` 真算一遍 DESTRUCTIVE（判据 ②）。返回 (集合, 说明)。

    ★ **只把「声明 + 随后的 Set 方法调用」送进 node**，不执行整个探针文件——
    **探针文件顶层就会 require playwright 并真的去开浏览器**。
    送到 node 里的片段被改名成局部 `D`，因此不会碰真实全局。
    ★ **求值不出来就返回 `None` 并说明原因，由调用方判失败**——
    **「算不出来」绝不能当成「算出来是空的」**（F42）。
    """
    text = script.read_text(encoding="utf-8")
    decl = DESTRUCTIVE_RE.search(text)
    if not decl:
        return None, "读不出 DESTRUCTIVE 声明"
    muts = re.findall(r"DESTRUCTIVE\s*\.\s*\w+\s*\([^)]*\)\s*;", text)
    # ★ 裸赋值同样要送进 node（见 REASSIGN_RE 上方注释）
    body = text[decl.end():]
    reassigns = ["DESTRUCTIVE = " + m.group(1)
                 for m in re.finditer(r"DESTRUCTIVE\s*=\s*(new Set\(.*?\)|[^;\n]+);", body, re.S)]
    js = decl.group(0).replace("const DESTRUCTIVE", "let D") + "\n"
    js += "\n".join(m.replace("DESTRUCTIVE", "D") for m in muts) + "\n"
    js += "\n".join(m.replace("DESTRUCTIVE", "D", 1) for m in reassigns)
    js += "\nconsole.log(JSON.stringify([...D].sort()));"
    try:
        done = subprocess.run(
            ["node", "-e", js], capture_output=True, text=True, timeout=20,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return None, f"调不动 node：{exc}"
    if done.returncode != 0:
        first = (done.stderr.strip().splitlines() or ["(无 stderr)"])[0]
        return None, f"node 求值失败：{first[:80]}"
    try:
        return sorted(json.loads(done.stdout.strip())), "ok"
    except (ValueError, TypeError) as exc:
        return None, f"node 输出不是 JSON：{exc}"


def destructive_items(script: Path) -> list[str]:
    """从探针源码里解析出不可逆按钮白名单。

    ★ **M242 提醒：这是「正则读源码字面量」的读数，只在
    「白名单确实是字面量写的」时等于真实值。**
    运行时改写由 `destructive_mutations`（判据 ①）与
    `destructive_runtime_items`（判据 ②）各守一半，三条合起来才等于真相。
    """
    match = DESTRUCTIVE_RE.search(script.read_text(encoding="utf-8"))
    if not match:
        raise SystemExit(
            f"[探针契约] 读不出 DESTRUCTIVE 集合：{script}\n"
            "  若该常量已改名或删除，请同步修改本门禁，不要让它静默失效。"
        )
    return [a or b for a, b in STRING_RE.findall(match.group("body"))]


def discipline_section(publish: Path) -> str:
    text = publish.read_text(encoding="utf-8")
    start = text.find(HEADING)
    if start < 0:
        raise SystemExit(
            f"[探针契约] PUBLISH.md 里找不到「{HEADING}」小节。\n"
            "  本门禁守的就是这张表；它被改名或删除时请同步修改本门禁。"
        )
    end = text.find("\n### ", start)
    return text[start : end if end > 0 else len(text)]


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    script = root / "scripts/probe-toolbar-states.js"
    publish = root / "PUBLISH.md"
    for path in (script, publish):
        if not path.exists():
            print(f"[探针契约] 找不到文件：{path.relative_to(root)}")
            return 1

    items = destructive_items(script)
    if not items:
        print("[探针契约] DESTRUCTIVE 解析出 0 项 —— 解析多半失效了，拒绝放行。")
        return 1
    # ★★ M242 判据 ①：白名单不许在运行时被改写
    muts = destructive_mutations(script)
    if muts:
        print(
            f"  [探针契约] {script.relative_to(root)} 的 DESTRUCTIVE 在声明之后被改写："
            + "；".join(muts)
        )
        print(
            "    **这份名单是探针唯一的硬闸，命中就跳过那个按钮。**"
            "本门禁是用正则读源码里的 `new Set([...])` 字面量，"
            "运行时改出来的那几项它一个字都看不见——"
            "而 `DESTRUCTIVE.clear()` 会让硬闸**完全清空**，"
            "探针就会去点真正的删除，本门禁却仍报「白名单 6 项与文档一致」。"
        )
        return 1

    # ★★ M242 判据 ②：用 node 真算一遍，与正则读数对账
    runtime, why = destructive_runtime_items(script)
    if runtime is None:
        print(f"  [探针契约] **没查**：无法求值 DESTRUCTIVE 的真实内容（{why}）。")
        print("    这是全库最要命的一份名单（探针唯一的硬闸），"
              "算不出来就不能当「没问题」放行——请装好 node 后重跑。")
        return 1
    if runtime != sorted(items):
        print(
            f"  [探针契约] **两个读数不一致**：正则读源码得 {len(items)} 项，"
            f"node 真跑一遍得 {len(runtime)} 项。"
        )
        only_src = sorted(set(items) - set(runtime))
        only_run = sorted(set(runtime) - set(items))
        print(f"    只在源码字面量里：{only_src or '无'}")
        print(f"    只在运行时才有：{only_run or '无'}")
        print("    两者都是**不可逆按钮**，差的那几项决定了探针到底会点哪些按钮。")
        return 1

    section = discipline_section(publish)

    missing = [name for name in items if name not in section]
    if missing:
        print(
            f"  [探针契约] PUBLISH.md 的「{HEADING}」漏列了不可逆按钮："
            + "、".join(missing)
        )
        print(
            f"    源码 {script.relative_to(root)} 的 DESTRUCTIVE 共 {len(items)} 项，"
            "文档必须逐项列出——"
            "读者查手册查不到清单，就等于没有这道闸。"
        )
        return 1

    # ---------- 第二项：定位标记表双向核对（M178 新增） ----------
    #
    # M177 连续栽在「找错元素」上：按 class 找 data-* 承载的菜单，一个都找不到；
    # 按「有贝塞尔曲线」抓 path，把 39 个 lucide 图标全抓了进来。
    # 两件事的共同点是**用「看起来像」的特征去定位**，而不是用语义标记。
    # 于是把标记表补进第九条纪律，并让本门禁双向守住它：
    #   正向 —— 探针用到的每个 data-* 必须在表里（防「探针偷偷用了新标记」）
    #   反向 —— 表里的每个必须真在应用源码里存在（防「表过期」）
    # 少任何一向都是**假门禁**：只有正向，表可以永远空着；只有反向，探针可以随便用。
    marker_section = None
    ms = s_txt = publish.read_text(encoding="utf-8")
    mi = ms.find(MARKER_HEADING)
    if mi < 0:
        print(
            f"  [探针契约] PUBLISH.md 里找不到「{MARKER_HEADING}…」小节。\n"
            "  本门禁守的就是那张定位标记表；它被改名或删除时请同步修改本门禁。"
        )
        return 1
    mj = ms.find("\n### ", mi)
    marker_section = ms[mi : mj if mj > 0 else len(ms)]

    probes = sorted(root.glob("scripts/probe-*.js"))
    used: dict[str, list[str]] = {}
    for pr in probes:
        for m in MARKER_RE.findall(pr.read_text(encoding="utf-8")):
            used.setdefault(m, []).append(pr.name)

    listed = set(MARKER_RE.findall(marker_section))
    missing = sorted(m for m in used if m not in listed)
    if missing:
        print(
            f"  [探针契约] 探针用到的定位标记没进 PUBLISH.md 第九条的表："
            + "、".join(missing)
        )
        print(
            "    用到的标记必须在表里——**读者查不到这张表，等于没有这道闸**。"
            "    补表时顺手确认它在应用源码里真的存在。"
        )
        return 1

    # 反向：表里的必须真存在
    stale: list[str] = []
    if not APP_REPO.exists():
        print(f"  [skip] 本机没有应用仓副本（{APP_REPO}），跳过「标记表是否过期」的反向核对")
    else:
        src = APP_REPO / "web" / "src"
        if not src.is_dir():
            print(f"  [skip] 应用仓里没有 web/src（{src}），跳过反向核对")
        else:
            real: set[str] = set()
            for f in src.rglob("*.ts*"):
                if f.suffix in (".ts", ".tsx"):
                    real.update(MARKER_RE.findall(f.read_text(encoding="utf-8", errors="ignore")))
            stale = sorted(m for m in listed if m not in real)
            if stale:
                print(
                    f"  [探针契约] PUBLISH.md 第九条的表里列了应用源码中**不存在**的标记："
                    + "、".join(stale)
                )
                print("    表过期比表缺失更坏：维护者会照着它去找一个不存在的元素。")
                return 1

    print(
        f"  [ ok ] 定位标记表：探针用到 {len(used)} 个、表里列了 {len(listed)} 个，"
        f"正向无遗漏"
        + ("，反向逐个核对通过" if APP_REPO.exists() and not stale else "（反向已跳过）")
    )

    # ---------- 第三项：危险按钮不许用子串/正则去选（M193 新增） ----------
    #
    # 前两项守的是「哪些按钮危险」与「怎么定位」，
    # **都没管「选中它时用的是全名还是子串」**——而 M192 正是栽在这一条上：
    #   用 `/删除/` 去匹配按钮，先命中了页面上的「删除全部」而不是卡片上的「删除」，
    #   确认弹窗没读就点了「删除」，**两张画布一起没了、不可恢复**。
    # 「删除全部」与「删除」只差两个字，实测按钮列表里前者还排得更前——
    # **子串匹配碰上这种命名，必然先命中更严重的那个。**
    #
    # 判据：对每个危险文案取**长度 ≥2 的真前缀**（前缀本身不是完整文案），
    # 若某个探针在正则字面量或 includes/indexOf 里用了这个前缀，
    # **而该探针里又没出现过完整文案**，判为「模糊选中危险按钮」并报错。
    # **出现完整文案即放行**——那是精确匹配，正是这条纪律要的做法。
    #
    # ★ **扫之前必须先剥注释**（M194 实测的假阳性，M106 的同一个陷阱）：
    #   判据一上线就把我自己的 `probe-node-toolbars.js` 判成违规——
    #   那支探针**根本没选任何删除按钮**，是**文件头的注释在描述这个坑**
    #   （写着「M192 用 `/删除/` 这类子串匹配」）。注释里的话不是选择器。
    #   M106 当年在 `check-publish-sync.py` 上撞过一模一样的坑：
    #   `audit_manual.py` 在 `build-site.sh` 里出现 3 次、**全部在注释里**，
    #   当年的解法就是剥掉整行注释再比对。**同一个坑，换个门禁又踩一次。**
    FUZZY_RES = (
        re.compile(r"/[^/\n]*%s[^/\n]*/"),
        re.compile(r"\.(?:includes|indexOf)\(\s*['\"]%s['\"]"),
    )
    fuzzy_hits: list[str] = []
    for pr in probes:
        body = strip_js_comments(pr.read_text(encoding="utf-8"))
        for label in items:
            if len(label) < 3:
                continue  # 两字文案没有「真前缀」，写了全名就是精确匹配
            for n in range(2, len(label)):
                prefix = label[:n]
                hit = False
                for rx in FUZZY_RES:
                    rx2 = re.compile(rx.pattern % re.escape(prefix))
                    if rx2.search(body) and label not in body:
                        hit = True
                        break
                if hit:
                    fuzzy_hits.append(f"{pr.name}：用「{prefix}」这类子串去选「{label}」")
    if fuzzy_hits:
        print("  [探针契约] 探针用子串/正则去选不可逆按钮：")
        for h in sorted(set(fuzzy_hits)):
            print(f"    - {h}")
        print(
            "    「删除」与「删除全部」只差两个字，而前者排得更前——"
            "**子串匹配碰上这种命名，必然先命中更严重的那个**（M192 因此丢了两张画布）。\n"
            "    改用全名精确匹配（=== \"删除全部\"），或改用 data-* 语义标记定位。"
        )
        return 1

    print(
        f"  [ ok ] 危险按钮选择：{len(probes)} 支探针均未用子串/正则去选 "
        f"{len(items)} 项不可逆按钮"
    )

    # ---------- 第四项：加载 Playwright 的方式必须十支统一，且变量名要写进文档（M239 新增） ----------
    #
    # 前三项守的是「哪些按钮危险」「怎么定位」「怎么选中」，
    # **都没管「探针自己怎么跑起来」**——而这恰恰是最容易悄悄烂掉的一处。
    #
    # ★ **M238 实测**：十支探针当时分三套写法：
    #   6 支读环境变量 PLAYWRIGHT_PATH；2 支读**另一个环境变量名 TD_PW**；
    #   2 支（absolute-coords / copy-title）**完全裸硬编码、连环境变量都没有**。
    #   **后果不是「报错」，而是「10 支里有 4 支在换 node 版本时直接废掉、另 6 支还能跑」**
    #   ——**这是「不一致」最坏的那种形态：它不出错，它只是慢慢变成一半是死的。**
    #   而**一道门禁都不管这件事**（本文件原先只查 DESTRUCTIVE 与定位标记）。
    #
    # ★ **判据只管 PLAYWRIGHT_PATH，不管别的环境变量**：探针里还有
    #   TD_PROBE_PROFILE（换 profile 目录，4 支在用）与 TD_APP（换被测地址，2 支在用），
    #   **它们是「可选覆盖」而不是「必须一致」**——十支不必齐，也**不该**强求齐
    #   （M195：判据必须窄到能全对，误报率过高的判据连分析工具都不该留）。
    #
    # ★ **第二半条判据：变量名必须出现在 PUBLISH.md 里**（M144「判据要放在会被读到的地方」）。
    #   M238 统一完代码之后实测：`PLAYWRIGHT_PATH` 在 PUBLISH.md 里**出现 0 次**——
    #   换 node 版本的人在这一节找不到任何提示。**代码统一了而文档没跟上，等于没统一。**
    #
    # ⚠ **必须先剥注释再判**（M194 实测的同一个假阳性，见上面第三项那段）：
    #   探针的文件头注释里会**提到**别的环境变量名（描述这段历史），
    #   **注释里的话不是选择器**，按 M194 的解法整行剥掉。
    pw_missing: list[str] = []
    pw_hardcoded: list[str] = []
    for pr in probes:
        body = strip_js_comments(pr.read_text(encoding="utf-8"))
        if "process.env.PLAYWRIGHT_PATH" not in body:
            pw_missing.append(pr.name)
        # 剥完注释后仍出现 playwright 的绝对路径 ⇒ 它被写死在代码里
        hard = re.findall(r"['\"](/[^\n'\"]*node_modules/(?:@playwright/)?playwright)['\"]", body)
        if hard and "process.env.PLAYWRIGHT_PATH" not in body:
            pw_hardcoded.append(f"{pr.name}：{hard[0]}")

    if pw_missing or pw_hardcoded:
        print(f"  [探针契约] 探针加载 Playwright 的方式不统一（应为 {len(probes)}/{len(probes)} 支"
              f"读环境变量 PLAYWRIGHT_PATH）：")
        for m in pw_missing:
            print(f"    - {m} 没读 process.env.PLAYWRIGHT_PATH")
        for h in pw_hardcoded:
            print(f"    - {h} 把路径写死在源码里")
        print(
            "    **M238 实测的后果不是「报错」，而是「十支里有几支在换 node 版本时直接废掉、"
            "另几支还能跑」**——它不出错，它只是慢慢变成一半是死的。\n"
            "    改法：const { chromium } = require(process.env.PLAYWRIGHT_PATH || '<包目录>');"
            "（默认值写**包目录**而不是 index.js，换版本时不必猜文件名）。"
        )
        return 1

    # ★ M239 注入 4 + 两次「判据自身失效」的修正：
    #   ① 原先只判「PUBLISH.md 全文出现 PLAYWRIGHT_PATH」，于是把它挪到别的章节也照样放行、
    #      **而输出却宣称「在『跑探针前必读』里查得到」——判据和它自己的报读对不上。**
    #   ② 收紧时我**先错用了上面那个 marker_section**——它是「第九条：定位靠 data-*」，
    #      **不是「跑探针前必读」**，于是正常数据也被判失败。
    #   ③ ★ **第二次错**是我**用子串 `跑探针前必读` 去 find 标题**——
    #      **而我自己刚在门禁表那一行（PUBLISH.md 第 232 行）写了同一句话**，
    #      于是 `find` 命中的是**表格行、不是第 330 行那节的标题**，
    #      **判据安静地判在了错误的那一段上，一声不吭。**
    #   ★ **三次都是同一个病：判据引用的那段区间，和它在报错里说的那段区间，不是同一段。**
    #   **判据必须与报读一致**，否则「通过」这两个字就不代表它声称的那件事。
    #   **而 ③ 正是 M195「判据不够窄」的经典形态**——不是误报率问题，
    #   **是判错了对象还不吭声**：它拿错误的区间判了一遍，然后报「通过」。
    #   ★ **正确做法：锚定完整标题**（`### ★ 跑探针前必读`），**绝不用子串去找小节**——
    #   子串会让你自己写在别处的同一句话劫持这个判据。
    #   这才是 M144 的原话——**判据要放在会被读到的地方**
    #   （全文某个角落提到不算，读者会翻的那一节才算）。
    PROBE_READ_HEADING = "### ★ 跑探针前必读"
    ri = ms.find(PROBE_READ_HEADING)
    if ri < 0:
        print(
            f"  [探针契约] PUBLISH.md 里找不到「{PROBE_READ_HEADING}」那一节。\n"
            "  本门禁守的就是那一节（读者跑探针前会翻的地方）；它被改名时请同步修改本门禁。"
        )
        return 1
    rj = ms.find("\n## ", ri)
    probe_read_section = ms[ri : rj if rj > 0 else len(ms)]

    if "PLAYWRIGHT_PATH" not in probe_read_section:
        print(
            f"  [探针契约] PUBLISH.md 的「{PROBE_READ_HEADING}」一节里查不到 `PLAYWRIGHT_PATH` —— "
            "**代码统一了而读者看不到提示，等于没统一**：换 node 版本的人在这一节找不到任何线索"
            "（M144：判据要放在会被读到的地方；全文别处提到不算，这一节才是读者会翻的地方）。"
        )
        return 1

    print(
        f"  [ ok ] 探针启动方式：{len(probes)}/{len(probes)} 支均读环境变量 PLAYWRIGHT_PATH"
        f"（无裸硬编码），且该变量名在 PUBLISH.md「{PROBE_READ_HEADING}」一节里查得到"
    )

    print(
        f"  [ ok ] 探针契约：不可逆按钮白名单 {len(items)} 项"
        f"（{'、'.join(items)}）与文档一致"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
