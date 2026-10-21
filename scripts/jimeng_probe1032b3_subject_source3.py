"""batch 1032-②b-3 取证 v3：在源站上**造出「有资源的视频节点」**，进重拍/编辑态，
读那枚 @ 钮点开什么。

⭐⭐⭐ 为什么必须 v3（前两版为什么进不去）
------------------------------------------
v1 / v2 的诚实结论都是「选中视频节点后没有编辑入口」，读数逐字：
  视频 1 / No resources: 0 ready, 0 processing
⇒ ⇒ **那个视频节点是空的** ⇒ ⇒ 源站**空节点不给「局部重拍」/「视频编辑」**
   （手册 20-reference §节点类型表：视频（空）→ 视频生成面板；
     视频（带媒体）→ 视频工具条才有 局部重拍✦/视频编辑✦）
⇒ ⇒ 不是探针不行，是**样本不满足前置条件**。

⇒ v3 换路：**上传一个本地小视频**（上传本身免费、**不扣积分**），
  让画布上出现一个**有资源的视频节点** ⇒ ⇒ 才进得了重拍/编辑态。

⚠️ 纪律（与前两版同）：
  · 上传 = 有副作用的 CRUD，**允许**（手册 TEST_MEDIA_ASSETS.md 明确：可上传/可删除）
  · **绝不点「生成」「发送」「购买」「充值」**；进入编辑态不扣费，**发送才扣费**
    （手册 20-reference.md:297「进入不扣费，发送才扣费」）
  · 探针必须**逐步落盘** + 每步包 try（源站是 SPA，evaluate 在页面忙时会无限等）

用法：
    PYTHONUNBUFFERED=1 timeout 600 ~/.venvs/liblib-harness/bin/python \
      scripts/jimeng_headless.py --url "" --timeout 180000 run \
      scripts/jimeng_probe1032b3_subject_source3.py
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path("docs/research/jimeng-canvas/inputs/source-subject-mention-1032b3-v3.json")
URL = (
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create"
)
# ⭐ 用仓库登记过的小视频（34KB）⇒ 上传快、不占用户配额
MEDIA = "/Users/yangjiefeng/Downloads/134_mock-task-1778068676388-15981.mp4"

READY_JS = """() => ({
  preparing: !!document.querySelector('[data-testid="workspace-preparing-state"]'),
  n_nodes: document.querySelectorAll('[data-testid^="rf__node-"]').length,
})"""

# 视频节点（含空/有资源两种）
VIDEO_NODES_JS = """() => {
  const els = [...document.querySelectorAll('[data-testid^="rf__node-"]')];
  return els.map((el) => {
    const b = el.getBoundingClientRect();
    const aria = [...el.querySelectorAll('[aria-label]')]
      .map((x) => x.getAttribute('aria-label')).filter(Boolean);
    return {
      tid: el.getAttribute('data-testid'),
      rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
      text: (el.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 90),
      aria: aria.slice(0, 6),
      n_video: el.querySelectorAll('video').length,
      n_img: el.querySelectorAll('img').length,
      has_media: /ready|已就绪|\\d+s|00:0/.test(el.innerText || ''),
    };
  });
}"""

# 工具条：选中「有资源」的视频节点后出现的一排按钮
TOOLBAR_JS = """() => {
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

# 面板 / 浮层（重拍面板是画布内联的，不一定有 role ⇒ 额外扫可见的定尺容器）
PANELS_JS = """() => {
  const out = [];
  const cands = [...document.querySelectorAll(
    '[role="dialog"],[role="listbox"],[role="menu"],[role="popover"],[aria-modal="true"],' +
    '[data-testid*="mention"],[data-testid*="picker"],[data-testid*="panel"]')];
  for (const el of cands) {
    const b = el.getBoundingClientRect();
    if (b.width < 10 || b.height < 10) continue;
    out.push({
      role: el.getAttribute('role') || '',
      aria: el.getAttribute('aria-label') || '',
      testid: el.getAttribute('data-testid') || '',
      rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
      text: (el.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 300),
      n_btns: el.querySelectorAll('button').length,
    });
  }
  return out;
}"""

# 可见 input / textarea / contenteditable（面板里的提示词面）
INPUTS_JS = """() => {
  const out = [];
  for (const el of document.querySelectorAll('input,textarea,[contenteditable="true"]')) {
    const b = el.getBoundingClientRect();
    if (b.width < 2 || b.height < 2) continue;
    if (b.bottom < 0 || b.top > window.innerHeight) continue;
    out.push({
      tag: el.tagName.toLowerCase(),
      aria: el.getAttribute('aria-label') || '',
      ph: el.getAttribute('placeholder') || '',
      slot: el.getAttribute('data-slot') || '',
      rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
      value_len: typeof el.value === 'string' ? el.value.length : -1,
    });
  }
  return out;
}"""

# 页面里所有 <input type=file>（上传入口）
FILE_INPUTS_JS = """() => {
  const out = [];
  for (const el of document.querySelectorAll('input[type="file"]')) {
    const b = el.getBoundingClientRect();
    out.push({
      accept: el.getAttribute('accept') || '',
      multiple: el.hasAttribute('multiple'),
      visible: b.width > 0 && b.height > 0,
      rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
      parent_testid: el.parentElement ? (el.parentElement.getAttribute('data-testid') || '') : '',
    });
  }
  return out;
}"""


def _save(result):
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
        print("  !! 这一步失败：%s" % str(e)[:140])
        return default


def main() -> int:
    result = {
        "generated_by": "scripts/jimeng_probe1032b3_subject_source3.py",
        "measured_at": "2026-10-21",
        "canvas_url": URL,
        "uploaded_media": MEDIA,
        "how": "登录源站 → 等画布就绪 → **上传一个本地小视频**（上传免费、不扣积分）"
               "→ 选中新出现的「有资源的视频节点」→ 点工具条「局部重拍」/「视频编辑」"
               "（**进入编辑态不扣费，发送才扣费**）→ 枚举面板里的按钮 → 找 @ 那一枚 "
               "→ 点它 → 读开了什么。⚠️ 绝不点生成/发送/购买/充值。",
        "v1_v2_finding": "v1/v2 选中的那个视频节点是空的（No resources: 0 ready, 0 "
                         "processing）⇒ 空节点不提供「局部重拍」/「视频编辑」入口 ⇒ "
                         "进不了编辑态 ⇒ 探针不是坏了，是样本不满足前置条件。",
        "steps": [],
    }

    page.goto(URL, wait_until="domcontentloaded", timeout=180_000)
    page.wait_for_timeout(3000)

    ready = {}
    for i in range(60):
        try:
            ready = page.evaluate(READY_JS)
        except Exception as e:  # noqa: BLE001
            print("[%4.1fs] evaluate 失败：%s" % (2 * (i + 1), str(e)[:80]))
            ready = {}
        print("[%4.1fs] preparing=%s n_nodes=%d" % (
            2 * (i + 1), ready.get("preparing"), ready.get("n_nodes", -1)))
        if not ready.get("preparing") and ready.get("n_nodes", 0) > 0:
            print("=> 画布就绪")
            break
        page.wait_for_timeout(2000)

    before = _try(lambda: page.evaluate(VIDEO_NODES_JS), []) or []
    result["n_nodes_before"] = len(before)
    result["video_nodes_before"] = before
    print("== 上传前 节点 %d ==" % len(before))

    # ── 上传（免费；不点任何生成钮）──────────────────────────────────
    file_inputs = _try(lambda: page.evaluate(FILE_INPUTS_JS), []) or []
    result["file_inputs"] = file_inputs
    print("== file input %d 个 ==" % len(file_inputs))
    for fi in file_inputs:
        print("   %r accept=%r visible=%s" % (fi["parent_testid"], fi["accept"], fi["visible"]))

    uploaded = False
    if not file_inputs:
        # ⭐⭐⭐ v3 第一版的两个真读数（都写进产物，别让后人重踩）：
        #   ① 源站页面里 `input[type=file]` 数量 = **0**
        #      ⇒ 上传**不是**靠一个常驻 file input ⇒ ⇒ 必然是「点按钮 ⇒ 弹
        #      filechooser 事件」⇒ ⇒ 必须 `page.on("filechooser")` 全局监听。
        #      （手册 20-reference.md:2498 早就写过这条，我第一版忘了先查手册。）
        #   ② `button[aria-label="上传"]` 定位到 **0 枚**
        #      ⇒ 真因：该钮的 `title` 是逐字 **「画布编辑尚未准备就绪」**、
        #      `svg_paths=0`（图标没渲染）⇒ ⇒ **它是禁用态**，
        #      而 Playwright 的 `count()` 只数**匹配的元素**、不数「可点的」——
        #      之所以 count()=0，是因为它在 **v3 读数那一刻还没渲染**。
        #      ⇒ ⇒ 正确做法：**轮询等它出现且 title 不是「尚未准备就绪」**。
        print("== 无 file input ⇒ 改走 filechooser 事件 ==")
        try:
            page.on(
                "filechooser",
                lambda fc: fc.set_files(MEDIA),
            )
            # 轮询等「上传」钮就绪（title 不再是「画布编辑尚未准备就绪」）
            up = None
            for i in range(30):                    # 30 × 2s = 60s
                cand = page.locator('button[aria-label="上传"]')
                n = cand.count()
                if n:
                    t = cand.first.get_attribute("title") or ""
                    print("   上传钮 %d 枚 title=%r" % (n, t))
                    if "尚未准备就绪" not in t:
                        up = cand.first
                        break
                page.wait_for_timeout(2000)
            if up is not None:
                up.click(timeout=15000)
                uploaded = True
                print("== 已点上传（就绪态），等待 filechooser ==")
            else:
                print("   ⚠️ 上传钮始终未就绪 ⇒ 记为未测量")
        except Exception as e:  # noqa: BLE001
            print("  !! filechooser 路径失败：%s" % str(e)[:160])
    elif file_inputs:
        try:
            page.set_input_files("input[type=file]", MEDIA)
            uploaded = True
            print("== 已投递上传 ==")
        except Exception as e:  # noqa: BLE001
            print("  !! set_input_files 失败：%s" % str(e)[:160])

    # 等新节点出现（**有资源的视频节点**）
    # ⭐⭐⭐ v3 第一版的一个**真 bug**：`has_media` 判据写成了
    #   `/ready|已就绪|\d+s|00:0/.test(innerText)` ⇒ ⇒ **时间线节点**
    #   （innerText 里含「00:00」「00:05」…）也匹配 ⇒ ⇒ 选中了「时间线 1」
    #   ⇒ ⇒ 于是「选中后」读到的是时间线工具条（导出时间线/全屏编辑/静音），
    #   ⇒ ⇒ 自然找不到「局部重拍」。**这是探针的判据错，不是源站没有入口。**
    # ⇒ 收紧：只认**真正的视频节点**（`n_video > 0` 或 aria/text 含「视频」）
    #   且**不是**时间线/导演台/音频/图片。
    target = None
    before_tids = {b["tid"] for b in before}
    for i in range(40):                       # 40 × 3s = 120s
        page.wait_for_timeout(3000)
        vids = _try(lambda: page.evaluate(VIDEO_NODES_JS), []) or []
        print("[upload wait %4.1fs] 视频节点 %d 个" % (3 * (i + 1), len(vids)))
        for v in vids:
            blob = " ".join([v.get("text", "")] + list(v.get("aria") or []))
            is_video = v.get("n_video", 0) > 0 or "视频" in blob
            is_other = any(k in blob for k in ("时间线", "导演台", "音频", "图片", "文本"))
            if is_video and not is_other and v["tid"] not in before_tids:
                target = v
                break
        if target:
            break
    if not target:
        # 没等到**新**视频节点 ⇒ 退而求其次：找画布上**任意**有资源的视频节点
        vids = _try(lambda: page.evaluate(VIDEO_NODES_JS), []) or []
        for v in vids:
            blob = " ".join([v.get("text", "")] + list(v.get("aria") or []))
            if v.get("n_video", 0) > 0 or ("视频" in blob and "时间线" not in blob):
                target = v
                break
    result["n_nodes_after_upload"] = len(_try(lambda: page.evaluate(VIDEO_NODES_JS), []) or [])
    result["uploaded"] = uploaded
    result["target_video_node"] = target
    print("== 目标视频节点 ==", target)
    _save(result)

    if not target:
        result["not_measured"] = ["上传后没等到新视频节点 ⇒ 进不了编辑态"]
        print("=> 没等到新节点，如实记录")
        _save(result)
        return 0

    # ── 选中它 → 读工具条 ────────────────────────────────────────────
    cx = target["rect"][0] + target["rect"][2] / 2
    cy = target["rect"][1] + target["rect"][3] / 2
    page.mouse.click(cx, cy)
    page.wait_for_timeout(1500)
    btns = _try(lambda: page.evaluate(TOOLBAR_JS), []) or []
    result["toolbar_buttons"] = btns
    print("== 选中后可见按钮 %d 枚 ==" % len(btns))
    for b in btns:
        print("   al=%-24r txt=%-12r tid=%-22r %s svg=%d" % (
            b["al"], b["txt"], b["testid"], b["rect"], b.get("svg_paths", 0)))
    _save(result)

    # ── 进「局部重拍」或「视频编辑」态 ───────────────────────────────
    entry = None
    for key in ("局部重拍", "视频编辑"):
        hit = [b for b in btns if key in (b["al"] + b["txt"])]
        if hit:
            entry = hit[0]
            print("== 找到编辑入口：%s ==" % key)
            break
    if not entry:
        result["not_measured"] = ["有资源的视频节点选中后仍没找到「局部重拍」/「视频编辑」"]
        print("=> 仍没找到编辑入口，如实记录")
        _save(result)
        return 0

    page.mouse.click(entry["rect"][0] + entry["rect"][2] / 2,
                     entry["rect"][1] + entry["rect"][3] / 2)
    page.wait_for_timeout(2500)

    edit_btns = _try(lambda: page.evaluate(TOOLBAR_JS), []) or []
    panels = _try(lambda: page.evaluate(PANELS_JS), []) or []
    inputs = _try(lambda: page.evaluate(INPUTS_JS), []) or []
    result["edit_mode_buttons"] = edit_btns
    result["edit_mode_panels"] = panels
    result["edit_mode_inputs"] = inputs
    print("== 编辑态按钮 %d / 浮层 %d / 输入面 %d ==" % (
        len(edit_btns), len(panels), len(inputs)))
    for b in edit_btns:
        print("   al=%-24r txt=%-12r %s svg=%d" % (
            b["al"], b["txt"], b["rect"], b.get("svg_paths", 0)))
    for L in panels:
        print("   PANEL role=%-10s aria=%-20r %s %r" % (
            L["role"], L["aria"], L["rect"], L["text"][:100]))
    for I in inputs:
        print("   INPUT %s aria=%r ph=%r slot=%r %s" % (
            I["tag"], I["aria"], I["ph"], I["slot"], I["rect"]))
    _save(result)

    # ── 找 @ 那一枚，点它，读开了什么 ─────────────────────────────────
    at_btn = None
    for b in edit_btns:
        blob = " ".join([b["al"], b["txt"], b["title"], b["cls"], b["html"]]).lower()
        if "@" in blob or "at-sign" in blob or "atsign" in blob:
            at_btn = b
            break
    if at_btn is None:
        # 也可能 @ 是一枚**没有可访问名**的图标钮 ⇒ 用 svg 子元素数 + 位置再找
        print("== 没按名字找到 @ ⇒ 按 svg 形状枚举编辑态里的小图标钮 ==")
        result["at_button"] = None
        result["not_measured"] = ["编辑态里没按可访问名找到 @ 钮"]
        _save(result)
        return 0

    print("== 点 @ 钮：al=%r txt=%r ==" % (at_btn["al"], at_btn["txt"]))
    page.mouse.click(at_btn["rect"][0] + at_btn["rect"][2] / 2,
                     at_btn["rect"][1] + at_btn["rect"][3] / 2)
    page.wait_for_timeout(1800)

    after_panels = _try(lambda: page.evaluate(PANELS_JS), []) or []
    after_btns = _try(lambda: page.evaluate(TOOLBAR_JS), []) or []
    after_inputs = _try(lambda: page.evaluate(INPUTS_JS), []) or []
    result["at_button"] = at_btn
    result["after_at_panels"] = after_panels
    result["after_at_inputs"] = after_inputs
    print("== 点 @ 后：浮层 %d / 输入面 %d ==" % (len(after_panels), len(after_inputs)))
    for L in after_panels:
        print("   PANEL role=%-10s aria=%-20r %s %r" % (
            L["role"], L["aria"], L["rect"], L["text"][:160]))
    for I in after_inputs:
        print("   INPUT %s aria=%r ph=%r slot=%r %s" % (
            I["tag"], I["aria"], I["ph"], I["slot"], I["rect"]))
    for b in after_btns:
        blob = " ".join([b["al"], b["txt"], b["title"], b["cls"]]).lower()
        if "暂无" in blob or "主体" in blob or "图片" in blob or "视频" in blob or "音频" in blob:
            print("   CAND al=%-24r txt=%-16r %s" % (b["al"], b["txt"], b["rect"]))
    result["after_at_candidate_buttons"] = [
        b for b in after_btns
        if any(k in (" ".join([b["al"], b["txt"], b["title"], b["cls"]]))
               for k in ("暂无", "主体", "图片", "视频", "音频"))
    ]
    _save(result)

    print("\n写入 %s" % OUT)
    return 0


main()
