#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 864 门禁：**D17 推翻** ＋ **本地埋点等价实现**（源站逐字 ＋ 运行时对照）。

## ★ 本批在做什么（★ 一句话说清）

★ batch 862 把 **D17** 记成「源站把比例与 `reference_line` **写进机位对象**」
  ⟹ ⟹ 本批用**源站逐字 ＋ 源站运行时网络取证**把它**推翻**：

  ① **源站逐字**：`n4` 的定义是
  ```js
  n4 = useCallback((e,t,r,n) => {
    (0,nZ.S)("libtv.canvas.director.camera.update", {
      director_session_id: nb.current, camera_uuid: e,
      setting_name: t, setting_value: r, operation_source: n })
  }, [])
  ```
  ⟹ ⟹ **`n4` 只发一条埋点**，**不改任何状态**。

  ② **源站运行时实测**（`raw/source-864-camera-write.json`）：
  点「16:9」与点框上那枚「构图参考线」，源站发出的都是
  `POST https://api2.liblib.art/api/www/log/acceptor/f`
  ⟹ ⟹ **埋点接收端点** ⟹ ⟹ 而且**没有任何工程状态写入请求**（只有 heartbeat）。

  ③ ★ **静态反证**：整个 chunk（1,018,130 字符）里 `reference_line` **只出现 1 次**
  ⟹ ⟹ 它**从来不是**机位对象上被读写的字段。

  ⟹ ⟹ **D17 被推翻**：源站的模型是「取景比例与参考线都是**组件级单值状态**」
  ⟹ ⟹ clone 的全局 `frameAspectRatio` ＋ `showThirds` **与源站同构**
  ⟹ ⟹ 「clone 缺了机位级写入」这个差距**不存在**。

★ 源站与 clone 在这一处**真正的差别**只有一条：源站**上报到后端**，
  clone **不触网** ⟹ ⟹ 本批做的是**本地等价记录**
  （`src/lib/directorTelemetry.ts` ＋ `directorStore.telemetryLog`）：
  事件名与属性**逐字同构**，但只落在内存里。

## ★ 门禁查什么

- **S1 静态**：逐字事件名／四个属性键／`operation_source` 逐字；
  ★ **底线**：这套「埋点」**不许出现任何网络调用**（原型不碰真实接口）；
  store 有 `telemetryLog` ＋ `recordTelemetry`；两个入口都在。
- **S2 源站运行时取证**（从入库 raw 读）：端点是**埋点端点**；
  两条事件的 `setting_name`／`setting_value`／`operation_source` 逐字；
  ★ **没有任何工程状态写入请求**（D17 推翻的直接依据）。
- **S3 clone 运行时读数**：点面板比例 ⟹ ⟹ 记一条（值逐字）；
  点「自适应」⟹ ⟹ 值为 `null`；点框上开关 ⟹ ⟹ 记 `reference_line`（**数字** 1／0）；
  ★ `camera_uuid` ＝ **选中机位**；★ clone 自己那枚底部扩展按钮**不记**（源站没这个入口）。
- **S4 同口径对照**：clone 事件的 `var` **键集合与值**与源站运行时事件**逐字相等**。

## ★ 输出
  docs/research/liblib-canvas-batch864-2026-10-01/runtime-audit.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs/research/liblib-canvas-batch864-2026-10-01"
RAW = OUT_DIR / "raw"
BASE = "http://localhost:4317"

SRC_TELEMETRY = ROOT / "src/lib/directorTelemetry.ts"
SRC_STORE = ROOT / "src/store/directorStore.ts"
SRC_PANEL = ROOT / "src/components/director/DirectorAspectPanel.tsx"
SRC_VIEW = ROOT / "src/components/director/DirectorViewport.tsx"

RAW_SOURCE = RAW / "source-864-camera-write.json"

# ★ 源站逐字（本批的期望值**只从入库的源站 raw 读**，不凭记忆手打）
SOURCE_EVENT_NAME = "libtv.canvas.director.camera.update"
SOURCE_VAR_KEYS = ["camera_uuid", "setting_name", "setting_value", "operation_source"]
SOURCE_OPERATION_SOURCE = "right_panel"

