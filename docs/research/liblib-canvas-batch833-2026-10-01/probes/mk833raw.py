#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 833：把源站 15 枚机位预设的**语义**读数整理成 raw（门禁的期望值来源）。

★ 为什么要单独成型：batch 832 只落了**呈现**（几何/文字/path），
  语义（位置/旋转/注视/FOV）是 batch 833 才逐枚实测的 ⟹ 必须单独入库。

★ ★ 机器整理（不手打）：本脚本从活体读数 JSON 里**程序化**抽出 15 组数值
  ⟹ 门禁 S7 的期望值来自这份 raw ⟹ 不是我手抄的。

★ ★ ★ 本版（batch 833）改用**规则 R**（按字段标题分组）作为**唯一**入库口径：
  - 旧版是「把所有 number 输入按 y 升序拼起来 → 切 [0:3]/[3:6]/[6:9]」；
  - ★ 那条切法**只在源站成立**（源站没有「缩放」行）⟹ clone 多一行「缩放」⟹ 索引就错位了
  ⟹ ⟹ 两边不可比。
  ⟹ 新口径 = probes/reader833.py 的规则 R（位置/旋转/注视坐标**各按标题分组**，FOV 按标题下的 range）。

★ ★ ★ 双路交叉校验（本脚本会**自己**核对，不一致就**拒绝出 raw**）：
  路①：规则 R 按标题分组 ⟹ 位置/旋转/注视；
  路②：旧口径的 y 升序索引切片；
  ⟹ 两路必须**逐字段相等** ⟹ 否则说明「切片」或「分组」有一个是错的 ⟹ 停。
  另加一路：FOV 与**粘性预览角标**「FOV nn°」的文字独立比对（源站 DOM 实测有这枚角标）。

★ 每一组的字段：
    位置 [x,y,z] / 旋转 [x,y,z]（度）/ 注视 [x,y,z] / FOV（度）

## 用法

    python3 mk833raw.py <活体读数JSON> <输出raw路径>
"""
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from reader833 import semantics_from_capture  # noqa: E402

DEFAULT_IN = pathlib.Path("/tmp/liblib_source_desk833_presets.json")
DEFAULT_OUT = (pathlib.Path(__file__).resolve().parent.parent
               / "raw" / "source-833-camera-preset-semantics.json")


def _badge_fov(props):
    """源站粘性预览角标「FOV nn°」里的数字（DOM 实测：DIV x=1669 y=134）。"""
    for lab in props.get("labels") or []:
        t = (lab.get("t") or "").strip()
        if t.startswith("FOV ") and t.endswith("°"):
            try:
                return float(t[4:-1])
            except ValueError:
                return None
    return None


def main():
    src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_IN
    out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT
    if not src.exists():
        raise SystemExit("找不到活体读数：%s" % src)
    doc = json.loads(src.read_text(encoding="utf-8"))
    sem = doc.get("④预设语义") or []
    if len(sem) != 15:
        raise SystemExit("预设语义条目数不对：%d（期望 15）" % len(sem))

    presets = []
    mismatches = []
    for p in sem:
        props = p.get("props") or {}
        nums = [x.get("value") for x in (props.get("nums") or [])]
        if len(nums) != 9:
            raise SystemExit("#%s 的 number 输入框只有 %d 个（期望 9）"
                             % (p.get("label"), len(nums)))
        # 路①：规则 R
        grouped = semantics_from_capture(props)
        # 路②：旧口径索引切片（只作交叉校验，不作入库口径）
        sliced = {"位置": nums[0:3], "旋转": nums[3:6], "注视": nums[6:9],
                  "FOV": props.get("fov")}
        for key in ("位置", "旋转", "注视"):
            gv = [float(x) for x in grouped[key]]
            sv = [float(x) for x in sliced[key]]
            if gv != sv:
                mismatches.append("#%s %s：规则R=%s 切片=%s"
                                  % (p.get("label"), key, gv, sv))
        # FOV：与粘性角标独立比对
        badge = _badge_fov(props)
        fov = float(props.get("fov"))
        if badge is None or abs(badge - fov) > 1e-9:
            mismatches.append("#%s FOV：range=%s 角标=%s"
                              % (p.get("label"), props.get("fov"), badge))
        presets.append({
            "idx": p.get("idx"),
            "label": p.get("label"),
            "位置": grouped["位置"],
            "旋转": grouped["旋转"],
            "注视": grouped["注视"],
            "FOV": grouped["FOV"],
            "新建机位名": p.get("新建机位名"),
        })

    if mismatches:
        raise SystemExit("双路交叉校验失败（拒绝出 raw）：\n  "
                         + "\n  ".join(mismatches))

    result = {
        "来源": "源站导演台 rail「添加机位」→ 15 枚机位预设，**逐枚**点开后的"
                "右栏机位属性读数",
        "采集方式": "probes/presets833.py 逐枚实测（点开 → 读右栏 → 切回场景 → "
                    "按名字删掉 → 复验少了一台）⟹ 本脚本**程序化**整理成 raw "
                    "⟹ 门禁 S7 的期望值来自这份 raw，不是手抄的",
        "★读数口径": "**规则 R**（probes/reader833.py）：按**字段标题**分组 —— "
                    "「位置」「旋转」「注视坐标」各自取其标题下方 60px 内、"
                    "同一行的 3 个 number 输入（按 x 升序）；"
                    "FOV 取「视野角度 (FOV)」标题下方 60px 内的第一个 range",
        "★为什么不用 y 升序索引切片": "那条只在源站成立（源站没有「缩放」行）"
                    "⟹ clone 的 Inspector **多一行「缩放」** ⟹ 索引会整体错位 ⟹ 两边不可比",
        "★双路交叉校验": "入库前逐枚核对：规则 R 的分组结果 vs 旧口径索引切片 "
                        "（位置/旋转/注视），且 FOV 与源站粘性预览角标「FOV nn°」"
                        "独立比对 ⟹ 15 枚全部一致 ⟹ 不一致则本脚本拒绝出 raw",
        "★双路交叉校验结果": {
            "枚数": len(presets),
            "比对字段": ["位置", "旋转", "注视"],
            "FOV独立比对": "源站粘性预览角标「FOV nn°」",
            "全部一致": True,
        },
        "★为什么逐枚测而不是「测一枚推 15 枚」": "batch 832 只测了「正面中景」"
                        "（位置 (0,1.5,4) / 旋转 (4.29,180,0) / FOV 50 / 注视 (0,1.2,0)）"
                        "⟹ ★ 「俯拍全景」的 FOV 是 55、「低角度广角」是 70、"
                        "「正面特写」是 35 ⟹ **差异很大** ⟹ 不凭一枚推 15 枚",
        "★副作用与复原": "点预设会**真的新建机位** ⟹ 每枚测完**立刻删掉**并复验"
                        "（删除日志 15 条「2 → 1 台 ✔」）⟹ "
                        "末次树只剩「机位1」⟹ **全新浏览器 context 复验** ✔",
        "活体读数文件": str(src),
        "活体读数_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
        "基线树": doc.get("①基线树"),
        "末次树": doc.get("末次树"),
        "删除日志": doc.get("删除日志"),
        "预设项数": len(presets),
        "预设": presets,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已落盘：", out)
    print("预设项数：", len(presets))
    print("双路交叉校验：15/15 一致 ✔")
    for p in presets:
        print("  #%2d %-12s 位置=%s 旋转=%s 注视=%s FOV=%s"
              % (p["idx"], p["label"], p["位置"], p["旋转"], p["注视"], p["FOV"]))


if __name__ == "__main__":
    main()
