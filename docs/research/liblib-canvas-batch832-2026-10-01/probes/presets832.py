#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 832 源站探针（第二轮）：**逐枚**点 15 个机位预设，量每枚的语义。

★ 为什么必须逐枚测：batch 832 第一版只点了「正面中景」⟹ 只知道一枚的值
  （机位2 / 位置 (0,1.5,4) / 旋转 (4.29,180,0) / FOV 50 / 注视 (0,1.2,0)）。
  ⟹ ★ 而「正面特写」「荷兰角」「鸟瞰」等的 FOV 与位置**各不相同**
  ⟹ 只测一枚就等于**凭一枚推 15 枚** ⟹ 不做。

★ 测法：
  1. 点第 N 枚预设 ⟹ 右栏出现该机位的属性（名称/位置/旋转/注视坐标/FOV）
  2. 读出这些值 ⟹ 记成第 N 枚的语义
  3. ★ **删掉刚建的机位**（右栏有删除入口；场景树右键也行）⟹ 恢复原状
  4. 下一枚

★ ★ ★ 纪律（红线）：本探针**会改源站项目** ⟹ 每枚测完**立刻删掉**
  ⟹ 最后**再跑一次全新 context 复验**，确认场景树里只剩「机位1」。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk832_presets.json")
SHOTS = pathlib.Path("/tmp/liblib_source_desk832")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

DUMP_PRESETS = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  const cands=Array.from(document.querySelectorAll('div')).filter(e=>{
    const c=getComputedStyle(e); const r=e.getBoundingClientRect();
    if(!vis(e)) return false;
    if(c.display!=='flex'||c.flexDirection!=='column') return false;
    if(Math.abs(r.width-232)>1) return false;
    return r.height>200;});
  const panel=cands[cands.length-1];
  if(!panel) return {found:false};
  const grid=panel.querySelector('div.grid');
  const cells=grid?Array.from(grid.children):[];
  return {found:true, labels:cells.map(c=>(c.textContent||'').trim().slice(0,20))};
}"""

# ★ 右栏机位属性读数（名称/位置/旋转/注视坐标/FOV）
DUMP_CAMPROPS = """()=>{
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  const aside=Array.from(document.querySelectorAll('aside')).filter(e=>{
    const r=e.getBoundingClientRect(); return r.x>1500&&r.width>200;})[0];
  if(!aside) return {found:false};
  const inputs=Array.from(aside.querySelectorAll('input')).filter(vis).map(i=>({
    type:i.type, aria:i.getAttribute('aria-label'), value:i.value,
    min:i.getAttribute('min'), max:i.getAttribute('max')}));
  // 分组标题（名称/位置/旋转/注视目标/注视坐标/视场角）
  const labels=Array.from(aside.querySelectorAll('*')).filter(vis)
    .map(e=>(e.textContent||'').trim())
    .filter(t=>['名称','切换机位','位置','旋转','注视目标','注视坐标','视场角 (FOV)']
      .includes(t));
  return {found:true, inputs, labels:[...new Set(labels)]};
}"""

# ★ 场景树里的机位名（用于判据与复原）
DUMP_TREE = """()=>{
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  return [...new Set(Array.from(document.querySelectorAll('span')).filter(vis)
    .map(s=>(s.textContent||'').trim())
    .filter(t=>/^机位\\s*\\d+$/.test(t)))];
}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(800)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(8_000)


def delete_camera(page):
    """删掉刚建的机位：场景树里右键 → 删除"""
    try:
        n = page.locator("span").filter(has_text=__import__("re").compile(r"^机位\\s*\\d+$"))
        # 取最后一个（新建的在后面）
        cnt = n.count()
        if cnt == 0:
            return False
        item = n.nth(cnt - 1)
        item.click()
        page.wait_for_timeout(700)
        item.click(button="right")
        page.wait_for_timeout(1_200)
        page.get_by_text("删除", exact=True).first.click()
        page.wait_for_timeout(1_200)
        for label in ("确认删除", "确定"):
            try:
                b = page.get_by_role("button", name=label, exact=True)
                if b.count() and b.first.is_visible():
                    b.first.click()
                    page.wait_for_timeout(900)
                    break
            except Exception:
                pass
        page.wait_for_timeout(800)
        return True
    except Exception:
        return False


def run(out, cookies):
    import re
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
            nav = page.locator("nav").filter(
                has=page.locator("button[aria-label='场景']")).first
            nav.locator("button[aria-label='添加机位']").first.click()
            page.wait_for_timeout(2_200)
            labels = (page.evaluate(DUMP_PRESETS) or {}).get("labels") or []
            out["①预设标签"] = labels
            grid = page.locator("div.grid.min-h-0.flex-1").first
            cells = grid.locator("button")
            sem = []
            for i in range(len(labels)):
                try:
                    cells.nth(i).click()
                    page.wait_for_timeout(2_200)
                    props = page.evaluate(DUMP_CAMPROPS)
                    tree = page.evaluate(DUMP_TREE)
                    sem.append({"idx": i, "label": labels[i],
                                "props": props, "树": tree})
                    print("  #%d %s → %s" % (i, labels[i],
                                             json.dumps(props.get("inputs"),
                                                        ensure_ascii=False)))
                    delete_camera(page)
                    # 面板可能被关掉了 ⟹ 重开
                    if not page.evaluate(DUMP_PRESETS).get("found"):
                        nav.locator("button[aria-label='添加机位']").first.click()
                        page.wait_for_timeout(1_500)
                        grid = page.locator("div.grid.min-h-0.flex-1").first
                        cells = grid.locator("button")
                except Exception as exc:  # noqa: BLE001
                    sem.append({"idx": i, "label": labels[i] if i < len(labels) else "?",
                                "异常": str(exc)[:300]})
                    try:
                        delete_camera(page)
                        nav.locator("button[aria-label='添加机位']").first.click()
                        page.wait_for_timeout(1_500)
                        grid = page.locator("div.grid.min-h-0.flex-1").first
                        cells = grid.locator("button")
                    except Exception:
                        pass
            out["预设语义"] = sem
            out["⓬末次树"] = page.evaluate(DUMP_TREE)
        except Exception:
            out["异常"] = traceback.format_exc()[-1800:]
        try:
            page.locator("[aria-label='关闭']:visible").first.click()
            page.wait_for_timeout(3_000)
        except Exception:
            pass
        ctx.close()
        br.close()


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {}
    try:
        run(out, cookies)
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        print("机位名（末次读数）:", out.get("⓬末次树"))
        for p in out.get("预设语义") or []:
            print("  ", p)


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
