#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 832 诊断探针（第二轮）：源站 rail 入口点开的东西**到底有没有出现**？

★ 上一版读数的问题：6 枚入口点开后的读数**一模一样**（都是那张常驻的
  Agent promo 卡 280×311 @(1040,700)）⟹ 两个可能：
    (a) 点击没落到 rail 按钮上（`[aria-label='场景']` 在源站**不唯一** ⟹
        `.first` 可能选中左侧对象树里的同名元素）；
    (b) 打开的东西不符合读数器的形状过滤（不是 absolute/fixed、尺寸不在区间）。
  ⟹ ★ 两个可能都必须排除，不能靠猜。

★ 本探针的办法：
  1. **scoped** 到 rail 那个 `nav` 里点（不靠全局 aria-label）；
  2. 点前点后**各拍一次「可见元素签名表」** ⟹ 用**集合差**找新出现的元素
     ⟹ 不依赖任何形状假设；
  3. 顺带处理那张常驻 promo 卡（点「下次再说」关掉），免得它污染读数。

★ 纪律：只读 + 只点 rail 入口；不改源站数据。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_diag832b.json")
SHOTS = pathlib.Path("/tmp/liblib_source_diag832b")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 可见元素「签名表」：用元素的 DOM 路径 + 类名 + 文本前若干字做签名
DUMP_SIG = """()=>{
  const sig=(e)=>{
    const r=e.getBoundingClientRect();
    if(r.width<=0||r.height<=0) return null;
    const c=getComputedStyle(e);
    if(c.display==='none'||c.visibility==='hidden'||c.opacity==='0') return null;
    // ★ 只收「叶子-ish」的容器：带可见文本或带背景的
    const t=(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,40);
    const tag=e.tagName;
    const cls=String(e.className||'').slice(0,80);
    const role=e.getAttribute('role')||'';
    const aria=e.getAttribute('aria-label')||'';
    return {tag, cls, role, aria, t,
            box:{x:Math.round(r.x),y:Math.round(r.y),
                 w:Math.round(r.width),h:Math.round(r.height)}};
  };
  const out=[];
  for(const e of document.querySelectorAll('body *')){
    const s=sig(e);
    if(!s) continue;
    // 只收「有辨识度」的：带文本 或 带 role/aria
    if(!s.t && !s.role && !s.aria) continue;
    out.push(s);
  }
  return out;
}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(800)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(8_000)


def rail_nav(page):
    """★ 用**几何**找那根 48px 宽的竖条（不靠 nav 标签 ⟹ 结构变了也不怕）"""
    return page.locator("nav").filter(
        has=page.locator("button[aria-label='场景']")).first


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {}
    try:
        run(out, cookies)
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)


def run(out, cookies):
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                             locale="zh-CN")
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
        SHOTS.mkdir(exist_ok=True)
        try:
            # ── 先关掉常驻 promo 卡（免得它出现在每一次读数里）
            try:
                page.get_by_text("下次再说", exact=True).first.click()
                page.wait_for_timeout(1_500)
                out["promo已关"] = True
            except Exception:
                out["promo已关"] = False

            nav = rail_nav(page)
            out["nav数量"] = page.locator("nav").count()
            out["rail按钮数"] = nav.locator("button").count()
            out["rail按钮名"] = nav.locator("button").evaluate_all(
                "els=>els.map(e=>e.getAttribute('aria-label'))")

            for aria in ["场景", "添加角色", "添加机位", "全景图",
                         "选择画幅比例", "AI 识图导入"]:
                key = "◆" + aria
                try:
                    before = page.evaluate(DUMP_SIG)
                    nav.locator("button[aria-label='%s']" % aria).first.click()
                    page.wait_for_timeout(2_000)
                    after = page.evaluate(DUMP_SIG)
                    # ★ 集合差：按 (tag,cls,aria,role,text,box) 做键
                    def keyset(rows):
                        return {json.dumps({k: r[k] for k in
                                            ("tag", "cls", "role", "aria", "t", "box")},
                                           ensure_ascii=False, sort_keys=True)
                                for r in rows}
                    kb, ka = keyset(before), keyset(after)
                    new = [json.loads(x) for x in (ka - kb)]
                    gone = [json.loads(x) for x in (kb - ka)]
                    out[key] = {"新出现": new[:25], "新出现数": len(new),
                                "消失": gone[:8], "消失数": len(gone)}
                    page.screenshot(path=str(SHOTS / ("b_%s.png" % aria.replace(" ", ""))))
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(700)
                    page.mouse.click(1400, 950)
                    page.wait_for_timeout(1_000)
                except Exception as exc:  # noqa: BLE001
                    out[key] = {"异常": str(exc)[:400]}
                    try:
                        page.keyboard.press("Escape")
                        page.wait_for_timeout(500)
                    except Exception:
                        pass
        except Exception:
            out["异常"] = traceback.format_exc()[-1500:]
        try:
            page.locator("[aria-label='关闭']:visible").first.click()
            page.wait_for_timeout(2_500)
        except Exception:
            pass
        ctx.close()
        br.close()


if __name__ == "__main__":
    main()
