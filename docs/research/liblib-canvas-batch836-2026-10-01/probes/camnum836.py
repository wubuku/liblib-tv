#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 836 源站探针：实测「机位N」的**编号规则** —— 是 `count+1` 还是 `max+1`？

★ 为什么要问这个（batch 833 明确留的未测项）：
  源站新建的机位叫「机位N」。batch 833 只测了「已有 1 台 → 新建的那台叫 机位2」这一种情形
  ⟹ **连续编号下 count+1 与 max+1 结果相同 ⟹ 分不出**。
  ⟹ clone 现在写的是 `机位${cameraIndex}`（cameraIndex 来自现有机位数 ⟹ **count+1**）
  ⟹ 若源站其实是 max+1 ⟹ clone 在「删掉中间一台再新建」时会**重名**。

★ 区分实验（关键）：**先删掉编号最小的那台**，让场景里出现编号空洞
  （例如只剩「机位2」⟹ max=2 但 count=1）
  ⟹ 再新建一台：
    - 若叫「机位2」 ⟹ **count+1** ⟹ 会与已有的「机位2」**重名**；
    - 若叫「机位3」 ⟹ **max+1** ⟹ 不重名。

★ ★ 纪律（红线，与 batch 833 同款）：
  - 本探针**会改源站项目**（新建/删除机位）；
  - ⟹ 每一步**删完必须复验**（机位数真的少了才算成功）；
  - ⟹ **收尾必须复原**（把测出来的机位删回只剩原有的那些）；
  - ⟹ 源站账号的引导已被标记成「看过」⟹ 不依赖引导。
  - ⟹ 若中途出错，**也要在 finally 里跑一次清理**。
