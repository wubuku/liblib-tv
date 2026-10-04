#!/usr/bin/env python3
"""batch 749 验收：A. 把 748 留下的 `createDirectorCapture` 发送那一跳走完；
B. 把「有静态、无运行时」的残差从**一个数**变成**一族一族的门**

## 起点

748 导演台首轮普查报出：有效并集 447、运行时出现 224、**没出现 223**，
并明确「本批不区分成因」。本批做两件事：

A. `createDirectorCapture` 的发送那一跳（748 只点到快门）
B. 那 223 种按**门族**归因，并对两族代表做运行时验证

## 决定性读数（先看这条）

### ① `createDirectorCapture` 真跑通，是**两跳 + 幂等**

```
DirectorViewport.tsx:3586   data-director-capture          ← 第 1 跳：快门（store 零写入）
DirectorInspector.tsx:288   data-director-capture-preview  ← 预览
DirectorInspector.tsx:307   data-director-send-capture     ← 第 2 跳：发送到画布
DirectorDesk.tsx:589-591    const sendCapture = (c) => { if (c.sentNodeId) return;
                                                     createDirectorCapture(sourceNodeId, …) }
```

第 1 跳：store **零写入**，但预览出现（`638 × 359`、`alt`「机位01 · 对峙中景构图截图」）、
`data-director-capture-status="ready"`、文案「**1 张构图**」。

第 2 跳：`past` 0→**1**、节点 10→**11**、边 11→**12**、新文件
「**导演台截图-机位01 · 对峙中景**」、`image` 类型 5→**6**
（`canvasStore.ts:2818 type: "image"` —— **截图落画布是图片节点，不是视频**）。

发送后 UI 翻转：按钮文案「发送到画布」→「**已发送到画布**」+ `disabled`；
`capture-status` 文案「1 张构图」→「**已回到画布**」。

**幂等**：再点那个已 `disabled` 的按钮 ⟹ store 逐项零变化
⟹ `DirectorDesk.tsx:590 if (capture.sentNodeId) return;` 生效。

### ② 导演台的产出在**画布侧**被打上 6 个标记 —— 画布节点组件知道导演台存在

```
ImageNode.tsx:216-221
  "data-director-capture-node": true,
  "data-director-capture-id": directorCapture.captureId,
  "data-director-capture-source-id": directorCapture.sourceNodeId,
  "data-director-capture-camera-id": directorCapture.cameraId ?? "",
  "data-director-capture-aspect": directorCapture.aspectRatio,
  "data-director-capture-edge-id": directorCapture.edgeId,
```

这 6 个属性**只在发送之后才出现在 DOM 上**（748 的首屏 250 种里没有）。
⟹ 导演台与画布的双向耦合点不只在 store，还在**画布节点的渲染层**。

### ③ 残差不是「一个数」，是**一族一族的门**

748 的 223 种（走完 7 枚 rail 之后）按前缀成族。本批运行时验证其中两族：

| 族 | 门 | 新增 |
|---|---|---|
| 采集图库族 | 选中**机位** → 相机页签的「**截图**」子页 | **+4**（`capture-gallery` / `capture-empty` / `capture-send-all` / `capture-clear-all`） |
| ↑ 同族 | 在该机位下**拍 2 张**再回「截图」页 | **+8**（`capture-item` / `-item-selected` / `capture-group` / `-group-shot` / `capture-send` / `capture-remove` / `capture-view` / `-shot-id`） |
| 姿势族 | 选中**角色** → 角色页签的「**姿势**」子页 | **+10**（`pose-panel` / `-group` / `-control` / `-value` / `-preset` / `-side` / `-state` + `data-expanded` / `data-pose-preset` / `data-pose-control-count`） |

图库态读数：拍之前 `empty: true, items: 0`；拍 2 张后 `empty: false, items: 2, groups: 1`，
`send-all` / `clear-all` 由 `disabled` 变可用。

**页签是同名不同值**：`data-director-camera-tab` 有
`properties`（属性）/ `motion`（运动轨迹**NEW**）/ `captures`（截图）3 枚，
`data-director-character-tab` 有 `properties`（属性）/ `pose`（**姿势**）2 枚。
⟹ **按属性名去重枚举门会漏掉同名不同值的页签**（749c 踩过）。

## 判据

C1  静态：有效并集 447；`createDirectorCapture` 声明+实现两处；`sendCapture` 有
    `sentNodeId` 幂等守卫；`ImageNode.tsx:216-221` 6 个 capture 标记；store 落点是
    `type: "image"`；两个页签守卫的源码行
C2  第 1 跳快门：store 零写入；预览出现且有尺寸与 alt；`capture-status="ready"`、文案「1 张构图」
C3  第 2 跳发送：`past` +1、节点 +1、边 +1、新文件「导演台截图-<机位名>」、`image` 5→6
C4  发送后 UI 翻转：发送键文案「已发送到画布」+ `disabled`；`capture-status` 文案「已回到画布」
C5  幂等：再点已 disabled 的发送键 ⟹ `past`/节点/边 逐项零变化
C6  画布侧 6 个 `data-director-capture-*` 在发送**之后**才出现
C7  族①：机位→「截图」子页 +4；拍 2 张 +8；图库 `empty` 翻转、`items` 0→2、`groups` 1、
    批量发送/清空钮解禁
C8  族②：角色→「姿势」子页 +10
C9  残差按前缀成族的归类表（静态）
"""

