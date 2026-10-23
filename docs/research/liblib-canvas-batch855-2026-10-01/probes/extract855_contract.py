#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 855 契约提取器：**从源站 chunk 机器提取**导演台**组 rig（锚点／成员偏移／
组轨道／解组 reducer）**的逐字实现**。

## ★ 本批靶子

★ batch 854 让组**可以包含任意场景成员**（含机位）⟹ ⟹ 但 **clone 的组 rig
仍然只认角色**：

- `src/components/director/directorGroupMath.ts` 的 `getDirectorGroupMembers`
  过滤 `object.kind === "character"` ⟹ ⟹ **锚点、成员偏移、整体变换都漏掉机位**；
- `src/lib/directorProjectDocument.ts` 的组轨道校验仍要求
  `memberOffsets` 的键 ⊆ `group.characterIds` ⟹ ⟹ **混合组的轨道建不出来**。

★ 本批把**组 rig 整条链**按「全部成员」对齐源站。

## ★ 源站的逐字依据（见 raw/source-855-contract.json）

```js
function H(e,t){var r=O(e).map(t).filter(e=>!!e);if(0===r.length)return null;
  let n=r.reduce((e,t)=>({x:e.x+t.x,y:e.y+t.y,z:e.z+t.z}),{x:0,y:0,z:0});
  return{x:n.x/r.length,y:n.y/r.length,z:n.z/r.length}}        // ★ 锚点＝全部成员位置的**平均值**
function V(e,t,r){return O(e).reduce((e,n)=>{let a=r(n);
  return a&&(e[N(n)]={x:a.x-t.x,y:a.y-t.y,z:a.z-t.z}),e},{})}    // ★ 成员偏移，键＝N(n)＝kind:id
let i=t.memberOffsets??V(r,a,f);O(r).forEach(t=>{let r=i[N(t)];…})  // ★ 成员偏移缺失时现算；遍历 O(r)＝全部成员
```

★ ★ **两个关键点**：
1. `H` 与 `V` **都遍历 `O(e)`** ＝ **权威成员列表**（任意类别）⟹ ⟹ **机位入组后，
   锚点与偏移都算机位** ⟹ ⟹ 机位会**跟着组一起动**（源站行为）。
2. 源站的 `H` **只返回位置**（没有 rotation／scale）⟹ ⟹ clone 借「第一个成员的
   rotation／scale」来补全 transform 三元组 ⟹ ⟹ 属**实现差异**，如实登记。

## ★ 提取纪律（沿用 852／853／854）

1. 每个锚点**必须恰好命中 1 次** ⟹ 否则记 `命中数` 并置空（不许静默取第一条）。
2. 片段**逐字**复制，记录**字节偏移**。
3. 片段里不许出现**截断**的 Tailwind 任意值类名（缺右方括号的那种）。

## 输出

  raw/source-855-contract.json
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch855-2026-10-01"
RAW = BATCH / "raw"
CHUNK = pathlib.Path("/tmp/liblib_srcjs2/0fmehki05gkzw.js.js")

