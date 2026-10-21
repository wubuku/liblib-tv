#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 836 clone 侧探针：读 clone 的机位编号行为，并**验证它是不是 count+1**。

★ 与源站探针**同口径**：同样的「造出多台 → 删掉中间那台 → 新建 → 看编号」实验，
同样的**硬前提**（删后编号必须不连续，否则实验无效、不下结论）。

★ 本探针**直接读 store**（`window.__libtv_store`）而不是 DOM ——
  ⟹ 因为「机位名」在 clone 里是 store 里的 `authoredObjects[].name`，
     读 DOM 会拿到渲染层的别的东西（batch 833 已经踩过「读数器定位不到右栏」那个坑）。
"""
import json
import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BASE = "http://localhost:4317"
OUT = pathlib.Path("/tmp/b836-clone-camnum.json")
CAM_RE = re.compile(r"^机位\s*(\d+)$")

# ★ 读 store 里的机位（名字 + 顺序）
DUMP_CAMS = """() => {
  const s = window.__director_store.getState();
  const cams = (s.authoredObjects||[]).filter(o=>o.kind==='camera');
  return cams.map(o=>({id:o.id, name:o.name}));
}"""

# ★ 调 store 的命令：新建一台机位（等价于点 rail「添加机位」的第一枚预设）
ADD_CAM = """() => {
  const s = window.__director_store.getState();
  const r = s.addDirectorCamera();
  return {ok: !!(r && r.ok !== false), result: r ? String(r.kind||r.commandKind||'') : null};
}"""


def nums_of(cams):
    out = []
    for c in cams:
        m = CAM_RE.match(c["name"] or "")
        if m:
            out.append(int(m.group(1)))
    return sorted(out)


def has_gap(nums):
    if len(nums) < 2:
        return False
    s = sorted(nums)
    return any(b - a > 1 for a, b in zip(s, s[1:]))


def main():
    out = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.goto(BASE + "/?batch836=1", wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
        page.wait_for_function("() => Boolean(window.__libtv_store && window.__director_store)",
                               timeout=60_000)
        # 打开导演台
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

        base = page.evaluate(DUMP_CAMS)
        out["①基线"] = base
        out["①基线编号"] = nums_of(base)
        print("基线机位：", base)

        # 造出 3 台
        for _ in range(3):
            page.evaluate(ADD_CAM)
            page.wait_for_timeout(500)
        cams = page.evaluate(DUMP_CAMS)
        out["②造出三台"] = cams
        out["②编号"] = nums_of(cams)
        print("三台：", cams)

        # ★ 删掉「编号第二小」的那台 ⟹ 制造空洞
        nums = nums_of(cams)
        victim_num = nums[1] if len(nums) >= 3 else None
        victim_name = "机位%d" % victim_num
        out["③要删的"] = victim_name
        # 找它的 id
        vid = next((c["id"] for c in cams if c["name"] == victim_name), None)
        out["③被删的id"] = vid
        if vid:
            page.evaluate("""(id) => {
                const s = window.__director_store.getState();
                const r = s.deleteDirectorEntity({kind:'DELETE_OBJECT', objectId:id});
                return r ? String(r.disposition||'') : 'NO_RESULT';
            }""", vid)
            page.wait_for_timeout(700)
        out["③删除结果"] = page.evaluate(DUMP_CAMS)
        cams4 = out["③删除结果"]
        nums4 = nums_of(cams4)
        out["③删后编号"] = nums4
        print("删后：", cams4)

        gap = has_gap(nums4)
        out["③有编号空洞"] = gap
        if not gap:
            out["④实验无效"] = "删后编号 %r 不连续 ⟹ 没做出空洞 ⟹ 不下结论" % (nums4,)
            print("★ 实验无效（删后编号不连续）")
        else:
            page.evaluate(ADD_CAM)
            page.wait_for_timeout(600)
            cams5 = page.evaluate(DUMP_CAMS)
            out["④空洞态新建后"] = cams5
            new_num = None
            for c in cams5:
                if c["id"] != vid and c["id"] not in {x["id"] for x in cams4}:
                    m = CAM_RE.match(c["name"] or "")
                    if m:
                        new_num = int(m.group(1))
            out["④新机位编号"] = new_num
            dup = new_num is not None and new_num in nums4
            out["⑤判定"] = {
                "前提_删后编号不连续": True,
                "删后已有的编号": nums4,
                "新机位编号": new_num,
                "与已有编号重名": dup,
                "规则": ("count+1（**会与已有编号重名**）" if dup
                         else "max+1（不重名）" if new_num is not None else "读不到"),
            }
            print("判定：", json.dumps(out["⑤判定"], ensure_ascii=False))
        page.close()
        ctx.close()
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