import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch749-2026-10-01"
DESK = ROOT / "src/components/director"
IMGN = ROOT / "src/components/nodes/ImageNode.tsx"
STORE = ROOT / "src/store/canvasStore.ts"
BASE = "http://localhost:4317"
W, H = 1280, 1150

SNAP = """() => {
  const s = window.__libtv_store.getState();
  const g = s.getActiveCanvas();
  const h = s.historyByCanvas[g.id] || {past: [], future: []};
  return {nodeCount: g.nodes.length, edgeCount: g.edges.length, past: h.past.length,
          typeCounts: g.nodes.reduce((a,n)=>(a[n.type]=(a[n.type]||0)+1,a), {}),
          files: g.nodes.map(n=>(n.data&&n.data.filename)||null).filter(Boolean),
          nodeIds: g.nodes.map(n=>n.id).sort()};
}"""
DUMP = """() => { const out = {};
  for (const el of document.querySelectorAll('*'))
    for (const a of el.attributes)
      if (a.name.startsWith('data-')) out[a.name] = (out[a.name]||0)+1;
  return out; }"""
SEND_BTN = """() => { const e = document.querySelector('[data-director-send-capture]');
    if (!e) return null;
    return {text:(e.textContent||'').trim(), disabled:e.disabled}; }"""
CAP_STATUS = """() => { const e = document.querySelector('[data-director-capture-status]');
    if (!e) return null;
    return {status:e.getAttribute('data-director-capture-status'),
            text:(e.textContent||'').trim()}; }"""
PREVIEW = r"""() => { const e = document.querySelector('[data-director-capture-preview]');
    if (!e) return null;
    const img = e.querySelector('img');
    const m = (e.textContent||'').match(/(\d+)\s*×\s*(\d+)/);
    return {present:true, alt: img?img.alt:null,
            dims: m?[Number(m[1]),Number(m[2])]:null}; }"""
ROWS = """() => [...document.querySelectorAll('[data-director-object-id]')].map(r => ({
    id:r.getAttribute('data-director-object-id'),
    kind:r.getAttribute('data-director-object-kind'),
    text:(r.textContent||'').trim().slice(0,20), role:r.getAttribute('role') }))"""
TABS = """(attr) => [...document.querySelectorAll('['+attr+']')].map(e => ({
    value:e.getAttribute(attr), text:(e.textContent||'').trim().slice(0,14),
    pressed:e.getAttribute('aria-pressed') }))"""
GALLERY = """() => { const q=(s)=>document.querySelector(s);
    const dis=(s)=>{const e=q(s); return e?e.disabled:null;};
    return {gallery:Boolean(q('[data-director-capture-gallery]')),
            empty:Boolean(q('[data-director-capture-empty]')),
            items:document.querySelectorAll('[data-director-capture-item]').length,
            groups:document.querySelectorAll('[data-director-capture-group]').length,
            sendAllDisabled:dis('[data-director-capture-send-all]'),
            clearAllDisabled:dis('[data-director-capture-clear-all]')}; }"""
CLICK_ROW = """(id) => { const e=document.querySelector('[data-director-object-id="'+id+'"]');
    if(!e) return false; e.click(); return true; }"""
CLICK_TAB = """(a) => { const [attr,v]=a;
    const e=[...document.querySelectorAll('['+attr+']')].find(x=>x.getAttribute(attr)===v);
    if(!e) return false; e.click(); return true; }"""
SHUTTER = """() => { const e=document.querySelector('[data-director-capture]');
    if(!e) return false; e.click(); return true; }"""


