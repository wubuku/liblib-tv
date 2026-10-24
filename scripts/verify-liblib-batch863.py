#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 863 门禁：**取景框外的遮罩**（源站逐字 ＋ clone 运行时读数 ＋ 红色探针）。

## ★ 本批整改的是什么

★ clone 的取景框（batch 860 接上的、batch 862 补了开关的）**框外**靠框自己的
  `shadow-[0_0_0_9999px_rgba(0,0,0,0.24)]` 撑出一层遮罩
  ⟹ ⟹ **黑 24%、没有模糊** ⟹ ⟹ 与源站不同构（D20）。
★ 源站逐字（chunk 的 `mP` 组件，**已入库** `raw/source-863-mask-literal.txt`）：

```js
(0,o.jsx)("div",{ref:l,
  className:"pointer-events-none absolute bottom-0 left-0 right-0 top-0 z-10",
  children:u&&(0,o.jsxs)(i.Fragment,{children:[
    (0,o.jsx)("div",{className:"absolute inset-0 bg-black/20 backdrop-blur-md",
      style:{WebkitMaskImage:"linear-gradient(#000 0 0), linear-gradient(#000 0 0)",
             WebkitMaskPosition:`0 0, ${u.left}px ${u.top}px`,
             WebkitMaskRepeat:"no-repeat, no-repeat",
             WebkitMaskSize:`100% 100%, ${u.width}px ${u.height}px`,
             WebkitMaskComposite:"xor",maskComposite:"exclude"}}),
    (0,o.jsx)("div",{className:"outline-white/18 absolute rounded-xl outline -outline-offset-1",
      style:{left:u.left,top:u.top,width:u.width,height:u.height}}), …]})})
```

⟹ ⟹ 四条**逐字**结论：
① 遮罩是**独立的一层**，铺满整个容器（`absolute inset-0`），
   **不是**框自己的 box-shadow；
② 框外＝ **黑 20% ＋ 背景模糊**（`bg-black/20 backdrop-blur-md`）；
③ 框内被 **CSS mask 挖空**（`mask-composite: exclude` ＋ 两次 `linear-gradient`）
   ⟹ ⟹ 框内**不压暗、不模糊**；
④ 遮罩与框都在 `z-10` 的**同一个容器**里，容器 `pointer-events-none`。

## ★ ★ 期望值从哪来（★ 不得凭记忆手打）

★ 本门禁的**源站侧期望值**全部从**入库证据**派生：
  `docs/research/liblib-canvas-batch863-2026-10-01/raw/source-863-mask-literal.txt`
  （源站 chunk 的**逐字摘录**，含来源 chunk 路径、字符偏移与两个 sha256）。
★ 证据文件缺失或解析不出关键片段 ⟹ ⟹ **直接判失败**，不许"凭印象补上"。

## ★ ★★ 源站运行时复核：**待补**（不是"已实测"）

★ 本批取证时**源站项目页打不开**（画布节点 0、正文停在「项目加载中...」、
  **不发任何 XHR/fetch、无 4xx/5xx、无 WebSocket**，而首页正常渲染 ⟹ ⟹ 登录态有效
  ⟹ ⟹ 判定为**源站侧临时故障/风控**，不是本地环境问题）。
⇒ ⇒ 故本门禁的源站侧是**逐字静态判据**，**不是**运行时读数。
⇒ ⇒ 源站恢复后必须补跑 `probes/source863_frame_mask.py`，
     并把运行时读数补进 `raw/source-863-frame-mask.json`（本门禁不因此假装已实测）。

## ★ ★★ 为什么用「红色探针」证明 mask 真的挖空了

★ 「框内/框外亮度比」**不能**当判据：3D 场景**一直在动** ⟹ ⟹ 两次截图内容不同
  ⟹ ⟹ 亮度比会漂移（实测 0.87 ↔ 0.90）⟹ ⟹ 只能作参考。
★ 红色探针是**确定性**的：把遮罩层临时染成 `rgba(255,0,0,0.85)`
  ⟹ ⟹ 框外**必须是红的**、框内**必须不是红的**（被 mask 挖空）
  ⟹ ⟹ 判据＝「框外 R − 框内 R ≥ 40」**且**「**红味** R−G：框外 ≥ 60、框内 ≤ 30」。
