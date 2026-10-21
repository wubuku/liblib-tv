"""batch 1032-②b-3 取证：重拍面板 / 视频编辑态里的「@ 提及主体」按钮，点它会发生什么。

背景
----
复刻那边有两枚**死按钮**（1032 审计登记）：
· `src/components/jimeng/JimengRepaintPanel.tsx` 的「提及主体」
· `src/components/jimeng/JimengVideoEditMode.tsx` 的「提及主体」
⇒ ⇒ 要修它们，得先知道**源站同位置的 @ 钮点开什么**（浮层？列表？主体库？）。

⚠️ 纪律：
· 只点**不消耗积分**的控件（「局部重拍」「视频编辑」「@」这些都不是生成动作）
· **绝不点「生成」「发送」「购买」「充值」**
· ⭐ 源站画布要 **轮询到就绪**才读（第一版只等 6s ⇒ 读到「画布是空的」）
· ⭐ 源站的节点 testid 是 `rf__node-<uuid>`（**不是** `.react-flow__node`）

用法：
    ~/.venvs/jimeng-py312/bin/python scripts/jimeng_headless.py run \
        scripts/jimeng_probe1032b3_subject_source.py
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path("docs/research/jimeng-canvas/inputs/source-subject-mention-1032b3.json")
URL = (
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create"
)

READY_JS = """() => ({
  preparing: !!document.querySelector('[data-testid="workspace-preparing-state"]'),
  empty_open: !!document.querySelector('[data-testid="canvas-empty-opening"]'),
  n_nodes: document.querySelectorAll('[data-testid^="rf__node-"]').length,
})"""

# 视频节点：按内部构成找（有 <video> 或 aria 含「视频」）
VIDEO_NODES_JS = """() => {
  const els = [...document.querySelectorAll('[data-testid^="rf__node-"]')];
  return els.map((el) => {
    const b = el.getBoundingClientRect();
    const aria = [...el.querySelectorAll('[aria-label]')]
      .map((x) => x.getAttribute('aria-label')).filter(Boolean).slice(0, 8);
    return {
      tid: el.getAttribute('data-testid'),
      rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
      text: (el.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 40),
      aria: aria,
      n_video: el.querySelectorAll('video').length,
      n_img: el.querySelectorAll('img').length,
    };
  }).filter((n) => n.n_video > 0 || /视频|video/i.test(n.aria.join(' ') + ' ' + n.text));
}"""

# 面板里的按钮：⭐ **穷举**（不按 aria-label / 文本过滤）——
#   上一版带过滤 ⇒ 工具条上那些「图标钮」被全滤掉了 ⇒ ⇒ 读成「没有工具条」
#   ⇒ ⇒ 而真相是「工具条在，只是那些钮**没有可访问名**」。
#   ⇒ ⇒ 每一枚都带上**全部**可能带信息的属性，交回人来认。
PANEL_BTNS_JS = """() => {
  const out = [];
  for (const el of document.querySelectorAll('button,[role="button"]')) {
    const b = el.getBoundingClientRect();
    if (b.width < 4 || b.height < 4) continue;
    if (b.width > 260 || b.height > 260) continue;
    if (b.bottom < 0 || b.top > window.innerHeight) continue;
    out.push({
      al: el.getAttribute('aria-label') || '',
      txt: (el.innerText || '').trim().slice(0, 30),
      title: el.getAttribute('title') || '',
      testid: el.getAttribute('data-testid') || '',
      cls: String(el.getAttribute('class') || '').slice(0, 60),
      rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
      svg_paths: el.querySelectorAll('svg path,svg circle,svg rect').length,
      html: el.innerHTML.replace(/\s+/g, ' ').slice(0, 120),
    });
  }
  return out;
}"""

# 点开之后：读所有可能的浮层
LAYERS_JS = """() => {
  const cands = [...document.querySelectorAll(
    '[role="dialog"],[role="listbox"],[role="menu"],[role="popover"],[aria-modal="true"]')];
  const out = [];
  for (const el of cands) {
    const b = el.getBoundingClientRect();
    if (b.width < 10 || b.height < 10) continue;
    out.push({
      role: el.getAttribute('role') || '',
      aria: el.getAttribute('aria-label') || '',
      testid: el.getAttribute('data-testid') || '',
      rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
      text: (el.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 300),
      n_items: el.querySelectorAll('[role="option"],[role="menuitem"],li,button').length,
    });
  }
  return out;
}"""


def _save(result):
    """**每一步都落盘** ⇒ 探针挂死时，已经量到的东西不会一起丢。"""
    try:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n",
                       encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


def _try(fn, default=None):
    """包一层 try：源站是 SPA，**evaluate 在页面忙的时候会无限等** ⇒ ⇒ 崩一步不该带走全部读数。"""
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        print("  !! 这一步失败：%s" % str(e)[:140])
        return default


def main() -> int:
    # ⭐ 超时给足（源站是 SPA + XHR，45s 不够）；并且**每轮都包 try**
    #   ⇒ 一轮 evaluate 卡住/抛错时**继续轮询**而不是整个探针挂死。
    page.goto(URL, wait_until="domcontentloaded", timeout=120_000)
    page.wait_for_timeout(3000)

    ready = {}
    for i in range(60):                       # 60 × 2s = 120s
        try:
            ready = page.evaluate(READY_JS)
        except Exception as e:                # noqa: BLE001
            print("[%4.1fs] evaluate 失败：%s" % (2 * (i + 1), str(e)[:80]))
            ready = {}
        print("[%4.1fs] preparing=%s empty=%s n_nodes=%d" % (
            2 * (i + 1), ready.get("preparing"), ready.get("empty_open"),
            ready.get("n_nodes", -1)))
        if not ready.get("preparing") and not ready.get("empty_open") \
                and ready.get("n_nodes", 0) > 0:
            print("=> 画布就绪")
            break
        page.wait_for_timeout(2000)

    vids = _try(lambda: page.evaluate(VIDEO_NODES_JS), []) or []
    _save({"generated_by": "scripts/jimeng_probe1032b3_subject_source.py",
           "measured_at": "2026-10-21", "canvas_url": URL, "stage": "nodes_found",
           "video_nodes": vids, "steps": []})
    print("== 视频节点 %d 个 ==" % len(vids))
    for v in vids:
        print("   %s %s %r" % (v["tid"], v["rect"], v["text"][:30]))

    result = {
        "generated_by": "scripts/jimeng_probe1032b3_subject_source.py",
        "measured_at": "2026-10-21",
        "canvas_url": URL,
        "how": "登录源站 → 等画布就绪 → 找视频节点 → 点它 → 找工具条上的「局部重拍」/「视频编辑」→ "
               "进编辑态 → 枚举面板里的按钮 → 找 @ 那一枚 → 点它 → 读开了什么。"
               "⚠️ 只点不消耗积分的控件，绝不点生成/发送/购买/充值。",
        "video_nodes": vids,
        "steps": [],
    }

    if not vids:
        result["not_measured"] = ["没有视频节点 ⇒ 无法进编辑态"]
        print("=> 没有视频节点，如实记录")
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n",
                       encoding="utf-8")
        print("写入 %s" % OUT)
        return 0

    target = vids[0]
    cx = target["rect"][0] + target["rect"][2] / 2
    cy = target["rect"][1] + target["rect"][3] / 2
    print("== 点视频节点 %s ==" % target["tid"])
    page.mouse.click(cx, cy)
    page.wait_for_timeout(1200)
    # ⚠️ **不悬停**：源站的视频节点悬停可能触发播放/重绘 ⇒ ⇒ 主线程被占住
    #   ⇒ ⇒ 之后的 `page.evaluate` 会**无限等**（sync API 的 evaluate 没有超时）
    #   ⇒ ⇒ 那正是上一版挂死的位置 ⇒ ⇒ 教训：**evaluate 会无限等 ⇒ 关键步骤要包 try + 逐步落盘**。

    btns = _try(lambda: page.evaluate(PANEL_BTNS_JS), []) or []
    _save({"generated_by": "scripts/jimeng_probe1032b3_subject_source.py",
           "measured_at": "2026-10-21", "canvas_url": URL, "stage": "after_select",
           "video_nodes": vids, "n_buttons": len(btns), "buttons": btns, "steps": []})
    print("== 选中后可见按钮 %d 枚 ==" % len(btns))
    for b in btns:
        print("   al=%-26r txt=%-14r tid=%-22r %s svg=%d" % (
            b["al"], b["txt"], b["testid"], b["rect"], b.get("svg_paths", 0)))
        if not b["al"] and not b["txt"]:
            print("        ↳ 无可访问名：title=%r cls=%r html=%r" % (
                b["title"], b["cls"], b["html"][:90]))

    # 找「局部重拍」/「视频编辑」入口
    entry = None
    for key in ("局部重拍", "视频编辑", "编辑"):
        cand = [b for b in btns if key in (b["al"] + b["txt"])]
        if cand:
            entry = cand[0]
            break
    if not entry:
        result["not_measured"] = ["选中视频节点后没找到「局部重拍」/「视频编辑」入口"]
        print("=> 没找到编辑入口，如实记录")
        _save(result)
        return 0

    print("== 进编辑态：%r ==" % (entry["al"] or entry["txt"]))
    page.mouse.click(entry["rect"][0] + entry["rect"][2] / 2,
                     entry["rect"][1] + entry["rect"][3] / 2)
    page.wait_for_timeout(2000)

    btns2 = _try(lambda: page.evaluate(PANEL_BTNS_JS), []) or []
    _save({"generated_by": "scripts/jimeng_probe1032b3_subject_source.py",
           "measured_at": "2026-10-21", "canvas_url": URL, "stage": "in_edit_mode",
           "video_nodes": vids, "n_buttons": len(btns2), "buttons": btns2, "steps": []})
    print("== 编辑态可见按钮 %d 枚 ==" % len(btns2))
    for b in btns2:
        print("   al=%-26r txt=%-14r tid=%-22r %s svg=%d" % (
            b["al"], b["txt"], b["testid"], b["rect"], b.get("svg_paths", 0)))
        if not b["al"] and not b["txt"]:
            print("        ↳ 无可访问名：title=%r cls=%r html=%r" % (
                b["title"], b["cls"], b["html"][:90]))

    at_btn = None
    for b in btns2:
        blob = (b["al"] + " " + b["txt"] + " " + b["title"])
        if "@" in blob or "提及" in blob or "主体" in blob:
            at_btn = b
            break

    step = {"entry": entry, "n_buttons_in_edit": len(btns2),
            "at_button": at_btn, "layers_before": _try(lambda: page.evaluate(LAYERS_JS), [])}
    if not at_btn:
        step["result"] = "编辑态里没找到 @ / 主体按钮 ⇒ 如实记录"
        result["steps"].append(step)
        print("=> 没找到 @ 按钮，如实记录")
    else:
        print("== 点 @ 按钮：%r ==" % (at_btn["al"] or at_btn["txt"]))
        page.mouse.click(at_btn["rect"][0] + at_btn["rect"][2] / 2,
                         at_btn["rect"][1] + at_btn["rect"][3] / 2)
        page.wait_for_timeout(1500)
        layers = _try(lambda: page.evaluate(LAYERS_JS), []) or []
        step["layers_after"] = layers
        step["result"] = "已点 @ 按钮"
        print("== 点开后的浮层 ==")
        for L in layers:
            print("   role=%-10s aria=%-22r %s %r" % (
                L["role"], L["aria"], L["rect"], L["text"][:120]))
        result["steps"].append(step)

    _save(result)
    print("\n写入 %s" % OUT)
    return 0


main()
