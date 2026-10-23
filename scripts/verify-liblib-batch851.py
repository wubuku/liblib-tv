#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 851 门禁：导演台的**视图类快捷键**（T／Y／H／裸 WASDQE）。

## ★ 这批要守住的东西（源站实测 ＋ 源站 chunk 逐字实现）

★ 源站实测（`raw/source-851-*.json`）证明三件事：

1. **T（俯视视角）／Y（正面视角）／H（重置视角）都真的生效**
   （源站视口像素差分别为 1.4M／767K／153K）。
2. ★★ **WASDQE 必须「按住」** ⟹ ⟹ **单击（按下即松开）没有任何位移**。
   源站 chunk 的实现是：`oo` 只把键**登记进一个 Set**、位移在 `requestAnimationFrame`
   回调里算、`keyup` 把键删掉 ⟹ ⟹ 单击时键在下一帧前就被删了。
   ★ 前三版探针用 `keyboard.press` ⟹ ⟹ 读数全是 0 ⟹ ⟹ **那是探针口径错，不是源站没实现**。
3. **Shift 加速 ×3**（源站 `nW.current?3:1`）。

★ 源站 chunk 的逐字实现（`0fmehki05gkzw.js.js`）：

- `iK("top")` ⟹ `position = target + normalize(0,1,0.001) × |position−target|` ⟹ **只改方向、不改视距**
- `iK("front")` ⟹ 同上，方向 `(0,0,1)`
- `iK("default")` ⟹ 绝对默认位姿
- `H` ⟹ `eJ("director")` ＋ `iK("default")` ⟹ ⟹ **会先切到导演视角**
- `oi` 每帧 ⟹ `w→+forward, s→−forward, d→+right, a→−right, e→+up, q→−up`，
  `right = forward × up`（长度² < 1e-6 时兜底 `(1,0,0)`），
  步长 `1.2 × max(|camera.position − controls.target|, 0.5) × (Shift ? 3 : 1)`，
  `dt` 钳制 `[0, 0.05]` ⟹ ⟹ **相机与 orbit 中心同步平移**（视距不变）

## ★ 判据分工（★ 各条读的字段互不重叠）

