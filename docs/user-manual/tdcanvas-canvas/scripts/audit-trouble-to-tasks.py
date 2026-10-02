#!/usr/bin/env python3
"""排障页 ↔ 任务页 的交叉引用审计（M121 建立，M122 升级）。

**要回答的问题**：排障页收着 36 条「读者已经踩到」的坑，这些坑里涉及的
**界面元素**，在任务页/概念页/参考页里有没有提前讲过？

**为什么这是个真问题**：读者的路径是「先查任务页学操作 → 出问题再查排障页」。
如果排障页写了「悬浮工具条被屏幕边缘裁掉」，而任务页从头到尾没提工具条会被裁，
那读者在**遇到问题之前**没有任何机会知道——两页各自都读得通，只有照着做的人
会发现对不上（M113 撞到过单个实例，M121 做了全量扫描）。

**★ M122 升级：加了一层「i18n 白名单」过滤。**
第一版的提取规则太宽——它把正文里**所有**「」都当成界面文案，于是零命中清单里
混着一堆散文片段（`不知不觉`、`源码里有`、`换成素材`…），真正要查的反而被淹没。
现在改成：**先用应用的中文文案表把「真界面文案」筛出来**，判据两条——
① 引号文案整体出现在 i18n 字符串里；② 去掉数字与分隔符后的**文字骨架**能落在某个
i18n 字符串的骨架里（后者用来覆盖 `{{count}} 个节点 · {{connections}} 条连线`
这类**模板拼接**出来的动态文案）。

**i18n 文件读不到时明确降级**：脚本会打印一行警告并**跳过白名单过滤**，
而不是悄悄当成「全部都是界面文案」——否则用户会误以为清单已经净化过了。

**★ 修正记录（M121 自身踩坑）**：第一版脚本的【二】把「被几条排障条目提到」
错标成了「只在某页出现」——`pages` 变量被丢弃、存进去的是排障条目标题，
于是整段输出是**错的**。grep 反查 `锁比例` / `复制错误` / `多角度` 等词在
10-tasks 全部有命中，与脚本输出直接矛盾，才暴露出来。**这类「列名与内容不符」
的错误，正是本脚本想查的那类问题在脚本自己身上的复现。**

**★ M124 补记：工具给出的「唯一页面」不能当断裂清单用。**
M124 把【二】那 11 项逐条人工核完，结论是**全部覆盖充分**——要么该概念天然只属于一页
（`文本1` 只可能在概念页），要么所在小节正文极厚、表格行只是入口，要么那一行恰好写全了
读者要的东西。**这说明本脚本的输出是候选清单，任何一条都还需要人读过再决定改不改。**

**★ M124 同时查出一处手册错误，正是本脚本的输出指向的位置**：
「打开历史版本，共 N 个」是 `aria-label`（读屏软件读的），而 `canvas-node.tsx:967` 的
`title` 才是给人看的浮层提示，写的是「历史版本」。**界面文案有「看到的」「悬停出来的」
「读屏听到的」三套字符串，它们可以是三句不同的话**——而本脚本只会把它们统统当成一个词
去数出现次数，**分不出这三者**。这既解释了为什么「只在一页出现」未必是问题，
也提示：若某条界面文案值得深查，得回到源码看它挂在 `title` / `aria-label` / 子节点里的哪一个。

**★ 读本脚本的批量输出时的一条纪律（M124 踩到）**：
一次批量 grep 的结果被截断成 head+tail，被切掉的那一行恰好是判断"某词在不在某文件里"的
关键行，于是得出「grep 无命中」，进而差点反过来说本工具算错了。**截断标记覆盖范围内的行，
一律不能作为「不存在」的证据。**

**判据的边界（如实声明）**：即便加了白名单，本脚本仍只做「**字面出现与否**」的统计，
**不判断语义**。「某词出现过」不等于「讲清楚了」，「没出现过」也不等于「该讲而没讲」
（任务页可能用了别的说法）。输出是**候选清单**，逐条需人工确认后再决定改不改——
**不直接当门禁用**。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TROUBLE = ROOT / "90-troubleshooting.md"
TASK_DIR = ROOT / "10-tasks"
EXTRA = ("30-concepts.md", "20-reference.md", "00-quickstart.md", "README.md")
APP_I18N = Path("/Users/yangjiefeng/Documents/AICoderTudou/TDCanvas/web/src/i18n/locales/zh-CN.ts")


def split_sections(text):
    """按 ### 标题切分排障页，返回 [(标题, 正文)]。"""
    parts = re.split(r"^### ", text, flags=re.M)[1:]
    return [(p.split("\n")[0].strip(), "\n".join(p.split("\n")[1:])) for p in parts]


def strip_md(t):
    """剥掉 markdown 强调/代码标记。

    **为什么必须剥**：手册遵守「`**` 不能紧邻中文引号」的渲染约束，于是界面文案
    在正文里长成 `「**复制错误**」` 而不是 `「复制错误」`。提取器抓到的是带星号的
    版本，`'**复制错误**' in '复制错误'` 恒为 False，于是**真界面文案会被误判成散文**
    ——M122 第一版正是这样把 `复制错误` / `多角度` / `更多` / `我的资产` 错滤掉的。
    **过滤器两个方向都会错：把该留的滤掉（假阴性），和把不该留的留下（假阳性）。**
    M122 先修好了后者，又引入了前者，故在此显式记录。
    """
    return t.replace("**", "").replace("*", "").replace("`", "").strip()


