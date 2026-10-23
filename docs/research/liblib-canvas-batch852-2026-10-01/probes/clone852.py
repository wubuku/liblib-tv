#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 852 clone 探针：导演台的**变换类快捷键**（V／R／F）与**网格吸附**（X）。

## ★ 判据：**等于目标值**，不是「变了」

★ clone 把自己暴露成 DOM 属性 ⟹ ⟹ 本探针读**具体值**：

| 读数 | 元素 | 属性 | 期望 |
| --- | --- | --- | --- |
| 变换模式 | `[data-director-transform-mode]` | `aria-pressed="true"` 的那一枚 | translate／rotate／scale |
| 网格吸附 | `[data-director-scene-snap-to-grid]` | `aria-checked` | true／false |

★ 再用 `window.__director_store.getState()` 做**副读数**（store 里的
`transformMode` / `scene.snapToGrid`）⟹ ⟹ 两条独立通路必须一致。

## ★ 键序与源站探针**完全一致**（R → F → V）

★ 源站探针 `source852_transformkeys.py` 用的就是 R→F→V ⟹ ⟹ 两边读数可直接对表。
★ ★ 而且起点都是 translate ⟹ 每一步都把模式推到**下一个** ⟹ 判据强。

## ★ 只读保证

★ 只按键盘（r／f／v／x）＋ 读 DOM ⟹ ⟹ 不改场景数据、不触发付费控件。

## 输出

  raw/clone-852-transformkeys.json
  images/852clone_*.png
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch852-2026-10-01"
RAW = BATCH / "raw"
SHOTS = BATCH / "images"
BASE = "http://localhost:4317"

# ★ 源站的键位表（机器提取自 raw/source-852-contract.json）
KEY_TO_MODE = {"v": "translate", "r": "rotate", "f": "scale"}


def load_key_to_mode() -> dict:
    """★ 从**入库的源站原文**里解析键位表（不手打）"""
    data = json.loads((RAW / "source-852-contract.json").read_text(encoding="utf-8"))
    src = data["片段"]["底部工具栏的变换模式表 R"]["原文"]
    import re
    items = re.findall(r'mode:"([^"]+)"[^}]*?shortcut:"([^"]+)"', src)
    if not items:
        raise SystemExit("★ 契约里没解析出键位表")
    table = {letter.lower(): mode for mode, letter in items}
    if set(table) != set(KEY_TO_MODE):
        raise SystemExit("★ 解析出的键位表与预期不一致：%r" % table)
    return table


READ_MODES = r"""()=>{
  const btns = Array.from(document.querySelectorAll('[data-director-transform-mode]'));
  const pressed = btns.filter(b=>b.getAttribute('aria-pressed')==='true');
  const sw = document.querySelector('[data-director-scene-snap-to-grid]');
  const insp = document.querySelector('[data-director-inspector]');
  return {
    按钮数: btns.length,
    按钮: btns.map(b=>({mode:b.getAttribute('data-director-transform-mode'),
                         pressed:b.getAttribute('aria-pressed')})),
    选中数: pressed.length,
    模式: pressed.length===1 ? pressed[0].getAttribute('data-director-transform-mode') : null,
    吸附元素存在: !!sw,
    吸附: sw ? sw.getAttribute('aria-checked') : null,
    面板类别: insp ? insp.getAttribute('data-director-inspector-kind') : null,
  };
}"""

READ_STORE = r"""()=>{
  const s = window.__director_store ? window.__director_store.getState() : null;
  if(!s) return null;
  return {transformMode:s.transformMode, snapToGrid:!!(s.scene && s.scene.snapToGrid),
          draft: !!(s.timeline && s.timeline.motionPathDraft)};
}"""


def open_desk(pg):
    pg.goto(BASE + "/?batch852=1", wait_until="domcontentloaded")
    pg.wait_for_timeout(3000)
    pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
    pg.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
    pg.wait_for_timeout(1200)
    node = pg.locator(".react-flow__node-script-execution").first
    try:
        node.scroll_into_view_if_needed(timeout=8000)
    except Exception:
        pass
    pg.wait_for_timeout(400)
    try:
        node.hover(timeout=8000)
        pg.wait_for_timeout(600)
    except Exception:
        pass
    pg.locator("[data-open-director]").first.click(timeout=15000)
    pg.wait_for_timeout(6000)
    pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")


def read(pg):
    dom = pg.evaluate(READ_MODES)
    store = pg.evaluate(READ_STORE)
    return {"DOM": dom, "store": store}


def shot(pg, name):
    p = SHOTS / ("852clone_%s.png" % name)
    p.parent.mkdir(parents=True, exist_ok=True)
    pg.screenshot(path=str(p))
    return p



def deselect(pg):
    """★ 点 3D 视口**空白处**（左上角天空）⟹ `onPointerMissed` ⟹ 取消选择
    ⟹ ⟹ 右栏从「角色面板」换成「场景面板」⟹ ⟹ 网格吸附开关出现在 DOM 里。
    ★ ★ 不能用 Escape：clone 的 DirectorDesk 里 Escape 最后会 `closeWorkspace()`
    ⟹ ⟹ **整个导演台会被关掉**（源站也差不多）⟹ 探测就断了。
    """
    box = pg.evaluate(
        """()=>{const s=document.querySelector('[data-director-viewport]');
          if(!s)return null;const r=s.getBoundingClientRect();
          return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};}"""
    )
    if not box or box["w"] <= 0:
        return False
    pg.mouse.click(box["x"] + 24, box["y"] + 24)
    pg.wait_for_timeout(600)
    return True