| 判据 | 读什么 |
| --- | --- |
| S1 | clone 源码里的组件/函数/面板键帽**结构** |
| S2 | clone 源码里的**常量**（逐字对源站） |
| S3 | clone 读数 `②按T` |
| S4 | clone 读数 `③按Y` |
| S5 | clone 读数 `④按H` |
| S6 | clone 读数 `⑤单击W` |
| S7 | clone 读数 `⑥按住{W,A,E,Q}` 的**视距前后**与**方向点积** |
| S8 | clone 读数 `⑦按住Shift+W` 与 `⑥按住W` 的**位移长度** |
| S9 | **源站**读数（`source-851-pan.json` / `source-851-camkeys3.json`） |
"""
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BATCH = ROOT / "docs/research/liblib-canvas-batch851-2026-10-01"
RAW = BATCH / "raw"

SRC_VIEWPORT = ROOT / "src/components/director/DirectorViewport.tsx"
SRC_MATH = ROOT / "src/components/director/directorViewportMath.ts"
SRC_PANEL = ROOT / "src/components/director/DirectorShortcutsDialog.tsx"

# ★ 源站的默认位姿（clone 的 DEFAULT_DIRECTOR_VIEWPORT_SNAPSHOT）
DEFAULT_POSITION = (6.2, 4.25, 7.4)
DEFAULT_TARGET = (0.0, 1.0, 0.0)
DEFAULT_FOV = 45.0
# ★ 源站 `iK` 的方向向量（逐字）
PRESET_DIRECTIONS = {"top": (0.0, 1.0, 0.001), "front": (0.0, 0.0, 1.0)}

EPS_EXACT = 1e-9
EPS_PLAIN = 1e-6

results = []


def record(name, ok, detail):
    results.append({"判据": name, "通过": bool(ok), "详情": detail})
    print(("  PASS  " if ok else "  FAIL  ") + name + " ｜ " + detail)


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def scale(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def length(a):
    return math.sqrt(dot(a, a))


def norm(a, fallback=(0.0, 0.0, -1.0)):
    n = length(a)
    if n == 0:
        return fallback
    return (a[0] / n, a[1] / n, a[2] / n)


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def expect_preset(direction, position, target):
    """源站 `iK(preset)`：**只改方向、不改视距**"""
    d = PRESET_DIRECTIONS[direction]
    dist = length(sub(position, target))
    s = length(d) or 1.0
    return add(target, scale((d[0] / s, d[1] / s, d[2] / s), dist))


def close(a, b, eps):
    return abs(a - b) <= eps


def vec_close(a, b, eps):
    return all(abs(a[i] - b[i]) <= eps for i in range(3))


def main() -> int:
    clone = json.loads((RAW / "clone-851-viewkeys.json").read_text(encoding="utf-8"))
    src_pan = json.loads((RAW / "source-851-pan.json").read_text(encoding="utf-8"))
    src_cam = json.loads((RAW / "source-851-camkeys3.json").read_text(encoding="utf-8"))
    src_viewport = (SRC_VIEWPORT).read_text(encoding="utf-8")
    src_math = (SRC_MATH).read_text(encoding="utf-8")
    src_panel = (SRC_PANEL).read_text(encoding="utf-8")

    # ══ S1 结构
    need_viewport = [
        "DirectorViewShortcutController",
        "computeDirectorViewPanDelta",
        "getDirectorViewPresetPose",
        "DIRECTOR_VIEW_PAN_KEYS",
        # ★ 带等号 ⟹ ⟹ 精确到「属性赋值」⟹ ⟹ 否则 `data-director-view-position2`
        #   仍会被子串匹配命中 ⟹ ⟹ 阴性 N3 就没有牙了。
        "data-director-view-position=",
        "data-director-view-target=",
    ]
    miss_v = [k for k in need_viewport if k not in src_viewport]
    need_math = [
        "DIRECTOR_VIEW_PAN_SPEED",
        "DIRECTOR_VIEW_PAN_MIN_DISTANCE",
        "DIRECTOR_VIEW_PAN_SHIFT_MULTIPLIER",
        "DIRECTOR_VIEW_PAN_MAX_DELTA_SECONDS",
        "DIRECTOR_VIEW_PRESET_DIRECTIONS",
    ]
    miss_m = [k for k in need_math if k not in src_math]
    # ★ 面板必须印着这四个键帽（源站面板文案照抄，clone 早已有）
    panel_rows = [
        '"俯视视角"',
        '"重置视角"',
        '"正面视角"',
        '"WASDQE"',
    ]
    miss_p = [k for k in panel_rows if k not in src_panel]
    ok = not miss_v and not miss_m and not miss_p
    record(
        "S1 结构：快捷键组件 ＋ 纯函数 ＋ 面板键帽都在",
        ok,
        "viewport缺=%s math缺=%s panel缺=%s" % (miss_v, miss_m, miss_p),
    )

    # ══ S2 常量与源站逐字一致
    const_checks = [
        ("DIRECTOR_VIEW_PAN_SPEED = 1.2", "DIRECTOR_VIEW_PAN_SPEED = 1.2" in src_math),
        (
            "DIRECTOR_VIEW_PAN_MIN_DISTANCE = 0.5",
            "DIRECTOR_VIEW_PAN_MIN_DISTANCE = 0.5" in src_math,
        ),
        (
            "DIRECTOR_VIEW_PAN_SHIFT_MULTIPLIER = 3",
            "DIRECTOR_VIEW_PAN_SHIFT_MULTIPLIER = 3" in src_math,
        ),
        (
            "DIRECTOR_VIEW_PAN_MAX_DELTA_SECONDS = 0.05",
            "DIRECTOR_VIEW_PAN_MAX_DELTA_SECONDS = 0.05" in src_math,
        ),
        ("top 方向 [0,1,0.001]", "top: [0, 1, 0.001]" in src_math),
        ("front 方向 [0,0,1]", "front: [0, 0, 1]" in src_math),
        (
            "平移键集合 = w/a/s/d/q/e",
            all('"%s"' % k in src_math for k in ("w", "a", "s", "d", "q", "e")),
        ),
        (
            "源站 right 兜底阈值 1e-6",
            "DIRECTOR_VIEW_PAN_MIN_RIGHT_LENGTH_SQUARED = 1e-6" in src_math,
        ),
    ]
    bad = [n for n, v in const_checks if not v]
    record(
        "S2 常量：与源站 chunk 的数值逐字一致",
        not bad,
        "不符=%s（共 %d 项）" % (bad, len(const_checks)),
    )

    # ══ S3 T（俯视视角）精确命中源站 iK("top")
    t = clone["②按T"]
    got = tuple(t["后"]["position"])
    want = expect_preset("top", tuple(t["前"]["position"]), tuple(t["前"]["target"]))
    ok = vec_close(got, want, EPS_EXACT) and vec_close(
        tuple(t["后"]["target"]), tuple(t["前"]["target"]), EPS_EXACT
    )
    record(
        "S3 按 T：position 精确等于源站 iK(top) 且 target 不变",
        ok,
        "实测=%s 期望=%s target前=%s 后=%s"
        % (got, want, t["前"]["target"], t["后"]["target"]),
    )

    # ══ S4 Y（正面视角）精确命中源站 iK("front")
    y = clone["③按Y"]
    got = tuple(y["后"]["position"])
    want = expect_preset("front", tuple(y["前"]["position"]), tuple(y["前"]["target"]))
    ok = vec_close(got, want, EPS_EXACT) and vec_close(
        tuple(y["后"]["target"]), tuple(y["前"]["target"]), EPS_EXACT
    )
    record(
        "S4 按 Y：position 精确等于源站 iK(front) 且 target 不变",
        ok,
        "实测=%s 期望=%s" % (got, want),
    )

    # ══ S5 H（重置视角）回到默认位姿
    h = clone["④按H"]
    after = h["后"]
    ok = (
        vec_close(tuple(after["position"]), DEFAULT_POSITION, EPS_PLAIN)
        and vec_close(tuple(after["target"]), DEFAULT_TARGET, EPS_PLAIN)
        and close(after["fov"], DEFAULT_FOV, EPS_PLAIN)
    )
    record(
        "S5 按 H：回到默认位姿 {fov:45, position:[6.2,4.25,7.4], target:[0,1,0]}",
        ok,
        "position=%s target=%s fov=%s"
        % (after["position"], after["target"], after["fov"]),
    )

    # ══ S6 单击 W（按下即松开）不得产生任何位移
    single = clone["⑤单击W"]
    d = sub(tuple(single["后"]["position"]), tuple(single["前"]["position"]))
    ok = length(d) <= EPS_PLAIN
    record(
        "S6 单击 W：位移为 0（源站的 keydown 只登记、keyup 就删掉）",
        ok,
        "位移=%s 长度=%.12f" % (d, length(d)),
    )

    # ══ S7 按住平移：视距不变 ＋ 方向与源站一致
    dir_detail = []
    all_ok = True
    for key, expect_dir in (
        ("W", None),
        ("A", None),
        ("E", None),
        ("Q", None),
    ):
        item = clone["⑥按住%s" % key]
        before = item["前"]
        after_v = item["后"]
        dist_before = length(sub(tuple(before["position"]), tuple(before["target"])))
        dist_after = length(sub(tuple(after_v["position"]), tuple(after_v["target"])))
        forward = norm(sub(tuple(before["target"]), tuple(before["position"])))
        right = norm(cross(forward, (0.0, 1.0, 0.0)), (1.0, 0.0, 0.0))
        up = (0.0, 1.0, 0.0)
        want_dir = {
            "W": forward,
            "A": scale(right, -1.0),
            "E": up,
            "Q": scale(up, -1.0),
        }[key]
        move = sub(tuple(after_v["position"]), tuple(before["position"]))
        cos = dot(move, want_dir) / (length(move) * length(want_dir))
        ok_one = (
            abs(dist_before - dist_after) <= 1e-6
            and length(move) > 1e-6
            and cos > 0.999
        )
        all_ok = all_ok and ok_one
        dir_detail.append(
            "%s:视距%.4f→%.4f cos=%.6f 位移=%.4f"
            % (key, dist_before, dist_after, cos, length(move))
        )
    record(
        "S7 按住 WASDQE：视距不变（纯平移）且方向与源站一致",
        all_ok,
        " ｜ ".join(dir_detail),
    )

    # ══ S8 Shift 加速（源站 ×3）
    plain_len = clone["⑥按住W"]["位移长度"]
    shift_len = clone["⑦按住Shift+W"]["位移长度"]
    ratio = shift_len / plain_len if plain_len else 0.0
    ok = ratio >= 2.5
    record(
        "S8 按住 Shift+W：位移显著大于裸 W（源站 ×3）",
        ok,
        "裸W=%.4f Shift+W=%.4f 倍数=%.3f" % (plain_len, shift_len, ratio),
    )

    # ══ S9 源站侧证据（★ 证明「按住才有效」是源站事实，不是 clone 的发明）
    pan_keys = ["W", "A", "S", "D", "Q", "E"]
    pan_ok = []
    for k in pan_keys:
        item = src_pan.get("③按%s" % k)
        if not item:
            pan_ok.append((k, False, 0))
            continue
        pan_ok.append((k, item["差异像素"] > 0, item["差异像素"]))
    # ★ 源站的 T 在 5 种前置条件下都生效
    t_all = [
        v
        for k, v in src_cam.items()
        if k.endswith("_按T_与基线差") and isinstance(v, int)
    ]
    t_ok = len(t_all) >= 5 and all(v > 0 for v in t_all)
    # ★ 源站的 WASDQE 单击无效（v2/v3 探针用 press ⟹ ⟹ 全部 0）
    press_all = [
        v
        for k, v in src_cam.items()
        if "_按" in k and "与基线差" in k and isinstance(v, int) and v == 0
    ]
    ok = (
        all(ok2 for _, ok2, _ in pan_ok)
        and t_ok
        and len(press_all) >= 30
    )
    record(
        "S9 源站证据：按住六键都生效、单击全为 0、T 在 5 种条件下都生效",
        ok,
        "按住=%s ｜ T各条件=%s ｜ 单击零差异条数=%d"
        % (
            [(k, v) for k, _, v in pan_ok],
            t_all,
            len(press_all),
        ),
    )

    passed = sum(1 for r in results if r["通过"])
    print("\n批次 851 门禁：%d/%d 通过" % (passed, len(results)))
    (BATCH / "runtime-audit.json").write_text(
        json.dumps(
            {
                "批次": 851,
                "通过": passed,
                "总数": len(results),
                "判据": results,
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
