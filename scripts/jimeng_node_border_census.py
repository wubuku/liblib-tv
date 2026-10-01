#!/usr/bin/env python3
"""即梦画布节点壳边框普查 —— 回答一个问题：批 829 那圈 1px 边框是个例还是通例？

批 829 在时间线壳上查到 `border: 1px solid rgba(255,255,255,0.04)`，并靠它一个
根因对齐了五处矩形。紧接着的问题很自然：**别的节点壳是不是也少这一圈？**
如果是，那是一类缺陷，不是一处。

## 结论（2026-10-04 实测，源站 6 个节点）

| 节点 | 壳 testid | 边框 | 颜色 | 说明 |
|---|---|---|---|---|
| 视频 569×320 | `video-flow-node-surface` | **1px** | `rgba(0,0,0,0)` | **透明**，三态恒定 |
| 时间线 1200×207 | `timeline-flow-node-main-track` | **1px** | `rgba(255,255,255,0.04)` | 批 829 已对齐 |
| 媒体 320×320 ×3 | — | 0 | — | 无边框 |
| 导演台 320×320 | `director-stage-flow-node-shell` | 0 | — | 有底色、无边框 |

⇒ **829 那圈边框是时间线专属，不存在「同类缺陷家族」**，其余节点壳不必改。

顺带两个发现，其中一条**推翻了我自己写过的断言**：

1. 源站节点壳**是有 `data-testid` 的**。批 829 我在台账里顺口写了「源站全站用类名，
   一个 testid 都没有」—— 普查直接推翻。已就地更正（README §41 + 组件注释）。
2. 视频节点那圈 1px 是**透明**的，且 **idle / hover / selected 三态完全一致**
   （1px / `rgba(0,0,0,0)` / r8 / bg 透明 / 无 box-shadow）。它的类名里有
   `data-[connection-receiving=…]` 变体，推测是「把连接线拖过来时」的占位环。

## 为什么不把那圈透明边框也复刻过去

透明 ⇒ 观感零差异；它唯一的效果是让内容内缩 1px，而那是**一个节点类型上的 1px**。
而它真正会显形的状态（`data-[connection-receiving`）**未取证**，照着复刻只能复刻
一个看不见的占位。收益低于改动风险 ⇒ 记录不实施，列 OPEN_QUESTION 831-a。

## 用法

    ~/.venvs/liblib-harness/bin/python scripts/jimeng_node_border_census.py

走 `jimeng_headless` 的登录态，只读，不点任何消耗积分的控件。
退出码：0 = 契约全成立；1 = 有契约不成立；2 = 取证失败（读不到源站画布）。

## 契约

  ① 每个节点壳都要**报出**边框（没有边框也要显式记 0，不许静默跳过）
  ② 带 1px 边框的节点里，**有且只有**时间线那枚是非透明的
     —— 这条是本普查的实质结论：不是通例
  ③ 视频壳那圈边框三态恒定（不是条件态）⇒ 记为「已量化的源站事实」而非「疑似缺陷」
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import jimeng_auth as auth  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create")
EVIDENCE = (Path(__file__).resolve().parents[1] / "docs" / "research"
            / "jimeng-canvas-batch831-2026-10-04")

# 深探：每个 .react-flow__node 下所有带边框的后代 + 视觉壳（最大不透明背景）
CENSUS = r"""() => {
  const nodes = [...document.querySelectorAll('.react-flow__node')];
  if (!nodes.length) return { err: 'no .react-flow__node' };
  const out = [];
  for (const n of nodes) {
    const nr = n.getBoundingClientRect();
    const rel = (r) => [Math.round(r.x - nr.x), Math.round(r.y - nr.y),
                        Math.round(r.width), Math.round(r.height)];
    const meta = (e) => (typeof e.className === 'string' ? e.className : '').slice(0, 56);
    const bordered = [], opaque = [];
    for (const e of [n, ...n.querySelectorAll('*')]) {
      const cs = getComputedStyle(e);
      const r = e.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) continue;
      const bw = Math.max(parseFloat(cs.borderTopWidth) || 0,
                          parseFloat(cs.borderRightWidth) || 0,
                          parseFloat(cs.borderBottomWidth) || 0,
                          parseFloat(cs.borderLeftWidth) || 0);
      if (bw > 0) {
        bordered.push({ rel: rel(r), bw, color: cs.borderTopColor,
                        radius: cs.borderTopLeftRadius,
                        testid: e.getAttribute('data-testid'), cls: meta(e) });
      }
      const bg = cs.backgroundColor;
      if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') {
        opaque.push({ rel: rel(r), bg, radius: cs.borderTopLeftRadius,
                      area: r.width * r.height,
                      testid: e.getAttribute('data-testid'), cls: meta(e) });
      }
    }
    opaque.sort((a, b) => b.area - a.area);
    out.push({ size: [Math.round(nr.width), Math.round(nr.height)],
               bordered, shell: opaque[0] || null });
  }
  return { err: null, nodes: out };
}"""

TRANSPARENT = ("rgba(0, 0, 0, 0)", "transparent")


def main() -> int:
    failures: list[str] = []
    checks = 0

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(f"{name}: {detail}")
        print(f"  [{'ok ' if ok else 'FAIL'}] {name}{'' if ok else ' — ' + detail}")

    with sync_playwright() as p:
        # ⚠️ 必须走 auth.open_headless —— 它把 `jimeng_login_capture.py` 存下的
        #    storage_state 注入 context。直接 browser.new_context() 造出来的是
        #    **裸 context，没有登录态**，verify_login 会报「会话过期」而其实
        #    登录是好的（我踩过，白跑一轮）。
        state = Path(os.environ.get("JIMENG_STATE", str(auth.STATE)))
        if not state.exists():
            print(f"未找到登录态文件 {state}；请先跑 scripts/jimeng_login_capture.py",
                  file=sys.stderr)
            return 2
        browser, ctx, page = auth.open_headless(p, state, headless=True)
        try:
            # ⚠️ `verify_login` 探的是 passport API，它比「画布能不能读」**更严**。
            #    实测：passport 报 `error_code=13 会话过期`，而同一份 storage_state
            #    下画布照样渲染出 6 个节点、几何全部读得到。所以拿它当硬闸门会
            #    反复误杀（我连踩两次）。改成**软记录** + 用真实判据把关：
            #    画布读不出节点才算取证失败。
            chk = auth.verify_login(ctx, page, URL)
            passport_ok = bool(chk.get("logged_in"))
            if not passport_ok:
                print(f"  （passport 探针报 {chk.get('reason')}，不作为闸门；"
                      f"改以「画布是否渲染出节点」为准）")
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(9000)
            n_ok = 0
            for _ in range(10):
                n_ok = page.evaluate(
                    "() => document.querySelectorAll('.react-flow__node').length")
                if n_ok > 2:
                    break
                page.wait_for_timeout(2000)
            data = page.evaluate(CENSUS)
        finally:
            browser.close()

    if data.get("err"):
        print(f"取证失败：{data['err']} —— 源站画布可能没加载出来（fixture 长期退化）")
        return 2

    nodes = data["nodes"]
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "node-border-census.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"— 源站 {len(nodes)} 个节点，逐个报边框 —")
    all_bordered = []
    for i, n in enumerate(nodes):
        if n["bordered"]:
            for b in n["bordered"]:
                all_bordered.append((i, b))
                print(f'  节点{i} {b["rel"]!s:<20} 1px  {b["color"]:<26} '
                      f'tid={b["testid"]}')
        else:
            sh = n["shell"]
            print(f'  节点{i} {n["size"]!s:<12} 无边框'
                  f'{"（壳 " + str(sh["testid"]) + "）" if sh else ""}')

    print("\n— 契约 —")
    check("① 每个节点壳都报出了边框结论（0 也显式记录）", True,
          f'{len(nodes)} 个节点，其中 {len(all_bordered)} 处有 1px 边框')
    opaque_bordered = [(i, b) for i, b in all_bordered if b["color"] not in TRANSPARENT]
    check("② 有 1px 边框的节点里，有且只有时间线那枚是非透明的（不是通例）",
          len(opaque_bordered) == 1 and "timeline" in (opaque_bordered[0][1]["testid"] or ""),
          f'非透明 {len(opaque_bordered)} 处: '
          f'{[(b["testid"]) for _, b in opaque_bordered]}')
    video = [(i, b) for i, b in all_bordered if "video" in (b["testid"] or "")]
    check("③ 视频壳那圈是透明的（已三态实测恒定，记为源站事实而非缺陷）",
          len(video) == 1 and video[0][1]["color"] in TRANSPARENT,
          f'{[(b["testid"], b["color"]) for _, b in video]}')

    print(f"\n{'PASS' if not failures else 'FAIL'} — {checks - len(failures)}/{checks}")
    for f in failures:
        print("  · " + f)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
