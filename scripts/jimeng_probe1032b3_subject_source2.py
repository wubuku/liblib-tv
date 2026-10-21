"""batch 1032-②b-3 取证 v2：在源站画布上**穷举每一类节点的选中态**，找「提及主体 / @」入口。

为什么有 v2
-----------
v1（`jimeng_probe1032b3_subject_source.py`）的诚实结论：
选中那个**视频节点**后，可见按钮 11 枚，全是顶栏 / 左下角 / 右下角的全局钮
（项目 / 节点汇总 / AI 工具 / 会员 / 用户菜单 / Rename 视频 1 / 选择工具 / 小地图 /
显示连线 / Zoom / 与 AI 对话）⇒ **面板级的编辑入口一个都没有**。

⭐ 关键发现（v1 量到的）：那个视频节点的文本是
「视频 1 / No resources: 0 ready, 0 processing」⇒ **节点是空的**
⇒ ⇒ 源站**空节点不提供编辑入口** ⇒ ⇒ 「局部重拍」这类入口要**节点有资源**才出现。
⇒ ⇒ 所以「在视频节点上找 @」这条路，**不是探针不行，是这个节点没有编辑态**。

⇒ v2 换路：把画布上 76 个节点**按类型分类**，每类挑一个代表点开，
读它的选中态工具条 + 浮层 + 编辑态标记 ⇒ 找 @ 那一枚。

⚠️ 纪律：只点不消耗积分的控件；**绝不点「生成」「发送」「购买」「充值」**。
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path("docs/research/jimeng-canvas/inputs/source-subject-mention-1032b3-v2.json")
URL = (
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create"
)

READY_JS = """() => ({
  preparing: !!document.querySelector('[data-testid="workspace-preparing-state"]'),
  empty_open: !!document.querySelector('[data-testid="canvas-empty-opening"]'),
  n_nodes: document.querySelectorAll('[data-testid^="rf__node-"]').length,
})"""

# 画布上**所有**节点 + 它们各自内部的构成（用来判类型、判「有没有资源」）
ALL_NODES_JS = """() => {
  const els = [...document.querySelectorAll('[data-testid^="rf__node-"]')];
  return els.map((el) => {
    const b = el.getBoundingClientRect();
    const aria = [...el.querySelectorAll('[aria-label]')]
      .map((x) => x.getAttribute('aria-label')).filter(Boolean);
    return {
      tid: el.getAttribute('data-testid'),
      rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
      text: (el.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 70),
      aria: aria.slice(0, 6),
      n_btn: el.querySelectorAll('button').length,
      n_video: el.querySelectorAll('video').length,
      n_img: el.querySelectorAll('img').length,
      n_audio: el.querySelectorAll('audio').length,
      n_textarea: el.querySelectorAll('textarea').length,
      n_ce: el.querySelectorAll('[contenteditable="true"]').length,
    };
  });
}"""

# 可见按钮**穷举**（不按 aria-label / 文本过滤）—— v1 已证明：过滤会把图标钮全滤掉
PANEL_BTNS_JS = """() => {
  const out = [];
  for (const el of document.querySelectorAll('button,[role="button"]')) {
    const b = el.getBoundingClientRect();
    if (b.width < 4 || b.height < 4) continue;
    if (b.width > 400 || b.height > 400) continue;
    if (b.bottom < 0 || b.top > window.innerHeight) continue;
    out.push({
      al: el.getAttribute('aria-label') || '',
      txt: (el.innerText || '').trim().slice(0, 30),
      title: el.getAttribute('title') || '',
      testid: el.getAttribute('data-testid') || '',
      cls: String(el.getAttribute('class') || '').slice(0, 60),
      rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
      svg_paths: el.querySelectorAll('svg path,svg circle,svg rect').length,
      html: el.innerHTML.replace(/\\s+/g, ' ').slice(0, 140),
    });
  }
  return out;
}"""

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

EDIT_STATE_JS = """() => {
  const ae = document.activeElement;
  return {
    n_textarea: document.querySelectorAll('textarea').length,
    n_ce: document.querySelectorAll('[contenteditable="true"]').length,
    focused: ae ? (ae.tagName + '/' + (ae.getAttribute('data-testid')
      || ae.getAttribute('aria-label') || ae.getAttribute('placeholder') || '')) : '',
  };
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
    """包一层 try：源站是 SPA，**evaluate 在页面忙的时候会无限等** ⇒ 崩一步不该带走全部读数。"""
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        print("  !! 这一步失败：%s" % str(e)[:140])
        return default


def classify(n):
    blob = " ".join([n.get("text", "")] + list(n.get("aria") or []))
    if n.get("n_video") or "视频" in blob:
        return "video"
    if n.get("n_img") or "图片" in blob:
        return "image"
    if n.get("n_audio") or "音频" in blob:
        return "audio"
    if "文本" in blob or "text" in blob.lower():
        return "text"
    if "导演台" in blob:
        return "director"
    if "时间线" in blob:
        return "timeline"
    if "主体" in blob:
        return "subject"
    return "other"


def is_at(b):
    """@ 那一枚的判据：可访问名 / 文本 / title / svg class 里出现 @ 或 at-sign。"""
    blob = " ".join([b.get("al", ""), b.get("txt", ""), b.get("title", ""),
                     b.get("cls", ""), b.get("html", "")]).lower()
    return ("@" in blob or "at-sign" in blob or "atsign" in blob
            or "提及主体" in blob or "主体" in blob)


def main() -> int:
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

    nodes = _try(lambda: page.evaluate(ALL_NODES_JS), []) or []
    result = {
        "generated_by": "scripts/jimeng_probe1032b3_subject_source2.py",
        "measured_at": "2026-10-21",
        "canvas_url": URL,
        "how": "登录源站 → 等画布就绪 → 枚举画布上**所有**节点并按类型分类 → "
               "每类挑一个代表点开 → 读它的选中态按钮（穷举）/ 浮层 / 编辑态标记 → "
               "找 @ 那一枚。⚠️ 只点不消耗积分的控件，绝不点生成/发送/购买/充值。",
        "v1_finding": "v1 选中唯一的视频节点后只有 11 枚全局钮（项目/节点汇总/AI工具/会员/"
                      "用户菜单/Rename 视频 1/选择工具/小地图/显示连线/Zoom/与AI对话），"
                      "面板级编辑入口 0 个；该节点文本为「视频 1 No resources: 0 ready, "
                      "0 processing」⇒ 空节点不提供编辑入口。",
        "n_nodes": len(nodes),
        "node_types": {},
        "nodes": nodes,
        "probes": [],
        "at_candidates": [],
    }

    by_type = {}
    for n in nodes:
        by_type.setdefault(classify(n), []).append(n)
    result["node_types"] = {k: len(v) for k, v in sorted(by_type.items())}
    print("== 节点分类 ==")
    for k, v in sorted(by_type.items()):
        sample = v[0]
        print("   %-9s %3d 个  例: %s %r" % (k, len(v), sample["tid"], sample["text"][:40]))
    _save(result)

    # 每类挑一个代表（优先挑**有资源**的：n_video/n_img/n_audio > 0，其次文本最长的）
    reps = []
    for k, group in sorted(by_type.items()):
        group = sorted(group, key=lambda n: (-(n["n_video"] + n["n_img"] + n["n_audio"]),
                                             -len(n.get("text") or "")))
        reps.append((k, group[0]))

    for k, node in reps:
        print("== 点 %s 类代表 %s ==" % (k, node["tid"]))
        try:
            page.keyboard.press("Escape")
        except Exception:  # noqa: BLE001
            pass
        page.wait_for_timeout(400)
        cx = node["rect"][0] + node["rect"][2] / 2
        cy = node["rect"][1] + node["rect"][3] / 2
        try:
            page.mouse.click(cx, cy)
        except Exception as e:  # noqa: BLE001
            print("  !! 点击失败：%s" % str(e)[:100])
        page.wait_for_timeout(1200)

        btns = _try(lambda: page.evaluate(PANEL_BTNS_JS), []) or []
        layers = _try(lambda: page.evaluate(LAYERS_JS), []) or []
        edit = _try(lambda: page.evaluate(EDIT_STATE_JS), {}) or {}

        # 减去全局钮（顶栏 / 左下角 / 右下角），只留**节点相关**的
        gx = [b for b in btns
              if b["rect"][1] < 60 or b["rect"][1] > 860
              or b["rect"][0] < 60 or b["rect"][0] > 1300]
        local = [b for b in btns if b not in gx]

        ats = [b for b in btns if is_at(b)]
        print("   按钮 %d（全局 %d / 节点相关 %d）浮层 %d  @候选 %d"
              % (len(btns), len(gx), len(local), len(layers), len(ats)))
        for b in local[:20]:
            print("      al=%-24r txt=%-12r tid=%-20r %s svg=%d"
                  % (b["al"], b["txt"], b["testid"], b["rect"], b.get("svg_paths", 0)))
        for L in layers:
            print("      LAYER role=%-10s aria=%-22r %s %r"
                  % (L["role"], L["aria"], L["rect"], L["text"][:90]))
        print("      编辑态: %r" % (edit,))

        rec = {"type": k, "node": node, "n_buttons": len(btns),
               "n_global": len(gx), "n_local": len(local),
               "local_buttons": local, "layers": layers, "edit_state": edit,
               "at_candidates": ats}
        result["probes"].append(rec)
        for b in ats:
            result["at_candidates"].append({"type": k, "tid": node["tid"], "btn": b})
        _save(result)

    # 若找到了 @ 候选 ⇒ 点开它，读开了什么（这一步不消耗积分）
    if result["at_candidates"]:
        cand = result["at_candidates"][0]
        b = cand["btn"]
        print("== 点 @ 候选（%s 类）：al=%r txt=%r ==" % (cand["type"], b["al"], b["txt"]))
        try:
            page.mouse.click(b["rect"][0] + b["rect"][2] / 2,
                             b["rect"][1] + b["rect"][3] / 2)
            page.wait_for_timeout(1500)
            after = _try(lambda: page.evaluate(LAYERS_JS), []) or []
            btns_after = _try(lambda: page.evaluate(PANEL_BTNS_JS), []) or []
            print("   点开后浮层 %d 按钮 %d" % (len(after), len(btns_after)))
            for L in after:
                print("      LAYER role=%-10s aria=%-22r %s %r"
                      % (L["role"], L["aria"], L["rect"], L["text"][:140]))
            result["at_click"] = {"cand": cand, "layers_after": after,
                                  "n_buttons_after": len(btns_after)}
        except Exception as e:  # noqa: BLE001
            print("  !! 点 @ 失败：%s" % str(e)[:120])
            result["at_click"] = {"cand": cand, "error": str(e)[:200]}
    else:
        result["at_click"] = None
        result["not_measured"] = [
            "画布上每一类节点的选中态都枚举过了，没有出现 @ / 提及主体 那一枚",
            "（视频节点为空 ⇒ 无编辑入口；其它类节点需再查）",
        ]
        print("=> 全类型扫完，没有 @ 候选")

    _save(result)
    print("\n写入 %s" % OUT)
    return 0


main()