"""
import json
import pathlib
import re
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_camnum836.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

CAM_RE = re.compile(r"^机位\s*(\d+)$")

# ★ 右栏第一个输入框 = 选中机位的名字（batch 833 实测：值是「机位2」等）
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

# ★ 场景树里的机位名
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
    return page.evaluate(DUMP_TREE)


def back_to_scene(page):
    try:
        nav = page.locator("nav").filter(
            has=page.locator("button[aria-label='场景']")).first
        nav.locator("button[aria-label='场景']").first.click()
        page.wait_for_timeout(1_400)
    except Exception:
        pass


def delete_camera(page, log, name):
    """删掉**指定名字**的那台 ⟹ 删完**复验**少了一台才算成功。"""
    back_to_scene(page)
    cams = tree_cameras(page)
    if name not in cams:
        log.append("★ %s 不在场景树里（%s）⟹ 无需删" % (name, cams))
        return True
    item = page.get_by_text(name, exact=True).first
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
    log.append("删 %s：%d → %d 台 %s" % (name, len(cams), len(after),
                                        "✔" if ok else "✘ 未减少"))
    return ok


def new_camera_via_preset(page, log):
    """点 rail 的「添加机位」→ 点**第一枚预设** ⟹ 真的新建一台机位。

    ★ 返回新机位的名字（从右栏第一个输入框读）⟹ 那是**唯一可靠**的来源。
    """
    nav = page.locator("nav").filter(
        has=page.locator("button[aria-label='场景']")).first
    nav.locator("button[aria-label='添加机位']").first.click()
    page.wait_for_timeout(2_200)
    grid = page.locator("div.grid.min-h-0.flex-1").first
    cells = grid.locator("button")
    n = cells.count()
    if not n:
        log.append("★ 机位预设面板里没有格子")
        return None
    cells.nth(0).click()
    page.wait_for_timeout(2_400)
    name = page.evaluate(DUMP_NEWNAME)
    log.append("点第一枚预设后右栏读到的新机位名：%r" % (name,))
    return name


def nums_of(names):
    out = []
    for n in names:
        m = CAM_RE.match(n)
        if m:
            out.append(int(m.group(1)))
    return sorted(out)


def run(out, cookies):
    log = out.setdefault("删除日志", [])
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
        try:
            # ---------- ① 基线 ----------
            back_to_scene(page)
            base = tree_cameras(page)
            out["①基线树"] = base
            out["①基线编号"] = nums_of(base)
            log.append("基线树：%s" % base)

            # ---------- ② 先新建一台 ⟹ 看编号（count+1 / max+1 在连续时相同）----------
            n1 = new_camera_via_preset(page, log)
            back_to_scene(page)
            t2 = tree_cameras(page)
            out["②新建一台后树"] = t2
            out["②新机位名"] = n1
            log.append("新建一台后树：%s" % t2)

            # ---------- ③ 再新建一台 ⟹ 连续编号下应是 3 ----------
            n2 = new_camera_via_preset(page, log)
            back_to_scene(page)
            t3 = tree_cameras(page)
            out["③再建一台后树"] = t3
            out["③新机位名"] = n2
            log.append("再建一台后树：%s" % t3)

            # ---------- ④ ★ 关键：删掉**编号最小**的那台 ⟹ 制造编号空洞 ----------
            cur = nums_of(tree_cameras(page))
            smallest_name = "机位%d" % min(cur) if cur else None
            out["④要删的最小编号机位"] = smallest_name
            ok_del = delete_camera(page, log, smallest_name)
            out["④删除成功"] = ok_del
            back_to_scene(page)
            t4 = tree_cameras(page)
            out["④删后树"] = t4
            out["④删后编号"] = nums_of(t4)
            log.append("删 %s 后树：%s" % (smallest_name, t4))

            # ---------- ⑤ ★ 决定性：在有编号空洞的状态下新建 ----------
            n3 = new_camera_via_preset(page, log)
            back_to_scene(page)
            t5 = tree_cameras(page)
            out["⑤空洞态新建后树"] = t5
            out["⑤新机位名"] = n3
            out["⑤新机位编号"] = (int(CAM_RE.match(n3).group(1))
                                  if n3 and CAM_RE.match(n3) else None)
            log.append("空洞态新建后树：%s" % t5)

            # ---------- ⑥ 判定 ----------
            nums5 = nums_of(t5)
            existing_before = set(nums_of(t4))
            new_num = out["⑤新机位编号"]
            out["⑥判定"] = {
                "删后已有的编号": sorted(existing_before),
                "新建后的编号": nums5,
                "新机位编号": new_num,
                "与已有编号重名": bool(new_num is not None and new_num in existing_before),
                "规则": ("count+1（会重名）" if (new_num is not None and new_num in existing_before)
                         else "max+1（不重名）" if new_num is not None else "读不到"),
            }
            log.append("判定：%s" % out["⑥判定"])

            # ---------- ⑦ 复原：把多出来的机位删掉，只留基线那几台 ----------
            back_to_scene(page)
            for nm in sorted(set(tree_cameras(page)) - set(base), key=lambda x: -nums_of([x])[0]
                             if nums_of([x]) else 0):
                delete_camera(page, log, nm)
            back_to_scene(page)
            out["⑦复原后树"] = tree_cameras(page)
            out["⑦复原正确"] = sorted(tree_cameras(page)) == sorted(base)
            log.append("复原后树：%s（正确=%s）" % (tree_cameras(page), out["⑦复原正确"]))
        finally:
            try:
                back_to_scene(page)
                cur = tree_cameras(page)
                for nm in sorted(set(cur) - set(base)):
                    delete_camera(page, log, nm)
                out["收尾树"] = tree_cameras(page)
            except Exception:
                out["收尾异常"] = traceback.format_exc()
            try:
                page.screenshot(path="/tmp/liblib_source_camnum836.png")
            except Exception:
                pass
            br.close()


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {}
    try:
        run(out, cookies)
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        for k in ("①基线树", "②新建一台后树", "③再建一台后树", "④删后树",
                  "⑤空洞态新建后树", "⑤新机位名", "⑥判定", "⑦复原后树", "⑦复原正确"):
            print("%-16s %s" % (k, json.dumps(out.get(k), ensure_ascii=False)))
        print("删除日志：")
        for line in out.get("删除日志") or []:
            print("  ", line)
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()
