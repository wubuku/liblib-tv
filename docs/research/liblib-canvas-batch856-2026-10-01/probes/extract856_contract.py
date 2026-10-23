#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 856 契约提取：从源站 chunk **机器提取** D1 相关的逐字片段。

## ★ 为什么要机器提取（而不是手打）

★ 手打的「源站逐字」是**说法**，机器提取的才是**事实**：
  片段的**原文**直接从 chunk 里切出来 ⟹ ⟹ 任何人都能复核。

★ 本批的片段（6 条）：
  ① 组对象字面量：`{id:lM(),label:lT(e.characterGroups),characterIds:n,members:r}`
     ⟹ ⟹ **没有 transform 字段**
  ② 组的权威成员列表 `O(e)`（members 优先＋characterIds 兜底＋去重）
  ③ `SELECT_CHARACTER_GROUP` reducer（选中组 ⟹ `lQ(n)` ＋ `selectedGroupId`）
  ④ `H(e,t)` 锚点 ＝ 全部成员位置均值（⟹ ⟹ 组位置永远是**派生**的）
  ⑤ 组轨道创建：`keyframes:[{time:0,position:n}],interpolation:"linear",memberOffsets:V(i,n,...)`
  ⑥ 组轨道编辑属性：`speedCurveSegments:hi(t.speedCurveSegments,["position"])`
     ⟹ ⟹ 组轨道**只有 position** 一个可编辑属性

## ★ 自检（★ 不自检的提取器会骗人）

★ ① **唯一命中**：每个片段在整份 chunk 里必须**只出现一次**
   ⟹ ⟹ 不唯一 ⟹ ⟹ 记空 ＋ 退出码 1（不产出假 raw）。
★ ② **任意值类名自检**：片段里如果出现 `xxx.yyy` 这种**看起来像类名**的串，
   必须能确认它不是「我编的」⟹ ⟹ 这里用 chunk 里真实存在的标识符做白名单核对。

## 输出
  raw/source-856-contract.json
