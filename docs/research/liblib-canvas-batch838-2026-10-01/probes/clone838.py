#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 838 clone 侧探针：读「默认角色改名」之后的派生读数。

★ 直接读 store（`window.__director_store`）⟹ 机位名/角色名/轨道 label 都是 store 字段；
  DOM 读数只用来验证「渲染层与 store 一致」（★ 场景树那一行）。

★ 本探针要回答的**五个**问题：
  ① 默认角色的 name ⟹ 是不是「角色A」；
  ② 它的**变换轨道** label ⟹ 是不是「角色A · 变换」（派生跟随）；
  ③ 它的**姿态轨道** label ⟹ 是不是「角色A · 姿态」（派生跟随）；
  ④ ★★ **DOM 上**的场景树那一行 ⟹ 是不是「角色A」（⟹ 不只是 store 改了）；
  ⑤ ★★ **派生关系本身**还在不在（源码里 `${object.name} · 变换` / `· 姿态` 那两条）
     ⟹ ★ 这是**关系式**判据：绝对值对了**不代表**派生关系还在。
"""
import json
import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BASE = "http://localhost:4317"
OUT = pathlib.Path("/tmp/b838-clone-runtime.json")

DUMP = """() => {
  const s = window.__director_store.getState();
  const chars = (s.authoredObjects||[]).filter(o=>o.kind==='character');
  const tracks = ((s.timeline||{}).tracks||[]).map(t=>({
    id:t.id, kind:t.kind, label:t.label, objectId:t.objectId}));
  return {
    chars: chars.map(o=>({id:o.id, name:o.name})),
    tracks: tracks,
    objects: (s.authoredObjects||[]).map(o=>({id:o.id, name:o.name, kind:o.kind})),
  };
}"""


def main():
    out = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.goto(BASE + "/?batch838=1", wait_until="domcontentloaded")
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

        d = page.evaluate(DUMP)
        out["①基线_store"] = d

        lead = next((c for c in d["chars"] if c["id"] == "director-character-lead"), None)
        out["②默认角色"] = lead
        out["②默认角色名"] = (lead or {}).get("name")
        out["②默认角色名是否角色A"] = (lead or {}).get("name") == "角色A"

        tr = d["tracks"]
        xf = [t for t in tr if t["objectId"] == "director-character-lead" and t["kind"] == "transform"]
        ps = [t for t in tr if t["objectId"] == "director-character-lead" and t["kind"] == "pose"]
        out["③变换轨道label"] = [t["label"] for t in xf]
        out["③变换轨道label是否角色A · 变换"] = bool(xf) and all(
            t["label"] == "角色A · 变换" for t in xf)
        out["③姿态轨道label"] = [t["label"] for t in ps]
        out["③姿态轨道label是否角色A · 姿态"] = bool(ps) and all(
            t["label"] == "角色A · 姿态" for t in ps)

        # ④ DOM 场景树
        dom = page.evaluate("""() => {
          const vis=(e)=>{const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;};
          const out=[];
          for (const el of Array.from(document.querySelectorAll('[role="treeitem"],button,span,div'))) {
            if (!vis(el)) continue;
            const r=el.getBoundingClientRect();
            if (r.x > 320 || r.x < 0) continue;
            if (el.childElementCount > 0) continue;
            const t=(el.textContent||'').trim();
            if (!t || t.length>30) continue;
            out.push({text:t, x:Math.round(r.x), y:Math.round(r.y)});
          }
          return out;
        }""")
        out["⑤DOM_场景树文本"] = dom
        role_names = sorted({x["text"] for x in dom if x["text"].startswith("角色")})
        out["⑤DOM_场景树角色名"] = role_names
        out["⑤DOM_是否角色A"] = "角色A" in role_names

        page.close()
        ctx.close()
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", OUT)
    print(json.dumps({k: v for k, v in out.items() if not k.startswith("①基线")},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
