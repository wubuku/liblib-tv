"""batch 839 取证：源站「添加参考」的条目列表**凭什么**才有内容？

838 已经确定：源站这块画布上每个分类都是「暂无相关节点」—— 连画布上明明存在的
「视频 1」都没列出来。所以「它列画布节点」这个推断不成立，本仓拒绝据此造数据
（台账 §55 的 838-b）。

本探针就是去把那个「凭什么」问出来。三个候选假设，一次跑完：

  H1 只列**选中**的节点        → 先选中「视频 1」再打开，条目里应出现它
  H2 列**画布上全部**同类节点  → 不选也该有（已排除：838 量到是空的）
  H3 需要先有**主体库/资产库** → 分类名带「库」字，可能走的是库而不是画布

顺手量一件事：选中态本身。源站节点选中后有没有可见变化（描边/高亮/工具条），
这也是复刻可以对照的。

⚠ 全程不点「发送」「生成」，不消耗积分；只点选中与打开浮层。

用法：
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
        scripts/jimeng_839_refsource.py
"""

from __future__ import annotations

import json
from pathlib import Path

OUT_DIR = Path("docs/research/jimeng-canvas-batch839-2026-10-04")
URL = (
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create"
)

# 画布节点：位置 + 选中态的可观测特征
NODES_JS = """() => [...document.querySelectorAll('[data-testid^="rf__node-"]')].map((n) => {
  const b = n.getBoundingClientRect();
  const cs = getComputedStyle(n);
  return { tid: n.getAttribute('data-testid'), role: n.getAttribute('role') || '',
           rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
           outline: cs.outline, borderColor: cs.borderColor, boxShadow: cs.boxShadow.slice(0, 50),
           ariaSelected: n.getAttribute('aria-selected'), cls: String(n.className || '').slice(0, 70),
           text: (n.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 40) };
})"""

# 添加参考的两块面板（几何定位，因为它没有 testid）
REF_JS = """() => {
  const cats = [], items = [];
  for (const el of document.querySelectorAll('div')) {
    const b = el.getBoundingClientRect();
    if (b.width !== 240) continue;
    if (b.x < innerWidth - 900 || b.y < 380 || b.y > 900) continue;
    const rows = [...el.querySelectorAll('li,button,[role="menuitem"],[role="option"]')]
      .map((n) => { const nb = n.getBoundingClientRect();
        return { text: (n.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 24),
                 rect: [Math.round(nb.x), Math.round(nb.y), Math.round(nb.width), Math.round(nb.height)] }; })
      .filter((r) => r.text);
    const entry = { rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
                    rows };
    if (rows.some((r) => ['主体','图片','视频','音频','文本'].includes(r.text))) cats.push(entry);
    else if (rows.length) items.push(entry);
  }
  return { categories: cats, items };
}"""


def open_ref(page) -> None:
    page.click('[data-testid="canvas-agent-composer-mention"]')
    page.wait_for_timeout(900)


def close_ref(page) -> None:
    # 点同一个触发器收起（批 835 记过：Escape 对这个面板无效）
    try:
        page.click('[data-testid="canvas-agent-composer-mention"]')
        page.wait_for_timeout(600)
    except Exception:  # noqa: BLE001
        pass


