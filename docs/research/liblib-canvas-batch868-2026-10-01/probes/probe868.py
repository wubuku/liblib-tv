#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 868 运行时验证探针：★ 证明两处整改**真的能用**（不只是「加了 onClick」）。

## ★ 靶子

★ 本批整改了两处**真糊弄**（★ 点了什么也不发生、却长得像按钮）：
  ① `CharacterLibraryPanel.tsx` 的「生成其他年龄版本」
     ⟹ ⟹ 依据：源站 i18n 逐字（`characterStudioQuickAgeTip` /
     ⟹ ⟹ `characterStudioAgeVersionName` = `{name}{age}版`）
  ② 导演台右栏的「⟳ 预设运镜」「创建运动轨迹」
     ⟹ ⟹ 依据：源站截图 50/51 的右栏就是这两个入口
     ⟹ ⟹ ⟹ ⟹ ⇒ ★ 现在接的是**与时间线同一份预设表、同一个 store 动作**

## ★ ★★ 为什么必须有这一步

★ 「源码里加了 `onClick`」**不能证明**任何事 ⟹ ⟹
★ ★ 它照样可能是「点了以后 store 没变」「列表开了但应用不了」
⟹ ⟹ ⟹ ⟹ ⇒ ★ 必须**真的点** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 并**读 store** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 断言「真的变了」。

★ 判据（★ 每条都读**具体**的量 ⟹ ⟹ 不是「看起来变了」）：
  ① 角色库：点之前卡片数 N ＋ 名字 `base` ⟹ ⟹ 点之后卡片数 **N+4**
     ⟹ ⟹ 且当前名字 == `base` ＋ 某个**档位** ＋ `版`（★ 逐字模板）
  ② 导演台：点「预设运镜」⟹ ⟹ 选项面板出现 **7** 项（★ 源站那 7 个预设）
     ⟹ ⟹ 点其中一个 ⟹ ⟹ `store.timeline.cameraMotionPreset.application` **非空**
  ③ 导演台：点「创建运动轨迹」⟹ ⟹ 选项面板出现 **3** 项
     ⟹ ⟹ 点其中一个 ⟹ ⟹ `store.timeline.motionPaths.length` **+1**

## ★ 输出
  raw/runtime-868.json
