#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 836 clone 侧运行时探针：★ **门禁自己跑这份**（不读任何外部缓存）。

★ 为什么要有这一支：门禁若去读一个预先算好的 JSON，
  那个 JSON 可能**过期**（代码改了它没变）⟹ **拿着过期读数报绿** ⟹
  「跑通了 ≠ 看到了」的又一形态。
  ⟹ 所以这一支**当场开浏览器、当场读、当场写**，门禁直接调它。

★ 实测四件事（顺序有讲究，见下）：
  ① 有 3 台时删**主机位** ⟹ 应被拒，理由 `DIRECTOR_PRIMARY_CAMERA_REQUIRED`；
  ② 有 3 台时删**非主机位** ⟹ 应成功（保护不能误伤）；
  ③ 只剩一台时删它 ⟹ 应被拒，理由**仍是** `DIRECTOR_LAST_CAMERA_REQUIRED`
     ⟹ ★ 新增那条**没有**绕开原有那条；
  ④ 主机位的名字与 id（记录用，便于核对）。

★ 顺序：先做 ②（删掉一台非主机位）会让台数变成 2 ⟹ 所以**先做 ①**（3 台时删主机位）⟹
  再做 ②（3 台时删非主机位）⟹ 最后 ③（清到只剩一台再删它）。
"""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path("/tmp/b836-clone-836-runtime.json")

DUMP_CAMS = """() => {
  const s = window.__director_store.getState();
  return (s.authoredObjects||[]).filter(o=>o.kind==='camera')
    .map(o=>({id:o.id, name:o.name}));
}"""

ADD_CAM = """() => {
  const s = window.__director_store.getState();
  const r = s.addDirectorCamera();
  return r ? String(r.disposition||'') : 'NO_RESULT';
}"""

DEL_CAM = """(id) => {
  const s = window.__director_store.getState();
  const r = s.deleteDirectorEntity({kind:'DELETE_OBJECT', objectId:id});
  return {
    disposition: r ? String(r.disposition||'') : 'NO_RESULT',
    reason: r ? String(r.reason||'') : '',
  };
}"""


def main():
    out = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.goto(BASE + "/?batch836c=1", wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
        page.wait_for_function("() => Boolean(window.__libtv_store && window.__director_store)",
                               timeout=60_000)
        page.evaluate("""() => {
            const cands = [...document.querySelectorAll('button,[role="button"]')];
            const b = cands.find(e => e.getAttribute('data-open-director') ||
                (e.textContent||'').includes('打开导演台') || (e.textContent||'').includes('导演台'));
            if (b) b.click(); }""")
        page.wait_for_timeout(1800)
        page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
        if not page.evaluate("() => Boolean(document.querySelector('[data-director-workspace]'))"):
            print("★ 导演台没打开")
            br.close()
            return 2

        base = page.evaluate(DUMP_CAMS)
        out["④主机位"] = next((c for c in base if c["id"] == "director-camera-main"), None)
        out["④基线全部"] = base

        # 造到 3 台
        for _ in range(2):
            page.evaluate(ADD_CAM)
            page.wait_for_timeout(500)
        cams = page.evaluate(DUMP_CAMS)
        out["①三台"] = cams

        # ---------- ① 有 3 台时删主机位 ----------
        r1 = page.evaluate(DEL_CAM, "director-camera-main")
        page.wait_for_timeout(600)
        after1 = page.evaluate(DUMP_CAMS)
        out["①删主机位_返回"] = r1["disposition"]
        out["①删主机位_理由"] = r1["reason"]
        out["①删主机位_前台数"] = len(cams)
        out["①删主机位_后台数"] = len(after1)
        out["①删主机位_前后台数"] = [len(cams), len(after1)]
        print("① 删主机位：", r1, len(cams), "→", len(after1))

        # ---------- ② 有 3 台时删非主机位 ----------
        victim = next((c for c in after1 if c["id"] != "director-camera-main"), None)
        if victim:
            r2 = page.evaluate(DEL_CAM, victim["id"])
            page.wait_for_timeout(600)
            after2 = page.evaluate(DUMP_CAMS)
            out["②删非主机位_返回"] = r2["disposition"]
            out["②删非主机位_理由"] = r2["reason"]
            out["②删非主机位_成功"] = len(after2) == len(after1) - 1
            out["②删非主机位_前台数"] = len(after1)
            out["②删非主机位_后台数"] = len(after2)
            out["②删非主机位_前后台数"] = [len(after1), len(after2)]
            out["②删的是"] = victim
            print("② 删非主机位：", r2, len(after1), "→", len(after2))
        else:
            out["②删非主机位_成功"] = False
            out["②_为何没做"] = "找不到非主机位的机位"

        # ---------- ③ 清到只剩主机位，再删它 ----------
        cur = page.evaluate(DUMP_CAMS)
        for c in list(cur):
            if c["id"] == "director-camera-main":
                continue
            if len(page.evaluate(DUMP_CAMS)) <= 1:
                break
            page.evaluate(DEL_CAM, c["id"])
            page.wait_for_timeout(400)
        left = page.evaluate(DUMP_CAMS)
        out["③只剩"] = left
        if len(left) == 1 and left[0]["id"] == "director-camera-main":
            r3 = page.evaluate(DEL_CAM, "director-camera-main")
            page.wait_for_timeout(500)
            out["③只剩一台_返回"] = r3["disposition"]
            out["③只剩一台_理由"] = r3["reason"]
            out["③只剩一台_后台数"] = len(page.evaluate(DUMP_CAMS))
            print("③ 只剩一台时删它：", r3)
        else:
            out["③只剩一台_返回"] = "SKIPPED"
            out["③_为何没做"] = "没清到只剩主机位（%r）" % (left,)

        page.close()
        ctx.close()
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