★ ★ **为什么还要看「红味」**：★ 只看 R 通道**分不清**「被染红」与「底色本来就亮」
  ⟹ ⟹ 3D 场景顶部可能是亮的（实测框外 R 可达 **222**）
  ⟹ ⟹ 加上 G 通道后：红色油漆压在任何底色上 R−G 都很大，
  而「本来就白」(255,255,255) 的 R−G ≈ **0** ⟹ ⟹ 不会冒充。
★ 若 mask 没挖空 ⟹ ⟹ 框内也会被染红 ⟹ ⟹ 差值 ≈ 0 ⟹ ⟹ 判据翻红。

## ★ 判据只读绝对几何与 DOM 可见读数

★ `elementFromPoint` **会穿透** `pointer-events:none` 的框 ⟹ ⟹ 不用它证明可见性。

## ★ 输出
  docs/research/liblib-canvas-batch863-2026-10-01/runtime-audit.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs/research/liblib-canvas-batch863-2026-10-01"
RAW = OUT_DIR / "raw"
BASE = "http://localhost:4317"

SRC_VIEW = ROOT / "src/components/director/DirectorViewport.tsx"
EVIDENCE = RAW / "source-863-mask-literal.txt"

# ★ 六档比例（源站逐字顺序）
RATIOS = ["21:9", "16:9", "4:3", "1:1", "3:4", "9:16"]

READ = r"""()=>{
  const norm=(c)=>{
    const cv=document.createElement('canvas'); cv.width=8; cv.height=8;
    const ctx=cv.getContext('2d');
    ctx.clearRect(0,0,8,8);
    ctx.fillStyle='#000';
    ctx.fillStyle=c;
    ctx.fillRect(0,0,8,8);
    const d=ctx.getImageData(4,4,1,1).data;
    return {raw:c, rgba:[d[0],d[1],d[2],d[3]]};
  };
  const container=document.querySelector('[data-director-aspect-mask-container]');
  const mask=document.querySelector('[data-director-aspect-mask]');
  const f=document.querySelector('[data-director-aspect-frame]');
  const btn=document.querySelector('[data-director-frame-thirds-toggle]');
  const out={容器在场:!!container, 遮罩层在场:!!mask, 框在场:!!f, 开关在场:!!btn};
  let cr=null;
  if(container){
    const r=container.getBoundingClientRect(); cr=r;
    const cs=getComputedStyle(container);
    out.容器={cls:container.getAttribute('class')||'',
              rect:{x:Math.round(r.x),y:Math.round(r.y),
                    w:Math.round(r.width),h:Math.round(r.height)},
              pointerEvents:cs.pointerEvents, zIndex:cs.zIndex,
              position:cs.position};
    out.容器首子元素是遮罩层=!!(container.firstElementChild===mask);
    out.容器含框=!!(f && container.contains(f));
  }
  if(mask){
    const r=mask.getBoundingClientRect(); const cs=getComputedStyle(mask);
    out.遮罩层={cls:mask.getAttribute('class')||'',
                rect:{x:Math.round(r.x),y:Math.round(r.y),
                      w:Math.round(r.width),h:Math.round(r.height)},
                背景:norm(cs.backgroundColor), 背景原文:cs.backgroundColor,
                backdropFilter:cs.backdropFilter,
                maskImage:cs.maskImage, maskComposite:cs.maskComposite,
                maskPosition:cs.maskPosition, maskSize:cs.maskSize,
                maskRepeat:cs.maskRepeat, pointerEvents:cs.pointerEvents};
  }
  if(f){
    const r=f.getBoundingClientRect(); const cs=getComputedStyle(f);
    out.框={x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};
    out.框样式={boxShadow:cs.boxShadow, borderWidth:cs.borderTopWidth,
                outlineWidth:cs.outlineWidth, outlineOffset:cs.outlineOffset,
                outlineColor:norm(cs.outlineColor), radius:cs.borderRadius};
    if(cr) out.框相对容器={left:Math.round((r.x-cr.x)*100)/100,
                          top:Math.round((r.y-cr.y)*100)/100};
  }
  out.分线条数=document.querySelectorAll('[data-director-thirds] span').length;
  return out;
}"""


