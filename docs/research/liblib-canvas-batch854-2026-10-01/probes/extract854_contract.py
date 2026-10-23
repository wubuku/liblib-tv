#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 854 契约提取器：**从源站 chunk 机器提取**导演台**组模型**的逐字实现。

## ★ 本批靶子

★ batch 853 把「打组／解组快捷键」接上了，但同时暴露了一个**功能差异**：
★ 源站的组**可以包含任意场景成员**（character／prop／emptyObject／camera），
★ 而 clone 的 `groupSelectedCharacters` **只收角色** ⟹ ⟹ 源站能对两个机位打组、
★ clone 不能。本批把**组成员语义**搬过来。

★ 另外两条同源差异：
- 源站的组**默认展开**（成员作为缩进子行常驻），clone 的组**默认折叠**；
- 源站的树多选是 **⇧／⌘／Ctrl ＋ 点击**且**只对可分组类别**生效，
  clone 是 **⇧ ＋ 点击且仅限 character**。

## ★ 提取纪律（沿用 852／853）

1. 每个锚点**必须恰好命中 1 次** ⟹ 否则记 `命中数` 并置空（不许静默取第一条）。
2. 片段**逐字**复制，记录**字节偏移**。
3. 片段里不许出现**截断**的 Tailwind 任意值类名（缺右方括号的那种）。

## ★★ 为什么组名要**实测**而不是从 i18n 猜

★ 源站有**两套**组名模板：`canvas:nodeTypeGroup`（导演台建组路径用）与
★ `directorCharacterGroupAutoLabel`＝`角色组{index}`（另一条路径用）。
★ ★ 而 `canvas:nodeTypeGroup` 的**值不在这个 chunk 里**（i18n 资源在别的 chunk）
⟹ ⟹ 只能靠**实测**：853 的源站探针读到组行标签是 **`分组1`**
⟹ ⟹ 导演台建组路径的组名口径 ＝ **「分组N」**，不是「角色组N」。

## 输出

  raw/source-854-contract.json
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch854-2026-10-01"
RAW = BATCH / "raw"
CHUNK = pathlib.Path("/tmp/liblib_srcjs2/0fmehki05gkzw.js.js")

# ── 逐字锚点：(名字, 锚点串, 追加尾巴长度) ─────────────────────────────────
SPECS = [
    # ── 成员引用的键（kind:id）──
    ("成员引用的键 N(e)",
     'function N(e){return`${e.kind}:${e.id}`}', 0),
    # ── 组的成员列表 O(e)：members 优先，characterIds 兜底，按 N 去重 ──
    ("组的成员列表 O(e)（members 优先 ＋ characterIds 兜底 ＋ 去重）",
     'function O(e){let t=[],r=new Set,n=e=>{if(!e.id)return;let n=N(e);'
     'r.has(n)||(r.add(n),t.push(e))};return(e.members??[]).forEach(n),'
     '(e.characterIds??[]).forEach(e=>n({kind:"character",id:e})),t}',
     0),
    # ── characterIds 由 members 派生 ──
    ("characterIds 由 members 派生 U(e)",
     'function U(e){return O(e).filter(e=>"character"===e.kind).map(e=>e.id)}', 0),
    # ── 成员解析 lB(...)：只保留「场景里还存在」的成员，并去重 ──
    ("成员解析 lB（按场景集合过滤 ＋ 去重）",
     'function lB(e,t,r,n,a){let i=new Set(t.map(e=>e.id)),o=new Set(r.map(e=>e.id)),'
     's=new Set(n.map(e=>e.id)),l=new Set(a.map(e=>e.id)),c=new Set;'
     'return e.filter(e=>{if(!("character"===e.kind&&i.has(e.id)||"prop"===e.kind&&o.has(e.id)'
     '||"emptyObject"===e.kind&&s.has(e.id)||"camera"===e.kind&&l.has(e.id)))return!1;'
     'let t=N(e);return!c.has(t)&&(c.add(t),!0)})}',
     0),
    # ── 选择态 lQ(...) ──
    ("选择态 lQ（selectedSceneMembers ＋ selectedCharacterIds）",
     'function lQ(e,t){let r=t&&e.some(e=>lK(e,t))?t:e.at(-1);'
     'return{selectedId:r?.id??null,selectedCategory:r?.kind??null,'
     'selectedSceneMembers:e,'
     'selectedCharacterIds:e.flatMap(e=>"character"===e.kind?[e.id]:[])}}',
     0),
    # ── 可分组的类别 ──
    ("可分组类别 sg(e)",
     'function sg(e){return"character"===e||"prop"===e||"emptyObject"===e||"camera"===e}',
     0),
    # ── 建组 reducer ──
    ("reducer case：CREATE_CHARACTER_GROUP",
     'case"CREATE_CHARACTER_GROUP":', 520),
    # ── 解组 reducer ──
    ("reducer case：UNGROUP_CHARACTER_GROUP",
     'case"UNGROUP_CHARACTER_GROUP":', 560),
    # ── 右键菜单的 canGroup ──
    ("右键菜单的 canGroup 判定式",
     'X(e,s,!l&&s.length>1&&s.every(e=>sg(e.category)),l?.id)', 0),
    # ── 树行的 onClick：⇧／⌘／Ctrl ＝ additive（且仅对 sg 类别）──
    ("树行的 onClick：⇧／⌘／Ctrl ＝ additive（且仅对 sg 类别）",
     'onClick:t=>{if("motionPath"===e.category)return void s?.(e.id);'
     'let r=t.shiftKey||t.metaKey||t.ctrlKey;'
     'a(e.id,e.category,sg(e.category)?{additive:r,individual:!0}:void 0)}',
     0),
    # ── 树里「当前选中的场景成员」集合 ──
    ("树里当前选中的场景成员集合（selectedSceneMembers → N 键集合）",
     'K=new Set(u.map(N)),', 120),
    # ── 树里「已选的可分组成员」过滤 ──
    ("树里已选的可分组成员过滤",
     'W=[...U,...H,...G,...V].filter(e=>!!sg(e.category)&&K.has(N({kind:e.category,id:e.id})))',
     0),
    # ── 组的展开态：默认展开（j 是「被折叠」的集合）──
    ("组的展开态：默认展开（!!F 是搜索词，j 是被折叠的组集合）",
     'expanded:!!F||!j.has(e.id)', 0),
    # ── 组成员作为缩进子行渲染 ──
    ("组成员作为缩进子行渲染（indent:!0）",
     '(F||!j.has(e.id))&&r.map((e,t)=>(0,i.jsx)(sM,{row:e,indent:!0,',
     120),
    # ── 组的可见／锁定按「全部成员」算 ──
    ("组的可见／锁定按全部成员算",
     'visible:0===t.length||t.every(e=>e.visible),'
     'locked:t.length>0&&t.every(e=>e.locked)', 0),
]