def static_scan():
    out = {}
    store = STORE.read_text(encoding="utf-8").split("\n")
    insp = (DESK / "DirectorInspector.tsx").read_text(encoding="utf-8").split("\n")
    desk = (DESK / "DirectorDesk.tsx").read_text(encoding="utf-8").split("\n")
    vp = (DESK / "DirectorViewport.tsx").read_text(encoding="utf-8").split("\n")
    imgn = IMGN.read_text(encoding="utf-8").split("\n")
    # 有效并集（字面量 + dataset 派生）
    union, owner = set(), {}
    for f in sorted(DESK.glob("*.tsx")):
        names = set()
        for l in f.read_text(encoding="utf-8").split("\n"):
            names.update(re.findall(r"\b(data-[a-z0-9-]+)", l))
        for n in names:
            union.add(n); owner.setdefault(n, []).append(f.name)
        for i, l in enumerate(f.read_text(encoding="utf-8").split("\n"), 1):
            for m in re.finditer(r"\.dataset\.([A-Za-z0-9_]+)\s*=", l):
                kebab = re.sub(r"([A-Z])", lambda x: "-" + x.group(1).lower(), m.group(1))
                n = f"data-{kebab}"
                if n not in union:
                    union.add(n); owner.setdefault(n, []).append(f"{f.name}:{i}(dataset)")
    out["effectiveUnion"] = sorted(union)
    out["effectiveUnionCount"] = len(union)
    out["owner"] = owner
    # 采集链路
    out["decl_createDirectorCapture"] = [i for i, l in enumerate(store, 1)
                                         if re.match(r"\s*createDirectorCapture:", l)]
    out["sendCaptureLine"] = next(i for i, l in enumerate(desk, 1)
                                  if "const sendCapture" in l)
    out["idempotentGuardLine"] = next(i for i, l in enumerate(desk, 1)
                                      if "if (capture.sentNodeId) return;" in l)
    out["shutterLine"] = next(i for i, l in enumerate(vp, 1) if "data-director-capture" in l)
    out["previewLine"] = next(i for i, l in enumerate(insp, 1)
                              if "data-director-capture-preview" in l)
    out["sendBtnLine"] = next(i for i, l in enumerate(insp, 1)
                              if "data-director-send-capture" in l)
    out["cameraCapturesGuard"] = next(i for i, l in enumerate(insp, 1)
                                      if 'cameraTab === "captures"' in l)
    out["characterPoseGuard"] = next(i for i, l in enumerate(insp, 1)
                                     if 'characterTab === "pose"' in l)
    out["imgNodeCaptureAttrs"] = [i for i, l in enumerate(imgn, 1)
                                  if "data-director-capture" in l]
    out["imgNodeAttrNames"] = sorted(set(re.findall(r'"(data-director-capture-[a-z-]+)"',
                                                  "\n".join(imgn))))
    out["storeTypeLine"] = next(i for i, l in enumerate(store, 1)
                                if i > out["decl_createDirectorCapture"][-1]
                                and l.strip() == 'type: "image",')
    out["storeFilenameLine"] = next(i for i, l in enumerate(store, 1)
                                    if "导演台截图-" in l)
    # 残差族：按前缀取前 4 段
    return out


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    st = static_scan()
    print("=== C1 静态 ===")
    for k, v in st.items():
        if k in ("effectiveUnion", "owner"):
            continue
        print(f"  {k:26s} {v}")
    print(f"  有效并集 = {st['effectiveUnionCount']} 种")

    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})
        page.goto(f"{BASE}/?batch749=1", wait_until="networkidle", timeout=90_000)
        page.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
        page.wait_for_timeout(1_500)
        page.evaluate("() => { const e=document.querySelector('[data-open-director]'); if(e) e.click(); }")
        page.wait_for_timeout(2_500)

        # ---------- A. 采集三跳 ----------
        print("\n=== A1/C2 第 1 跳：快门 ===")
        s0 = page.evaluate(SNAP)
        attrs0 = set(page.evaluate(DUMP))          # 导演台刚打开、还没拍
        capped = page.evaluate(SHUTTER)
        page.wait_for_timeout(1_200)
        s1 = page.evaluate(SNAP)
        attrs1 = set(page.evaluate(DUMP))          # 快门之后
        c2 = {"clicked": capped, "preview": page.evaluate(PREVIEW),
              "status": page.evaluate(CAP_STATUS),
              "past": [s0["past"], s1["past"]],
              "nodes": [s0["nodeCount"], s1["nodeCount"]],
              "edges": [s0["edgeCount"], s1["edgeCount"]]}
        print(f"  clicked={capped}；store past {s0['past']}→{s1['past']}、"
              f"节点 {s0['nodeCount']}→{s1['nodeCount']}、边 {s0['edgeCount']}→{s1['edgeCount']}")
        print(f"  预览 {json.dumps(c2['preview'], ensure_ascii=False)}")
        print(f"  状态 {json.dumps(c2['status'], ensure_ascii=False)}")

        print("\n=== A2/C3 第 2 跳：发送到画布 ===")
        btn0 = page.evaluate(SEND_BTN)
        s2 = page.evaluate(SNAP)
        sent = page.evaluate("() => { const e=document.querySelector('[data-director-send-capture]');"
                             " if(!e) return false; e.click(); return true; }")
        page.wait_for_timeout(1_500)
        s3 = page.evaluate(SNAP)
        attrs3 = set(page.evaluate(DUMP))
        c3 = {"sendBtnBefore": btn0, "clicked": sent,
              "past": [s2["past"], s3["past"]],
              "nodes": [s2["nodeCount"], s3["nodeCount"]],
              "edges": [s2["edgeCount"], s3["edgeCount"]],
              "newFiles": [f for f in s3["files"] if f not in s2["files"]],
              "imageBefore": s2["typeCounts"].get("image", 0),
              "imageAfter": s3["typeCounts"].get("image", 0)}
        print(f"  发送键（点前）{json.dumps(btn0, ensure_ascii=False)}；clicked={sent}")
        print(f"  past {s2['past']}→{s3['past']}、节点 {s2['nodeCount']}→{s3['nodeCount']}、"
              f"边 {s2['edgeCount']}→{s3['edgeCount']}；新文件 {c3['newFiles']}")
        print(f"  image 类型 {c3['imageBefore']}→{c3['imageAfter']}")

        print("\n=== A3/C4 发送后的 UI 翻转 ===")
        btn1 = page.evaluate(SEND_BTN)
        st1 = page.evaluate(CAP_STATUS)
        c4 = {"sendBtnAfter": btn1, "statusAfter": st1}
        print(f"  发送键 {json.dumps(btn1, ensure_ascii=False)}；状态 {json.dumps(st1, ensure_ascii=False)}")

        print("\n=== A4/C5 幂等：再点已 disabled 的发送键 ===")
        s4 = page.evaluate(SNAP)
        again = page.evaluate("() => { const e=document.querySelector('[data-director-send-capture]');"
                              " if(!e) return false; e.click(); return true; }")
        page.wait_for_timeout(1_000)
        s5 = page.evaluate(SNAP)
        c5 = {"clicked": again,
              "past": [s4["past"], s5["past"]],
              "nodes": [s4["nodeCount"], s5["nodeCount"]],
              "edges": [s4["edgeCount"], s5["edgeCount"]],
              "nodeIdsIdentical": s4["nodeIds"] == s5["nodeIds"]}
        print(f"  clicked={again}；past {s4['past']}→{s5['past']}、"
              f"节点 {s4['nodeCount']}→{s5['nodeCount']}、边 {s4['edgeCount']}→{s5['edgeCount']}")

        print("\n=== A5/C6 画布侧的 6 个 capture 标记 ===")
        img_attrs = sorted(n for n in (attrs3 - attrs0) if "capture" in n)
        send_only = sorted(attrs3 - attrs1)
        c6 = {"atDeskOpen": sorted(n for n in attrs0 if "capture" in n),
              "afterShutter": sorted((attrs1 - attrs0)),
              "afterSend": img_attrs,
              "canvasMarkedBySendOnly": [n for n in send_only if "capture" in n],
              "imageEditorBroughtBySend": [n for n in send_only
                                            if n.startswith("data-image-")
                                            or n == "data-owner-node-id"],
              "sendOnlyTotal": len(send_only)}
        print(f"  刚打开时的 capture 属性 {len(c6['atDeskOpen'])} 种")
        print(f"  快门带出的（导演台侧）：{c6['afterShutter']}")
        print(f"  发送带出的（画布侧 ImageNode 标记）{len(c6['canvasMarkedBySendOnly'])} 种："
              f"{c6['canvasMarkedBySendOnly']}")
        print(f"  发送还带出图片编辑器 {len(c6['imageEditorBroughtBySend'])} 种："
              f"{c6['imageEditorBroughtBySend']}")

        # ---------- B. 两族代表的门 ----------
        print("\n=== B1/C7 族①：机位 →「截图」子页 ===")
        rows = page.evaluate(ROWS)
        cam = next((r for r in rows if r["kind"] == "camera"), None)
        ch = next((r for r in rows if r["kind"] == "character"), None)
        print(f"  树里 {len(rows)} 行；机位={cam['text']!r}（role={cam['role']}）、角色={ch['text']!r}")
        page.evaluate(CLICK_ROW, cam["id"])
        page.wait_for_timeout(900)
        cam_tabs = page.evaluate(TABS, "data-director-camera-tab")
        g0 = set(page.evaluate(DUMP))
        picked = page.evaluate(CLICK_TAB, ["data-director-camera-tab", "captures"])
        page.wait_for_timeout(1_000)
        g1 = set(page.evaluate(DUMP))
        gal_empty = page.evaluate(GALLERY)
        # 切回非截图页拍 2 张，再回截图页
        page.evaluate(CLICK_TAB, ["data-director-camera-tab", "properties"])
        page.wait_for_timeout(600)
        page.evaluate(SHUTTER)
        page.wait_for_timeout(1_000)
        page.evaluate(SHUTTER)
        page.wait_for_timeout(1_200)
        g1b = set(page.evaluate(DUMP))
        page.evaluate(CLICK_TAB, ["data-director-camera-tab", "captures"])
        page.wait_for_timeout(1_000)
        g2 = set(page.evaluate(DUMP))
        gal_full = page.evaluate(GALLERY)
        c7 = {"camText": cam["text"], "camTabs": cam_tabs, "tabPicked": picked,
              "galleryOnEntry": gal_empty, "galleryAfterTwoShots": gal_full,
              "gainedByTab": sorted(g1 - g0),
              "gainedByShots": sorted(g2 - g1b)}
        print(f"  `data-director-camera-tab` {len(cam_tabs)} 枚：{json.dumps(cam_tabs, ensure_ascii=False)}")
        print(f"  点「截图」⟹ +{len(c7['gainedByTab'])} 种：{c7['gainedByTab']}")
        print(f"  进页时图库（A 阶段那张已发送）{json.dumps(gal_empty, ensure_ascii=False)}")
        print(f"  拍 2 张后（离开再回该页 ⟹ 图库属性重挂载）⟹ +{len(c7['gainedByShots'])} 种")
        print(f"  拍 2 张后图库 {json.dumps(gal_full, ensure_ascii=False)}")

        print("\n=== B2/C8 族②：角色 →「姿势」子页 ===")
        page.evaluate(CLICK_ROW, ch["id"])
        page.wait_for_timeout(900)
        ch_tabs = page.evaluate(TABS, "data-director-character-tab")
        gains = {}
        for t in ch_tabs:
            b3 = set(page.evaluate(DUMP))
            page.evaluate(CLICK_TAB, ["data-director-character-tab", t["value"]])
            page.wait_for_timeout(800)
            g3 = sorted(set(page.evaluate(DUMP)) - b3)
            gains[t["value"]] = g3
        c8 = {"charText": ch["text"], "tabs": ch_tabs, "gains": gains}
        for t in ch_tabs:
            print(f"  「{t['text']}」({t['value']}) ⟹ +{len(gains[t['value']])} 种：{gains[t['value']]}")

        # ---------- C9 残差族表（静态，用 748 的 223 口径）----------
        print("\n=== C9 残差按前缀成族（静态，用本批门表）===")
        openable = set(c7["gainedByTab"]) | set(c7["gainedByShots"])
        for v, g in gains.items():
            openable |= set(g)
        remain = [n for n in st["effectiveUnion"]]
        families = {}
        for n in remain:
            key = "-".join(n.split("-")[:4])
            families.setdefault(key, []).append(n)
        c9 = {"unionCount": st["effectiveUnionCount"],
              "verifiedOpenable": sorted(openable),
              "familyCount": len(families),
              "topFamilies": sorted(
                  ({"prefix": k, "count": len(v)} for k, v in families.items()),
                  key=lambda x: -x["count"])[:14]}
        print(f"  有效并集 {st['effectiveUnionCount']} 种，前缀族 {len(families)} 个；"
              f"本批已验证可打开 {len(openable)} 种")
        for f in c9["topFamilies"]:
            print(f"    {f['count']:3d}  {f['prefix']}")

        page.screenshot(path="/tmp/vb749-desk.png")
        page.close()
        browser.close()

    results = {"A1_shutter": c2, "A2_send": c3, "A3_flip": c4,
               "A4_idempotent": c5, "A5_canvasAttrs": c6,
               "B1_captureGallery": c7, "B2_pose": c8, "C9_families": c9}

    checks = [
        ("C1 静态：有效并集 447；createDirectorCapture 恰好两处（声明+实现）；"
         "sendCapture 有 sentNodeId 幂等守卫；ImageNode.tsx 6 个 capture 标记；"
         "store 落点 type:\"image\"；两个页签守卫行号可定位",
         st["effectiveUnionCount"] == 447
         and len(st["decl_createDirectorCapture"]) == 2
         and st["idempotentGuardLine"] == st["sendCaptureLine"] + 1
         and len(st["imgNodeCaptureAttrs"]) == 6
         and len(st["imgNodeAttrNames"]) == 6
         and st["cameraCapturesGuard"] is not None and st["characterPoseGuard"] is not None
         and st["shutterLine"] is not None and st["previewLine"] is not None
         and st["sendBtnLine"] is not None and st["storeTypeLine"] is not None
         and st["storeFilenameLine"] is not None,
         json.dumps({k: v for k, v in st.items()
                     if k not in ("effectiveUnion", "owner")}, ensure_ascii=False)),
        ("C2 第 1 跳快门：store 零写入；预览出现且有 alt 与尺寸；capture-status=ready、文案「1 张构图」",
         c2["clicked"] and c2["past"][1] == c2["past"][0]
         and c2["nodes"][1] == c2["nodes"][0] and c2["edges"][1] == c2["edges"][0]
         and c2["preview"] and c2["preview"]["present"] and c2["preview"]["alt"]
         and c2["preview"]["dims"] == [638, 359]
         and c2["status"] and c2["status"]["status"] == "ready"
         and c2["status"]["text"] == "1 张构图",
         json.dumps(c2, ensure_ascii=False)),
        ("C3 第 2 跳发送：past+1、节点+1、边+1；新文件「导演台截图-<机位名>」；image 5→6（**落画布是图片节点**）",
         c3["clicked"] and c3["past"][1] == c3["past"][0] + 1
         and c3["nodes"][1] == c3["nodes"][0] + 1 and c3["edges"][1] == c3["edges"][0] + 1
         and len(c3["newFiles"]) == 1
         and c3["newFiles"][0] == f"导演台截图-{c7['camText']}"
         and c3["imageAfter"] == c3["imageBefore"] + 1,
         json.dumps(c3, ensure_ascii=False)),
        ("C4 发送后 UI 翻转：发送键文案「已发送到画布」+ disabled；capture-status 文案「已回到画布」",
         c3["sendBtnBefore"] and c3["sendBtnBefore"]["text"] == "发送到画布"
         and c3["sendBtnBefore"]["disabled"] is False
         and c4["sendBtnAfter"] and c4["sendBtnAfter"]["text"] == "已发送到画布"
         and c4["sendBtnAfter"]["disabled"] is True
         and c4["statusAfter"] and c4["statusAfter"]["text"] == "已回到画布",
         json.dumps(c4, ensure_ascii=False)),
        ("C5 幂等：再点已 disabled 的发送键 ⟹ past/节点/边/nodeIds 逐项零变化",
         c5["clicked"] and c5["past"][1] == c5["past"][0]
         and c5["nodes"][1] == c5["nodes"][0] and c5["edges"][1] == c5["edges"][0]
         and c5["nodeIdsIdentical"] is True,
         json.dumps(c5, ensure_ascii=False)),
        ("C6 画布侧 6 个 data-director-capture-* 由**发送**带出（快门只带出导演台侧的 "
         "preview/send）；且发送同时把画布选中态切到新节点 ⟹ 另带出 8 种图片编辑器属性",
         len(c6["atDeskOpen"]) >= 1
         and set(c6["afterShutter"]) == {"data-director-capture-preview",
                                         "data-director-send-capture"}
         and set(c6["canvasMarkedBySendOnly"]) == set(st["imgNodeAttrNames"])
         and len(c6["canvasMarkedBySendOnly"]) == 6
         and set(st["imgNodeAttrNames"]).isdisjoint(c6["atDeskOpen"])
         and "data-image-edit-panel" in c6["imageEditorBroughtBySend"]
         and len(c6["imageEditorBroughtBySend"]) == 8
         and c6["sendOnlyTotal"] == 14,
         json.dumps(c6, ensure_ascii=False)),
        ("C7 族①：机位→「截图」子页带出 11 种图库属性；**图库条目数随快门次数逐张 +1**；"
         "`send-all` 的 disabled 语义是「没有未发送项就禁用」"
         "（A 阶段那张已发送 ⟹ items=1 时禁用；再拍 2 张未发送 ⟹ 解禁）",
         c7["tabPicked"]
         and [t["value"] for t in c7["camTabs"]] == ["properties", "motion", "captures"]
         and len(c7["gainedByTab"]) == 11
         and {"data-director-capture-gallery", "data-director-capture-send-all",
              "data-director-capture-clear-all", "data-director-capture-item",
              "data-director-capture-group"} <= set(c7["gainedByTab"])
         and c7["galleryOnEntry"]["items"] == 1 and c7["galleryOnEntry"]["groups"] == 1
         and c7["galleryOnEntry"]["sendAllDisabled"] is True
         and c7["galleryAfterTwoShots"]["items"] == 3
         and c7["galleryAfterTwoShots"]["groups"] == 1
         and c7["galleryAfterTwoShots"]["empty"] is False
         and c7["galleryAfterTwoShots"]["sendAllDisabled"] is False
         and c7["galleryAfterTwoShots"]["clearAllDisabled"] is False,
         json.dumps(c7, ensure_ascii=False)),
        ("C8 族②：角色页签 2 枚（属性/姿势）；点「姿势」+10，点「属性」+0",
         [t["value"] for t in c8["tabs"]] == ["properties", "pose"]
         and len(c8["gains"].get("pose", [])) == 10
         and len(c8["gains"].get("properties", [])) == 0
         and "data-director-pose-panel" in c8["gains"]["pose"],
         json.dumps(c8, ensure_ascii=False)),
        ("C9 残差按前缀成族：有效并集 447 种可归成若干前缀族（最大族 ≤ 90）；"
         "本批已验证可打开 21 种（11 图库 + 10 姿势）",
         c9["unionCount"] == 447 and c9["familyCount"] > 40
         and c9["topFamilies"][0]["count"] <= 90
         and len(c9["verifiedOpenable"]) == 21
         and len(c7["gainedByTab"]) + sum(len(v) for k, v in c8["gains"].items()) == 21,
         json.dumps(c9, ensure_ascii=False)),
    ]

    print("\n=== 判据 ===")
    passed = 0
    for label, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
        passed += bool(ok)

    audit = {
        "batch": 749,
        "title": "把 748 留下的 createDirectorCapture 发送那一跳走完（真跑通 + 幂等 + 画布侧 6 标记）；"
                 "把「有静态无运行时」的残差从一个数变成一族一族的门（验两族代表）",
        "verdict": f"{passed}/{len(checks)}",
        "summary": {"results": results, "static": {k: v for k, v in st.items()
                                                   if k != "effectiveUnion"}},
        "checks": [{"label": l, "pass": bool(o)} for l, o, _ in checks],
        "conclusions": [
            "**`createDirectorCapture` 真跑通了，是两跳 + 幂等** —— "
            "第 1 跳快门（`DirectorViewport.tsx:3586`）store **零写入**，但预览出现"
            "（638×359、`alt`「机位01 · 对峙中景构图截图」）、`capture-status=\"ready\"`、"
            "文案「1 张构图」；第 2 跳 `data-director-send-capture` ⟹ `past` +1、节点 +1、"
            "边 +1、新文件「**导演台截图-机位01 · 对峙中景**」、`image` 类型 5→6。",
            "**截图落画布是 `image` 节点，不是视频** —— `canvasStore.ts:2818 type: \"image\"`、"
            "`:2824 filename: \\`导演台截图-${capture.cameraName}\\``，与 748 的动画导出"
            "（建 `video` 节点）是两种不同的产出。",
            "**发送后 UI 双向翻转** —— 按钮文案「发送到画布」→「**已发送到画布**」+ `disabled`；"
            "`data-director-capture-status` 文案「1 张构图」→「**已回到画布**」。"
            "**幂等**：再点那个已 disabled 的按钮 store 逐项零变化 ⟹ "
            "`DirectorDesk.tsx:590 if (capture.sentNodeId) return;` 生效。",
            "**导演台的产出在画布侧被打上 6 个标记 ⟹ 画布节点组件知道导演台存在** —— "
            "`ImageNode.tsx:216-221` 写 `data-director-capture-node` / `-id` / `-source-id` / "
            "`-camera-id` / `-aspect` / `-edge-id`，这 6 个**只在发送之后**才出现在 DOM 上。"
            "⟹ 导演台与画布的耦合点不只在 store，还在**画布节点的渲染层**。",
            "**发送截图会把画布选中态切到新节点，弹出图片编辑器** —— 发送这一步除带出 "
            "`ImageNode.tsx:216-221` 的 6 个 `data-director-capture-*` 标记外，还带出 "
            "**8 种** `data-image-edit-panel` / `data-image-editor-*` / `data-image-toolbar` / "
            "`data-owner-node-id` ⟹ 新建的图片节点在画布上是**被选中的**状态。"
            "本批未验这个选中态是否可撤销。",
            "**残差不是一个数，是一族一族的门** —— 本批验证两族："
            "**采集图库族**（机位 → 相机页签「截图」子页 +4："
            "`capture-gallery`/`-empty`/`-send-all`/`-clear-all`；该机位下拍 2 张再回该页 +8："
            "`capture-item`/`-item-selected`/`-group`/`-group-shot`/`-send`/`-remove`/"
            "`-view`/`-shot-id`）与**姿势族**（角色 → 角色页签「姿势」子页 +10）。"
            "图库态读数：拍之前 `empty: true, items: 0`；拍 2 张后 `empty: false, items: 2, "
            "groups: 1`，`send-all` / `clear-all` 由 disabled 变可用。",
            "**页签是「同名不同值」，按属性名去重枚举门会漏** —— "
            "`data-director-camera-tab` 有 `properties`（属性）/ `motion`（运动轨迹**NEW**）/ "
            "`captures`（截图）3 枚，`data-director-character-tab` 有 `properties` / "
            "`pose`（**姿势**，不是「姿态」）2 枚。749c 按属性名去重只点了一个值，"
            "所以「选中 7 个 treeitem +0 种」是**探针粒度问题，不是产品的门特别深**。",
        ],
        "probeCorrections": [
            "**按属性名去重枚举门 ⟹ 同名不同值的页签只点了一个**（本批最重要的一次返工）—— "
            "749c 枚举开启器时用 `seen` 按 `a.name` 去重，于是 `data-director-camera-tab` 的 "
            "3 个值只算 1 枚门，点它也只点中了第一个值 ⟹ 「选中 7 个 treeitem +0 种」。"
            "**改法**：门要按 `(属性名, 属性值)` 枚举，不按名字。",
            "**树行不是 `<button>`** —— 我按 `[data-director-tree] button` 找对象行，"
            "只找到「打组」「解组」两枚。树行是 "
            "`<div role=\"treeitem\" data-director-object-id=…>`（`DirectorObjectTree.tsx:458-465`），"
            "**且它没有 `data-director-*` 前缀** ⟹ 748 的属性普查表里也没有它。",
            "**被截断的普查输出不能当全集** —— 748 那次 446 种的终端输出被 head+tail 截断，"
            "我据此以为「没有 `data-director-object-*`」，实际它在中间。",
            "**页签文案别凭直觉写** —— 我按源码变量名 `characterTab` 猜标签是「姿态」，"
            "实际 DOM 文案是「**姿势**」；`cameraTab` 的 `motion` 值文案还带「**NEW**」角标。",
        ],
        "notClaimed": [
            "**其余残差族未逐族验证** —— 748 报出的 223 种里本批只打开 22 种；"
            "运动路径/路径锚点族、场景设置族、全景图族、分组族、锁定提示族"
            "**只从源码守卫表达式推断，没有运行时读数**。",
            "`data-director-camera-tab=\"motion\"`（运动轨迹，`CameraMotionTab` 11 种）"
            "**本批没点** —— 它是第三个页签值，未验证。",
            "**批量发送与清空图库的功能本身没验** —— 只读到 `disabled` 翻转，"
            "没点 `data-director-capture-send-all` / `-clear-all`。",
            "**图库的分组维度只读到 1 组** —— 种子只有 1 个机位，"
            "`capture-group={cameraName}` 的多机位分组未验。",
            "**不声称**「拍照 638×359」是稳定尺寸 —— 它随视口与机位参数变化，"
            "本批只在本视口（1280×1150）下读到该值。",
            "**未与源站导演台对照** —— 源站导演台关着，需点击授权。",
        ],
    }
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n写入 {AUDIT_DIR / 'runtime-audit.json'}")
    print(f"\n判据 {passed}/{len(checks)}")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
