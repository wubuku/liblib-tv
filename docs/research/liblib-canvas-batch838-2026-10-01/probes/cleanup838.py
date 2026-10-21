#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 838：★ **清理**源站里实验遗留的角色（用 API 权威读数 + 轮询复核）。

★ 为什么需要它：v19（charname838j）那趟把多余的 B／C 删掉并**落盘**了，
  但它自己**新建**的那个「角色B」（id `p6past1f`）**没删掉** ⟹
  `F_★是否点了删除 = False`（场景树里按 class 找不到那一行 —— 选中态下 class 变了）。

★ 本脚本的判据与动作：
  1. ★ **权威读数** = API（带 `token` ＋ `webid` 头，从页面自己的请求里抄）；
  2. ★ **只删多出来的**（基线是「角色A」这一个）⟹ 逐个删到只剩 A；
  3. ★ **删除定位**：先按场景树里的**文本**找（class 口径失效时用**更宽**的几何口径兜底），
     找到就右键删；找不到就**如实报告**（不谎称删了）；
  4. ★ **每次删完都轮询 API** 确认落盘 ⟹ 复原由 API 自证。
"""
import json
import pathlib
import sys
import time
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_cleanup838.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")
DETAIL_API = ("https://api.liblib.tv/api/canvas/project/detail-by-space"
              "?spaceId=7709759"
              "&projectUuid=a860e1da8e9e4504bececda022386429")

# ★ 场景树行：**先试 class 口径**（`pl-1` ＋ `z-10`），失败则**用几何兜底**
#    （x∈[80,240] 且 y∈[140,320] ⟹ 实测机位1@154／角色A@218／角色B@250 全在这个带里，
#    而浮层面板行在 x=86 但 y 从 106 起 —— ★ **两者的 y 区间重叠**，
#    ⟹ 兜底口径**可能**读到面板行 ⟹ 故**优先**用 class 口径，只在它失败时兜底，
#    且**校验**找出来的行的文本确实等于目标名（面板行不会叫「角色B」）。
LOCATE = """(label) => {
  const vis=(e)=>{const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;};
  const all=[];
  for (const el of Array.from(document.querySelectorAll('span,div,button'))) {
    if (!vis(el) || el.childElementCount>0) continue;
    const t=(el.textContent||'').trim();
    if (t !== label) continue;
    const r=el.getBoundingClientRect();
    all.push({text:t, x:Math.round(r.x), y:Math.round(r.y),
              w:Math.round(r.width), h:Math.round(r.height),
              cls:(el.className||'').toString().slice(0,60)});
  }
  // ① class 口径优先
  const byCls = all.filter(e=>e.cls.indexOf('pl-1')>=0 && e.cls.indexOf('z-10')>=0);
  if (byCls.length) return {row: byCls[0], how: 'class(pl-1+z-10)'};
  // ② 几何兜底（排除浮层面板那一带：面板行的 x 是 86 且 y≥106 ⟹ 取 x≈96 的）
  const byGeo = all.filter(e=>e.x>=80 && e.x<=240 && e.y>=140 && e.y<=320);
  if (byGeo.length) return {row: byGeo[0], how: '几何兜底'};
  return {row: null, how: '没找到', candidates: all.slice(0,6)};
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


def api_characters(page, auth) -> list:
    resp = page.request.get(DETAIL_API, headers=auth)
    raw = resp.text()
    d = json.loads(raw)
    node_list = ((d.get("data") or {}).get("projectDetail") or {}).get("nodeList")
    if not node_list:
        raise RuntimeError("API 没返回 nodeList（len=%d, msg=%s）⟹ 读数方法坏了"
                           % (len(raw), d.get("msg")))
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
    raise RuntimeError("API 里没有导演台节点 ⟹ 不下结论")


def poll(page, auth, want_len, timeout_s=120, step=8):
    t0 = time.time()
    last = []
    while time.time() - t0 < timeout_s:
        last = api_characters(page, auth)
        if len(last) == want_len:
            return True, last, round(time.time() - t0)
        time.sleep(step)
    return False, last, round(time.time() - t0)


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
            auth = {}

            def on_req(req):
                try:
                    if 'detail-by-space' not in req.url:
                        return
                    h = req.headers
                    if h.get('token'):
                        auth['token'] = h['token']
                    if h.get('webid'):
                        auth['webid'] = h['webid']
                except Exception:
                    pass

            page.on('request', on_req)
            page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
            page.wait_for_timeout(12_000)
            if 'token' not in auth:
                raise RuntimeError("没抓到 token ⟹ 读数方法坏了 ⟹ 不下结论")
            open_desk(page)
            clean(page)

            base = api_characters(page, auth)
            out["①API基线_角色"] = base
            out["①★API基线_标签"] = [c["label"] for c in base]

            attempts = []
            for _ in range(6):
                chars = api_characters(page, auth)
                if len(chars) <= 1:
                    break
                victim = chars[-1]
                loc = page.evaluate(LOCATE, victim["label"])
                rec = {"删的是": victim, "定位方式": loc.get("how")}
                row = loc.get("row")
                if not row:
                    rec["成功"] = False
                    rec["原因"] = "场景树里找不到那一行"
                    attempts.append(rec)
                    break
                page.mouse.click(row["x"] + 10, row["y"] + row["h"] / 2, button="right")
                page.wait_for_timeout(1_500)
                clean(page)
                clicked = False
                for lab in ("删除", "删除⌘⌫"):
                    try:
                        el = page.get_by_text(lab, exact=True).first
                        if el.is_visible():
                            el.click()
                            clicked = True
                            break
                    except Exception:
                        continue
                rec["★是否点到删除项"] = clicked
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
                ok, now, secs = poll(page, auth, len(chars) - 1, timeout_s=120)
                rec["★API是否落盘"] = ok
                rec["★耗时秒"] = secs
                rec["★现在的角色"] = now
                attempts.append(rec)
                if not ok:
                    break

            out["②清理尝试"] = attempts
            final = api_characters(page, auth)
            out["③★最终API角色"] = final
            out["③★最终标签"] = [c["label"] for c in final]
            out["③★★是否已复原"] = (
                len(final) == 1 and final[0]["label"] == "角色A")
            try:
                page.screenshot(path="/tmp/liblib_source_cleanup838.png")
            except Exception:
                pass
            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        for k in ("①★API基线_标签", "③★最终标签"):
            print("%-20s %s" % (k, out.get(k)))
        print("★是否已复原 =", out.get("③★★是否已复原"))
        for a in out.get("②清理尝试") or []:
            print("  ", json.dumps(a, ensure_ascii=False))
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()
