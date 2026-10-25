"""1032-⑫ 源站取证：媒体播放页的三个待复核点。

背景
----
手册 `docs/user-manual/jimeng-canvas/10-tasks/media-playback.md` 记的是**源站**读数。
本轮要在**复刻**上复核这一页，同时补两个从未实测过的点：
  ① 中央大播放键的**尺寸**（手册写 44×44；复刻代码注释却把 32px 标成 SOURCE_FACT）；
  ② 全屏播放器里的**音量滑杆**（手册记了读数，但从没在**当前**源站上复验过）；
  ③ 带媒体视频节点的**右键菜单「下载」**可用态。

⚠️ 纪律：
  · 只读 DOM + 只点**不消耗积分**的控件（选中节点 / 开全屏 / 右键）；
  · **绝不点「生成」「发送」「购买」「充值」**；
  · 源站是 SPA ⇒ `evaluate` 可能无限等 ⇒ 每步包 try + 每步落盘；
  · 产物里不许出现随机量（时间戳 / 耗时 / 临时路径）。

用法：
    ~/.venvs/jimeng-py312/bin/python scripts/jimeng_headless.py run \
        scripts/jimeng_probe1039_source_media_playback.py
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path("docs/research/jimeng-canvas/inputs/source-media-playback-1039.json")
URL = (
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create"
)
MEASURED_AT = "2026-10-25"

READY_JS = """() => ({
  preparing: !!document.querySelector('[data-testid="workspace-preparing-state"]'),
  empty_open: !!document.querySelector('[data-testid="canvas-empty-opening"]'),
  n_nodes: document.querySelectorAll('[data-testid^="rf__node-"]').length,
})"""

# 视口缩放：README §22.3 立规 —— 量到的 rect 要除以 viewport 变换矩阵的 a，
# 才是 100% 档下的「画布像素」。
SCALE_JS = """() => {
  const vp = document.querySelector('.react-flow__viewport');
  if (!vp) return null;
  const t = getComputedStyle(vp).transform;
  if (!t || t === 'none') return 1;
  const m = t.match(/matrix\\(([^,]+)/);
  return m ? parseFloat(m[1]) : null;
}"""

# 视频节点（含有没有 <video> / 资源账文字）
VIDEO_NODES_JS = """() => {
  const els = [...document.querySelectorAll('[data-testid^="rf__node-"]')];
  return els.map((el) => {
    const b = el.getBoundingClientRect();
    const text = (el.innerText || '').replace(/\\s+/g, ' ').trim();
    return {
      tid: el.getAttribute('data-testid'),
      rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
      n_video: el.querySelectorAll('video').length,
      n_img: el.querySelectorAll('img').length,
      aria_label: el.getAttribute('aria-label') || '',
      text: text.slice(0, 200),
    };
  }).filter((n) => n.n_video > 0 || /video|视频/i.test(n.aria_label + ' ' + n.text));
}"""

# 节点内的关键 testid + 大播放键几何
CARD_JS = """(tid) => {
  const el = document.querySelector('[data-testid="' + tid + '"]');
  if (!el) return null;
  const box = (q) => {
    const n = el.querySelector(q);
    if (!n) return null;
    const b = n.getBoundingClientRect();
    return [Math.round(b.width * 100) / 100, Math.round(b.height * 100) / 100,
            Math.round(b.x), Math.round(b.y)];
  };
  const simple = el.querySelector('[data-testid="video-simple-player"]');
  const sb = simple ? simple.getBoundingClientRect() : null;
  return {
    has_simple_player: !!simple,
    simple_player_aria: simple ? simple.getAttribute('aria-label') : null,
    simple_player_box: sb ? [Math.round(sb.width * 100) / 100,
                             Math.round(sb.height * 100) / 100,
                             Math.round(sb.x), Math.round(sb.y)] : null,
    simple_player_tag: simple ? simple.tagName : null,
    n_video: el.querySelectorAll('video').length,
    n_img: el.querySelectorAll('img').length,
    has_player_bar: !!el.querySelector('[data-testid="video-node-player-bar"]'),
    has_player_controls: !!el.querySelector('[data-testid="video-node-player-controls"]'),
    has_mute_toggle: !!el.querySelector('[data-testid="video-node-mute-toggle"]'),
    has_fullscreen_toggle: !!el.querySelector('[data-testid="video-node-fullscreen-toggle"]'),
    has_slider_track: !!el.querySelector('[data-testid="slider-track"]'),
    buttons: [...el.querySelectorAll('button')].map((b) => ({
      al: b.getAttribute('aria-label') || '',
      tid: b.getAttribute('data-testid') || '',
      rect: (() => { const r = b.getBoundingClientRect();
        return [Math.round(r.width * 100) / 100, Math.round(r.height * 100) / 100]; })(),
    })),
    text: (el.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 260),
  };
}"""

# 全屏播放器里的 slider（进度 + 音量）
FULLSCREEN_SLIDERS_JS = """() => {
  const fs = document.fullscreenElement;
  const scope = fs || document.body;
  const out = [...scope.querySelectorAll('[data-testid="slider-track"],[role="slider"]')].map((n) => {
    const b = n.getBoundingClientRect();
    return {
      tid: n.getAttribute('data-testid') || '',
      role: n.getAttribute('role') || '',
      aria_label: n.getAttribute('aria-label') || '',
      valuemin: n.getAttribute('aria-valuemin'),
      valuemax: n.getAttribute('aria-valuemax'),
      valuenow: n.getAttribute('aria-valuenow'),
      rect: [Math.round(b.width * 100) / 100, Math.round(b.height * 100) / 100,
             Math.round(b.x), Math.round(b.y)],
    };
  });
  return { in_fullscreen: !!fs, n: out.length, sliders: out };
}"""

# 右键菜单
CTX_JS = """() => {
  const m = document.querySelector('[role="menu"],[data-testid="canvas-context-menu"]');
  if (!m) return { present: false };
  const b = m.getBoundingClientRect();
  const items = [...m.querySelectorAll('[role="menuitem"],li,button')].map((n) => ({
    text: (n.innerText || '').replace(/\\s+/g, ' ').trim(),
    disabled: n.getAttribute('aria-disabled') === 'true' || n.disabled === true,
    aria: n.getAttribute('aria-label') || '',
  }));
  return { present: true,
           box: [Math.round(b.width), Math.round(b.height)],
           n_items: items.length, items };
}"""


def _save(result) -> None:
    try:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n",
                       encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


def _try(fn, default=None):
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        print("  !! 这一步失败：%s" % str(e)[:160])
        return default


def main(page) -> int:
    page.goto(URL, wait_until="domcontentloaded", timeout=120_000)
    page.wait_for_timeout(3000)

    ready = {}
    for i in range(60):                       # 60 × 2s = 120s
        ready = _try(lambda: page.evaluate(READY_JS), {}) or {}
        print("[%4.1fs] preparing=%s empty=%s n_nodes=%s" % (
            2 * (i + 1), ready.get("preparing"), ready.get("empty_open"),
            ready.get("n_nodes")))
        if (not ready.get("preparing")) and (not ready.get("empty_open")) \
                and (ready.get("n_nodes") or 0) > 0:
            print("=> 画布就绪")
            break
        page.wait_for_timeout(2000)

    result = {
        "generated_by": "scripts/jimeng_probe1039_source_media_playback.py",
        "measured_at": MEASURED_AT,
        "canvas_url": URL,
        "how": "登录源站 → 等画布就绪 → 找视频节点 → 量未选中态 → 点它(选中) → 再量 → "
               "右键读菜单 → 点全屏钮 → 读全屏里的 slider。"
               "⚠️ 只点不消耗积分的控件；绝不点生成/发送/购买/充值。",
        "ready": ready,
        "steps": [],
    }
    _save(result)

    scale = _try(lambda: page.evaluate(SCALE_JS), None)
    result["viewport_scale"] = scale
    print("== 视口缩放 = %r ==" % scale)

    vids = _try(lambda: page.evaluate(VIDEO_NODES_JS), []) or []
    result["video_nodes"] = vids
    print("== 视频节点 %d 个 ==" % len(vids))
    for v in vids:
        print("   %s %s video=%d img=%d %r" % (
            v["tid"], v["rect"], v["n_video"], v["n_img"], v["text"][:50]))
    _save(result)

    if not vids:
        result["not_measured"] = ["画布上没有视频节点 ⇒ 三个点都量不到"]
        _save(result)
        print("=> 没有视频节点，如实记录")
        return 0

    # 优先挑**有媒体**（有 <video>）的那个
    target = None
    for v in vids:
        if v["n_video"] > 0:
            target = v
            break
    if target is None:
        target = vids[0]
        result["steps"].append({
            "step": "pick_target",
            "note": "画布上**没有**带媒体的视频节点（只有空节点）⇒ 下面的读数是空节点口径",
            "tid": target["tid"],
        })
        print("!! 只有空视频节点")

    # ① 未选中态
    card0 = _try(lambda: page.evaluate(CARD_JS, target["tid"]), None)
    result["steps"].append({"step": "unselected", "card": card0})
    if card0:
        print("== 未选中 ==")
        print("   simple_player=%s box=%s" % (
            card0["has_simple_player"], card0["simple_player_box"]))
        print("   n_video=%s n_img=%s player_bar=%s" % (
            card0["n_video"], card0["n_img"], card0["has_player_bar"]))
        print("   buttons=%s" % [b["al"] or b["tid"] for b in card0["buttons"]])
    _save(result)

    # ② 点它 → 选中态
    cx = target["rect"][0] + target["rect"][2] / 2
    cy = target["rect"][1] + target["rect"][3] / 2
    _try(lambda: page.mouse.click(cx, cy))
    page.wait_for_timeout(1500)
    card1 = _try(lambda: page.evaluate(CARD_JS, target["tid"]), None)
    result["steps"].append({"step": "selected", "card": card1})
    if card1:
        print("== 选中后 ==")
        print("   simple_player=%s box=%s" % (
            card1["has_simple_player"], card1["simple_player_box"]))
        print("   n_video=%s n_img=%s player_bar=%s mute=%s fs=%s" % (
            card1["n_video"], card1["n_img"], card1["has_player_bar"],
            card1["has_mute_toggle"], card1["has_fullscreen_toggle"]))
        print("   buttons=%s" % [b["al"] or b["tid"] for b in card1["buttons"]])
    _save(result)

    # ③ 右键菜单
    _try(lambda: page.mouse.click(cx, cy, button="right"))
    page.wait_for_timeout(900)
    menu = _try(lambda: page.evaluate(CTX_JS), None)
    result["steps"].append({"step": "context_menu", "menu": menu})
    if menu:
        print("== 右键菜单 ==")
        print("   box=%s n=%s" % (menu.get("box"), menu.get("n_items")))
        for it in menu.get("items", []):
            print("   %-28r disabled=%s" % (it["text"][:28], it["disabled"]))
    _try(lambda: page.keyboard.press("Escape"))
    page.wait_for_timeout(400)
    _save(result)

    # ④ 全屏播放器里的 slider（音量）
    fs_sliders = None
    if card1 and card1.get("has_fullscreen_toggle"):
        _try(lambda: page.locator(
            '[data-testid="%s"] [data-testid="video-node-fullscreen-toggle"]' % target["tid"]
        ).first.click())
        page.wait_for_timeout(1500)
        fs_sliders = _try(lambda: page.evaluate(FULLSCREEN_SLIDERS_JS), None)
        result["steps"].append({"step": "fullscreen_sliders", "readings": fs_sliders})
        if fs_sliders:
            print("== 全屏 slider ==")
            print("   in_fullscreen=%s n=%s" % (fs_sliders["in_fullscreen"],
                                                fs_sliders["n"]))
            for s in fs_sliders["sliders"]:
                print("   tid=%-16r role=%-8r label=%-12r min=%s max=%s now=%s %s" % (
                    s["tid"], s["role"], s["aria_label"], s["valuemin"],
                    s["valuemax"], s["valuenow"], s["rect"]))
        _try(lambda: page.keyboard.press("Escape"))
        page.wait_for_timeout(400)
    else:
        result["steps"].append({
            "step": "fullscreen_sliders",
            "not_measured": "选中态没有 video-node-fullscreen-toggle ⇒ 进不了全屏",
        })

    _save(result)
    print("写入 %s" % OUT)
    return 0


# ⚠️ runner（scripts/jimeng_headless.py run）用 `exec` 注入全局 `page` ⇒
#    这里**必须**直接调用 main(page) —— 写成 `if __name__ == "__main__"` 也行
#    （runner 把 __name__ 设成 "__main__"），但**不能**只定义不调用：
#    那样整个脚本会静默跑完、什么也不打印、什么也不落盘。
main(page)