class Verifier:
    def __init__(self) -> None:
        self.count = 0
        self.failures: list[str] = []
        self.result: dict[str, Any] = {}

    def check(self, name: str, ok: bool, detail: Any = "") -> None:
        self.count += 1
        if not ok:
            self.failures.append(f"{name}  ⟵ {detail}")


def strip_comments(src: str) -> str:
    """去掉 `//` 行注释与 `/* */` 块注释 ⟹ ⟹ 静态判据只读**代码**。

    ★ batch 859 的教训：注释里逐字抄的类串**足以**让判据变绿 ⟹ ⟹ 假绿。
    ★ batch 863 沿用同一条纪律：**注释里不许抄 clone 自己的 JSX 字面量**。
    """
    out = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    out = re.sub(r"//[^\n]*", " ", out)
    return out


def grab(pattern: str, text: str, flags: int = 0) -> str:
    m = re.search(pattern, text, flags)
    return m.group(1) if m else ""


def shape(tpl: str) -> str:
    """把 `${…}` 变量名归一化 ⟹ ⟹ 比「结构」而不是比「变量名」。

    ★ 源站是 `${u.left}`、clone 是 `${frameRect.left}` ⟹ ⟹ 逐字比会假红
    ⟹ ⟹ 期望值只比**结构**（`0 0, Xpx Xpx`）。
    """
    return re.sub(r"\$\{[^}]*\}", "X", tpl)


def pick_rgba(entry: Any) -> list[int] | None:
    if isinstance(entry, dict) and isinstance(entry.get("rgba"), list):
        return [int(x) for x in entry["rgba"]]
    if isinstance(entry, str):
        nums = re.findall(r"[\d.]+", entry)
        if len(nums) >= 4:
            alpha = float(nums[3])
            return [int(float(nums[0])), int(float(nums[1])), int(float(nums[2])),
                    int(round(alpha * 255)) if alpha <= 1 else int(alpha)]
    return None


def parse_pairs(value: str) -> list[tuple[float, float]]:
    """把 `0px 0px, 65.6667px 32px` 解析成 [(0,0), (65.67,32)]。"""
    out: list[tuple[float, float]] = []
    for part in (value or "").split(","):
        nums = re.findall(r"-?[\d.]+", part)
        if len(nums) >= 2:
            out.append((float(nums[0]), float(nums[1])))
    return out


