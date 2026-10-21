#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 836 clone 侧对照之二：**默认机位可不可删**（在有 3 台时）。

★ 为什么单独测这个：源站 v2 实测「机位1 删不掉」⟹ 但那是在**只有 1 台**时 ⟹
  只证明「最后一台不可删」⟹ ★ **区分不了**「默认机位受保护」⟹ 需要源站 v3 的对照。

★ 探查报告显示 clone 的删除保护**只有**一条：
  `src/lib/directorDeletePlanner.ts:258` ⟹ `survivingCameras.length === 0` ⟹ `DIRECTOR_LAST_CAMERA_REQUIRED`
  ⟹ ★ **与被删对象是不是默认机位无关** ⟹ 「有 2 台时能删掉默认机位」⟹ 与源站**若真受保护**则是差异。

★ 本探针用**同一套实验**（造 3 台 → 删默认机位）⟹ 与源站 v3 **同口径**。
★ 只读 store ＋ 直接调命令 ⟹ 不点 UI ⟹ ★ 不声称「调命令 == 点 UI」，
  但本批只读**可删性**这一个结果，且两条路径共用同一个删除规划器。
"""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path("/tmp/b836-clone-default-deletable.json")

DUMP_CAMS = """() => {
  const s = window.__director_store.getState();
  return (s.authoredObjects||[]).filter(o=>o.kind==='camera')
    .map(o=>({id:o.id, name:o.name}));
}"""

ADD_CAM = """() => {
  const s = window.__director_store.getState();
  const r = s.addDirectorCamera();
  return r ? String(r.disposition||r.kind||'') : 'NO_RESULT';
}"""

DEL_CAM = """(id) => {
  const s = window.__director_store.getState();
  const r = s.deleteDirectorEntity({kind:'DELETE_OBJECT', objectId:id});
  return r ? String(r.disposition||'') : 'NO_RESULT';
}"""


def main():
    out = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.goto(BASE + "/?batch836b=1", wait_until="domcontentloaded")
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
        out["①基线"] = base
        print("基线：", base)

        # 造出 3 台
        for _ in range(2):
            page.evaluate(ADD_CAM)
            page.wait_for_timeout(500)
        cams = page.evaluate(DUMP_CAMS)
        out["②造出三台"] = cams
        print("三台：", cams)

        # ★ 删默认机位（director-camera-main）
        default_id = "director-camera-main"
        before_n = len(cams)
        disp = page.evaluate(DEL_CAM, default_id)
        page.wait_for_timeout(700)
        after = page.evaluate(DUMP_CAMS)
        out["③删除默认机位的返回"] = disp
        out["③删后"] = after
        out["③前提_删之前有几台"] = before_n
        out["③默认机位可删"] = (len(after) == before_n - 1)
        out["③判定"] = (
            "★ clone 的默认机位**可删**（在有 %d 台时）⟹ clone **没有**「默认机位受保护」规则"
            "⟹ 与源站若「受保护」则是**实质差异**" % before_n
            if out["③默认机位可删"] else
            "clone 的默认机位**删不掉** ⟹ clone **也**有「默认机位受保护」规则")
        print("判定：", out["③判定"])

        # 再验证：只有一台时能不能删（应当被「最后一台机位」保护拒绝）
        while len(page.evaluate(DUMP_CAMS)) > 1:
            cams = page.evaluate(DUMP_CAMS)
            victim = next(c for c in cams if c["id"] != default_id)
            page.evaluate(DEL_CAM, victim["id"])
            page.wait_for_timeout(500)
        only = page.evaluate(DUMP_CAMS)
        disp_last = page.evaluate(DEL_CAM, default_id) if len(only) == 1 else "N/A"
        page.wait_for_timeout(500)
        out["④只剩一台时删它"] = {"台数": len(only), "返回": disp_last,
                              "删后": page.evaluate(DUMP_CAMS)}
        print("只剩一台时删它：", out["④只剩一台时删它"])

        page.close()
        ctx.close()
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
