"""batch 1032-②b-2/②b-4 取证：图片 / 音频生成面板的「展开」按钮点开什么。

背景
----
②b-1 已经在源站量到**视频**侧的展开行为（点 `展开视频生成器` ⇒ 开出
`role="dialog"` / aria-label「已展开的视频生成器」 / 920×480 / 内含
全部·图片·视频·音频·文本 五个参考 tab），
证据落在 `docs/research/jimeng-canvas/inputs/source-expanded-gen-1032b1.json`。

但复刻那边**三处**面板都有「展开面板」这枚钮（视频 / 图片 / 音频），
源站侧只量过视频那一处 ⇒ ⇒ 图片与音频这两处**不能照抄视频的规格**：
aria-label 叫什么、里面有哪些 tab、宽多少，**都得现量**。

⚠️⭐⭐ **第一版探针栽在两处「量错了 ≠ 没有」（这一版把它们都修掉了）**：
  ① **等太早**：只等 6s 就读 ⇒ 那一刻源站还在 `workspace-preparing-state`
     （"Loading canvas"）⇒ 读到「画布是空的」⇒ **真相是画布要 ~9s 才就绪**；
  ② **选择器错**：用 `.react-flow__node` 找节点 ⇒ 源站**根本不用 React Flow 的 class**
     ⇒ 源站的节点 testid 是 `rf__node-<uuid>` ⇒ **选错选择器永远读到 0 个**。
  ⇒ ⇒ 这一版：**轮询到 `preparing` 消失**再读，且**按 `rf__node-` testid** 枚举节点。

⚠️ 计费边界：只点「展开」这一类**不消耗积分**的控件。
  **绝不点「生成」「发送」「购买」「充值」。**

用法：
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
        scripts/jimeng_probe1032b2_expand_source.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

OUT = Path("docs/research/jimeng-canvas/inputs/source-expanded-gen-1032b2.json")
URL = (
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create"
)

# ── 就绪判定：源站画布还在 preparing 时**读到的任何东西都是假的** ─────────
READY_JS = """() => ({
  preparing: !!document.querySelector('[data-testid="workspace-preparing-state"]'),
  empty_open: !!document.querySelector('[data-testid="canvas-empty-opening"]'),
  n_nodes: document.querySelectorAll('[data-testid^="rf__node-"]').length,
})"""

# ── 节点普查：按 testid 枚举，并按**内部构成**判类型 ─────────────────────
NODES_JS = """() => {
  const els = [...document.querySelectorAll('[data-testid^="rf__node-"]')];
  return els.map((el) => {
    const b = el.getBoundingClientRect();
    const txt = (el.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 40);
    const aria = [...el.querySelectorAll('[aria-label]')]
      .map((x) => x.getAttribute('aria-label'))
      .filter((s) => s && s.length < 40).slice(0, 6);
    return {
      tid: el.getAttribute('data-testid'),
      rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
      text: txt,
      aria: aria,
      n_img: el.querySelectorAll('img').length,
      n_video: el.querySelectorAll('video').length,
      n_audio: el.querySelectorAll('audio').length,
      n_svg: el.querySelectorAll('svg').length,
    };
  });
}"""


def classify(n):
    """按**内部构成**判节点类型（不看 class —— 源站没有可依赖的 class）。"""
    if n["n_video"] or n["n_audio"]:
        return "media"
    if n["n_img"]:
        return "image"
    joined = " ".join(n["aria"]) + " " + n["text"]
    if "音频" in joined or "audio" in joined.lower():
        return "audio"
    if "图片" in joined or "image" in joined.lower():
        return "image"
    if "视频" in joined or "video" in joined.lower():
        return "video"
    if "文本" in joined or "text" in joined.lower():
        return "text"
    if "主体" in joined:
        return "subject"
    return "unknown"


def main() -> int:
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    # ── 等就绪（第一版栽在这：6s 就读，读到的是「还在加载」）──────────
    ready = {}
    for i in range(30):                       # 30 × 2s = 60s
        ready = page.evaluate(READY_JS)
        print("[%4.1fs] preparing=%s empty=%s n_nodes=%d" % (
            2 * (i + 1), ready.get("preparing"), ready.get("empty_open"),
            ready.get("n_nodes", -1)))
        if not ready.get("preparing") and not ready.get("empty_open") \
                and ready.get("n_nodes", 0) > 0:
            print("=> 画布就绪（第 %d 次轮询）" % (i + 1))
            break
        page.wait_for_timeout(2000)
    else:
        print("=> 60 秒仍未就绪 ⇒ 如实记录，不猜")

    nodes = page.evaluate(NODES_JS)
    print("== 节点 %d 个 ==" % len(nodes))
    kinds = {}
    for n in nodes:
        k = classify(n)
        kinds.setdefault(k, []).append(n)
        print("  %-10s %-22s %s img=%d vid=%d aud=%d %r"
              % (k, n["tid"], n["rect"], n["n_img"], n["n_video"], n["n_audio"],
                 n["text"][:24]))
    print("== 类型分布 ==")
    for k, v in sorted(kinds.items(), key=lambda kv: -len(kv[1])):
        print("  %-10s %d" % (k, len(v)))

    result = {
        "generated_by": "scripts/jimeng_probe1032b2_expand_source.py",
        "measured_at": "2026-10-21",
        "canvas_url": URL,
        "how": "登录源站 → 打开示例画布 → **轮询到画布就绪** → 按 `rf__node-` testid "
               "枚举节点并按内部构成判类型 → 选中目标节点 → 找它面板上的展开钮 → 点它 → 读展开层。",
        "first_attempt_failure": {
            "what": "⭐ 第一版探针读到「0 个节点」，**两处都是量法错，不是产品没有**",
            "err_1": "只等 6s 就读 ⇒ 那一刻源站还在 `workspace-preparing-state`（Loading canvas）"
                     "⇒ ⇒ **画布要 ~9s 才就绪**",
            "err_2": "用 `.react-flow__node` 找节点 ⇒ 源站**不用 React Flow 的 class**，"
                     "它的节点 testid 是 `rf__node-<uuid>` ⇒ ⇒ **选错选择器永远读到 0 个**",
            "lesson": "⭐⭐ 「读数为 0」先问「我的探针量到的是不是那个东西」——"
                      "**等够了吗？选对了吗？** ⇒ 两问都过了才轮到「它真的不存在」",
        },
        "nodes_total": len(nodes),
        "kind_counts": {k: len(v) for k, v in sorted(kinds.items())},
        "expanded": [],
        "not_measured": [],
    }
    print("\n写入 %s" % OUT)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    return 0


main()
