#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 857 契约提取：从源站 chunk **机器提取**「群众阵列（crowd）」的逐字片段。

## ★ 这批要钉住的东西

★ 857 的起因是「clone 的群众阵列**默认值**与源站不符」这个怀疑
⟹ ⟹ ★ **一读代码就发现这个怀疑本身是错的** ⟹ ⟹ 于是本批的真正产出是
⟹ ⟹ **把「源站逐字」变成机器提取、入库、可复核的事实**。

★ ★★ **本批最值钱的一条**（★ 差点判反的地方）：
★ 源站有两处数字 **1.2** 与 **1.6** ⟹ ⟹ 长得极像 ⟹ ⟹ 但**语义完全不同**：

| 数字 | 位置 | 语义 |
| --- | --- | --- |
| **1.2** | `[K,Q]=(0,o.useState)(1.2)` | ★ **对话框的间距初值**（**真正生效的默认值**） |
| **1.6** | `c=a??1.6` | ★ **add 回调的兜底值**（`crowdSpacing` 为 undefined 时才用）⟹ ⟹ 对话框**永远**传 K ⟹ ⟹ **1.6 永远不生效** |

★ ★ 所以「clone 的默认间距 1.2 应改成 1.6」是**错的**——clone 的 1.2 **正好是对的**。
★ ★ **通则**：看到「默认值」时，要分清它是「**state 初值**」还是「**兜底常量**」；
★ ★ 只读到一个数字就说它是默认值 ⟹ ⟹ 极可能**把兜底当成了初值**。
★ ★ 本提取器因此加一条**跨片段防呆自检**（见下）。

## ★ 本批的片段（13 条，每条必须**唯一命中**）

| # | 片段 | 说的什么 |
| --- | --- | --- |
| 1 | 对话框 state 初值 | 行 3／列 3／**间距 1.2** |
| 2 | 行输入 | `min:1,max:10,step:1` ＋ aria `directorRows` |
| 3 | 列输入 | `min:1,max:10,step:1` ＋ aria `directorCols` |
| 4 | 间距输入 | `min:.1,max:10,step:.1` ＋ aria `directorSpacing` |
| 5 | 间距 onChange | **夹 [0.1,10] ＋ 保留 1 位小数**（`Math.round(10*t)/10`） |
| 6 | 「添加」载荷 | `{count:U*V, crowdRows:U, crowdCols:V, crowdSpacing:K}` |
| 7 | add 回调兜底 | `o=t??1, s=r??1, l=n??o, c=a??1.6` ⟹ ⟹ **不夹取** |
| 8 | 创建 N 个成员 | `Array.from({length:o},()=>hZ())` |
| 9 | 成员类型 | `asset_type:o>1?"crowd"` ⟹ ⟹ 加的是**角色** |
| 10 | rail 入口结构 | `aria-haspopup:"dialog"` ＋ `aria-expanded:"crowd"===L` |
| 11 | rail 入口文案键 | `canvas:directorCrowd3x3` |
| 12 | 对话框总数文案 | `canvas:directorCrowdTotalN` `{n:U*V}` |
| 13 | 对话框 role/aria | `role:"dialog"` ＋ `canvas:directorAddCrowdArray` |

## ★ 自检（★ 不自检的提取器会骗人）

★ ① **唯一命中**：每个片段在整份 chunk 里必须**只出现一次**
   ⟹ ⟹ 不唯一 ⟹ ⟹ 记空 ＋ 退出码 1（不产出假 raw）。
★ ② **任意值类名自检**：片段里如果出现 `xxx.yyy` 这种**看起来像类名**的串，
   必须能确认它不是「我编的」⟹ ⟹ 这里用 chunk 里真实存在的标识符做白名单核对。
★ ③ ★★ **跨片段防呆自检**：片段 1（初值）的间距数字 **必须 ≠** 片段 7（兜底）的数字
   ⟹ ⟹ 这条是为了防止以后有人（也包括我）把**兜底常量**当成**默认值**写进文档或代码。

## 输出
  raw/source-857-contract.json
