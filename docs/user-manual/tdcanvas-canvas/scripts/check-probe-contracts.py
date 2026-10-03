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

import re
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


def destructive_items(script: Path) -> list[str]:
    """从探针源码里解析出不可逆按钮白名单。"""
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
    def strip_js_comments(text: str) -> str:
        """去掉 /* */ 块注释与「整行以 // 开头」的注释。

        **只去整行 // 注释、不做行内截断**，是因为探针里常有 `http://…` 这样的
        字符串，按 `//` 截到行尾会把 URL 砍成 `http:`。判据只找按钮文案的真前缀，
        残留的 URL 片段不影响结论。
        """
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        return "\n".join(
            line for line in text.splitlines() if not line.lstrip().startswith("//")
        )

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

    print(
        f"  [ ok ] 探针契约：不可逆按钮白名单 {len(items)} 项"
        f"（{'、'.join(items)}）与文档一致"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
