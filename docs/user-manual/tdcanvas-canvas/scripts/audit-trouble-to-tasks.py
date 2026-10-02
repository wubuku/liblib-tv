#!/usr/bin/env python3
"""排障页 ↔ 任务页 的交叉引用审计（M121）。

**要回答的问题**：排障页收着 36 条「读者已经踩到」的坑，这些坑里涉及的
**界面元素**，在任务页/概念页/参考页里有没有提前讲过？

**为什么这是个真问题**：读者的路径是「先查任务页学操作 → 出问题再查排障页」。
如果排障页写了「悬浮工具条被屏幕边缘裁掉」，而任务页从头到尾没提工具条会被裁，
那读者在**遇到问题之前**没有任何机会知道——两页各自都读得通，只有照着做的人
会发现对不上（M113 撞到过单个实例，这批做全量扫描）。

**★ 修正记录（M121 自身踩坑）**：第一版这段脚本的【二】把「被几条排障条目提到」
错标成了「只在某页出现」——`pages` 变量被丢弃、存进去的是排障条目标题，
于是整段输出是**错的**。grep 反查 `锁比例` / `复制错误` / `多角度` 等词在
10-tasks 全部有命中，与脚本输出直接矛盾。**这类「列名与内容不符」的错误，
正是本脚本想查的那类问题在脚本自己身上的复现**，故在此显式记录。

**判据的边界（如实声明）**：本脚本只做「**字面出现与否**」的统计，**不判断语义**。
「某词出现过」不等于「讲清楚了」，「没出现过」也不等于「该讲而没讲」（可能任务页
用了别的说法）。输出是**候选清单**，逐条需人工确认后再决定改不改——**不直接当门禁用**。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TROUBLE = ROOT / "90-troubleshooting.md"
TASK_DIR = ROOT / "10-tasks"
EXTRA = ("30-concepts.md", "20-reference.md", "00-quickstart.md", "README.md", "90-troubleshooting.md")


def split_sections(text):
    """按 ### 标题切分排障页，返回 [(标题, 正文)]。"""
    parts = re.split(r"^### ", text, flags=re.M)[1:]
    return [(p.split("\n")[0].strip(), "\n".join(p.split("\n")[1:])) for p in parts]


def quoted_terms(text):
    """抽取「」与双引号内的界面文案候选。"""
    terms = set()
    for pat in (r"「([^」]{2,14})」", r"\"([^\"]{2,14})\""):
        for m in re.finditer(pat, text):
            t = m.group(1).strip()
            if t and not re.search(r"[，。；：？！…、]", t):
                terms.add(t)
    return terms


def build_corpus():
    """读者会查的页面：任务页 + 概念/参考/快速上手/首页（**不含排障页自己**）。"""
    corpus = {}
    for p in sorted(TASK_DIR.glob("*.md")):
        corpus[f"10-tasks/{p.name}"] = p.read_text(encoding="utf-8")
    for name in EXTRA:
        if name == "90-troubleshooting.md":
            continue  # 关键：排障页自己不算「别处讲过」
        f = ROOT / name
        if f.exists():
            corpus[name] = f.read_text(encoding="utf-8")
    return corpus


def main():
    if not TROUBLE.exists():
        print("找不到 90-troubleshooting.md", file=sys.stderr)
        return 1
    sections = split_sections(TROUBLE.read_text(encoding="utf-8"))
    corpus = build_corpus()
    print(f"排障条目 {len(sections)} 条；对照语料 {len(corpus)} 份（**不含排障页本身**）\n")

    zero, thin, ok = [], [], 0
    all_terms = {}
    for title, body in sections:
        for t in quoted_terms(body):
            pages = [n for n, txt in corpus.items() if t in txt]
            all_terms.setdefault(t, {"pages": set(), "sections": set()})
            all_terms[t]["pages"].update(pages)
            all_terms[t]["sections"].add(title)

    for t, info in sorted(all_terms.items()):
        n = len(info["pages"])
        if n == 0:
            zero.append((t, sorted(info["sections"])))
        elif n == 1:
            thin.append((t, n, list(info["pages"])[0], sorted(info["sections"])))
        else:
            ok += 1

    print("═" * 78)
    print(f"【一】只在排障页出现、其余 18 份页面一个都没提的引号文案：{len(zero)} 个")
    print("═" * 78)
    if not zero:
        print("  （无）")
    for t, secs in zero:
        print(f"  ▸ {t}")
        print(f"    出现在排障条目：{'；'.join(secs)}")

    print("\n" + "═" * 78)
    print(f"【二】全站只被 1 份页面提到（覆盖最薄）：{len(thin)} 个  ｜【三】≥2 份：{ok} 个")
    print("═" * 78)
    for t, n, page, secs in thin:
        print(f"  {t:<16} 唯一页面 = {page}")
        print(f"  {'':<16} 排障条目：{'；'.join(secs)}")

    print(f"\n合计引号文案 {len(all_terms)} 个：零命中 {len(zero)}、单页 {len(thin)}、多页 {ok}。")
    print("\n**提醒**：这是字面统计，不是语义判断。逐条落地前必须人工确认。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
