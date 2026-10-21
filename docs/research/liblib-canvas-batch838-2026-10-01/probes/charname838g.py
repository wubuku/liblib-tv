#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 838 源站探针 v16：★ **按 class 精确识别场景树行**，并完成「清理 ＋ 单趟闭环」。

★★★ 为什么 v15 又失败了（★ 第三次读数器踩坑，但这次找到了**根因**）：
  v8/v11/v15 都用**几何**（x/y 区间）去区分「场景树对象行」与「体型预设面板行」⟹
  ★★ **面板是浮层，它会盖在场景树上面** ⟹ 它的行**也在 x∈[80,240] 里** ⟹ 几何分不开。

★ ★★ **根因与正解**：这两类元素的 **class 不同** ⟹ 用 **class** 判别，不靠几何：
  - 场景树对象行：`z-10 min-w-0 flex-1 truncate pl-1`（**含 `pl-1` ＋ `z-10`**）；
  - 体型预设面板行：`truncate`（**没有** `pl-1`）。
  ⟹ 判据：`className` **同时**含 `pl-1` 且含 `z-10` ⟹ 才是场景树对象行。
  ★ 这正是已入库的那条纪律「**读数器扫的元素类型必须与界面真实元素类型相交**」的升级版：
    同一个元素类型（叶子 span）⟹ 必须再用**另一个正交特征**（class）把它们分开。

★★ 本趟做两件事（**单趟闭环**）：
  ① **清理**：删掉上一趟遗留的「角色B」（跨刷新复验）；
  ② **闭环**：新建 → 读名 → 删 → 等自动保存（45 秒）→ **跨刷新**复验。

★ ★★ 铁律：
  - 只删「角色B」这一个（**先验证唯一**）；源站有并发活动 ⟹ 不删别的；
  - ★ 删完**等 45 秒**（v14 实测自动保存约 30 秒延迟）⟹ 否则会误判「没落盘」；
  - ★ 跨刷新用**新的 context**（同 context 会有内存缓存）；
  - ★ Playwright 同步 API **不能嵌套** `sync_playwright()` ⟹ 跨刷新那趟用**独立进程**
    （`verify_source_restored.py`）⟹ 不在同一进程里开第二个 playwright。
"""
import json
import pathlib
import subprocess
import sys
import traceback

from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_charname838g.json")
RESTORE_PROBE = HERE / "verify_source_restored.py"
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★★★ 场景树对象行：**class 同时含 `pl-1` 与 `z-10`** ⟹ 与浮层面板行区分开
DUMP_TREE_OBJ = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0 && getComputedStyle(e).visibility!=='hidden';};
  const out=[]; const seen=new Set();
  for (const el of Array.from(document.querySelectorAll('span,div,button,a,p,li'))) {
    if (!vis(el) || el.childElementCount>0) continue;
    const cls=(el.className||'').toString();
    if (cls.indexOf('pl-1')<0 || cls.indexOf('z-10')<0) continue;   // ★★ 场景树行特征
    const r=el.getBoundingClientRect();
    const t=(el.textContent||'').trim();
    if (!t || t.length>30) continue;
    const key=Math.round(r.y)+'|'+t;
    if (seen.has(key)) continue; seen.add(key);
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y),
              w:Math.round(r.width), h:Math.round(r.height), tag:el.tagName, cls:cls.slice(0,60)});
  }
  return out.sort((a,b)=> (a.y-b.y) || (a.x-b.x));
}"""