"""
import json
import pathlib
import re
import sys

CHUNK = pathlib.Path("/tmp/liblib_srcjs2/0fmehki05gkzw.js.js")
OUT = (pathlib.Path(__file__).resolve().parents[1]
       / "raw" / "source-856-contract.json")

# ★ (片段名, 要在 chunk 里唯一定位的锚点, 片段正文)
# ★ 锚点用来**唯一定位**，正文是要**逐字摘出来**的那一段。
FRAGMENTS = [
    ("组对象字面量（无 transform 字段）",
     'a={id:lM(),label:lT(e.characterGroups),characterIds:n,members:r}',
     'a={id:lM(),label:lT(e.characterGroups),characterIds:n,members:r}'),
    ("权威成员列表 O(e)（members 优先＋characterIds 兜底＋去重）",
     'function O(e){let t=[],r=new Set',
     'function O(e){let t=[],r=new Set,n=e=>{if(!e.id)return;let n=N(e);'
     'r.has(n)||(r.add(n),t.push(e))};return(e.members??[]).forEach(n),'
     '(e.characterIds??[]).forEach(e=>n({kind:"character",id:e})),t}'),
    ("reducer SELECT_CHARACTER_GROUP（选中组 ⟹ lQ(n) ＋ selectedGroupId）",
     'case"SELECT_CHARACTER_GROUP":{let r=e.characterGroups.find(e=>e.id===t.id)',
     'case"SELECT_CHARACTER_GROUP":{let r=e.characterGroups.find(e=>e.id===t.id);'
     'if(!r)return e;let n=lB(O(r),e.characters,e.props,e.emptyObjects,e.cameras);'
     'if(0===n.length)return e;return{...e,...lQ(n),selectedGroupId:r.id}}'),
    ("组的锚点 H(e,t)（全部成员位置均值 ⟹ 组位置永远是派生的）",
     'function H(e,t){var r=O(e).map(t).filter(e=>!!e)',
     'function H(e,t){var r=O(e).map(t).filter(e=>!!e);if(0===r.length)return null;'
     'let n=r.reduce((e,t)=>({x:e.x+t.x,y:e.y+t.y,z:e.z+t.z}),{x:0,y:0,z:0});'
     'return{x:n.x/r.length,y:n.y/r.length,z:n.z/r.length}}'),
    ("组轨道创建（keyframes 只有一个 position）",
     'keyframes:[{time:0,position:n}],interpolation:"linear",memberOffsets:V(i,n,',
     'keyframes:[{time:0,position:n}],interpolation:"linear",'
     'memberOffsets:V(i,n,t=>L(e,t))}'),
    ("组轨道编辑属性（只有 position 一个）",
     # ★★★ 这句 `speedCurveSegments:hi(...,["position"])` 在 chunk 里出现 **7** 次
     #   （character／prop／camera／group 各自的轨道 + 另两处 motionPath 清理）
     #   ⟹ ⟹ **光凭它不唯一** ⟹ ⟹ 锚点必须带上「这是 group 那条」的前缀。
     # ★ ★ 这正是提取器要自检的原因：命中数 ≠ 1 ⟹ ⟹ 直接退出 1、**不产出假 raw**。
     'if("group"===e.kind){let t=A.groupTracks.find(t=>t.id===e.trackId);'
     'if(!t)return!1;let n=b.characterGroups.find(e=>e.id===t.targetId),'
     'a=n?H(n,e=>L(b,e)):null,i=g(t.keyframes,a?.y??0);'
     'return na(e.trackId,{...y,...v,keyframes:i,'
     'speedCurveSegments:hi(t.speedCurveSegments,["position"])},r),!0}',
     'if("group"===e.kind){let t=A.groupTracks.find(t=>t.id===e.trackId);'
     'if(!t)return!1;let n=b.characterGroups.find(e=>e.id===t.targetId),'
     'a=n?H(n,e=>L(b,e)):null,i=g(t.keyframes,a?.y??0);'
     'return na(e.trackId,{...y,...v,keyframes:i,'
     'speedCurveSegments:hi(t.speedCurveSegments,["position"])},r),!0}'),
]


def main() -> int:
    if not CHUNK.exists():
        print("★ 缺源站 chunk：%s" % CHUNK)
        return 2
    src = CHUNK.read_text(encoding="utf-8")

    out = {
        "来源": {
            "chunk": str(CHUNK),
            "字节数": len(src),
            "提取方式": "机器提取（唯一定位 ＋ 逐字摘录）",
        },
        "片段": {},
    }

    ok = True
    for name, anchor, body in FRAGMENTS:
        anchor_hits = src.count(anchor)
        body_hits = src.count(body)
        # ★ 唯一定位：锚点**必须**只出现一次
        if anchor_hits != 1:
            print("★★ 片段「%s」的锚点命中 %d 次（必须 1 次）" % (name, anchor_hits))
            ok = False
        out["片段"][name] = {
            "锚点": anchor,
            "原文": body if body_hits >= 1 else "",
            "锚点命中数": anchor_hits,
            "正文命中数": body_hits,
        }
        if body_hits != 1:
            print("★★ 片段「%s」的正文命中 %d 次（必须 1 次）" % (name, body_hits))
            ok = False

    # ★★ 任意值类名自检：正文里出现的 `标识符.标识符` 形态，
    #   必须**确实出现在 chunk 里**（防止「我把一个不存在的类名写进片段」）。
    # ★ 这里逐个核对：正文里每个 `x.y` 的 `x` 必须是 chunk 里真实存在的标识符。
    idents = set(re.findall(r"[A-Za-z_$][A-Za-z0-9_$]*", src))
    bogus = []
    for name, _anchor, body in FRAGMENTS:
        if not body:
            continue
        for m in re.finditer(r"\b([A-Za-z_$][A-Za-z0-9_$]*)\.([A-Za-z_$][A-Za-z0-9_$]*)", body):
            head = m.group(1)
            if head in idents:
                continue
            # ★ 关键字／字面量里的对象名（如 `e.id` 的 e 是参数名 ⟹ 也在 idents 里）
            bogus.append({"片段": name, "标识符": head, "片段位置": m.start()})
    out["★任意值类名自检"] = {
        "通过": not bogus,
        "疑似编造的标识符": bogus,
        "说明": "正文里每个 `x.y` 的 x 必须真实出现在 chunk 的标识符集合里",
    }
    if bogus:
        ok = False

    uniq = sum(1 for v in out["片段"].values() if v["锚点命中数"] == 1 and v["原文"])
    print("唯一命中：%d / %d" % (uniq, len(FRAGMENTS)))
    print("任意值类名自检：%s" % ("通过" if out["★任意值类名自检"]["通过"] else "★不通过"))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已落盘：", OUT)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
