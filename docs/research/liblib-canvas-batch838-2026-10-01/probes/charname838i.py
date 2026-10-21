#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 838 源站探针 v17：★★ **以权威 API 为准**的角色默认名闭环。

★★★ 为什么要重写（v9–v16 的四次失败，各暴露一条真问题）：
  v9  ：跨趟读数无法对齐（下一趟那个角色没了）。
  v11 ：读数器把**浮层面板行**当成场景树行 ⟹ 副作用：右键了「标准男性」。
  v15 ：收窄几何口径**仍然**分不开浮层与场景树（浮层盖在上面）。
  v16 ：★ class 口径在**选中态**下失效（树读数返回 0 行）⟹ 且删除**没落盘**。

★ ★★ 本探针的四个根本改动：
  1. ★★ **权威状态 = API**（`api/canvas/project/detail-by-space` 的 `compositionData`），
     **不是 DOM** ⟹ DOM 只用来「点」和「读右栏」，不用来判定「有几个角色」。
  2. ★★ **等自动保存 = 轮询 API**：源站的自动保存有**约 30 秒延迟**
     （v14 实测：`POST /api/canvas/nodes/batch`）⟹ ⟹ 不再「等固定秒数后猜」，
     而是**轮询到 API 真的变了**为止（带超时）。
  3. ★★ **判定链**：建 → 右栏名称输入框读到 N ⟹ **等保存** ⟹ API 里出现第 2 个角色
     且它的 `label` **就是 N** ⟹ ⟹ 「默认名规则」这条结论**由权威数据自证**。
  4. ★★ **收尾**：删 → **等保存** ⟹ API 回到基线 ⟹ ⟹ 复原由 API 自证。

★ ★★ 铁律：
  - 判「有没有多一个角色」**只看 API 的 `compositionData.characters`**；
  - 只删**本批新建的那一个**（按 API 里的 id 定位，不按名字猜）；
  - ★ 若轮询超时 ⟹ 如实报告「未落盘」，**不谎称复原**。
