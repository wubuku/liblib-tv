"""batch 835 源站普查：**默认态**与几枚「默认态点了没反应」的按钮。

起因：本地死按钮普查（`jimeng_dead_button_audit.py`）报
`canvas-sidecar-launcher` / `canvas-pointer-tool-toggle` 不可验证，但那条
理由是**复刻自己写下的**（「已是当前激活工具」「单独跑时集合会变」）——
**照抄自己写的豁免不构成证据**（批 826 照抄批 820 措辞，批 827 撤回过一次）。
所以本脚本去源站量四件事：

1. **画布加载完成后的默认态**：AI 面板开着还是关着？「与 AI 对话」药丸在不在？
2. **药丸的两态**：开态它还在不在？缩到多少？`aria-expanded` 怎么变？
   多次采样是为了区分**落定值**和**过渡动画中态**（批 831 记过「220ms 不够，
   AI 抽屉 400ms 才稳定」，同一个坑不该踩第二次）。
3. **药丸的父层链**：可见文字其实**不在** button 里（两态 `innerText` 都为空、
   内部没有 svg），所以只量 button 会漏掉背景药丸那一层 —— 只量 button 就会
   把一个 60×18 的残影当成「药丸尺寸」。
4. **底部 dock / 左栏**的真实 testid 清单（复刻左栏 9 枚一枚 testid 都没有，
   实测源站**也**没有 —— 这一点决定了不该为了可测性给复刻硬加源站 testid）。

⚠️ 全程只读 + 点不消耗积分的控件。**绝不点「生成」/「发送」**。

用法（`page` 由 jimeng_headless.py 注入，不要自己开 sync_playwright）：
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
        scripts/jimeng_835_canvas_census.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

OUT_DIR = Path("docs/research/jimeng-canvas-batch835-2026-10-04")
URL = (
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create"
)

# 面板/药丸/工具条的几何指纹（批 797/811 记的源站实测值）
PANEL_W = 400
PILL_W = 120
PILL_H = 36

CENSUS_JS = """() => {
  const r = (el) => { const b = el.getBoundingClientRect();
    return [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)]; };
  const name = (el) => (el.getAttribute('aria-label') || el.innerText || '').trim().slice(0, 24);
  const vis = (el) => { const s = getComputedStyle(el);
    return s.display !== 'none' && s.visibility !== 'hidden' && el.offsetParent !== null; };
  const out = { tids: [], buttons: [], dock: [], rail: [] };
  document.querySelectorAll('[data-testid]').forEach((el) => {
    if (vis(el)) out.tids.push({ tid: el.getAttribute('data-testid'), rect: r(el) });
  });
  document.querySelectorAll('button, [role="button"]').forEach((el) => {
    if (!vis(el)) return;
    const b = r(el);
    out.buttons.push({
      name: name(el), rect: b, tid: el.getAttribute('data-testid') || '',
      pressed: el.getAttribute('aria-pressed'), expanded: el.getAttribute('aria-expanded'),
      disabled: el.getAttribute('aria-disabled') || (el.disabled ? 'true' : ''),
    });
  });
  // 底部 dock = 视口下缘那一行；左栏 = 视口左缘那一列
  const H = innerHeight, W = innerWidth;
  out.dock = out.buttons.filter((x) => x.rect[1] > H - 90);
  out.rail = out.buttons.filter((x) => x.rect[0] < 80 && x.rect[2] <= 48 && x.rect[1] > 60);
  return out;
}"""

PANEL_JS = """() => {
  // 面板 = 右缘一个约 400 宽、贴顶到底的高盒子
  const cands = [...document.querySelectorAll('div')].filter((el) => {
    const b = el.getBoundingClientRect();
    return Math.abs(b.width - 400) < 12 && b.x > innerWidth - 460 && b.height > 500;
  });
  return cands.map((el) => {
    const b = el.getBoundingClientRect();
    return { x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height),
             text: (el.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 60) };
  });
}"""

PILL_JS = """() => {
  const el = document.querySelector('[data-testid="canvas-sidecar-launcher"]')
    || [...document.querySelectorAll('div,button,span')].find((n) =>
         (n.innerText || '').trim() === '与 AI 对话' && n.getBoundingClientRect().width > 100);
  if (!el) return null;
  const b = el.getBoundingClientRect();
  return { x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height),
           testid: el.getAttribute('data-testid') || '(无 testid)', tag: el.tagName,
           ariaLabel: el.getAttribute('aria-label'), ariaExpanded: el.getAttribute('aria-expanded'),
           innerText: (el.innerText || '').replace(/\\s+/g, ' ').trim(), svg: el.querySelectorAll('svg').length };
}"""

# 父层链：可见文字不在 button 里，只量 button 会把残影当成「药丸尺寸」
CHAIN_JS = """() => {
  const el = document.querySelector('[data-testid="canvas-sidecar-launcher"]');
  if (!el) return null;
  const chain = [];
  let cur = el;
  for (let i = 0; cur && i < 3; i++, cur = cur.parentElement) {
    const b = cur.getBoundingClientRect();
    const cs = getComputedStyle(cur);
    chain.push({ depth: i, tag: cur.tagName, tid: cur.getAttribute('data-testid') || '',
      rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
      text: (cur.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 12), svg: cur.querySelectorAll('svg').length,
      bg: cs.backgroundColor, blur: cs.backdropFilter, radius: cs.borderRadius, position: cs.position });
  }
  return chain;
}"""


def snap(page, label: str) -> dict:
    out = {
        "label": label,
        "body_len": page.evaluate("() => document.body.innerText.length"),
        "crashed": page.evaluate(
            "() => !!document.body.innerText.match(/画布意外停止|Error code/)"
        ),
        "panel": page.evaluate(PANEL_JS),
        "pill": page.evaluate(PILL_JS),
        "pill_chain": page.evaluate(CHAIN_JS),
    }
    out["census"] = page.evaluate(CENSUS_JS)
    return out


def main() -> int:
    report: dict = {"url": URL, "viewport": page.viewport_size, "steps": []}
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    for _ in range(24):  # 最多再等 48s，等画布真的落定
        if not page.evaluate("() => document.body.innerText.includes('Loading canvas')"):
            break
        page.wait_for_timeout(2000)
    page.wait_for_timeout(2500)
    report["steps"].append(snap(page, "① 加载完成后的默认态"))

    # ② 点药丸开面板。开态要**多次采样**：只量 1.2s 那一帧，分不清落定值
    #    和过渡中态（面板有挂载动画）。四个采样一致才算数。
    pill = report["steps"][0]["pill"]
    if pill:
        page.mouse.click(pill["x"] + pill["w"] / 2, pill["y"] + pill["h"] / 2)
        samples = []
        for at_ms in (600, 1200, 2500, 5000):
            page.wait_for_timeout(at_ms - (samples[-1]["at_ms"] if samples else 0))
            s = snap(page, f"② 点「与 AI 对话」之后 @{at_ms}ms")
            s["at_ms"] = at_ms
            samples.append(s)
        report["steps"].append(samples[-1])
        report["open_settle_samples"] = [
            {"at_ms": s["at_ms"], "pill": s["pill"], "chain": s["pill_chain"]} for s in samples
        ]
        # 一致性判据写进报告：四个采样若有任何一个不同，落定值就不成立
        rects = {tuple(s["pill"][k] for k in ("x", "y", "w", "h")) for s in samples if s["pill"]}
        report["open_state_settled"] = len(rects) == 1

        # ③ 面板开着的时候，药丸还在吗？再点一次会怎样？
        st = samples[-1]
        if st["pill"]:
            p2 = st["pill"]
            page.mouse.click(p2["x"] + p2["w"] / 2, p2["y"] + p2["h"] / 2)
            page.wait_for_timeout(1500)
            report["steps"].append(snap(page, "③ 面板开着时再点一次药丸"))
        else:
            report["steps"].append({
                "label": "③ 面板开着时再点一次药丸",
                "pill": None,
                "note": "面板打开后药丸**不在 DOM 里**（不是被盖住）—— 面板与药丸互斥",
            })

    # ④ 底部 dock：选择工具是不是 toggle
    dock_toggle = page.locator('[data-testid="canvas-pointer-tool-toggle"]')
    if dock_toggle.count() > 0:
        before = dock_toggle.first.get_attribute("aria-pressed")
        dock_toggle.first.click()
        page.wait_for_timeout(500)
        report["steps"].append({
            "label": "④ 点「选择工具」前后",
            "aria_pressed_before": before,
            "aria_pressed_after": dock_toggle.first.get_attribute("aria-pressed"),
            "note": "⚠ 更正：首轮我在这里写的是「aria-pressed 不变 ⇒ 单态指示」——"
                    "**实测是 false → true，它确实是二态开关**。首轮那个 note 是"
                    "我按常理写的预期，不是读数 —— 又一次「预期当读数」。",
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "source-canvas-census.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    page.screenshot(path=str(OUT_DIR / "source-after-clicks.png"))
    print(f"写入 {OUT_DIR/'source-canvas-census.json'}")
    for s in report["steps"]:
        pill = s.get("pill") or {}
        print("-", s.get("label"), "| panel:", len(s.get("panel") or []),
              "| pill:", pill.get("testid"), pill.get("w"), "×", pill.get("h"),
              "| expanded:", pill.get("ariaExpanded"))
    if "open_settle_samples" in report:
        print("开态四次采样是否一致:", report["open_state_settled"])
        for s in report["open_settle_samples"]:
            print("   @", s["at_ms"], "ms", s["pill"]["w"], "×", s["pill"]["h"],
                  "| 外层", s["chain"][1]["rect"] if s["chain"] else None)
    return 0


if __name__ == "__main__":
    sys.exit(main())
