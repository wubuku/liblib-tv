#!/usr/bin/env python3
"""batch 865 第 0 步：把「这一层算不算**模态**」这个谓词**验出来**，不靠猜。

§82 抓到的两处修法之所以成立，依据都是「模态盖住了页面，就不该把焦点漏给
页面」。可这条依据现在只写在**注释**里 —— 审计的 `keyboard_no_initial_focus`
桶是**源站基线门控**的：源站没取过样的层，丢了焦点接管**不会**被报出来。
§82 的两个模态正好在基线表外 ⇒ 它们的修法**不是常备契约**，退回了一次性测量。

要让它们变成常备契约，得加一条**不依赖源站**的判据：「铺满视口且不透明的
浮层，必须接管焦点 + 困 Tab」。第一步就是把「铺满视口且不透明」这个谓词
**测准** —— 谓词不准，判据就是在制造假缺陷。

## 三种「不透明」要分开

1. 层**自己** `position:fixed; inset:0` + 不透明底（全屏预览）—— 模态。
2. 祖先铺满视口，其中某个**子元素**铺满视口且不透明（资产库：wrapper 无底、
   内含 `bg-black/55` 遮罩）—— 模态。
3. 祖先铺满视口且**自己不透明**（项目信息：它的祖先里就有页面根，
   画布背景不透明）—— **不是**模态。

第 3 条是关键陷阱：只看「祖先铺满视口 + 不透明」会把**每一个**层都算成模态，
判据立刻变成恒真。区分点必须是**位置**：真遮罩是 `position: fixed/absolute`
的独立浮层，页面根通常是 `static` / `relative`。

⚠️ 本探针**自己起浏览器**，只诊断不改产品。
跑法：/opt/miniconda3/bin/python3 scripts/jimeng_probe865_modalsh.py
"""

import json
import os
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "http://localhost:4317/jimeng/canvas/demo"
OUT = Path("/tmp/b865-modalsh.json")

# 谓词：从层元素往上走，找**定位过的**（fixed/absolute）铺满视口的祖先，
# 看它自己或它的孩子有没有不透明底。
MODALISH_JS = r"""
(tid) => {
  const el = document.querySelector(`[data-testid="${tid}"]`);
  if (!el) return {err: 'no layer'};
  const vw = innerWidth, vh = innerHeight;
  const opaque = (n) => {
    const bg = getComputedStyle(n).backgroundColor || '';
    return bg !== 'rgba(0, 0, 0, 0)' && !bg.startsWith('rgba(0, 0, 0, 0)');
  };
  const covers = (r) => r.width >= vw * 0.9 && r.height >= vh * 0.9;
  const positioned = (n) => {
    const p = getComputedStyle(n).position;
    return p === 'fixed' || p === 'absolute';
  };
  const trail = [];
  let verdict = {modalish: false, why: '没找到铺满视口且不透明的定位祖先'};
  for (let n = el; n && n !== document.body; n = n.parentElement) {
    const r = n.getBoundingClientRect();
    const s = getComputedStyle(n);
    const row = {tag: n.tagName, tid: n.getAttribute('data-testid') || '',
                 pos: s.position, w: Math.round(r.width), h: Math.round(r.height),
                 bg: s.backgroundColor, covers: covers(r),
                 self_opaque: opaque(n), positioned: positioned(n)};
    for (const c of n.children) {
      const cr = c.getBoundingClientRect();
      const cbg = getComputedStyle(c).backgroundColor || '';
      const cop = cbg !== 'rgba(0, 0, 0, 0)' && !cbg.startsWith('rgba(0, 0, 0, 0)');
      if (covers(cr) && cop) {
        row.kid = {cls: (c.className || '').toString().slice(0, 34), bg: cbg};
        row.kid_covers_opaque = true;
      }
    }
    trail.push(row);
    // 判据：**定位过的** + 铺满视口 + （自己不透明 或 有铺满视口的不透明孩子）
    if (positioned(n) && covers(r) && (opaque(n) || row.kid_covers_opaque)) {
      verdict = {modalish: true,
                 why: '定位祖先 ' + n.tagName
                       + (n.getAttribute('data-testid') ? '/'
                          + n.getAttribute('data-testid') : '')
                       + ' 铺满视口且不透明'};
      break;
    }
  }
  return {verdict, trail};
}
"""

# (名字, 打开路径, 期望 modalish)
CASES = [
    ("JimengAssetsModal",
     ['button[aria-label="资产库"]'], "jimeng-assets-modal", True,
     "有 bg-black/55 全屏遮罩 ⇒ 模态"),
    ("JimengProjectInfoModal",
     ['[data-testid="canvas-more-trigger"]', '[role="menuitem"]:text-is("项目信息")'],
     "project-info-modal", False,
     "居中 800×546、无遮罩 ⇒ 不是模态"),
    ("topbar-more-menu", ['[data-testid="canvas-more-trigger"]'],
     "topbar-more-menu", False, "顶栏下拉 ⇒ 不是模态"),
    ("canvas-zoom-menu", ['[data-testid="canvas-zoom-percent"]'],
     "canvas-zoom-menu", False, "缩放菜单 ⇒ 不是模态"),
]


def main() -> int:
    url = os.environ.get("SNAP_URL", URL)
    res = {"cases": {}}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context(viewport={"width": 1680, "height": 1050}).new_page()
        pg.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(4)
        print("===== 谓词实测（对照已知答案） =====")
        bad = 0
        for name, path, tid, want, why in CASES:
            pg.reload(wait_until="domcontentloaded", timeout=60000)
            time.sleep(3.2)
            for sel in path:
                el = pg.locator(sel).first
                el.wait_for(state="visible", timeout=8000)
                el.click()
                time.sleep(0.8)
            time.sleep(0.8)
            if pg.locator(f'[data-testid="{tid}"]').count() == 0:
                print(f"  {name}: ❌ 层 {tid} 没出现，跳过")
                res["cases"][name] = {"ok": False, "why": "层没出现"}
                continue
            r = pg.evaluate(MODALISH_JS, tid)
            v = r.get("verdict") or {}
            got = v.get("modalish")
            ok = got is want
            bad += (not ok)
            print(f"  {'OK ' if ok else 'BAD'} {name:<24} 期望={want!s:<5} 实测={got!s:<5}  {why}")
            print(f"      判据依据：{v.get('why')}")
            for row in (r.get("trail") or [])[:4]:
                kid = f" +不透明孩子({row['kid']['cls']})" if row.get("kid_covers_opaque") else ""
                print(f"        · {row['tag']}/{row['tid']} pos={row['pos']} "
                      f"{row['w']}×{row['h']} covers={row['covers']} "
                      f"自身不透明={row['self_opaque']}{kid}")
            res["cases"][name] = {"ok": ok, "expected": want, "got": got,
                                  "why_human": why, "verdict": v,
                                  "trail": r.get("trail")}
        b.close()
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n判错 {bad} 个 → 已写 {OUT}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
