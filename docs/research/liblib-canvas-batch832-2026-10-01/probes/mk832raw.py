#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 832：把源站「添加机位」机位预设面板的读数**落成 raw 证据**。

★ 为什么这份 raw 要单独成型：
  - 源站的 15 项机位预设**不在任何静态 chunk 里**（见 README §2.2）⟹
    唯一可靠来源是**活体 DOM** ⟹ raw 就是活体读数；
  - ★ 而 raw 里带着**每格的 SVG path 原文** ⟹ clone 可以逐字复现图标，
    门禁也能核验「clone 的图标 == 源站的图标」（而不是我手抄的）。

★ 机器提取（不手打）：本脚本从活体读数 JSON 里**程序化**整理成
  `raw/source-832-camera-presets.json` ⟹ 门禁 S3 的期望值来自它，
  不是来自我手打的清单。

## 用法

    python3 mk832raw.py <活体读数JSON> <输出raw路径>
"""
import hashlib
import json
import pathlib
import sys

DEFAULT_IN = pathlib.Path("/tmp/liblib_source_desk832_camera2.json")
DEFAULT_OUT = (pathlib.Path(__file__).resolve().parent.parent
               / "raw" / "source-832-camera-presets.json")


def main():
    src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_IN
    out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT
    if not src.exists():
        raise SystemExit("找不到活体读数：%s" % src)
    doc = json.loads(src.read_text(encoding="utf-8"))
    panel = doc.get("①机位预设面板") or {}
    if not panel.get("found"):
        raise SystemExit("活体读数里没有面板（found=%r）" % panel.get("found"))

    cells = panel.get("cells") or []
    presets = []
    for c in cells:
        d = c.get("pathD") or ""
        presets.append({
            "idx": c.get("idx"),
            "label": c.get("t"),
            "box": c.get("box"),
            "svgBox": c.get("svgBox"),
            "svgViewBox": c.get("svgViewBox"),
            "svgCls": c.get("svgCls"),
            "pathD": d,
            "pathStroke": c.get("pathStroke"),
            "pathStrokeWidth": c.get("pathStrokeWidth"),
            "pathFill": c.get("pathFill"),
            "spanBox": c.get("spanBox"),
            "spanCls": c.get("spanCls"),
            # ★ 源站第 0 格（「当前视角」）的边框更亮（border-white/85），
            #   其余是 border-white/10 ⟹ 记下来，别靠眼睛分辨。
            "borderBright": "border-white/85" in (c.get("cls") or ""),
        })

    # ★ 图标去重：15 格里如果 path 全同 ⟹ 记「共用一枚图标」
    uniq = sorted({p["pathD"] for p in presets})
    result = {
        "来源": "源站导演台 rail「添加机位」点开后的机位预设面板（活体 DOM 读数）",
        "采集方式": "probes/camera832b.py 活体读数 ⟹ 本脚本**程序化整理**成 raw "
                    "⟹ 门禁的期望值来自这份 raw，不是手打的清单",
        "★为什么只能活体": "15 项预设**不在**任何静态 chunk 里（导演台 chunk "
                          "里是 `eo.map(...)`；i18n 字典 chunk 里搜 12 个中文名"
                          "**全部 -1**）⟹ 走服务端下发 ⟹ 唯一可靠来源是 DOM",
        "活体读数文件": str(src),
        "活体读数_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
        "面板": {
            "box": panel.get("panelBox"),
            "cls": panel.get("panelCls"),
            "title": panel.get("title"),
            "gridBox": panel.get("gridBox"),
            "gridCls": panel.get("gridCls"),
            "gridTemplateColumns": panel.get("gridTemplateColumns"),
        },
        "预设项数": len(presets),
        "预设": presets,
        "唯一图标path数": len(uniq),
        "★图标是共用的": len(uniq) == 1,
        "唯一图标path": uniq[0] if len(uniq) == 1 else None,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已落盘：", out)
    print("预设项数：", len(presets))
    print("唯一图标 path 数：", len(uniq), "（共用一枚）" if len(uniq) == 1 else "")
    print("标签：", " / ".join(p["label"] for p in presets))


if __name__ == "__main__":
    main()