def open_desk(page: Any) -> None:
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    page.evaluate(
        "() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
    page.wait_for_function("() => Boolean(window.__director_store)", timeout=90_000)
    page.wait_for_timeout(1500)
    node = page.locator(".react-flow__node-script-execution").first
    try:
        node.scroll_into_view_if_needed(timeout=8000)
    except Exception:  # noqa: BLE001
        pass
    page.wait_for_timeout(400)
    try:
        node.hover(timeout=8000)
        page.wait_for_timeout(600)
    except Exception:  # noqa: BLE001
        pass
    page.locator("[data-open-director]").first.click(timeout=15000)
    page.wait_for_timeout(6500)
    page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")


def red_probe(page: Any, frame: dict, container: dict) -> dict:
    """★ 红色探针：把遮罩层染红 ⟹ ⟹ 框外必红、框内必不红（被 mask 挖空）。

    ★ 取样点必须**完全**落在遮罩区域内、且**完全**在框外／框内
    ⟹ ⟹ 采样框不能压到框的边界 ⟹ ⟹ 「框外」取**框正上方**那条带。
    ★ ★ 几何读数缺失 ⟹ ⟹ **直接返回「不可用」** ⟹ ⟹ 不许拿默认 0 去采样
    ⟹ ⟹ （否则 HEAD 态会采到两个毫不相干的点 ⟹ ⟹ 差值可能碰巧 ≥ 40）。
    """
    crect = container.get("rect") or {}
    frame_rect = frame.get("rect") or frame
    if not crect or not frame_rect or "x" not in frame_rect:
        return {"可用": False, "原因": "★ 框/容器的几何读数缺失 ⟹ ⟹ 探针无从进行"}
    page.evaluate(
        "() => { const m=document.querySelector('[data-director-aspect-mask]');"
        "if(m) m.style.backgroundColor='rgba(255,0,0,0.85)'; }")
    page.wait_for_timeout(600)
    # ★ ★ 取样点必须**完全**落在遮罩区域内、且**完全**在框外／框内
    #   ⟹ ⟹ 「框外」取**框正上方**那条带（容器顶边 ↔ 框顶边之间）⟹ ⟹ 采样框不压框边；
    #   ⟹ ⟹ 「框内」取框内靠左上处。
    inside = {"x": frame_rect.get("x", 0) + 150, "y": frame_rect.get("y", 0) + 60}
    outside = {"x": frame_rect.get("x", 0) + 150,
               "y": crect.get("y", 0) + 4}
    buf_in = page.screenshot(clip={"x": inside["x"], "y": inside["y"],
                                   "width": 24, "height": 24})
    buf_out = page.screenshot(clip={"x": outside["x"], "y": outside["y"],
                                    "width": 24, "height": 24})
    (RAW / "clone-863-redprobe-inside.png").write_bytes(buf_in)
    (RAW / "clone-863-redprobe-outside.png").write_bytes(buf_out)
    page.evaluate(
        "() => { const m=document.querySelector('[data-director-aspect-mask]');"
        "if(m) m.style.backgroundColor=''; }")
    page.wait_for_timeout(300)

    from PIL import Image
    import io

    def mean_rgb(buf: bytes) -> dict:
        im = Image.open(io.BytesIO(buf)).convert("RGB")
        px = list(im.getdata())
        n = max(1, len(px))
        r = sum(p[0] for p in px) / n
        g = sum(p[1] for p in px) / n
        b = sum(p[2] for p in px) / n
        # ★ ★ 「红味」＝ R − G：★ 只看 R 通道**分不清**「被染红」与「本来就很亮」
        #   ⟹ ⟹ 场景顶部可能是亮的（实测框外 R 可达 222）
        #   ⟹ ⟹ 必须同时看 G：★ 红色油漆 (255,0,0) 压在任何底色上 ⇒ R−G 都很大；
        #   ⟹ ⟹ 而「本来就白」(255,255,255) ⇒ R−G ≈ 0 ⟹ ⟹ 不会冒充。
        return {"R": round(r, 2), "G": round(g, 2), "B": round(b, 2),
                "红味": round(r - g, 2), "样本数": len(px)}

    rgb_in = mean_rgb(buf_in)
    rgb_out = mean_rgb(buf_out)
    return {"可用": True,
            "框内R": rgb_in["R"], "框外R": rgb_out["R"],
            "框内红味": rgb_in["红味"], "框外红味": rgb_out["红味"],
            "框内": rgb_in, "框外": rgb_out,
            "差值": round(rgb_out["R"] - rgb_in["R"], 2),
            "取样点": {"框内": inside, "框外": outside}}


def main() -> int:
    v = Verifier()
    audit: dict[str, Any] = {
        "batch": 863,
        "title": "取景框外的遮罩（源站逐字 ＋ 运行时读数 ＋ 红色探针）",
        "源站运行时复核": "★ 待补（源站项目页本批取证时不可用）",
    }

    # ══ S1 源站逐字证据必须在场且可解析 ═══════════════════════════
    v.check("source:the-verbatim-evidence-file-is-in-the-repo",
            EVIDENCE.exists(), detail=str(EVIDENCE))
    if not EVIDENCE.exists():
        print("缺源站逐字证据 ⟹ 判失败，不许通过")
        v.result = {"判据数": v.count, "失败": v.failures, "audit": audit}
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "runtime-audit.json").write_text(
            json.dumps(v.result, ensure_ascii=False, indent=1, default=str),
            encoding="utf-8")
        return 1

    lit = EVIDENCE.read_text(encoding="utf-8")
    ev_container = grab(r'className:"(pointer-events-none absolute bottom-0 left-0 '
                        r'right-0 top-0 z-10)"', lit)
    ev_mask_cls = grab(r'className:"(absolute inset-0 bg-black/20 backdrop-blur-md)"', lit)
    ev_mask_image = grab(r'WebkitMaskImage:"([^"]+)"', lit)
    ev_mask_pos = grab(r'WebkitMaskPosition:`([^`]+)`', lit)
    ev_mask_repeat = grab(r'WebkitMaskRepeat:"([^"]+)"', lit)
    ev_mask_size = grab(r'WebkitMaskSize:`([^`]+)`', lit)
    ev_webkit_comp = grab(r'WebkitMaskComposite:"([^"]+)"', lit)
    ev_std_comp = grab(r'maskComposite:"([^"]+)"', lit)
    ev_frame_cls = grab(r'className:"(outline-white/18 absolute rounded-xl outline '
                        r'-outline-offset-1)"', lit)
    ev_parse_ok = all([ev_container, ev_mask_cls, ev_mask_image, ev_mask_pos,
                       ev_mask_repeat, ev_mask_size, ev_webkit_comp, ev_std_comp,
                       ev_frame_cls])
    v.check("source:the-evidence-file-yields-every-expected-literal",
            ev_parse_ok,
            detail={"容器": ev_container, "遮罩类": ev_mask_cls,
                    "maskImage": ev_mask_image, "maskPosition": ev_mask_pos,
                    "maskRepeat": ev_mask_repeat, "maskSize": ev_mask_size,
                    "WebkitMaskComposite": ev_webkit_comp,
                    "maskComposite": ev_std_comp, "框类": ev_frame_cls})
    if not ev_parse_ok:
        v.result = {"判据数": v.count, "失败": v.failures, "audit": audit}
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "runtime-audit.json").write_text(
            json.dumps(v.result, ensure_ascii=False, indent=1, default=str),
            encoding="utf-8")
        return 1
    audit["源站逐字"] = {
        "容器类": ev_container, "遮罩类": ev_mask_cls, "maskImage": ev_mask_image,
        "maskPosition": ev_mask_pos, "maskRepeat": ev_mask_repeat,
        "maskSize": ev_mask_size, "WebkitMaskComposite": ev_webkit_comp,
        "maskComposite": ev_std_comp, "框类": ev_frame_cls,
    }
    # ★ 源站框描边是 `outline-white/18` ⟹ ⟹ 白 **18%**（从证据里解析，不手打）
    m18 = re.search(r"outline-white/(\d+)", ev_frame_cls)
    src_outline_pct = int(m18.group(1)) if m18 else 18
    # ★ 源站遮罩是 `bg-black/20` ⟹ ⟹ 黑 **20%**（从证据里解析，不手打）
    m20 = re.search(r"bg-black/(\d+)", ev_mask_cls)
    src_mask_pct = int(m20.group(1)) if m20 else 20
    audit["源站逐字"]["框描边百分比"] = src_outline_pct
    audit["源站逐字"]["遮罩黑度百分比"] = src_mask_pct

    # ══ S2 clone 源码契约（静态、剥注释后比）══════════════════════
    view_code = strip_comments(SRC_VIEW.read_text(encoding="utf-8"))
    v.check("source:the-mask-container-class-is-verbatim",
            ev_container in view_code, detail=ev_container)
    v.check("source:the-mask-layer-class-is-verbatim",
            ev_mask_cls in view_code, detail=ev_mask_cls)
    v.check("source:the-mask-image-is-verbatim",
            f'WebkitMaskImage:\n            "{ev_mask_image}"' in view_code
            or f'WebkitMaskImage:"{ev_mask_image}"' in view_code
            or ev_mask_image in view_code,
            detail=ev_mask_image)
    v.check("source:the-mask-position-shape-matches-the-source",
            shape(ev_mask_pos) == "0 0, Xpx Xpx"
            and re.search(r"WebkitMaskPosition:\s*`0 0, \$\{[^}]+\}px \$\{[^}]+\}px`",
                          view_code) is not None,
            detail={"源站": ev_mask_pos, "期望结构": "0 0, Xpx Xpx"})
    v.check("source:the-mask-size-shape-matches-the-source",
            shape(ev_mask_size) == "100% 100%, Xpx Xpx"
            and re.search(r"WebkitMaskSize:\s*`100% 100%, \$\{[^}]+\}px \$\{[^}]+\}px`",
                          view_code) is not None,
            detail={"源站": ev_mask_size, "期望结构": "100% 100%, Xpx Xpx"})
    v.check("source:the-mask-repeat-is-verbatim",
            f'WebkitMaskRepeat: "{ev_mask_repeat}"' in view_code, detail=ev_mask_repeat)
    v.check("source:the-mask-composite-is-verbatim",
            f'WebkitMaskComposite: "{ev_webkit_comp}"' in view_code
            and f'maskComposite: "{ev_std_comp}"' in view_code,
            detail={"WebkitMaskComposite": ev_webkit_comp,
                    "maskComposite": ev_std_comp})
    # ★ ★ 本批的核心整改：**框自己的 9999px box-shadow 必须删掉**
    v.check("source:the-frame-no-longer-carries-a-9999px-box-shadow",
            "9999px" not in view_code,
            detail="★ 源站的框**没有** box-shadow ⟹ ⟹ 遮罩由独立层承担")
    # ★ 框的描边（源站逐字 `outline-white/18` ⟹ ⟹ 18%）
    v.check("source:the-frame-outline-matches-the-source-percentage",
            f'outline: "1px solid rgba(255,255,255,{src_outline_pct / 100})"' in view_code
            and 'outlineOffset: "-1px"' in view_code
            and 'borderRadius: "12px"' in view_code,
            detail={"源站百分比": src_outline_pct,
                    "期望": f'1px solid rgba(255,255,255,{src_outline_pct / 100})'})
    # ★ ★ 回归：batch 862 的那枚开关与四条分线**不许**被本批改坏
    v.check("source:the-862-toggle-class-is-still-there",
            "nodrag nopan nowheel pointer-events-auto absolute z-20 flex h-8 w-8 "
            "items-center justify-center rounded-lg transition-colors" in view_code,
            detail="batch 862 的开关类名")
    v.check("source:the-862-four-thirds-are-still-there",
            view_code.count('"rgba(255,255,255,0.5)"') == 4,
            detail={"出现次数": view_code.count('"rgba(255,255,255,0.5)"')})

    # ══ S3 clone 运行时读数（门禁自己跑）══════════════════════════
    live: dict[str, Any] = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080},
                                    device_scale_factor=1)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            open_desk(page)

            auto = page.evaluate(READ)
            live["自适应"] = auto
            v.check("clone:auto-has-no-mask-container-no-mask-no-frame",
                    auto.get("容器在场") is False and auto.get("遮罩层在场") is False
                    and auto.get("框在场") is False,
                    detail=auto)

            page.locator("[data-director-rail-entry='aspect-ratio']").first.click(
                timeout=15000)
            page.wait_for_timeout(900)
            for ratio in RATIOS:
                page.locator(
                    f"[data-director-aspect-option='{ratio}']").first.click(timeout=8000)
                page.wait_for_timeout(700)
                g = page.evaluate(READ)
                live[ratio] = g
                mask = g.get("遮罩层") or {}
                cont = g.get("容器") or {}
                frame = g.get("框") or {}
                fstyle = g.get("框样式") or {}
                rel = g.get("框相对容器") or {}

                v.check(f"clone:the-mask-container-is-mounted-for-{ratio}",
                        g.get("容器在场") is True and g.get("遮罩层在场") is True
                        and g.get("框在场") is True,
                        detail={"容器": g.get("容器在场"),
                                "遮罩层": g.get("遮罩层在场"),
                                "框": g.get("框在场")})
                v.check(f"clone:the-mask-container-class-is-verbatim-for-{ratio}",
                        cont.get("cls") == ev_container,
                        detail={"实际": cont.get("cls"), "期望": ev_container})
                v.check(f"clone:the-mask-layer-class-is-verbatim-for-{ratio}",
                        mask.get("cls") == ev_mask_cls,
                        detail={"实际": mask.get("cls"), "期望": ev_mask_cls})
                v.check(f"clone:the-container-pierces-no-pointer-for-{ratio}",
                        cont.get("pointerEvents") == "none"
                        and cont.get("zIndex") == "10",
                        detail={"pointerEvents": cont.get("pointerEvents"),
                                "zIndex": cont.get("zIndex")})
                v.check(f"clone:the-mask-layer-fills-the-container-for-{ratio}",
                        mask.get("rect") == cont.get("rect"),
                        detail={"遮罩": mask.get("rect"), "容器": cont.get("rect")})
                v.check(f"clone:the-container-holds-both-mask-and-frame-for-{ratio}",
                        g.get("容器含框") is True
                        and g.get("容器首子元素是遮罩层") is True,
                        detail={"含框": g.get("容器含框"),
                                "首子元素是遮罩层": g.get("容器首子元素是遮罩层")})
                # ★ 遮罩黑度（源站 `bg-black/20` ⟹ ⟹ 20% ⟹ alpha ≈ 51/255）
                bg = pick_rgba(mask.get("背景"))
                want_alpha = round(src_mask_pct / 100 * 255)
                v.check(f"clone:the-mask-is-black-at-{src_mask_pct}-percent-for-{ratio}",
                        bg is not None and bg[0] <= 2 and bg[1] <= 2 and bg[2] <= 2
                        and abs(bg[3] - want_alpha) <= 2,
                        detail={"实际": bg, "期望alpha": want_alpha})
                # ★ 背景模糊（`backdrop-blur-md` ＝ blur(12px)）
                bf = mask.get("backdropFilter") or ""
                v.check(f"clone:the-mask-blurs-the-backdrop-for-{ratio}",
                        "blur(" in bf and "12px" in bf,
                        detail=bf)
                # ★ mask 图像／合成／重复
                mi = mask.get("maskImage") or ""
                v.check(f"clone:the-mask-image-is-two-linear-gradients-for-{ratio}",
                        mi.count("linear-gradient") == 2,
                        detail=mi)
                mc = mask.get("maskComposite") or ""
                v.check(f"clone:the-mask-composite-is-exclude-for-{ratio}",
                        "exclude" in mc, detail=mc)
                v.check(f"clone:the-mask-repeat-is-no-repeat-for-{ratio}",
                        mask.get("maskRepeat") == "no-repeat, no-repeat",
                        detail=mask.get("maskRepeat"))
                # ★ ★ mask 的第二个位置/尺寸必须**正好是框**（框在容器里的偏移与大小）
                pos = parse_pairs(mask.get("maskPosition") or "")
                size = parse_pairs(mask.get("maskSize") or "")
                v.check(f"clone:the-mask-hole-matches-the-frame-position-for-{ratio}",
                        len(pos) == 2 and abs(pos[1][0] - rel.get("left", -999)) <= 1
                        and abs(pos[1][1] - rel.get("top", -999)) <= 1,
                        detail={"maskPosition": mask.get("maskPosition"),
                                "框相对容器": rel})
                v.check(f"clone:the-mask-hole-matches-the-frame-size-for-{ratio}",
                        len(size) == 2 and abs(size[1][0] - frame.get("w", -999)) <= 1
                        and abs(size[1][1] - frame.get("h", -999)) <= 1,
                        detail={"maskSize": mask.get("maskSize"), "框": frame})
                # ★ 框自身：没有 box-shadow（遮罩已独立成层）
                v.check(f"clone:the-frame-has-no-box-shadow-for-{ratio}",
                        fstyle.get("boxShadow") == "none",
                        detail=fstyle.get("boxShadow"))
                oc = pick_rgba(fstyle.get("outlineColor"))
                want_o = round(src_outline_pct / 100 * 255)
                v.check(f"clone:the-frame-outline-matches-the-source-for-{ratio}",
                        fstyle.get("outlineWidth") == "1px"
                        and fstyle.get("outlineOffset") == "-1px"
                        and fstyle.get("radius") == "12px"
                        and fstyle.get("borderWidth") == "0px"
                        and oc is not None and oc[0] > 250 and oc[1] > 250
                        and oc[2] > 250 and abs(oc[3] - want_o) <= 4,
                        detail={"描边": fstyle, "outline色": oc,
                                "期望alpha": want_o})

                # ★ ★★ 红色探针：**就在 16:9 这一档当场做**
                #   ⟹ ⟹ 不用回头再点一次「16:9」⟹ ⟹ 避开一个真实坑：
                #   循环跑完页面停在 9:16 ⟹ ⟹ 再点「16:9」时**选项位置会挪**，
                #   那个点会被 3D 视口的坐标控件（gizmo，`right-5 top-5 z-20`）**挡住**
                #   ⟹ ⟹ Playwright 报 "subtree intercepts pointer events"。
                if ratio == "16:9":
                    # ★ ★ 「先计数、再决定要不要测」——★ 「源码换回 HEAD」时
                    #   **遮罩层根本不在场** ⟹ ⟹ 若照样去采样 ⟹ ⟹ 拿到的
                    #   是两个**毫不相干**的点 ⟹ ⟹ 差值可能**碰巧** ≥ 40
                    #   ⟹ ⟹ 那条判据就成了**随机灯** ⟹ ⟹ 受控对照会误判。
                    #   ⟹ ⟹ 遮罩层不在场 ⟹ ⟹ 这条判据**具名**判红。
                    if g.get("遮罩层在场") is True:
                        probe = red_probe(page, frame, cont)
                        live["红色探针"] = probe
                        v.check("clone:the-red-probe-proves-the-mask-hollows-the-frame",
                                probe.get("可用") is True
                                and probe.get("差值", 0) >= 40
                                # ★ ★ 「红味」判据：★ 框外必须**真的是红的**
                                #   （R−G 大）⟹ ⟹ 排除「底色本来就亮」的冒充；
                                #   ★ 框内必须**不是红的**（被 mask 挖空 ⟹ ⟹ 没被染到）。
                                and probe.get("框外红味", 0) >= 60
                                and probe.get("框内红味", 999) <= 30,
                                detail=probe)
                    else:
                        v.check("clone:the-red-probe-proves-the-mask-hollows-the-frame",
                                False,
                                detail={"遮罩层在场": g.get("遮罩层在场"),
                                        "why": "★ 遮罩层不在场 ⟹ ⟹ 探针无从进行"})

            # ★ ★★ 红色探针已在上面的六档循环里（16:9 那一档）当场做完
            #   ⟹ ⟹ 这里**不再**回头重选 16:9（选项位置会挪、会被 gizmo 挡住）。

            # ★ 回归：batch 862 的开关仍然可用（三分线 0 ⟹ 点一下 ⟹ 4 ⟹ 再点 ⟹ 0）
            toggle_count = page.locator("[data-director-frame-thirds-toggle]").count()
            v.check("clone:the-862-toggle-is-still-mounted",
                    toggle_count == 1, detail={"count": toggle_count})
            if toggle_count == 1:
                page.locator("[data-director-frame-thirds-toggle]").first.click(
                    timeout=8000)
                page.wait_for_timeout(800)
                after = page.evaluate(READ)
                live["点开关后"] = after
                v.check("clone:clicking-the-862-toggle-still-shows-four-thirds",
                        after.get("分线条数") == 4,
                        detail=after.get("分线条数"))
                page.locator("[data-director-frame-thirds-toggle]").first.click(
                    timeout=8000)
                page.wait_for_timeout(800)
                again = page.evaluate(READ)
                v.check("clone:clicking-it-again-still-hides-the-thirds",
                        again.get("分线条数") == 0,
                        detail=again.get("分线条数"))

            page.locator("[data-director-aspect-option='自适应']").first.click(
                timeout=8000)
            page.wait_for_timeout(700)
            back = page.evaluate(READ)
            live["回自适应"] = back
            v.check("clone:going-back-to-auto-removes-mask-container-and-frame",
                    back.get("容器在场") is False and back.get("遮罩层在场") is False
                    and back.get("框在场") is False,
                    detail=back)

            v.check("diagnostics:no-page-errors",
                    not [e for e in errors if "TransformControls" not in e],
                    detail=errors[:5])
            audit["live"] = live
        finally:
            browser.close()

    v.result = {"判据数": v.count, "失败": v.failures, "audit": audit}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "runtime-audit.json").write_text(
        json.dumps(v.result, ensure_ascii=False, indent=1, default=str),
        encoding="utf-8")
    print(f"\n{v.count} 判据，{len(v.failures)} 失败")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