def read_snap(pg):
    """网格吸附读数：★ **DOM 开关优先**（可见读数）⟹ 场景面板没显示时退回 store 读数
    ⟹ ⟹ 并**如实标注**用的是哪一条。"""
    dom = pg.evaluate(READ_MODES)
    store = pg.evaluate(READ_STORE)
    if dom.get("吸附") is not None:
        value, src = dom["吸附"], "DOM开关"
    else:
        value, src = (str(bool((store or {}).get("snapToGrid"))).lower()), "store"
    return {"值": value, "来源": src, "DOM开关": dom.get("吸附"),
            "DOM面板类别": dom.get("面板类别"),
            "store": (store or {}).get("snapToGrid")}


def main() -> int:
    out = {}
    try:
        table = load_key_to_mode()
        out["★键位表（源站原文解析）"] = table
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            pg = ctx.new_page()
            pg.set_default_timeout(30_000)
            open_desk(pg)

            out["①初始读数"] = read(pg)
            shot(pg, "initial")

            # ── 逐键实测：R → F → V（与源站探针同序）
            for key in ["r", "f", "v"]:
                rec = {}
                try:
                    before = read(pg)
                    rec["按前"] = before
                    pg.keyboard.press(key)
                    pg.wait_for_timeout(450)
                    after = read(pg)
                    rec["按后"] = after
                    rec["期望模式"] = table[key]
                    rec["DOM模式对"] = (after["DOM"]["模式"] == table[key])
                    rec["store模式对"] = (after["store"] or {}).get("transformMode") == table[key]
                    rec["两条一致"] = (after["DOM"]["模式"] == (after["store"] or {}).get("transformMode"))
                    rec["★吸附不该被改"] = (
                        before["DOM"]["吸附"] == after["DOM"]["吸附"]
                    )
                    shot(pg, "key-%s" % key)
                except Exception:
                    rec["★异常"] = traceback.format_exc()[-400:]
                out["②按%s" % key.upper()] = rec

            # ── Shift+V：源站对 v **没有**修饰键限制 ⟹ 先按 R 到 rotate，再 Shift+V
            try:
                pg.keyboard.press("r")
                pg.wait_for_timeout(400)
                before = read(pg)
                pg.keyboard.down("Shift")
                pg.keyboard.press("v")
                pg.keyboard.up("Shift")
                pg.wait_for_timeout(450)
                after = read(pg)
                out["③Shift+V"] = {
                    "按前": before, "按后": after,
                    "期望模式": table["v"],
                    "DOM模式对": after["DOM"]["模式"] == table["v"],
                    "★说明": "按前先按过 R ⟹ 模式是 rotate ⟹ Shift+V 若有效应变成 translate",
                }
            except Exception:
                out["★Shift+V异常"] = traceback.format_exc()[-400:]

            # ── X：网格吸附翻转
            try:
                ok = deselect(pg)
                out["④取消选择"] = {"已点空白": ok}
                before = read_snap(pg)
                shot(pg, "x-before")
                pg.keyboard.press("x")
                pg.wait_for_timeout(450)
                mid = read_snap(pg)
                shot(pg, "x-after")
                pg.keyboard.press("x")
                pg.wait_for_timeout(450)
                after = read_snap(pg)
                out["⑤按X"] = {
                    "按前": before, "按后一次": mid, "按后两次": after,
                    "★首次翻转": before["值"] != mid["值"],
                    "★再按翻回": mid["值"] != after["值"],
                    "★往返一致": before["值"] == after["值"],
                    "★两条通路一致": (
                        mid["DOM开关"] is None
                        or mid["DOM开关"] == str(bool(mid["store"])).lower()
                    ),
                }
            except Exception:
                out["★按X异常"] = traceback.format_exc()[-400:]

            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        RAW.mkdir(parents=True, exist_ok=True)
        (RAW / "clone-852-transformkeys.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", RAW / "clone-852-transformkeys.json")
        if out.get("异常"):
            print("异常：", out["异常"][-800:])
        init = out.get("①初始读数") or {}
        print("--- 初始 ---", json.dumps(init.get("DOM"), ensure_ascii=False),
              "store=", init.get("store"))
        for k in ["②按R", "②按F", "②按V"]:
            v = out.get(k) or {}
            b = ((v.get("按前") or {}).get("DOM") or {})
            a = ((v.get("按后") or {}).get("DOM") or {})
            print("  %-6s DOM %s→%s  期望=%s  对=%s  store对=%s  两条一致=%s 吸附未动=%s"
                  % (k, b.get("模式"), a.get("模式"), v.get("期望模式"),
                     v.get("DOM模式对"), v.get("store模式对"), v.get("两条一致"),
                     v.get("★吸附不该被改")))
        s3 = out.get("③Shift+V") or {}
        print("  Shift+V DOM %s→%s 期望=%s 对=%s"
              % (((s3.get("按前") or {}).get("DOM") or {}).get("模式"),
                 ((s3.get("按后") or {}).get("DOM") or {}).get("模式"),
                 s3.get("期望模式"), s3.get("DOM模式对")))
        s4 = out.get("⑤按X") or {}
        print("  按X 吸附 %s→%s→%s（来源 %s） 首次翻转=%s 再按翻回=%s 往返一致=%s 两路一致=%s"
              % (((s4.get("按前") or {}).get("值")),
                 ((s4.get("按后一次") or {}).get("值")),
                 ((s4.get("按后两次") or {}).get("值")),
                 ((s4.get("按前") or {}).get("来源")),
                 s4.get("★首次翻转"), s4.get("★再按翻回"), s4.get("★往返一致"),
                 s4.get("★两条通路一致")))
        print("  取消选择:", out.get("④取消选择"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