# ── 逐字锚点：(名字, 锚点串, 追加尾巴长度) ─────────────────────────────────
SPECS = [
    # ── 组的锚点 H(e,t)：全部成员位置的**平均值** ──
    ("组的锚点 H(e,t)（全部成员位置的平均值）",
     'function H(e,t){var r=O(e).map(t).filter(e=>!!e);if(0===r.length)return null;'
     'let n=r.reduce((e,t)=>({x:e.x+t.x,y:e.y+t.y,z:e.z+t.z}),{x:0,y:0,z:0});'
     'return{x:n.x/r.length,y:n.y/r.length,z:n.z/r.length}}',
     0),
    # ── 成员偏移 V(e,t,r)：键 ＝ N(n) ＝ kind:id ──
    ("成员偏移 V(e,t,r)（键 ＝ N(n) ＝ kind:id）",
     'function V(e,t,r){return O(e).reduce((e,n)=>{let a=r(n);'
     'return a&&(e[N(n)]={x:a.x-t.x,y:a.y-t.y,z:a.z-t.z}),e},{})}',
     0),
    # ── 组轨道 rig：memberOffsets 缺失时现算；遍历 O(r) ＝ 全部成员 ──
    ("组轨道 rig（memberOffsets 缺失时现算 ＋ 遍历全部成员 O(r)）",
     'let i=t.memberOffsets??V(r,a,f);O(r).forEach(t=>{let r=i[N(t)];',
     240),
    # ── 解组 reducer：复原成员 ＋ 相机重算绑定 ＋ 过滤该组轨道 ＋ 选择态 ──
    ("reducer case：UNGROUP_CHARACTER_GROUP（复原成员／相机重算／过滤轨道／选择态）",
     'case"UNGROUP_CHARACTER_GROUP":{let r=e.characterGroups.find(e=>e.id===t.id);'
     'if(!r)return e;let n=lB(O(r),e.characters,e.props,e.emptyObjects,e.cameras);'
     'return{...e,characterGroups:e.characterGroups.filter(e=>e.id!==t.id),'
     'cameras:e.cameras.map(r=>lV(r,e,new Set([t.id]))),'
     'animation:{...e.animation,groupTracks:e.animation.groupTracks.filter(e=>e.targetId!==t.id)},'
     '...lQ(n),selectedGroupId:null}}',
     0),
    # ── 相机在组变化后重算绑定 lV：按**各组锚点**重算 follow 目标 ──
    ("相机绑定重算 lV（按各组锚点 H 重算）",
     'function lV(e,t,r){let n=new Map;'
     't.characterGroups.forEach(e=>{let r=H(e,e=>L(t,e));r&&n.set(e.id,r)});',
     0),
    # ── 组的可见／锁定按**全部成员**算 ──
    ("组的可见／锁定按全部成员算",
     'visible:0===t.length||t.every(e=>e.visible),'
     'locked:t.length>0&&t.every(e=>e.locked)', 0),
    # ── 权威成员列表 O(e)（854 已提取，本批复用同一份）──
    ("权威成员列表 O(e)（members 优先 ＋ characterIds 兜底 ＋ 去重）",
     'function O(e){let t=[],r=new Set,n=e=>{if(!e.id)return;let n=N(e);'
     'r.has(n)||(r.add(n),t.push(e))};return(e.members??[]).forEach(n),'
     '(e.characterIds??[]).forEach(e=>n({kind:"character",id:e})),t}',
     0),
    # ── 成员的键 N(e)＝kind:id ──
    ("成员的键 N(e)＝kind:id",
     'function N(e){return`${e.kind}:${e.id}`}', 0),
]


def main() -> int:
    if not CHUNK.exists():
        print("★ 源站 chunk 不存在：", CHUNK)
        return 2
    text = CHUNK.read_text(encoding="utf-8", errors="replace")
    out = {"来源": {"chunk": str(CHUNK), "字节数": len(text.encode("utf-8"))},
           "片段": {}}
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

    arb = []
    for name, rec in out["片段"].items():
        src = rec["原文"] or ""
        for m in re.finditer(r"[A-Za-z0-9_:/\[\]().,#%!-]*-\[[^\]\s\"']*", src):
            frag = m.group(0)
            if not frag.endswith("]"):
                arb.append((name, frag))
    out["★任意值类名自检"] = {"疑似截断": arb, "通过": not arb}

    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / "source-855-contract.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已落盘：", path)
    ok = 0
    for name, rec in out["片段"].items():
        if rec["命中数"] == 1:
            ok += 1
        print("  [%s] %-56s 命中=%d"
              % ("OK " if rec["命中数"] == 1 else "BAD", name, rec["命中数"]))
    print("唯一命中：%d / %d" % (ok, len(out["片段"])))
    print("任意值类名自检：", "通过" if not arb else ("★ 疑似截断 %r" % (arb,)))
    if bad:
        print("★★ 锚点未唯一命中：", bad)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
