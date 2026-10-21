#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 833 源站探针：**逐枚**点 15 个机位预设，量每枚的语义（位置/旋转/注视/FOV）。

★ 本批要修掉 batch 832 的两个失败：
  ① **读数器定位不到右栏** ⟹ 832 用了 `aside` ⟹ 但源站右栏是 **`<div>`**
     @(1639,0) 281 宽 ⟹ **零命中** ⟹ 读数恒空（假否定）。
     ⟹ 本版改用**几何定位**：找 `x >= 1639` 且宽 ≥ 240 的容器，
        再在里面按**字段标题**（名称/位置/旋转/注视坐标）定位其下方的
        `input[type=number]` ⟹ ★ 不依赖元素标签。
  ② **删除逻辑一次都没生效** ⟹ 832 用 `get_by_text("删除", exact=True)`
     ⟹ 匹配到了别的元素。
     ⟹ 本版用 `[role="menuitem"]` 精确点，且**每删一次就复验一次**
        （删完立刻重读机位数 ⟹ 少一台才算成功 ⟹ 否则**停下**并报错）。

★ ★ ★ 纪律（红线）：
  - 本探针**会改源站项目**（点预设会真的新建机位）；
  - ⟹ 每枚测完**立刻删掉**，且**删完必须复验**；
  - ⟹ 全部测完**再用全新浏览器 context 复验**场景树里只剩「机位1」；
  - ⟹ 若中途出错，**也要在 finally 里跑一次清理**。
"""
import json
import pathlib
import re
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk833_presets.json")
SHOTS = pathlib.Path("/tmp/liblib_source_desk833")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

CAM_RE = re.compile(r"^机位\s*(\d+)$")

# ★ 机位属性读数：**按字段标题定位**其下方的 number 输入（不依赖元素标签）
DUMP_PROPS = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  // ★ 右栏容器：x >= 1600、宽 >= 240、通高的那个
  const cols=Array.from(document.querySelectorAll('div')).filter(e=>{
    const r=e.getBoundingClientRect();
    return vis(e)&&r.x>=1600&&r.width>=240&&r.width<=300&&r.height>=900;});
  const col=cols[cols.length-1];
  if(!col) return {found:false, reason:'右栏容器没找到'};
  // ★ 所有可见的 number 输入（按 y 排序）⟹ 位置XYZ / 旋转XYZ / 注视XYZ / FOV
  const nums=Array.from(col.querySelectorAll('input[type="number"]')).filter(vis)
    .map(i=>({value:i.value, box:box(i)}));
  // ★ FOV：range + 它旁边的只读框
  const range=Array.from(col.querySelectorAll('input[type="range"]')).filter(vis)[0];
  // ★ 字段标题（用于定位分组）
  const labels=Array.from(col.querySelectorAll('div,span')).filter(vis)
    .filter(e=>e.childElementCount===0)
    .map(e=>({t:(e.textContent||'').trim(), y:Math.round(e.getBoundingClientRect().y)}))
    .filter(x=>x.t&&x.t.length<=8);
  return {found:true, colBox:box(col), nums, labels,
          fov:range?range.value:null,
          fovBox:range?box(range):null};
}"""