DUMP_NAME_INPUT = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;};
  const out=[];
  for (const el of Array.from(document.querySelectorAll('input'))) {
    if (!vis(el)) continue;
    const r=el.getBoundingClientRect();
    if (r.x < 1300) continue;
    out.push({value:el.value||'', x:Math.round(r.x), y:Math.round(r.y)});
  }
  return out;
}"""

DUMP_PANEL_TITLE = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;};
  const out=[];
  for (const el of Array.from(document.querySelectorAll('span,div,h1,h2,h3'))) {
    if (!vis(el) || el.childElementCount>0) continue;
    const r=el.getBoundingClientRect();
    if (r.x < 1300 || r.y > 40) continue;
    const t=(el.textContent||'').trim();
    if (!t || t.length>20) continue;
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y)});
  }
  return out;
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


def tree_obj(page):
    rows = page.evaluate(DUMP_TREE_OBJ)
    names = []
    for r in rows:
        if r["text"] not in names:
            names.append(r["text"])
    return names, rows


def add_cookies(ctx, cookies):
    ctx.add_cookies([{"name": c["name"], "value": c["value"],
                      "domain": c["domain"], "path": c.get("path", "/"),
                      "expires": c.get("expires", -1),
                      "httpOnly": c.get("httpOnly", False),
                      "secure": c.get("secure", False),
                      "sameSite": c.get("sameSite", "Lax")} for c in cookies])


def delete_named(page, rows, name):
    """右键 → 菜单 → 删除。返回是否点到了删除项。"""
    cand = [r for r in rows if r["text"] == name]
    if len(cand) != 1:
        return False, len(cand)
    row = cand[0]
    page.mouse.click(row["x"] + 10, row["y"] + row["h"] / 2, button="right")
    page.wait_for_timeout(1_500)
    clean(page)
    for label in ("删除", "删除⌘⌫"):
        try:
            el = page.get_by_text(label, exact=True).first
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
                return True, 1
        except Exception:
            continue
    return False, 1


def run(out, cookies):
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport={"width": 1920, "height": 1080}, locale="zh-CN")
        add_cookies(ctx, cookies)
        page = ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(12_000)
        open_desk(page)
        clean(page)

        # A. 基线（★ 用 class 口径）
        a_names, a_rows = tree_obj(page)
        out["A_进站_场景树对象行"] = a_names
        out["A_★进站_行数"] = len(a_rows)
        out["A_行详情"] = a_rows

        # B. ★ 清理上一趟遗留的「角色B」（若有）
        out["B_★遗留角色B候选数"] = len([r for r in a_rows if r["text"] == "角色B"])
        if out["B_★遗留角色B候选数"] == 1:
            ok, _ = delete_named(page, a_rows, "角色B")
            out["B_★是否清掉遗留的"] = ok
            page.wait_for_timeout(45_000)     # ★ 等自动保存
            c_names, c_rows = tree_obj(page)
            out["B_清理后_行名"] = c_names
            out["B_清理后_行数"] = len(c_rows)
            a_names, a_rows = c_names, c_rows
            out["A_★清理后的基线行名"] = a_names
            out["A_★清理后的基线行数"] = len(a_rows)

        # C. ★ 单趟闭环：新建 → 读名
        page.locator("[aria-label='添加角色']").first.click()
        page.wait_for_timeout(1_500)
        clean(page)
        picked = None
        for label in ("标准男性", "标准女性", "健硕"):
            try:
                page.get_by_text(label, exact=True).first.click()
                picked = label
                break
            except Exception:
                continue
        out["C_★选中的体型"] = picked
        page.wait_for_timeout(2_500)
        clean(page)

        c_names, c_rows = tree_obj(page)
        out["C_新建后_场景树对象行"] = c_names
        out["C_★新建后_行数"] = len(c_rows)
        out["C_★★行数增量"] = len(c_rows) - len(a_rows)
        out["C_★★前提_真新增了一行"] = len(c_rows) == len(a_rows) + 1
        new_rows = [r for r in c_rows if r["text"] not in a_names]
        out["C_★新增的行"] = new_rows
        out["C_★新增行的文本"] = [r["text"] for r in new_rows]

        out["D_右栏标题"] = page.evaluate(DUMP_PANEL_TITLE)
        out["D_右栏输入框"] = page.evaluate(DUMP_NAME_INPUT)
        name_val = (out["D_右栏输入框"] or [{}])[0].get("value")
        out["D_★读到的默认名"] = name_val
        out["D_★★实验是否有效"] = bool(
            out["C_★★前提_真新增了一行"] and name_val
            and out["C_★新增行的文本"] and name_val in out["C_★新增行的文本"])
        try:
            page.screenshot(path="/tmp/liblib_source_charname838g.png")
        except Exception:
            pass

        # E. 删掉本批新建的
        deleted = False
        if new_rows:
            deleted, _ = delete_named(page, new_rows, new_rows[0]["text"])
        out["E_★是否点了删除"] = deleted
        e_names, e_rows = tree_obj(page)
        out["E_删除后_场景树对象行"] = e_names
        out["E_★删除后_行数"] = len(e_rows)
        out["E_★等自动保存秒数"] = 45
        page.wait_for_timeout(45_000)
        ctx.close()
        br.close()

    # F. ★ 跨刷新复验（**独立进程** ⟹ 绕开 Playwright 同步 API 不能嵌套的限制）
    r = subprocess.run([sys.executable, str(RESTORE_PROBE)], capture_output=True,
                       text=True, timeout=600)
    try:
        out["F_★跨刷新复验"] = json.loads(r.stdout)
    except Exception:
        out["F_★跨刷新复验"] = {"raw": r.stdout[-1500:], "err": r.stderr[-800:]}
    out["F_★跨刷新后_场景树对象行"] = (out["F_★跨刷新复验"] or {}).get("行名")
    out["F_★跨刷新后_行数"] = (out["F_★跨刷新复验"] or {}).get("行数")
    out["F_★跨刷新后还剩新建的"] = (out["F_★跨刷新复验"] or {}).get("还剩新建的")
    out["F_★★是否已复原"] = (out["F_★跨刷新复验"] or {}).get("是否已复原")


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
        for k in ("A_进站_场景树对象行", "B_清理后_场景树对象行", "C_新建后_场景树对象行",
                  "E_删除后_场景树对象行", "F_★跨刷新后_场景树对象行"):
            print("%-26s %s" % (k, out.get(k)))
        for k in ("A_★进站_行数", "B_★遗留角色B候选数", "B_★是否清掉遗留的",
                  "C_★新建后_行数", "C_★★行数增量", "C_★★前提_真新增了一行",
                  "C_★新增行的文本", "D_★读到的默认名", "D_★★实验是否有效",
                  "E_★是否点了删除", "E_★删除后_行数", "F_★跨刷新后_行数",
                  "F_★跨刷新后还剩新建的", "F_★★是否已复原"):
            print("%-26s %r" % (k, out.get(k)))
        print("  右栏标题 =", out.get("D_右栏标题"))
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()