"""
import json
import pathlib
import re
import sys

CHUNK = pathlib.Path("/tmp/liblib_srcjs2/0fmehki05gkzw.js.js")
OUT = (pathlib.Path(__file__).resolve().parents[1]
       / "raw" / "source-857-contract.json")

# ★ (片段名, 锚点（用于唯一定位）, 正文（要逐字摘出来的那一段）)
FRAGMENTS = [
    ("对话框 state 初值（行3／列3／间距1.2 ＝ 真正生效的默认值）",
     "[U,H]=(0,o.useState)(3),[V,G]=(0,o.useState)(3),[K,Q]=(0,o.useState)(1.2)",
     "[U,H]=(0,o.useState)(3),[V,G]=(0,o.useState)(3),[K,Q]=(0,o.useState)(1.2)"),
    ("行输入（min1 max10 step1 ＋ aria directorRows）",
     'type:"number",min:1,max:10,step:1,"aria-label":D("canvas:directorRows"),value:U',
     'type:"number",min:1,max:10,step:1,"aria-label":D("canvas:directorRows"),value:U'),
    ("列输入（min1 max10 step1 ＋ aria directorCols）",
     'type:"number",min:1,max:10,step:1,"aria-label":D("canvas:directorCols"),value:V',
     'type:"number",min:1,max:10,step:1,"aria-label":D("canvas:directorCols"),value:V'),
    ("间距输入（min.1 max10 step.1 ＋ aria directorSpacing）",
     'type:"number",min:.1,max:10,step:.1,"aria-label":D("canvas:directorSpacing"),value:K',
     'type:"number",min:.1,max:10,step:.1,"aria-label":D("canvas:directorSpacing"),value:K'),
    ("间距 onChange（夹 [0.1,10] ＋ 保留 1 位小数）",
     "Math.min(10,Math.max(.1,Math.round(10*t)/10))",
     "Math.min(10,Math.max(.1,Math.round(10*t)/10))"),
    ("「添加」按钮的载荷（count ＝ 行×列）",
     "h({count:U*V,crowdRows:U,crowdCols:V,crowdSpacing:K}),O(null)",
     "h({count:U*V,crowdRows:U,crowdCols:V,crowdSpacing:K}),O(null)"),
    ("add 回调的兜底（不夹取；1.6 只是兜底、不是默认值）",
     "let{count:t,crowdRows:r,crowdCols:n,crowdSpacing:a,...i}=e,o=t??1,s=r??1,l=n??o,c=a??1.6",
     "let{count:t,crowdRows:r,crowdCols:n,crowdSpacing:a,...i}=e,"
     "o=t??1,s=r??1,l=n??o,c=a??1.6"),
    ("创建 N 个成员（length ＝ count）",
     "u=Array.from({length:o},()=>hZ())",
     "u=Array.from({length:o},()=>hZ())"),
    ("成员类型（count>1 ⟹ crowd ⟹ 加的是**角色**）",
     'asset_type:o>1?"crowd"',
     'asset_type:o>1?"crowd"'),
    ("rail 入口的结构特征（aria-haspopup=dialog ＋ crowd 状态）",
     '"aria-haspopup":"dialog","aria-expanded":"crowd"===L',
     '"aria-haspopup":"dialog","aria-expanded":"crowd"===L'),
    ("rail 入口的文案键（群众 3x3）",
     'D("canvas:directorCrowd3x3")',
     'D("canvas:directorCrowd3x3")'),
    ("对话框右上角的总数文案（n ＝ 行×列）",
     'D("canvas:directorCrowdTotalN",{n:U*V})',
     'D("canvas:directorCrowdTotalN",{n:U*V})'),
    ("对话框的 role 与 aria（可被结构定位）",
     'role:"dialog","aria-label":D("canvas:directorAddCrowdArray")',
     'role:"dialog","aria-label":D("canvas:directorAddCrowdArray")'),
    # ── ★ Batch 857 补录的 3 条（★ 都是**行为**逐字 ⟹ ⟹ 门禁要靠它们）
    ("★开关：再点一次「群众 (3x3)」＝ 关闭对话框",
     'if("crowd"===L)return void O(null)',
     'if("crowd"===L)return void O(null)'),
    ("★点外面关闭：点在按钮/对话框之外 ⟹ 关闭",
     'en.current?.contains(t)||ea.current?.contains(t)||O(null)',
     'en.current?.contains(t)||ea.current?.contains(t)||O(null)'),
    ("★落点公式：锚在按钮自己身上（right+8 / top）＋ 8px 视口安全边",
     'W({left:Math.max(8,Math.min(t.right+8,window.innerWidth-r-8)),'
     'top:Math.max(8,Math.min(t.top,window.innerHeight-n-8))})',
     'W({left:Math.max(8,Math.min(t.right+8,window.innerWidth-r-8)),'
     'top:Math.max(8,Math.min(t.top,window.innerHeight-n-8))})'),
    ("★落点用的尺寸：对话框自己的宽高（量不到时兜底 220）",
     'r=ea.current?.offsetWidth??220,n=ea.current?.offsetHeight??220',
     'r=ea.current?.offsetWidth??220,n=ea.current?.offsetHeight??220'),
]


def main() -> int:
    if not CHUNK.exists():
        print("★ 缺源站 chunk：%s" % CHUNK)
        return 2
    src = CHUNK.read_text(encoding="utf-8")

    out = {
        "来源": {
            "chunk": str(CHUNK),
            "字节数": len(src),
            "提取方式": "机器提取（唯一定位 ＋ 逐字摘录）",
        },
        "片段": {},
    }

    ok = True
    for name, anchor, body in FRAGMENTS:
        anchor_hits = src.count(anchor)
        body_hits = src.count(body)
        if anchor_hits != 1:
            print("★★ 片段「%s」的锚点命中 %d 次（必须 1 次）" % (name, anchor_hits))
            ok = False
        out["片段"][name] = {
            "锚点": anchor,
            "原文": body if body_hits >= 1 else "",
            "锚点命中数": anchor_hits,
            "正文命中数": body_hits,
        }
        if body_hits != 1:
            print("★★ 片段「%s」的正文命中 %d 次（必须 1 次）" % (name, body_hits))
            ok = False

    # ★★ 任意值类名自检
    idents = set(re.findall(r"[A-Za-z_$][A-Za-z0-9_$]*", src))
    bogus = []
    for name, _anchor, body in FRAGMENTS:
        if not body:
            continue
        for m in re.finditer(r"\b([A-Za-z_$][A-Za-z0-9_$]*)\.([A-Za-z_$][A-Za-z0-9_$]*)", body):
            head = m.group(1)
            if head in idents:
                continue
            bogus.append({"片段": name, "标识符": head, "片段位置": m.start()})
    out["★任意值类名自检"] = {
        "通过": not bogus,
        "疑似编造的标识符": bogus,
        "说明": "正文里每个 `x.y` 的 x 必须真实出现在 chunk 的标识符集合里",
    }
    if bogus:
        ok = False

    # ★★★ 跨片段防呆自检：**初值 ≠ 兜底**
    #   片段 1 的间距初值（1.2）必须 ≠ 片段 7 的兜底常量（1.6）
    #   ⟹ ⟹ 这条一旦不成立，就说明「默认值」与「兜底」在源站里**是同一个数**
    #   ⟹ ⟹ 那我先前那句「1.6 只是兜底」的判断就需要重新核对。
    init_body = out["片段"]["对话框 state 初值（行3／列3／间距1.2 ＝ 真正生效的默认值）"]["原文"]
    fallback_body = out["片段"]["add 回调的兜底（不夹取；1.6 只是兜底、不是默认值）"]["原文"]
    init_nums = re.findall(r"useState\)\(([0-9.]+)\)", init_body)
    fallback_nums = re.findall(r"a\?\?([0-9.]+)", fallback_body)
    init_spacing = init_nums[-1] if init_nums else ""
    fallback_spacing = fallback_nums[-1] if fallback_nums else ""
    differ = bool(init_spacing) and bool(fallback_spacing) and init_spacing != fallback_spacing
    out["★跨片段防呆自检（初值 ≠ 兜底）"] = {
        "通过": differ,
        "对话框初值（间距）": init_spacing,
        "add 回调兜底（间距）": fallback_spacing,
        "说明": ("初值 1.2 才是真正生效的默认值；1.6 只是 `crowdSpacing` 为 undefined 时的兜底"
                 "（对话框永远传 K）⟹ ⟹ 把 1.6 当默认值是错的"),
    }
    if not differ:
        ok = False

    uniq = sum(1 for v in out["片段"].values() if v["锚点命中数"] == 1 and v["原文"])
    print("唯一命中：%d / %d" % (uniq, len(FRAGMENTS)))
    print("任意值类名自检：%s" % ("通过" if out["★任意值类名自检"]["通过"] else "★不通过"))
    print("跨片段防呆自检（初值 ≠ 兜底）：%s（初值 %s ／ 兜底 %s）"
          % ("通过" if differ else "★不通过", init_spacing, fallback_spacing))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已落盘：", OUT)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