def main() -> int:
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    for _ in range(24):
        if not page.evaluate("() => document.body.innerText.includes('Loading canvas')"):
            break
        page.wait_for_timeout(2000)
    page.wait_for_timeout(2500)
    page.click('[data-testid="canvas-sidecar-launcher"]')
    page.wait_for_timeout(1500)

    report: dict = {"viewport": page.viewport_size, "steps": []}
    report["nodes_initial"] = page.evaluate(NODES_JS)

    # 基线：什么都不选，打开条目面板
    open_ref(page)
    report["steps"].append({"label": "① 未选中任何节点", **page.evaluate(REF_JS)})
    page.screenshot(path=str(OUT_DIR / "source-ref-none-selected.png"))
    close_ref(page)

    # H1：点选一个**视频**节点（画布上第一个就是「视频 1」），再打开
    nodes = report["nodes_initial"]
    video = next((n for n in nodes if "视频" in (n["text"] or "")), nodes[0] if nodes else None)
    report["picked_node"] = video
    if video:
        r = video["rect"]
        page.mouse.click(r[0] + r[2] / 2, r[1] + r[3] / 2)
        page.wait_for_timeout(900)
        report["nodes_after_click"] = page.evaluate(NODES_JS)
        page.screenshot(path=str(OUT_DIR / "source-ref-node-selected.png"))
        open_ref(page)
        report["steps"].append({"label": f"② 选中「{(video['text'] or '')[:12]}」之后",
                                **page.evaluate(REF_JS)})
        page.screenshot(path=str(OUT_DIR / "source-ref-with-selection.png"))
        close_ref(page)

    # 逐个分类过一遍：到底哪些分类有内容、排序如何、行什么样
    for kind in ("主体", "图片", "视频", "音频", "文本"):
        try:
            page.click(f'[data-testid="canvas-agent-composer-mention"]')
            page.wait_for_timeout(700)
            # 按文字点分类行（分类行没有 testid）
            hit = page.evaluate("""(kind) => {
              for (const el of document.querySelectorAll('li,button,[role="menuitem"],[role="option"]')) {
                if ((el.innerText || '').trim() !== kind) continue;
                const b = el.getBoundingClientRect();
                return [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)];
              }
              return null;
            }""", kind)
            if hit:
                page.mouse.click(hit[0] + hit[2] / 2, hit[1] + hit[3] / 2)
                page.wait_for_timeout(900)
                report["steps"].append({"label": f"③ 切到「{kind}」分类", **page.evaluate(REF_JS)})
                page.screenshot(path=str(OUT_DIR / f"source-ref-kind-{kind}.png"))
            close_ref(page)
        except Exception as exc:  # noqa: BLE001
            report["steps"].append({"label": f"③ 切到「{kind}」失败", "error": str(exc)[:120]})

    # 最后一件：点一个条目，看它往 composer 里放了什么（这是复刻要对齐的后果）
    try:
        page.click('[data-testid="canvas-agent-composer-mention"]')
        page.wait_for_timeout(700)
        hit = page.evaluate("""() => {
          for (const el of document.querySelectorAll('li,button,[role="menuitem"],[role="option"]')) {
            if ((el.innerText || '').trim() === '文本') {
              const b = el.getBoundingClientRect();
              return [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)];
            }
          }
          return null;
        }""")
        if hit:
            page.mouse.click(hit[0] + hit[2] / 2, hit[1] + hit[3] / 2)
            page.wait_for_timeout(800)
        item = page.evaluate("""() => {
          for (const el of document.querySelectorAll('li,button,[role="menuitem"],[role="option"]')) {
            if ((el.innerText || '').trim() === '文本 3') {
              const b = el.getBoundingClientRect();
              return [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)];
            }
          }
          return null;
        }""")
        report["item_rect"] = item
        if item:
            page.mouse.click(item[0] + item[2] / 2, item[1] + item[3] / 2)
            page.wait_for_timeout(1200)
        report["after_item_click"] = {
            "body_tail": page.evaluate("() => document.body.innerText.replace(/\\s+/g, ' ').slice(-200)"),
            "popover_gone": page.evaluate(
                """() => ![...document.querySelectorAll('li,button')].some((n) => {
                     const b = n.getBoundingClientRect();
                     return b.width === 240 && b.x > innerWidth - 900 && b.y > 380; })"""),
        }
        page.screenshot(path=str(OUT_DIR / "source-ref-item-clicked.png"))
    except Exception as exc:  # noqa: BLE001
        report["after_item_click"] = {"error": str(exc)[:160]}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "source-refsource-probe.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("画布节点:")
    for n in report["nodes_initial"]:
        print(f"   {n['tid']} {n['rect']} text={n['text']!r} outline={n['outline']}")
    for s in report["steps"]:
        print("===", s["label"])
        if s.get("error"):
            print("   ", s["error"]); continue
        for e in s.get("items", []):
            print(f"    条目面板 {e['rect']} 行={[r['text'] for r in e['rows']]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