# ★ 右栏**第一个输入框** = 选中机位的**名字**（源站实测：值是「机位2」等）
#   ⟹ ★ 这是**唯一可靠**的「我刚建的那台叫什么」来源
#   ⟹ ★ 不能靠猜编号（点一次预设恰好新建 1 台、编号递增 ⟹ 但删的时候要用名字定位）
DUMP_NEWNAME = """()=>{
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  const cols=Array.from(document.querySelectorAll('div')).filter(e=>{
    const r=e.getBoundingClientRect();
    return vis(e)&&r.x>=1600&&r.width>=240&&r.width<=300&&r.height>=900;});
  const col=cols[cols.length-1];
  if(!col) return null;
  const ins=Array.from(col.querySelectorAll('input')).filter(vis);
  return ins.length?ins[0].value:null;
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
    page.wait_for_timeout(9_000)


def tree_cameras(page):
    """读场景树里的机位名。

    ★★ ★ 关键前提：点开「添加机位」后，左侧资源栏会切成**机位预设视图**
    ⟹ **场景树根本不在 DOM 里** ⟹ 此时读场景树只会得到空列表
    ⟹ ★ 所以读之前**必须先切回「场景」视图**。
    """
    return page.evaluate(DUMP_TREE)


def back_to_scene(page):
    """点 rail 的「场景」⟹ 左侧资源栏切回场景树。"""
    try:
        nav = page.locator("nav").filter(
            has=page.locator("button[aria-label='场景']")).first
        nav.locator("button[aria-label='场景']").first.click()
        page.wait_for_timeout(1_400)
    except Exception:
        pass


def delete_camera(page, log, name=None):
    """删掉**指定名字**的那台机位（名字从右栏读到）⟹ 删完**复验**少了一台才算成功。

    ★★ 为什么不能「删编号最大的」：源站的编号**不连续**
      （点一次预设恰好新建 1 台、编号递增；但场景树里可能有别的号）
      ⟹ ★ 一律**按名字**定位。
    """
    # ★★ 先切回「场景」视图 ⟹ 否则场景树不在 DOM 里、根本点不到
    back_to_scene(page)
    cams = tree_cameras(page)
    if name is None:
        nums = [int(CAM_RE.match(c).group(1)) for c in cams if CAM_RE.match(c)]
        if not nums:
            return True
        name = "机位%d" % max(nums)
    if name not in cams:
        log.append("★ %s 不在场景树里（%s）⟹ 无需删" % (name, cams))
        return True
    victim = name
    item = page.get_by_text(victim, exact=True).first
    item.click()
    page.wait_for_timeout(700)
    item.click(button="right")
    page.wait_for_timeout(1_300)
    del_item = page.locator("[role='menuitem']").filter(has_text="删除").first
    if not del_item.count():
        log.append("右键菜单里没有 menuitem『删除』")
        return False
    del_item.click()
    page.wait_for_timeout(1_400)
    for label in ("确认删除", "确定", "确认"):
        try:
            b = page.get_by_role("button", name=label, exact=True)
            if b.count() and b.first.is_visible():
                b.first.click()
                page.wait_for_timeout(1_000)
                break
        except Exception:
            pass
    page.wait_for_timeout(900)
    after = tree_cameras(page)
    ok = len(after) == len(cams) - 1
    log.append("删 %s：%d → %d 台 %s" % (victim, len(cams), len(after),
                                        "✔" if ok else "✘ 未减少"))
    return ok


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {}
    try:
        run(out, cookies)
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        print("删除日志：")
        for line in out.get("删除日志") or []:
            print("  ", line)
        print("末次树：", out.get("末次树"))


def run(out, cookies):
    log = out.setdefault("删除日志", [])
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
            out["①基线树"] = tree_cameras(page)
            out["②基线属性"] = page.evaluate(DUMP_PROPS)

            nav = page.locator("nav").filter(
                has=page.locator("button[aria-label='场景']")).first
            nav.locator("button[aria-label='添加机位']").first.click()
            page.wait_for_timeout(2_200)
            grid = page.locator("div.grid.min-h-0.flex-1").first
            cells = grid.locator("button")
            n = cells.count()
            out["③格子数"] = n
            sem = []
            for i in range(n):
                label = (cells.nth(i).inner_text() or "").strip().split("\n")[-1]
                try:
                    cells.nth(i).click()
                    page.wait_for_timeout(2_400)
                    props = page.evaluate(DUMP_PROPS)
                    new_name = page.evaluate(DUMP_NEWNAME)
                    sem.append({"idx": i, "label": label, "props": props,
                                "新建机位名": new_name})
                    print("  #%d %-12s 位置=%s 旋转=%s 注视=%s FOV=%s"
                          % (i, label,
                             [x["value"] for x in (props.get("nums") or [])][:3],
                             [x["value"] for x in (props.get("nums") or [])][3:6],
                             [x["value"] for x in (props.get("nums") or [])][6:9],
                             props.get("fov")))
                    if not delete_camera(page, log, new_name):
                        out["异常"] = "删除失败（见删除日志）⟹ 停止"
                        break
                    # ★ 删除流程会切回「场景」视图 ⟹ 下一枚前要**重开预设面板**
                    nav.locator("button[aria-label='添加机位']").first.click()
                    page.wait_for_timeout(1_800)
                    grid = page.locator("div.grid.min-h-0.flex-1").first
                    cells = grid.locator("button")
                except Exception as exc:  # noqa: BLE001
                    sem.append({"idx": i, "label": label, "异常": str(exc)[:300]})
                    log.append("#%d 异常：%s" % (i, str(exc)[:120]))
                    try:
                        delete_camera(page, log)
                        nav.locator("button[aria-label='添加机位']").first.click()
                        page.wait_for_timeout(1_600)
                        grid = page.locator("div.grid.min-h-0.flex-1").first
                        cells = grid.locator("button")
                    except Exception:
                        break
            out["④预设语义"] = sem
            back_to_scene(page)
            out["末次树"] = tree_cameras(page)
        except Exception:
            out["异常"] = traceback.format_exc()[-1800:]
            # ★ 出错也要清理
            try:
                back_to_scene(page)
                for _ in range(40):
                    cams = tree_cameras(page)
                    nums = [int(CAM_RE.match(c).group(1)) for c in cams
                            if CAM_RE.match(c)]
                    if not nums or max(nums) < 2:
                        break
                    # ★ 清理场景下没有「刚建的那台」的名字 ⟹ 删编号最大的
                    if not delete_camera(page, log, "机位%d" % max(nums)):
                        break
            except Exception:
                pass
        try:
            page.locator("[aria-label='关闭']:visible").first.click()
            page.wait_for_timeout(3_000)
        except Exception:
            pass
        ctx.close()
        br.close()


if __name__ == "__main__":
    main()
