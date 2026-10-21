#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 837 clone 侧探针：读「默认机位改名」之后，clone 的**四个派生读数**。

★ 直接读 store（`window.__director_store`）——机位名、镜头名、轨道 label 都是
  store 字段；DOM 读数只用来验证「渲染层与 store 一致」。

★ 本探针要回答的**四个**问题（缺一不可）：
  ① 默认机位的 name  ⟹ 是不是「机位1」；
  ② 默认机位**派生**的镜头名 ⟹ 是不是「机位1 · 镜头」（跟着改没有）；
  ③ 默认机位**派生**的轨道 label ⟹ 是不是「机位1 · 机位」（跟着改没有）；
  ④ ★★ **编号体系错位是否随之消失**：batch 836 记过一条「clone 那台默认机位
     **不占编号**（名字不匹配 ^机位\\d+$）⟹ 两边「编号 2」指向的机位序号不同」；
     改名成「机位1」后，clone 这台**占编号 1** ⟹ 这条错位**应当消失**。
     ★ 这一条是**推论**，必须**实测**（读默认机位名是否匹配正则 ＋ 新建一台是否叫「机位2」）
     ⟹ 不许只靠推理写结论。

★ 口径纪律（承 batch 836 的教训）：
  - 编号用 `^机位(\d+)$` 读**名字**；同时读**台数**（与名字无关的口径）做交叉校验；
  - 每一步读数都记下**读数来源**（store 字段名），不混口径。
"""
import json
import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BASE = "http://localhost:4317"
OUT = pathlib.Path("/tmp/b837-clone-runtime.json")
CAM_RE = re.compile(r"^机位(\d+)$")

DUMP = """() => {
  const s = window.__director_store.getState();
  const cams = (s.authoredObjects||[]).filter(o=>o.kind==='camera');
  const shots = (s.shots||[]).map(x=>({id:x.id, name:x.name, cameraId:x.cameraId}));
  const tracks = ((s.timeline||{}).tracks||[]).map(t=>({id:t.id, kind:t.kind, label:t.label, objectId:t.objectId}));
  return {
    cams: cams.map(o=>({id:o.id, name:o.name})),
    shots: shots,
    tracks: tracks,
    activeCameraId: s.activeCameraId,
    activeShotId: s.activeShotId,
    // ★ 与名字无关的口径：台数
    cameraCount: cams.length,
  };
}"""

ADD_CAM = """() => {
  const s = window.__director_store.getState();
  const r = s.addDirectorCamera();
  return {ok: !!(r && r.ok !== false), disposition: r ? String(r.disposition||'') : null};
}"""


def nums_of(cams):
    out = []
    for c in cams:
        m = CAM_RE.match(c["name"] or "")
        if m:
            out.append(int(m.group(1)))
    return sorted(out)


def main():
    out = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.goto(BASE + "/?batch837=1", wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
        page.wait_for_function("() => Boolean(window.__libtv_store && window.__director_store)",
                               timeout=60_000)
        page.evaluate("""() => {
            const cands = [...document.querySelectorAll('button,[role="button"]')];
            const b = cands.find(e => e.getAttribute('data-open-director') ||
                (e.textContent||'').includes('打开导演台') || (e.textContent||'').includes('导演台'));
            if (b) { b.click(); return true; } return false; }""")
        page.wait_for_timeout(1800)
        page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
        opened = page.evaluate("() => Boolean(document.querySelector('[data-director-workspace]'))")
        out["导演台已打开"] = opened
        if not opened:
            print("★ 导演台没打开")
            br.close()
            return 2

        base = page.evaluate(DUMP)
        out["①基线_store"] = base
        print("基线机位：", base["cams"])

        default_cam = next((c for c in base["cams"] if c["id"] == "director-camera-main"), None)
        out["②默认机位"] = default_cam
        default_name = (default_cam or {}).get("name")
        out["②默认机位名"] = default_name
        out["②默认机位名是否机位1"] = default_name == "机位1"
        out["②默认机位名是否匹配编号正则"] = bool(default_name and CAM_RE.match(default_name))
        out["②默认机位名是否仍含对峙中景"] = bool(default_name and "对峙中景" in default_name)

        # ③ 派生：镜头名 + 轨道 label
        shots = base["shots"]
        cam_shots = [s for s in shots if s["cameraId"] == "director-camera-main"]
        out["③默认机位的镜头"] = cam_shots
        out["③镜头名"] = [s["name"] for s in cam_shots]
        out["③镜头名是否机位1 · 镜头"] = all(s["name"] == "机位1 · 镜头" for s in cam_shots) and bool(cam_shots)
        cam_tracks = [t for t in base["tracks"] if t["objectId"] == "director-camera-main"]
        out["③默认机位的轨道"] = cam_tracks
        out["③轨道label"] = [t["label"] for t in cam_tracks]
        out["③轨道label是否机位1 · 机位"] = all(t["label"] == "机位1 · 机位" for t in cam_tracks) and bool(cam_tracks)

        # ④ ★★ 编号体系错位是否消失：新建一台 ⟹ 名字应叫「机位2」
        #    ★ 前提：默认机位名匹配 ^机位\d+$ ⟹ 它占编号 1
        page.evaluate(ADD_CAM)
        page.wait_for_timeout(800)
        after = page.evaluate(DUMP)
        out["④新建后机位"] = after["cams"]
        out["④新建后台数_与名字无关的口径"] = after["cameraCount"]
        out["④新建后编号"] = nums_of(after["cams"])
        new_cams = [c for c in after["cams"] if c["id"] != "director-camera-main"]
        # 新建的那台 = 名字是「机位N」且 id 不是默认机位的那台（取 id 排序后最新）
        new_cams_sorted = sorted(new_cams, key=lambda c: c["id"])
        new_name = new_cams_sorted[-1]["name"] if new_cams_sorted else None
        out["④新机位名"] = new_name
        out["④新机位名是否机位2"] = new_name == "机位2"
        out["④★编号体系错位是否消失"] = (
            bool(default_name and CAM_RE.match(default_name))
            and new_name == "机位2"
        )
        out["④★错位判定依据"] = (
            "默认机位名 %r 匹配 ^机位\\d+$ ⟹ 占编号 1；新建那台叫 %r ⟹ "
            "clone 的编号序列与源站（机位1→机位2）**逐字一致** ⟹ batch 836 记的"
            "「编号体系错位」**消失**"
            % (default_name, new_name)
        )

        # ⑤ DOM 渲染层是否与 store 一致（镜头条 chip 文本 + 轨道行标题）
        dom = page.evaluate("""() => {
          const chips = [...document.querySelectorAll('[data-director-shot-option]')]
            .map(e => (e.textContent||'').trim());
          const rows = [...document.querySelectorAll('[role="button"]')]
            .filter(e => (e.textContent||'').includes('机位'))
            .map(e => (e.textContent||'').trim());
          return {shotChips: chips, rowsWithCamera: rows.slice(0, 12)};
        }""")
        out["⑤DOM_镜头条chip"] = dom["shotChips"]
        out["⑤DOM_含机位的行"] = dom["rowsWithCamera"]
        out["⑤DOM含机位1 · 镜头"] = any("机位1 · 镜头" in t for t in dom["shotChips"])

        page.close()
        ctx.close()
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", OUT)
    print(json.dumps({k: v for k, v in out.items() if not k.startswith("①基线_store")},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