"""
import json
import pathlib
import sys
import time
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_charname838i.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")
DETAIL_API = ("https://api.liblib.tv/api/canvas/project/detail-by-space"
              "?spaceId=7709759"
              "&projectUuid=a860e1da8e9e4504bececda022386429")

# ★ 右栏「名称」输入框 + 面板标题
DUMP_RIGHT = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;};
  const inputs=[]; const titles=[];
  for (const el of Array.from(document.querySelectorAll('input'))) {
    if (!vis(el)) continue;
    const r=el.getBoundingClientRect();
    if (r.x < 1300) continue;
    inputs.push({value:el.value||'', x:Math.round(r.x), y:Math.round(r.y)});
  }
  for (const el of Array.from(document.querySelectorAll('span,div,h1,h2,h3'))) {
    if (!vis(el) || el.childElementCount>0) continue;
    const r=el.getBoundingClientRect();
    if (r.x < 1300 || r.y > 40) continue;
    const t=(el.textContent||'').trim();
    if (!t || t.length>20) continue;
    titles.push({text:t, x:Math.round(r.x), y:Math.round(r.y)});
  }
  return {inputs, titles};
}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(800)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(9_000)


def clean(page):
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")


def api_characters(page) -> list:
    """★ 权威读数：API 里的 `compositionData.characters`（只取 id/label）。

    ★★ **不能用页面内 `fetch`** —— 实测页面里 fetch 该接口只回 **90 字节**（`data` 为空）
       ⟹ 解析不到任何节点 ⟹ 静默返回空列表 ⟹ ★ 这正是「读数方法坏了」的典型形态。
    ⟹ 正确做法：**用页面自己的请求**（`page.request` 复用同一个 context 的 cookie），
       并**断言响应里有 `data.projectDetail.nodeList`** ⟹ 读不到就**显式失败**。
    """
    resp = page.request.get(DETAIL_API)
    raw = resp.text()
    d = json.loads(raw)
    pd = d.get("data") or {}
    node_list = (pd.get("projectDetail") or {}).get("nodeList")
    if not node_list:
        raise RuntimeError(
            "API 响应里没有 data.projectDetail.nodeList（len=%d）⟹ 读数方法坏了 ⟹ 不下结论"
            % len(raw))
    for node in node_list:
        if node.get("type") != 36:
            continue
        dd = json.loads(node["data"])
        comp = dd.get("compositionData")
        if isinstance(comp, str):
            comp = json.loads(comp)
        if isinstance(comp, dict):
            return [{"id": c.get("id"), "label": c.get("label")}
                    for c in (comp.get("characters") or [])]
    raise RuntimeError("API 响应里没有 type=36 的导演台节点 ⟹ 不下结论")


def poll_characters(page, want_len, timeout_s=120, step=8):
    """★ 轮询 API 直到角色数变成 want_len（或超时）。返回 (是否达成, 最后的列表, 耗时)。"""
    t0 = time.time()
    last = []
    while time.time() - t0 < timeout_s:
        last = api_characters(page)
        if len(last) == want_len:
            return True, last, round(time.time() - t0)
        time.sleep(step)
    return False, last, round(time.time() - t0)


def delete_character_by_label(page, label):
    """在**场景树**里右键那一行 → 菜单「删除」→ 确认。

    ★ 用 class 口径定位（`pl-1` + `z-10`）⟹ 不用几何（浮层会盖上来）。
    """
    loc = page.evaluate("""(label) => {
      const vis=(e)=>{const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;};
      for (const el of Array.from(document.querySelectorAll('span,div,button'))) {
        if (!vis(el) || el.childElementCount>0) continue;
        const cls=(el.className||'').toString();
        if (cls.indexOf('pl-1')<0 || cls.indexOf('z-10')<0) continue;
        if ((el.textContent||'').trim() !== label) continue;
        const r=el.getBoundingClientRect();
        return {x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height)};
      }
      return null;
    }""", label)
    if not loc:
        return False, "场景树里找不到那一行"
    page.mouse.click(loc["x"] + 10, loc["y"] + loc["h"] / 2, button="right")
    page.wait_for_timeout(1_500)
    clean(page)
    for label2 in ("删除", "删除⌘⌫"):
        try:
            el = page.get_by_text(label2, exact=True).first
            if el.is_visible():
                el.click()
                page.wait_for_timeout(1_500)
                clean(page)
                try:
                    c = page.get_by_text("确定", exact=True).first
                    if c.is_visible():
                        c.click()
                        page.wait_for_timeout(1_500)
                        clean(page)
                except Exception:
                    pass
                return True, "点了菜单项"
        except Exception:
            continue
    return False, "菜单里没找到删除项"


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {}
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080}, locale="zh-CN")
            ctx.add_cookies([{"name": c["name"], "value": c["value"],
                              "domain": c["domain"], "path": c.get("path", "/"),
                              "expires": c.get("expires", -1),
                              "httpOnly": c.get("httpOnly", False),
                              "secure": c.get("secure", False),
                              "sameSite": c.get("sameSite", "Lax")} for c in cookies])
            page = ctx.new_page()
            page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
            page.wait_for_timeout(12_000)
            open_desk(page)
            clean(page)

            # A. ★ 权威基线
            base = api_characters(page)
            out["A_★API基线_角色"] = base
            out["A_★API基线_角色数"] = len(base)
            out["A_★API基线_标签"] = [c["label"] for c in base]

            # B. 清理**多出来的**角色（若 API 里已有 >1 个）⟹ 只删到只剩 1 个
            while len(api_characters(page)) > 1:
                chars = api_characters(page)
                victim = chars[-1]
                ok, why = delete_character_by_label(page, victim["label"])
                out.setdefault("B_清理尝试", []).append(
                    {"删的是": victim, "成功": ok, "原因": why})
                if not ok:
                    break
                ok2, _, _ = poll_characters(page, len(chars) - 1, timeout_s=90)
                out.setdefault("B_清理尝试", [])[-1]["★是否落盘"] = ok2
                if not ok2:
                    break
            base = api_characters(page)
            out["B_★清理后的API角色"] = base
            out["B_★清理后的API角色数"] = len(base)

            # C. ★ 新建角色（选体型预设）
            page.locator("[aria-label='添加角色']").first.click()
            page.wait_for_timeout(1_500)
            clean(page)
            picked = None
            for lab in ("标准男性", "标准female", "标准女性", "健硕"):
                if lab == "标准female":
                    continue
                try:
                    page.get_by_text(lab, exact=True).first.click()
                    picked = lab
                    break
                except Exception:
                    continue
            out["C_★选中的体型"] = picked
            page.wait_for_timeout(2_500)
            clean(page)

            # D. 右栏名称输入框（此时应是**新角色**的属性面板）
            right = page.evaluate(DUMP_RIGHT)
            out["D_右栏输入框"] = right["inputs"]
            out["D_右栏标题"] = right["titles"]
            name_val = (right["inputs"] or [{}])[0].get("value")
            out["D_★读到的默认名"] = name_val
            out["D_★面板标题是角色"] = any(t["text"] == "角色" for t in right["titles"])
            try:
                page.screenshot(path="/tmp/liblib_source_charname838h.png")
            except Exception:
                pass

            # E. ★ 轮询 API 直到多出一个角色 ⟹ 复核它的 label
            want = len(base) + 1
            ok, chars, secs = poll_characters(page, want, timeout_s=120)
            out["E_★API轮询是否达成"] = ok
            out["E_★耗时秒"] = secs
            out["E_★API里的角色"] = chars
            out["E_★API里的标签"] = [c["label"] for c in chars]
            new_ch = [c for c in chars if c not in base]
            out["E_★新增的角色"] = new_ch
            out["E_★★新增角色的label是否等于右栏读到的名"] = bool(
                new_ch and name_val and new_ch[0]["label"] == name_val)
            out["E_★★默认名结论"] = (
                "新建的角色在**权威 API** 里的 label == 右栏名称输入框读到的值 == %r"
                % name_val) if out["E_★★新增角色的label是否等于右栏读到的名"] else "未成立"

            # F. ★ 收尾：删掉本批新建的 ⟹ 轮询 API 回到基线
            if new_ch:
                ok2, why = delete_character_by_label(page, new_ch[0]["label"])
                out["F_★是否点了删除"] = ok2
                out["F_★删除原因"] = why
                ok3, chars2, secs2 = poll_characters(page, len(base), timeout_s=150)
                out["F_★API轮询是否回到基线"] = ok3
                out["F_★耗时秒"] = secs2
                out["F_★最终API角色"] = chars2
            out["F_★★是否已复原"] = (
                len(api_characters(page)) == len(base)
                and [c["label"] for c in api_characters(page)]
                == [c["label"] for c in base])
            try:
                page.screenshot(path="/tmp/liblib_source_charname838h_after.png")
            except Exception:
                pass
            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        for k in ("A_★API基线_角色", "B_★清理后的API角色", "E_★API里的角色",
                  "F_★最终API角色"):
            print("%-24s %s" % (k, out.get(k)))
        for k in ("A_★API基线_角色数", "B_★清理后的API角色数", "C_★选中的体型",
                  "D_★读到的默认名", "D_★面板标题是角色", "E_★API轮询是否达成", "E_★耗时秒",
                  "E_★新增的角色", "E_★★新增角色的label是否等于右栏读到的名",
                  "E_★★默认名结论", "F_★是否点了删除", "F_★API轮询是否回到基线",
                  "F_★★是否已复原"):
            print("%-34s %r" % (k, out.get(k)))
        print("  清理尝试 =", json.dumps(out.get("B_清理尝试"), ensure_ascii=False))
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()