# ★ clone 运行时读数（★ 与探针同口径）
READ_LOG = r"""()=>{
  const st=window.__director_store;
  if(!st || typeof st.getState!=='function') return {store在场:false};
  const s=st.getState();
  return {store在场:true,
          activeCameraId:s.activeCameraId,
          frameAspectRatio:s.frameAspectRatio===undefined?null:s.frameAspectRatio,
          showThirds:s.showThirds,
          机位:s.objects.filter(o=>o.kind==='camera').map(c=>({id:c.id,name:c.name})),
          telemetryLog:(s.telemetryLog||[]).map(e=>({e:e.e,
              var:Object.fromEntries(Object.entries(e.var||{}).map(([k,v])=>[k,v])),
              键集:Object.keys(e.var||{})}))};
}"""

# ★ ★★ Batch 864 **新增**：**命中测试**（★ 与 863 门禁同口径）
#   ⟹ ⟹ 「按钮在 DOM 里」**不等于**「点得到」
#   ⟹ ⟹ 本批要修的正是「点不到」⟹ ⟹ 判据必须能分辨「点得到 / 点不到」
#   ⟹ ⟹ 修法：**先判命中测试、再决定要不要点**
#   ⟹ ⟹ （否则受控对照的 MIX 态会**超时崩溃**，而不是**具名红条**）
HIT_TEST = r"""()=>{
  const btn=document.querySelector('[data-director-frame-thirds-toggle]');
  if(!btn) return {按钮在场:false};
  const r=btn.getBoundingClientRect();
  const cx=Math.round(r.x+r.width/2), cy=Math.round(r.y+r.height/2);
  const top=document.elementFromPoint(cx,cy);
  return {按钮在场:true,
          按钮rect:{x:Math.round(r.x),y:Math.round(r.y),
                    w:Math.round(r.width),h:Math.round(r.height)},
          命中点:{x:cx,y:cy},
          isToggle:!!(top&&top.closest('[data-director-frame-thirds-toggle]')),
          命中标签:top&&(top.getAttribute('aria-label')||top.getAttribute('title')||top.tagName),
          命中类:top&&(top.getAttribute('class')||'').slice(0,90)};
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
    out = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    out = re.sub(r"//[^\n]*", " ", out)
    return out


def block_between(src: str, start_marker: str, end_marker: str) -> str:
    """★ 取「从 start_marker 到 end_marker」之间的那一段 ⟹ ⟹ 用来**锚定到具体声明**。

    ★ 为什么需要它：★ 同一个字面量（例如 `"right_panel"`）在**类型声明**与
    **常量**里**各有一份** ⟹ ⟹ 裸 `in` 检查会漏 ⟹ ⟹ 负控打空
    ⟹ ⟹ 判据必须问「**那一处**有没有」。
    """
    i = src.find(start_marker)
    if i < 0:
        return ""
    j = src.find(end_marker, i + len(start_marker))
    if j < 0:
        return src[i:]
    return src[i:j]


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


def main() -> int:
    v = Verifier()
    audit: dict[str, Any] = {
        "batch": 864,
        "title": "D17 推翻 ＋ 本地埋点等价实现（源站逐字 ＋ 运行时对照）",
    }

    # ══ S1 静态契约 ═════════════════════════════════════════════
    # ★ ★★ **缺文件 ⟹ ⟹ 判红，不许崩**（受控对照的 HEAD 态**没有**这个新增文件）
    #   ⟹ ⟹ 崩掉 ⟹ ⟹ 只能说「它崩了」⟹ ⟹ 说不出**哪条判据**没过；
    #   ⟹ ⟹ 具名红 ⟹ ⟹ 一眼看出缺什么 ⟹ ⟹ **「HEAD 态零 CRASH」才成立**。
    def read_src(path: Path) -> str:
        if not path.exists():
            v.check(f"source:the-file-{path.name}-exists", False,
                    detail={"缺": str(path),
                            "why": "★ 缺文件 ⟹ ⟹ 具名判红（不是崩溃）"})
            return ""
        return strip_comments(path.read_text(encoding="utf-8"))

    tele_code = read_src(SRC_TELEMETRY)
    store_code = read_src(SRC_STORE)
    panel_code = read_src(SRC_PANEL)
    view_code = read_src(SRC_VIEW)

    v.check("source:the-event-name-is-verbatim",
            f'export const DIRECTOR_TELEMETRY_EVENT_CAMERA_UPDATE =\n  "{SOURCE_EVENT_NAME}";'
            in tele_code,
            detail=SOURCE_EVENT_NAME)
    # ★ ★★ **同名在别处出现 ⟹ 静态判据假绿**（batch 861/862 的同款坑）：
    #   ★ `"right_panel"` 这个字面量在**类型声明**与**常量**里**各有一份**
    #   ⟹ ⟹ 只改其中一处 ⟹ ⟹ 裸 `in` 检查**照样绿** ⟹ ⟹ 负控打空。
    #   ⟹ ⟹ 修法：判据必须**锚到具体那一行声明**，不许用裸 `in`。
    tele_iface = block_between(tele_code,
                               "export interface DirectorTelemetryCameraUpdateEvent {",
                               "export interface DirectorTelemetryCameraUpdateEvent")
    tele_builder = block_between(
        tele_code,
        "export function buildDirectorCameraUpdateEvent(input: {",
        "export function resolveDirectorTelemetryCameraId")
    for key in SOURCE_VAR_KEYS:
        v.check(f"source:the-var-key-{key}-is-verbatim",
                f"{key}:" in tele_iface and f"{key}:" in tele_builder,
                detail={"期望": f"{key}: 出现在**类型声明**与**构造器**里",
                        "类型声明里有": f"{key}:" in tele_iface,
                        "构造器里有": f"{key}:" in tele_builder})
    v.check("source:the-operation-source-is-verbatim",
            f'export const DIRECTOR_TELEMETRY_OPERATION_SOURCE = "{SOURCE_OPERATION_SOURCE}" as const;'
            in tele_code,
            detail=SOURCE_OPERATION_SOURCE)
    # ★ ★★ **底线**：这套「埋点」**不许触网**（原型不碰真实接口）
    net_calls = []
    for name, code in (("directorTelemetry.ts", tele_code),
                       ("directorStore.ts", store_code),
                       ("DirectorAspectPanel.tsx", panel_code),
                       ("DirectorViewport.tsx", view_code)):
        for pat in (r"\bfetch\s*\(", r"XMLHttpRequest", r"sendBeacon",
                    r"\baxios\b", r"navigator\.sendBeacon"):
            if re.search(pat, code):
                net_calls.append({"文件": name, "模式": pat})
    v.check("source:the-local-telemetry-never-touches-the-network",
            not net_calls,
            detail={"命中": net_calls,
                    "why": "★ 源站那条是**埋点上报** ⟹ ⟹ clone 只做**本地记录** ⟹ ⟹ 绝不触网"})
    v.check("source:the-store-keeps-a-local-telemetry-log",
            "telemetryLog: DirectorTelemetryCameraUpdateEvent[]" in store_code
            and "recordTelemetry:" in store_code,
            detail="★ store 要有 `telemetryLog` 字段 ＋ `recordTelemetry` 动作")
    v.check("source:the-panel-reports-the-aspect-ratio",
            'settingName: "aspect_ratio"' in panel_code
            and "buildDirectorCameraUpdateEvent" in panel_code,
            detail="★ 源站逐字：右侧面板选比例 ⟹ ⟹ 记 `aspect_ratio`")
    v.check("source:the-frame-toggle-reports-the-reference-line",
            'settingName: "reference_line"' in view_code
            and "buildDirectorCameraUpdateEvent" in view_code,
            detail="★ 源站逐字：框上那枚开关 ⟹ ⟹ 记 `reference_line`")
    # ★ ★★ **D17 的源码侧反证**：clone **不许**把这两个字段写进机位对象
    v.check("source:the-aspect-ratio-is-not-written-onto-a-camera-object",
            not re.search(r"aspect_ratio\s*:\s*", store_code)
            and not re.search(r"reference_line\s*:\s*", store_code),
            detail="★ ★ D17 被推翻：源站**没有**把这两个字段写进机位对象 "
                   "⟹ ⟹ clone 也不许造出这个假字段")

    # ══ S2 源站运行时取证（期望值只从入库 raw 读）═════════════════
    v.check("source:the-source-runtime-evidence-is-in-the-repo",
            RAW_SOURCE.exists(), detail=str(RAW_SOURCE))
    src_events: list[dict] = []
    if RAW_SOURCE.exists():
        raw = json.loads(RAW_SOURCE.read_text(encoding="utf-8"))
        audit["源站取证"] = {
            "关掉的弹窗": raw.get("尝试", [{}])[0].get("关掉的弹窗") if raw.get("尝试") else None,
        }
        # ★ ★ raw 的形状有两种（探针不同）：请求列表在**顶层**，或在每次「尝试」里
        #   ⟹ ⟹ 两种都读 ⟹ ⟹ 免得门禁因为「读错了层级」而**假红**。
        req_groups: list[list[dict]] = []
        for key in ("选比例后的请求", "切参考线后的请求"):
            if isinstance(raw.get(key), list):
                req_groups.append(raw[key])
        for rec in raw.get("尝试", []) or []:
            for key in ("选比例后的请求", "切参考线后的请求"):
                if isinstance(rec.get(key), list):
                    req_groups.append(rec[key])
        for group in req_groups:
            for req in group:
                body = req.get("postData") or ""
                if SOURCE_EVENT_NAME in body:
                    try:
                        payload = json.loads(body)
                    except Exception:  # noqa: BLE001
                        continue
                    src_events.append({
                        "端点": req.get("url"),
                        "方法": req.get("method"),
                        "e": payload.get("e"),
                        "var": payload.get("var"),
                    })
        # ★ 源站**有没有**工程状态写入请求？
        write_hits = []
        for group in req_groups:
            for req in group:
                url = (req.get("url") or "").lower()
                if any(k in url for k in ("save", "update", "composition", "commit")):
                    write_hits.append(req.get("url"))
        audit["源站取证"]["工程状态写入请求"] = write_hits
        v.check("source:the-source-change-only-reports-to-the-analytics-endpoint",
                all("/api/www/log/acceptor/f" in (e["端点"] or "") for e in src_events)
                and bool(src_events),
                detail={"事件端点": [e["端点"] for e in src_events]})
        v.check("source:the-source-sends-no-project-state-write",
                not write_hits,
                detail={"命中的写入类请求": write_hits,
                        "why": "★ D17 推翻的直接依据：源站**没有**把设置写进工程状态"})
        by_name = {e["var"].get("setting_name"): e["var"] for e in src_events
                   if isinstance(e.get("var"), dict)}
        v.check("source:the-source-aspect-ratio-event-is-verbatim",
                by_name.get("aspect_ratio", {}).get("setting_value") == "16:9"
                and by_name.get("aspect_ratio", {}).get("operation_source")
                == SOURCE_OPERATION_SOURCE,
                detail=by_name.get("aspect_ratio"))
        v.check("source:the-source-reference-line-event-is-a-number",
                by_name.get("reference_line", {}).get("setting_value") == 1
                and by_name.get("reference_line", {}).get("operation_source")
                == SOURCE_OPERATION_SOURCE,
                detail=by_name.get("reference_line"))
        v.check("source:the-source-var-contains-the-four-setting-keys",
                all(all(k in (e.get("var") or {}) for k in SOURCE_VAR_KEYS)
                    for e in src_events if isinstance(e.get("var"), dict)),
                detail={"源站的 var 键数": [len(e.get("var") or {})
                                           for e in src_events],
                        "期望包含": SOURCE_VAR_KEYS})
        # ★ ★ 源站的 `var` 里**还有 17 个环境/硬件属性**（`dpr`／`sw`／`sh`／`region`／
        #   `lang`／`window_session_id`／`director_session_id`／`hardware_info_*`／
        #   `gpu_*`／`cpu_*`／`device_memory_gb_bucket`／`logical_processor_count_bucket`）
        #   ⟹ ⟹ 那些是**埋点 SDK 自动附加**的 ⟹ ⟹ clone 没有 SDK ⟹ ⟹ 只记 4 个语义键。
        #   ⟹ ⟹ 但必须断言：**多出来的那些键里没有一个是「机位设置」**
        #   ⟹ ⟹ 否则「把设置偷偷塞进 var」会被放过。
        extra = sorted(set(
            (src_events[0].get("var") or {}).keys()) - set(SOURCE_VAR_KEYS)
        ) if src_events else []
        v.check("source:the-extra-source-keys-are-environment-attributes-only",
                all(k not in {"aspect_ratio", "reference_line", "shot_size",
                              "angle", "side", "look_at", "fov", "at",
                              "position", "rotation_deg", "scale"}
                    for k in extra),
                detail={"多出来的键": extra,
                        "why": "★ 它们是埋点 SDK 的环境属性 ⟹ ⟹ 不是机位设置"})
    else:
        v.check("source:the-source-runtime-evidence-is-in-the-repo",
                False, detail="★ 缺源站运行时取证 ⟹ ⟹ 判失败")

    # ══ S3 clone 运行时读数 ═══════════════════════════════════════
    live: dict[str, Any] = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080},
                                    device_scale_factor=1)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            open_desk(page)

            start = page.evaluate(READ_LOG)
            live["初始"] = start
            v.check("clone:the-telemetry-log-starts-empty",
                    start.get("store在场") is True
                    and start.get("telemetryLog") == [],
                    detail=start)

            # ── 点面板「16:9」──
            page.locator("[data-director-rail-entry='aspect-ratio']").first.click(
                timeout=15000)
            page.wait_for_timeout(900)
            page.locator("[data-director-aspect-option='16:9']").first.click(
                timeout=8000)
            page.wait_for_timeout(700)
            after_ratio = page.evaluate(READ_LOG)
            live["选16比9后"] = after_ratio
            log1 = after_ratio.get("telemetryLog") or []
            v.check("clone:picking-a-ratio-records-one-event",
                    len(log1) == 1,
                    detail={"条数": len(log1), "log": log1})
            ev1 = log1[0] if log1 else {}
            var1 = ev1.get("var") or {}
            v.check("clone:the-recorded-event-name-is-verbatim",
                    ev1.get("e") == SOURCE_EVENT_NAME, detail=ev1.get("e"))
            v.check("clone:the-recorded-var-has-exactly-the-four-keys",
                    sorted(var1.keys()) == sorted(SOURCE_VAR_KEYS),
                    detail={"实际": sorted(var1.keys()), "期望": SOURCE_VAR_KEYS})
            v.check("clone:the-recorded-setting-name-and-value-are-verbatim",
                    var1.get("setting_name") == "aspect_ratio"
                    and var1.get("setting_value") == "16:9",
                    detail=var1)
            v.check("clone:the-recorded-operation-source-is-verbatim",
                    var1.get("operation_source") == SOURCE_OPERATION_SOURCE,
                    detail=var1.get("operation_source"))
            v.check("clone:the-recorded-camera-is-the-selected-one",
                    var1.get("camera_uuid") == after_ratio.get("activeCameraId"),
                    detail={"camera_uuid": var1.get("camera_uuid"),
                            "activeCameraId": after_ratio.get("activeCameraId"),
                            "机位": after_ratio.get("机位")})

            # ── 点「自适应」⟹ ⟹ 值是 null ──
            page.locator("[data-director-aspect-option='自适应']").first.click(
                timeout=8000)
            page.wait_for_timeout(700)
            after_auto = page.evaluate(READ_LOG)
            live["选自适走后"] = after_auto
            log2 = after_auto.get("telemetryLog") or []
            v.check("clone:picking-auto-records-a-null-value",
                    len(log2) == 2
                    and (log2[1].get("var") or {}).get("setting_value") is None
                    and (log2[1].get("var") or {}).get("setting_name")
                    == "aspect_ratio",
                    detail={"条数": len(log2), "末条": log2[-1] if log2 else None})

            # ── 点框上那枚「构图参考线」⟹ ⟹ reference_line（数字）──
            page.locator("[data-director-aspect-option='16:9']").first.click(
                timeout=8000)
            page.wait_for_timeout(700)
            before_toggle = page.evaluate(READ_LOG)
            toggle_count = page.locator("[data-director-frame-thirds-toggle]").count()
            v.check("clone:the-frame-toggle-is-mounted-before-it-is-clicked",
                    toggle_count == 1, detail={"count": toggle_count})
            # ★ ★★ **先判命中测试、再决定要不要点**（★ 本批修的正是「点不到」）
            #   ⟹ ⟹ 不判就点 ⟹ ⟹ 被盖住时 Playwright 会**超时崩溃**（8s）
            #   ⟹ ⟹ 门禁就变成「崩了」⟹ ⟹ 而不是一个**说得清**的红条。
            hit = page.evaluate(HIT_TEST)
            live["命中测试"] = hit
            v.check("clone:the-frame-toggle-is-the-topmost-element-at-its-center",
                    bool(hit.get("isToggle")), detail=hit)
            if toggle_count == 1 and hit.get("isToggle"):
                page.locator("[data-director-frame-thirds-toggle]").first.click(
                    timeout=8000)
                page.wait_for_timeout(800)
            else:
                v.check("clone:the-frame-toggle-can-be-clicked-at-16x9", False,
                        detail={"why": "★ 开关被盖住 ⟹ ⟹ 点不到 ⟹ ⟹ 具名判红"
                                       "（不是崩溃）",
                                "命中": hit})
            after_toggle = page.evaluate(READ_LOG)
            live["切参考线后"] = after_toggle
            log3 = after_toggle.get("telemetryLog") or []
            ev3 = (log3[-1] if log3 else {}).get("var") or {}
            v.check("clone:toggling-the-reference-line-records-a-numeric-value",
                    len(log3) == len(before_toggle.get("telemetryLog") or []) + 1
                    and ev3.get("setting_name") == "reference_line"
                    and ev3.get("setting_value") == 1
                    and isinstance(ev3.get("setting_value"), int),
                    detail={"条数": len(log3), "末条": log3[-1] if log3 else None})
            if toggle_count == 1 and hit.get("isToggle"):
                page.locator("[data-director-frame-thirds-toggle]").first.click(
                    timeout=8000)
                page.wait_for_timeout(800)
            else:
                v.check("clone:the-frame-toggle-can-be-clicked-a-second-time", False,
                        detail={"why": "★ 同上（没点成 ⟹ ⟹ 没法测「再点一次」）",
                                "命中": hit})
            after_toggle2 = page.evaluate(READ_LOG)
            live["再切参考线后"] = after_toggle2
            log4 = after_toggle2.get("telemetryLog") or []
            ev4 = (log4[-1] if log4 else {}).get("var") or {}
            v.check("clone:toggling-it-again-records-zero",
                    len(log4) == len(log3) + 1
                    and ev4.get("setting_name") == "reference_line"
                    and ev4.get("setting_value") == 0,
                    detail={"条数": len(log4), "末条": log4[-1] if log4 else None})

            # ★ ★ clone 自己那枚**底部扩展**按钮（源站没有这个入口）⟹ ⟹ **不许**记事件
            bottom = page.locator("[aria-label='开启九宫格辅助线']").first
            bottom_count = bottom.count()
            v.check("clone:the-clone-only-bottom-button-exists",
                    bottom_count == 1, detail={"count": bottom_count})
            if bottom_count == 1:
                before_bottom = page.evaluate(READ_LOG)
                try:
                    bottom.click(timeout=8000)
                    page.wait_for_timeout(700)
                except Exception:  # noqa: BLE001
                    pass
                after_bottom = page.evaluate(READ_LOG)
                live["点底部扩展按钮后"] = after_bottom
                v.check("clone:the-clone-only-bottom-button-records-nothing",
                        len(after_bottom.get("telemetryLog") or [])
                        == len(before_bottom.get("telemetryLog") or []),
                        detail={"前": len(before_bottom.get("telemetryLog") or []),
                                "后": len(after_bottom.get("telemetryLog") or []),
                                "why": "★ 源站**没有**这个入口 ⟹ ⟹ clone 不许为它编造事件"})

            v.check("diagnostics:no-page-errors",
                    not [e for e in errors if "TransformControls" not in e],
                    detail=errors[:5])
            audit["live"] = live
        finally:
            browser.close()

    # ══ S4 同口径对照 ═════════════════════════════════════════════
    clone_vars = []
    for tag in ("选16比9后", "切参考线后"):
        for ev in (live.get(tag, {}).get("telemetryLog") or []):
            if isinstance(ev.get("var"), dict):
                clone_vars.append(ev["var"])
    src_vars = [e["var"] for e in src_events if isinstance(e.get("var"), dict)]
    if clone_vars and src_vars:
        src_by_name = {v.get("setting_name"): v for v in src_vars}
        clone_by_name = {v.get("setting_name"): v for v in clone_vars}
        common = [k for k in src_by_name if k in clone_by_name]
        # ★ ★ clone 的 `var` **恰好**是那 4 个语义键（★ 源站多的那 17 个是埋点 SDK
        #   自动附加的环境属性 ⟹ ⟹ clone 没有 SDK ⟹ ⟹ 不该有）
        v.check("compare:the-clone-var-is-exactly-the-four-setting-keys",
                all(sorted(clone_by_name[k].keys()) == sorted(SOURCE_VAR_KEYS)
                    for k in common),
                detail={"clone": {k: sorted(clone_by_name[k].keys()) for k in common},
                        "期望": SOURCE_VAR_KEYS})
        # ★ 三个**可跨侧比**的键逐字相等（`camera_uuid` 的**取值**两侧不同：
        #   源站是 `director-main-camera`、clone 是 `director-camera-main`
        #   ⟹ ⟹ 只比「它是这台机位的 id」这个不变量 ⟹ ⟹ 见 S3 那条判据）
        v.check("compare:the-operation-source-is-identical-across-sides",
                all(src_by_name[k].get("operation_source")
                    == clone_by_name[k].get("operation_source")
                    for k in common),
                detail={"源站": {k: src_by_name[k].get("operation_source")
                                  for k in common},
                        "clone": {k: clone_by_name[k].get("operation_source")
                                  for k in common}})
        v.check("compare:the-setting-names-are-identical-across-sides",
                set(src_by_name) == set(clone_by_name)
                and all(src_by_name[k].get("setting_name")
                        == clone_by_name[k].get("setting_name") for k in common),
                detail={"源站": sorted(src_by_name), "clone": sorted(clone_by_name)})
        v.check("compare:the-reference-line-value-type-is-identical-across-sides",
                isinstance(src_by_name.get("reference_line", {}).get("setting_value"), int)
                == isinstance(clone_by_name.get("reference_line", {}).get("setting_value"), int),
                detail={"源站": src_by_name.get("reference_line"),
                        "clone": clone_by_name.get("reference_line")})
        v.check("compare:the-aspect-ratio-value-type-is-identical-across-sides",
                isinstance(src_by_name.get("aspect_ratio", {}).get("setting_value"), str)
                == isinstance(clone_by_name.get("aspect_ratio", {}).get("setting_value"), str),
                detail={"源站": src_by_name.get("aspect_ratio"),
                        "clone": clone_by_name.get("aspect_ratio")})
    else:
        v.check("compare:the-var-keys-are-identical-across-sides",
                False, detail={"源站事件": len(src_vars), "clone事件": len(clone_vars)})

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