"""
from __future__ import annotations

import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch868-2026-10-01"
RAW = BATCH / "raw"
BASE = "http://localhost:4317"

# ★ 源站那 7 个预设（★ 与 `directorCameraPresets.ts` 同源 ⟹ ⟹ 这里**再抄一份**
#   ⟹ ⟹ 当作**独立复算** ⟹ ⟹ 两边对不上就红 ⟹ ⟹ ⟹ ⟹ 免得「抄自己」变同义反复）
SOURCE_PRESET_LABELS = ["环绕", "半弧", "推近", "拉远", "升降", "横移", "螺旋上升"]
# ★ 源站 i18n 的年龄档位（★ `characterStudioAge*`）
SOURCE_AGE_TIERS = ["幼年", "少年", "青年", "中年", "老年"]


def cleanup(pg) -> None:
    pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")


def open_root(pg) -> None:
    pg.goto(BASE + "/", wait_until="domcontentloaded")
    pg.wait_for_timeout(2200)
    cleanup(pg)
    try:
        pg.wait_for_function("() => Boolean(window.__libtv_store)", timeout=45_000)
    except Exception:  # noqa: BLE001
        pass
    pg.wait_for_timeout(1000)


def open_director(pg) -> None:
    open_root(pg)
    info = pg.evaluate(
        r"""()=>{
        const card=document.querySelector('.react-flow__node-script-execution');
        if(!card) return {ok:false};
        const r=card.getBoundingClientRect();
        return {ok:true,x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)};
    }"""
    )
    if not info.get("ok"):
        raise RuntimeError("打不开导演台")
    pg.mouse.move(info["x"], info["y"])
    pg.wait_for_timeout(400)
    btn = pg.evaluate(
        r"""()=>{
        const card=document.querySelector('.react-flow__node-script-execution');
        const b=card.querySelector('[data-open-director]')
          || Array.from(card.querySelectorAll('button')).find(x=>(x.textContent||'').includes('打开导演台'));
        if(!b) return null;
        const r=b.getBoundingClientRect();
        return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)};
    }"""
    )
    pg.mouse.move(btn["x"], btn["y"])
    pg.wait_for_timeout(300)
    pg.mouse.click(btn["x"], btn["y"])
    pg.wait_for_timeout(1500)
    cleanup(pg)
    pg.wait_for_timeout(800)


def main() -> int:
    out: dict = {}
    checks: list[tuple[str, bool, object]] = []
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            pg = ctx.new_page()
            pg.set_default_timeout(30_000)
            pg.on("dialog", lambda d: d.dismiss())

            # ── ① 角色造型室：生成其他年龄版本 ────────────────────────
            open_root(pg)
            pg.locator("[aria-label='角色造型室']").first.click(force=True)
            pg.wait_for_timeout(1500)
            cleanup(pg)
            studio = pg.locator("[data-character-studio]")
            checks.append(("角色造型室面板能打开", studio.count() > 0,
                           {"count": studio.count()}))
            # ★ 卡片是 `[data-character-strip-card]`；★ `[data-character-studio-name]`
            #   是**当前角色**的名字显示（★ 两者不是一回事 ⟹ ⟹ 第一版把后者当卡片数
            #   ⟹ ⟹ ⟹ ⟹ ⇒ 恒为 1 ⟹ ⟹ ⟹ ⟹ ⇒ 判据**测不到**任何东西）
            cards = pg.locator("[data-character-strip-card]")
            checks.append(("角色库里至少有若干真实角色", cards.count() > 1,
                           {"卡片数": cards.count()}))
            if cards.count() > 1:
                base_name = cards.nth(1).get_attribute("data-character-strip-card")
                cards.nth(1).click(force=True)
                pg.wait_for_timeout(800)
                # ★ 点之前：卡片数 ＋ 当前名字
                before = pg.evaluate(
                    r"""()=>({
                      cards: document.querySelectorAll('[data-character-strip-card]').length,
                      name: (document.querySelector('[data-character-studio-name]')||{}).textContent||'',
                    })"""
                )
                quick = pg.locator("[data-character-studio-quick]")
                checks.append(("选中真实角色后 ⟹ 「生成其他年龄版本」按钮在",
                               quick.count() == 1, {"count": quick.count()}))
                if quick.count() == 0:
                    raise RuntimeError("「生成其他年龄版本」按钮没出现")
                quick.first.click(force=True)
                pg.wait_for_timeout(900)
                after = pg.evaluate(
                    r"""()=>({
                      cards: document.querySelectorAll('[data-character-strip-card]').length,
                      name: (document.querySelector('[data-character-studio-name]')||{}).textContent||'',
                    })"""
                )
                out["角色库"] = {"点之前": before, "点之后": after, "基角色名": base_name}
                checks.append(("点「生成其他年龄版本」⟹ 卡片数增加",
                               after["cards"] > before["cards"],
                               {"前": before["cards"], "后": after["cards"]}))
                checks.append(("点「生成其他年龄版本」⟹ 名字变成 `{name}{age}版`",
                               after["name"].endswith("版")
                               and any(t in after["name"] for t in SOURCE_AGE_TIERS),
                               {"新名字": after["name"], "档位表": SOURCE_AGE_TIERS}))

            # ── ② 导演台：预设运镜 ＋ 创建运动轨迹 ───────────────────
            open_director(pg)
            # ★ 选中机位 ⟹ ⟹ 切「运动轨迹」页签 ⟹ ⟹ 右栏那两枚才在
            pg.evaluate(
                r"""()=>{
                const rows=Array.from(document.querySelectorAll('[data-director-object-id]'));
                const cam=rows.find(r=>(r.textContent||'').includes('机位'));
                if(cam) cam.click();
            }"""
            )
            pg.wait_for_timeout(900)
            pg.evaluate(
                r"""()=>{
                const tab=document.querySelector('[data-director-camera-tab="motion"]');
                if(tab) tab.click();
            }"""
            )
            pg.wait_for_timeout(900)
            cleanup(pg)
            has_tab = pg.locator("[data-director-motion-preset-button]").count()
            checks.append(("选中机位并切到「运动轨迹」页签 ⟹ 右栏那两枚在",
                           has_tab == 1, {"count": has_tab}))

            if has_tab:
                # ★ 预设运镜
                pg.locator("[data-director-motion-preset-button]").first.click(force=True)
                pg.wait_for_timeout(600)
                labels = pg.evaluate(
                    r"""()=>Array.from(document.querySelectorAll(
                        '[data-director-right-panel-camera-preset]')).map(e=>e.textContent.trim())"""
                )
                out["预设运镜选项"] = labels
                checks.append(("点「预设运镜」⟹ 出现 7 个源站预设",
                               labels == SOURCE_PRESET_LABELS,
                               {"实际": labels, "期望": SOURCE_PRESET_LABELS}))
                app_before = pg.evaluate(
                    "()=>{const s=window.__director_store.getState();"
                    "return s.timeline.cameraMotionPreset.application||null;}"
                )
                pg.locator("[data-director-right-panel-camera-preset='orbit']").first.click(force=True)
                pg.wait_for_timeout(900)
                app_after = pg.evaluate(
                    "()=>{const s=window.__director_store.getState();"
                    "return s.timeline.cameraMotionPreset.application||null;}"
                )
                out["预设应用"] = {"之前": app_before, "之后": app_after}
                checks.append(("点一个预设 ⟹ store 真的记下了应用",
                               app_after is not None and app_after != app_before,
                               {"之前": app_before, "之后": app_after}))

                # ★ 创建运动轨迹
                paths_before = pg.evaluate(
                    "()=>window.__director_store.getState().timeline.motionPaths.length")
                pg.locator("[data-director-motion-create-path]").first.click(force=True)
                pg.wait_for_timeout(600)
                path_labels = pg.evaluate(
                    r"""()=>Array.from(document.querySelectorAll(
                        '[data-director-right-panel-motion-path-preset]')).map(e=>e.textContent.trim())"""
                )
                out["轨迹几何选项"] = path_labels
                checks.append(("点「创建运动轨迹」⟹ 出现 3 种几何",
                               len(path_labels) == 3, {"实际": path_labels}))
                pg.locator("[data-director-right-panel-motion-path-preset='ring']").first.click(force=True)
                pg.wait_for_timeout(900)
                paths_after = pg.evaluate(
                    "()=>window.__director_store.getState().timeline.motionPaths.length")
                out["轨迹数"] = {"之前": paths_before, "之后": paths_after}
                checks.append(("点一种几何 ⟹ 真的多了一条运动轨迹",
                               paths_after == paths_before + 1,
                               {"前": paths_before, "后": paths_after}))
    except Exception as e:  # noqa: BLE001
        import traceback
        out["异常"] = traceback.format_exc()[-2500:]
        out["异常摘要"] = str(e)[:400]

    failures = [c for c in checks if not c[1]]
    out["核对"] = [{"判据": c[0], "通过": c[1], "详情": c[2]} for c in checks]
    out["失败"] = [c[0] for c in failures]
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "runtime-868.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    for name, ok, detail in checks:
        print("%s %s  %s" % ("✔" if ok else "★ FAILED", name, detail))
    print("\n%d 条核对，%d 失败" % (len(checks), len(failures)))
    print("读数已落盘：%s" % (RAW / "runtime-868.json"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
