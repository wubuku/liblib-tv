#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 864 源站探针：**D17 复核**（源站到底把比例／参考线写进机位对象了吗？）

## ★ 靶子

★ batch 862 登记了 **D17**：「源站把比例与 `reference_line` **写进机位对象**」。
★ 那条登记的依据是 chunk 里这两处：

```js
// 右侧面板选比例：
o$ = useCallback(e => { tn(e);
  let t = e1 || rL.cameras[0]?.id;
  t && n4(t, "aspect_ratio", (0,nZ.R)(e), "right_panel"); }, [e1, rL.cameras, n4])

// 框上开关切参考线：
onToggleCompositionGrid: null !== tr ? () => {
  let e = !ti, t = e1 || rL.cameras[0]?.id;
  t && n4(t, "reference_line", (0,nZ.p)(e), "right_panel"), to(e); } : void 0
```

★ ★ **但 `n4` 的定义是**：

```js
n4 = useCallback((e,t,r,n) => {
  (0,nZ.S)("libtv.canvas.director.camera.update", {
    director_session_id: nb.current, camera_uuid: e,
    setting_name: t, setting_value: r, operation_source: n })
}, [])
```

⟹ ⟹ **`n4` 只是发一条埋点**（`nZ.S(事件名, 属性)`），
⟹ ⟹ **它到底只是「上报」，还是「通过接口把字段写进服务端的机位对象」，
必须用运行时取证来定性** ⟹ ⟹ 本探针就是干这个的。

★ 另一条**静态**反证：整个 chunk（1,018,130 字符）里
  **`reference_line` 只出现 1 次**（就在上面那条埋点里）
  ⟹ ⟹ 它**不可能**是机位对象上被读写的字段。

## ★ 本探针要读到的

① **点「16:9」时源站实际发出的请求**：URL／方法／body
   ⟹ ⟹ 里���有没有 `aspect_ratio`？是**埋点**还是**工程状态写入**？
② ★ **点框上那枚「构图参考线」时**同样记一遍（找 `reference_line`）；
③ 源站**是否把机位对象暴露在 window 上**（`__` 前缀的全局变量）
   ⟹ ⟹ 有的话就能直接读机位对象的字段，做**存储侧**的正面取证；
④ ★ 顺带把 **batch 863 的源站运行时遮罩读数**补齐（源站已恢复）。

## ★ 副作用声明

★ 只点「画幅比例」与框上那枚参考线开关 ⟹ ⟹ 本地视图态；
  **绝不点**「AI生成」「本地上传」「截图」「导出」⟹ ⟹ 不产生付费或生图动作。

## 输出
  raw/source-864-camera-write.json
"""
from __future__ import annotations

import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch864-2026-10-01"
RAW = BATCH / "raw"
COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 读源站 window 上的「__」前缀全局（看有没有暴露机位对象）
READ_GLOBALS = r"""()=>{
  const out={};
  try{
    out.双下划线全局=Object.keys(window).filter(k=>k.startsWith('__')).slice(0,80);
  }catch(e){ out.双下划线全局=['读失败']; }
  try{
    const st=window.__director_store || window.__libtv_store;
    out.store在场=!!st;
    if(st && typeof st.getState==='function'){
      const s=st.getState();
      out.state键=Object.keys(s).slice(0,120);
      if(s.cameras) out.机位=s.cameras.map(c=>({id:c.id,
        键:Object.keys(c), aspect_ratio:c.aspect_ratio,
        reference_line:c.reference_line}));
    }
  }catch(e){ out.store读失败=String(e).slice(0,200); }
  return out;
}"""

# ★ 读框上那枚「构图参考线」按钮
READ_TOGGLE = r"""()=>{
  const b=[...document.querySelectorAll('button')]
    .find(e=>e.getAttribute('title')==='构图参考线'
           || e.getAttribute('aria-label')==='构图参考线');
  if(!b) return {按钮在场:false};
  const r=b.getBoundingClientRect();
  return {按钮在场:true, title:b.getAttribute('title'),
          aria:b.getAttribute('aria-label'),
          rect:{x:Math.round(r.x),y:Math.round(r.y),
                w:Math.round(r.width),h:Math.round(r.height)},
          pressed:b.getAttribute('aria-pressed')};
}"""


def load_cookies(page) -> None:
    data = json.loads(COOKIE.read_text(encoding="utf-8"))
    cookies = data if isinstance(data, list) else data.get("cookies", [])
    page.context.add_cookies([
        {"name": c["name"], "value": c["value"], "domain": c["domain"],
         "path": c.get("path", "/")}
        for c in cookies if c.get("name")
    ])


def main() -> int:
    audit: dict = {"batch": 864, "probe": "source864_camera_write"}
    reqs: list[dict] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080})

            def on_request(req):
                try:
                    body = req.post_data
                except Exception:  # noqa: BLE001
                    body = None
                reqs.append({
                    "method": req.method,
                    "url": req.url[:400],
                    "postData": (body or "")[:2000],
                    "resourceType": req.resource_type,
                    "时间": req.timing.get("responseEnd") if req.timing else None,
                })

            page.on("request", on_request)
            load_cookies(page)
            page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(6_000)
            audit["全局"] = page.evaluate(READ_GLOBALS)
            page.locator(".react-flow__node-director-console-3d").first.hover()
            page.wait_for_timeout(600)
            page.locator(".react-flow__node-director-console-3d "
                         "button:has-text('打开导演台')").first.click()
            page.wait_for_timeout(8_000)

            # ── ① 点「16:9」，看发出了什么 ──
            mark_ratio = len(reqs)
            page.locator("[aria-label='选择画幅比例'], button:has-text('选择画幅比例')"
                         ).first.click(timeout=15_000)
            page.wait_for_timeout(1_500)
            page.locator("button:has-text('16:9')").first.click(timeout=15_000)
            page.wait_for_timeout(3_000)
            audit["选比例后的请求"] = reqs[mark_ratio:]
            audit["选比例后的全局"] = page.evaluate(READ_GLOBALS)
            audit["开关"] = page.evaluate(READ_TOGGLE)

            # ── ② 点框上那枚「构图参考线」，再看一次 ──
            toggle = page.locator("button[title='构图参考线'], "
                                  "button[aria-label='构图参考线']").first
            mark_toggle = len(reqs)
            if toggle.count() == 1:
                toggle.click(timeout=15_000)
                page.wait_for_timeout(3_000)
                audit["切参考线后的请求"] = reqs[mark_toggle:]
                audit["切参考线后的全局"] = page.evaluate(READ_GLOBALS)
                audit["切参考线后开关"] = page.evaluate(READ_TOGGLE)
            else:
                audit["切参考线后的请求"] = []
                audit["切参考线说明"] = f"★ 框上那枚按钮没找到（count={toggle.count()}）"

            audit["全程请求数"] = len(reqs)
            # ★ 只留**有 body** 的请求（埋点/写入请求才有 body）
            audit["带body的请求"] = [
                r for r in reqs if r.get("postData")
            ]
        except Exception:
            audit["异常"] = traceback.format_exc()[-2000:]
        finally:
            browser.close()

    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "source-864-camera-write.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=1)[:6000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