def quoted_terms(text):
    """抽取「」与双引号内的候选短语（**此阶段还分不清界面文案与散文**）。"""
    terms = set()
    for pat in (r"「([^」]{2,20})」", r"\"([^\"]{2,20})\""):
        for m in re.finditer(pat, text):
            t = strip_md(m.group(1))
            if t and not re.search(r"[，。；：？！…、]", t):
                terms.add(t)
    return terms


def skeleton(s):
    """文字骨架：去掉插值占位、数字与分隔符，只留实词。

    `{{count}} 个节点 · {{connections}} 条连线` → `个节点条连线`
    `2 个节点 · 0 条连线`               → `个节点条连线`   ← 两者因此可对上
    """
    s = re.sub(r"\{\{[^}]*\}\}", " ", s)
    s = re.sub(r"[\d\s·/×x｜|—–\-_.,:：]+", "", s)
    return s


def load_i18n():
    """载入应用的中文文案表。读不到就返回 (None, 警告)。"""
    if not APP_I18N.exists():
        return None, (f"⚠️ 读不到 i18n 文件（{APP_I18N}），**已跳过白名单过滤**——"
                      "清单里会混进散文片段，不能当作已净化")
    text = APP_I18N.read_text(encoding="utf-8")
    strings = set(re.findall(r"\"([^\"]*[一-鿿][^\"]*)\"", text))
    return strings, None


def is_ui_text(term, i18n_strings):
    """该候选是不是真的界面文案？两条判据：整体命中，或骨架命中。"""
    if any(term in s for s in i18n_strings):
        return True
    sk = skeleton(term)
    if len(sk) < 2:
        return False
    return any(sk in skeleton(s) for s in i18n_strings)


def build_corpus():
    """读者会查的页面：任务页 + 概念/参考/快速上手/首页（**不含排障页自己**）。

    同时预计算每页的**文字骨架**——搜索时字面与骨架都试。
    """
    raw = {}
    for p in sorted(TASK_DIR.glob("*.md")):
        raw[f"10-tasks/{p.name}"] = p.read_text(encoding="utf-8")
    for name in EXTRA:
        f = ROOT / name
        if f.exists():
            raw[name] = f.read_text(encoding="utf-8")
    return {n: {"text": t, "skel": skeleton(t)} for n, t in raw.items()}


def pages_for(term, corpus):
    """这个候选在哪些页面出现过？**字面与骨架都试**。

    **为什么必须试骨架**：同一件事，两页可能一个写实例、一个写占位符——
    排障页写「2 个节点 · 0 条连线」，任务页写「N 个节点 · M 条连线」；
    前者骨架 `个节点条连线`，后者骨架**完全相同**。
    只用字面搜索会把「任务页其实写了」误判成「任务页零提及」（M122 实测踩到 2 例）。
    """
    sk = skeleton(term)
    out = []
    for name, rec in corpus.items():
        if term and term in rec["text"]:
            out.append(name)
        elif len(sk) >= 3 and sk and sk in rec["skel"]:
            out.append(name)
    return out


def main():
    if not TROUBLE.exists():
        print("找不到 90-troubleshooting.md", file=sys.stderr)
        return 1
    sections = split_sections(TROUBLE.read_text(encoding="utf-8"))
    corpus = build_corpus()
    i18n, warn = load_i18n()
    if warn:
        print(warn + "\n")

    all_terms = {}
    for title, body in sections:
        for t in quoted_terms(body):
            rec = all_terms.setdefault(t, {"pages": set(), "sections": set()})
            rec["pages"].update(pages_for(t, corpus))
            rec["sections"].add(title)

    ui = {t: r for t, r in all_terms.items() if i18n and is_ui_text(t, i18n)}
    prose = {t: r for t, r in all_terms.items() if t not in ui}

    print(f"排障条目 {len(sections)} 条；对照语料 {len(corpus)} 份（不含排障页本身）")
    print(f"引号候选 {len(all_terms)} 个 → 判定为界面文案 **{len(ui)}** 个、散文片段 {len(prose)} 个"
          + ("" if i18n else "（**本轮未做白名单过滤**）"))
    print()

    zero, thin, ok = [], [], 0
    for t, r in sorted(ui.items()):
        n = len(r["pages"])
        if n == 0:
            zero.append((t, sorted(r["sections"])))
        elif n == 1:
            thin.append((t, list(r["pages"])[0], sorted(r["sections"])))
        else:
            ok += 1

    print("═" * 78)
    print(f"【一】**界面文案**且只在排障页出现、其余页面零提及：{len(zero)} 个")
    print("═" * 78)
    if not zero:
        print("  （无）—— 排障页涉及的每个界面文案，在别处都讲到了")
    for t, secs in zero:
        print(f"  ▸ {t}")
        print(f"    排障条目：{'；'.join(secs)}")

    print("\n" + "═" * 78)
    print(f"【二】全站只被 1 份页面提到：{len(thin)} 个 ｜【三】≥2 份：{ok} 个")
    print("═" * 78)
    for t, page, secs in thin:
        print(f"  {t:<22} 唯一页面 = {page}")
        print(f"  {'':<22} 排障条目：{'；'.join(secs)}")

    print(f"\n被滤掉的散文片段（不当成断裂，仅供人工参考）共 {len(prose)} 个，例："
          + "、".join(sorted(prose)[:8]))
    print("\n**提醒**：这是字面统计，不是语义判断。逐条落地前必须人工确认。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