REGEX_SPECS = [
    ("组名 lT(e)＝ i18n(canvas:nodeTypeGroup) ＋ N",
     r'function lT\(e\)\{return`\$\{\(0,tS\.V\)\("canvas:nodeTypeGroup"\)\}\$\{e\.length\+1\}`\}'),
    ("组树条目：带 Group 图标的那一支（树，非右键菜单）",
     r'title:h\(r\?"canvas:directorCollapseGroup":"canvas:directorExpandGroup"\)'
     r'.{0,520}?\(0,i\.jsx\)\(u\.p\.Group[^)]*\)'),
]


def main() -> int:
    if not CHUNK.exists():
        print("★ 源站 chunk 不存在：", CHUNK)
        return 2
    text = CHUNK.read_text(encoding="utf-8", errors="replace")
    out = {"来源": {"chunk": str(CHUNK), "字节数": len(text.encode("utf-8"))}, "片段": {}}
    bad = []
    for name, anchor, tail in SPECS:
        hits = [m.start() for m in re.finditer(re.escape(anchor), text)]
        rec = {"锚点": anchor, "命中数": len(hits),
               "偏移": hits[0] if len(hits) == 1 else None, "原文": None}
        if len(hits) == 1:
            rec["原文"] = text[hits[0]:hits[0] + len(anchor) + tail]
        else:
            bad.append((name, len(hits)))
        out["片段"][name] = rec

    for name, pattern in REGEX_SPECS:
        hits = list(re.finditer(pattern, text))
        rec = {"正则": pattern, "命中数": len(hits),
               "偏移": hits[0].start() if len(hits) == 1 else None,
               "原文": hits[0].group(0) if len(hits) == 1 else None}
        if len(hits) != 1:
            bad.append((name, len(hits)))
        out["片段"][name] = rec

    arb = []
    for name, rec in out["片段"].items():
        src = rec["原文"] or ""
        for m in re.finditer(r"[A-Za-z0-9_:/\[\]().,#%!-]*-\[[^\]\s\"']*", src):
            frag = m.group(0)
            if not frag.endswith("]"):
                arb.append((name, frag))
    out["★任意值类名自检"] = {"疑似截断": arb, "通过": not arb}

    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / "source-854-contract.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已落盘：", path)
    ok = 0
    for name, rec in out["片段"].items():
        if rec["命中数"] == 1:
            ok += 1
        print("  [%s] %-58s 命中=%d"
              % ("OK " if rec["命中数"] == 1 else "BAD", name, rec["命中数"]))
    print("唯一命中：%d / %d" % (ok, len(out["片段"])))
    print("任意值类名自检：", "通过" if not arb else ("★ 疑似截断 %r" % (arb,)))
    if bad:
        print("★★ 锚点未唯一命中：", bad)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
