#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 833 验收器 —— clone 导演台「添加机位」的 **15 枚机位预设语义**（**实施批次**）。

## 本批做了什么

batch 832 建出了「添加机位」的**面板**（几何逐字相等），但**没有**建出「点了会怎样」。
本批把 15 枚预设的**语义**补齐：

- 源站：**逐枚**实测（`probes/presets833.py`）——每枚点了会**真的新建**一台机位，
  右栏读出这台新机位的 位置 / 旋转 / 注视坐标 / FOV ⟹ 测完**立刻按名字删掉**并复验。
- clone：面板里 15 枚**每枚带完整语义**，点哪枚就按那枚的语义建机位
  （`src/store/directorStore.ts` 的 `addDirectorCameraWithPreset`）。

★ ★ ★ 15 枚的 FOV 从 **35**（正面特写）到 **70**（低角度广角）不等 ⟹
  **不凭一枚推 15 枚** ⟹ 门禁逐枚比 60 组数值。

## 门禁怎么判

★ **期望值从 raw 读**（4 份 raw 全部由探针**程序化**产出 ⟹ 不是手打）：

| raw | 谁产的 | 干什么用 |
|---|---|---|
| `source-833-camera-preset-semantics.json` | `probes/presets833.py` → `probes/mk833raw.py` | 15 枚的源站语义（期望值） |
| `clone-833-camera-preset-semantics.json` | `probes/presetsclone833.py` | clone 的活体读数 |
| `source-833-reader-selftest.json` | `probes/reader833src.py` | 读数器在**源站**上的自证 |
| `source-833-preset-panel-stays.json` | `probes/panelstay833.py` | 点完预设后面板**不关** |

★ ★ 本批还修掉了一个**读数口径**问题：clone 的 Inspector **多一行「缩放」** ⟹
  「把 number 输入拼起来再切 [0:3]/[3:6]/[6:9]」这条口径**只在源站成立** ⟹ 两边不可比。
  ⟹ 改成**规则 R**（`probes/reader833.py`）：按**字段标题**分组 ⟹ 两边永远可比。

★ 纪律：每条判据都有**只翻它自己那一条**的阴性对照（16 条判据 ↔ 16 条阴性）。
"""
import copy
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
BATCH = ROOT / "docs" / "research" / "liblib-canvas-batch833-2026-10-01"
RAW = BATCH / "raw"

SRC_RAW = RAW / "source-833-camera-preset-semantics.json"
CLONE_RAW = RAW / "clone-833-camera-preset-semantics.json"
SELFTEST_RAW = RAW / "source-833-reader-selftest.json"
PANELSTAYS_RAW = RAW / "source-833-preset-panel-stays.json"

SRC_PANEL = ROOT / "src" / "components" / "director" / "DirectorCameraPresetPanel.tsx"
SRC_STORE = ROOT / "src" / "store" / "directorStore.ts"
SRC_DESK = ROOT / "src" / "components" / "director" / "DirectorDesk.tsx"

# ── ★ 探针区开始 ────────────────────────────────────────────────────────────────
# ★ 本批的「探针」＝ **读入库读数的键名**（不是 DOM 选择器）：
#   键名一旦漂移，下面这些常量就取不到值 ⟹ 门禁自己会红。
K_SRC_COUNT = "预设项数"
K_SRC_PRESETS = "预设"
K_SRC_XCHECK = "★双路交叉校验结果"
K_SRC_LOG = "删除日志"
K_SRC_TREE_BEFORE = "基线树"
K_SRC_TREE_AFTER = "末次树"
K_SRC_NEWNAME = "新建机位名"

K_CLONE_ITEMS = "②逐枚"
K_CLONE_LOG = "③删除日志"
K_CLONE_END = "④末次机位"
K_CLONE_BASE = "⓪基线机位"
K_CLONE_SEM = "语义"
K_CLONE_LEFT = "点完后左侧"
K_CLONE_BEFORE = "前机位数"
K_CLONE_AFTER = "后机位数"
K_CLONE_NAMES = "后机位名"

K_SELF_JS = "规则R读数"
K_SELF_SEM = "规则R语义"
K_SELF_CROSS = "独立采集(对照)"

K_PANEL_AFTER = "③点完第 1 枚后"

# 语义字段（源站 raw 与 clone raw 同名 ⟹ 这是「两边可比」的前提）
FIELDS = ("位置", "旋转", "注视", "FOV")
# 源站 raw 每枚上的**元数据**键（不是语义 ⟹ 拿来比口径会把 S12 判错）
META_KEYS = {"idx", "label", K_SRC_NEWNAME}
# ── ★ 探针区结束 ────────────────────────────────────────────────────────────────

# 面板源码里那条预设字面量（15 枚）——用它核验「面板里的常量 == raw」
_PRESET_RE = re.compile(
    r"\{\s*label:\s*\"(?P<label>[^\"]*)\"\s*,\s*"
    r"position:\s*\[(?P<position>[^\]]*)\]\s*,\s*"
    r"rotation:\s*\[(?P<rotation>[^\]]*)\]\s*,\s*"
    r"target:\s*\[(?P<target>[^\]]*)\]\s*,\s*"
    r"fov:\s*(?P<fov>[0-9.]+)\s*\}"
)


def _triple(text):
    return [float(x.strip()) for x in text.split(",") if x.strip() != ""]


def parse_panel_presets(source_text):
    """从面板源码里解析出 15 枚预设的字面量（label + 四组数值）。"""
    out = []
    for m in _PRESET_RE.finditer(source_text):
        out.append({
            "label": m.group("label"),
            "位置": _triple(m.group("position")),
            "旋转": _triple(m.group("rotation")),
            "注视": _triple(m.group("target")),
            "FOV": float(m.group("fov")),
        })
    return out


def _num(x):
    return float(x)


def _same(a, b, tol=1e-9):
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return False
        return all(abs(float(x) - float(y)) <= tol for x, y in zip(a, b))
    return abs(float(a) - float(b)) <= tol


def build_checks(src_raw, clone_raw, self_raw, panel_raw,
                 panel_src, store_src, desk_src):
    C = []

    def ok(cid, cond, detail=None):
        C.append({"id": cid, "name": cid, "ok": bool(cond),
                  "detail": detail if detail is not None else ""})

    s_presets = src_raw.get(K_SRC_PRESETS) or []
    c_items = clone_raw.get(K_CLONE_ITEMS) or []

    # ── S1 源站采集的完备性（只读**元数据**，不碰任何单枚数值）──
    xcheck = src_raw.get(K_SRC_XCHECK) or {}
    s_log = src_raw.get(K_SRC_LOG) or []
    ok("S1:★★★ **源站采集完备**（元数据）：15 枚、**双路交叉校验**通过、"
       "删除日志 15 条全 ✔、基线树与末次树都只剩「机位1」"
       "⟹ ★ 源站侧**已复原**且**每枚都删掉了**",
       src_raw.get(K_SRC_COUNT) == 15
       and xcheck.get("全部一致") is True
       and xcheck.get("枚数") == 15
       and len(s_log) == 15
       and all("✔" in line for line in s_log)
       and src_raw.get(K_SRC_TREE_BEFORE) == ["机位1"]
       and src_raw.get(K_SRC_TREE_AFTER) == ["机位1"],
       {"预设项数": src_raw.get(K_SRC_COUNT),
        "双路交叉校验": xcheck,
        "删除日志条数": len(s_log),
        "删除日志全✔": all("✔" in line for line in s_log),
        "基线树": src_raw.get(K_SRC_TREE_BEFORE),
        "末次树": src_raw.get(K_SRC_TREE_AFTER)})

    # ── S2 15 枚的标签与顺序逐字相同（只读 label）──
    s_labels = [p.get("label") for p in s_presets]
    c_labels = [c.get("label") for c in c_items]
    ok("S2:★★★★★ clone 的 **15 枚标签与顺序**与源站**逐字相同**"
       "（当前视角/正面中景/正面特写/正面全景/侧面跟拍/侧面近景/背面中景/"
       "俯拍全景/45° 俯拍/低角度仰拍/低角度广角/过肩镜头/过肩镜头（右）/鸟瞰/荷兰角）",
       s_labels == c_labels and len(c_labels) == 15,
       {"源站": s_labels, "clone": c_labels})

    # ── S3/S4/S5/S6 四组数值**分字段**比 ⟹ 阴性互不串门 ──
    for idx, (key, title) in enumerate((("位置", "位置"), ("旋转", "旋转"),
                                        ("注视", "注视坐标"), ("FOV", "FOV"))):
        s_vals = [p.get(key) for p in s_presets]
        c_vals = [(c.get(K_CLONE_SEM) or {}).get(key) for c in c_items]
        same = (len(s_vals) == 15 and len(c_vals) == 15
                and all(_same(a, b) for a, b in zip(s_vals, c_vals)))
        extra = ""
        if key == "FOV":
            fovs = {float(v) for v in s_vals if v is not None}
            same = same and len(fovs) >= 5
            extra = ("⟹ ★ 且源站 15 枚的 FOV 有 %d 种取值（35…70）"
                     "⟹ **不凭一枚推 15 枚**" % len(fovs))
        ok("S%d:★★★★★ clone 的 **%s**（源站右栏「%s」）**逐枚相等**（15 组）%s"
           % (3 + idx, key, title, extra),
           same,
           {"源站": s_vals, "clone": c_vals,
            "不同的序号": [i for i, (a, b) in enumerate(zip(s_vals, c_vals))
                           if not _same(a, b)]})

    # ── S7 每枚点下去都**真的新建**了一台机位（只读机位数）──
    counts = [(c.get(K_CLONE_BEFORE), c.get(K_CLONE_AFTER)) for c in c_items]
    ok("S7:★★★★★ clone 的 **15 枚每一枚**点下去都**真的新建了一台机位**"
       "（机位数 +1）⟹ ★ 不是「点了没反应」也不是「一次建了好几台」",
       len(counts) == 15 and all(b is not None and a is not None
                                 and b == a + 1 for a, b in counts),
       {"逐枚的前/后机位数": counts,
        "不满足的序号": [i for i, (a, b) in enumerate(counts)
                         if not (a is not None and b is not None and b == a + 1)]})

    # ── S8 clone 测完是**干净**的（只读末次机位 ＋ clone 删除日志）──
    c_log = clone_raw.get(K_CLONE_LOG) or []
    end = clone_raw.get(K_CLONE_END) or {}
    base = clone_raw.get(K_CLONE_BASE) or {}
    ok("S8:★★★★★ clone 测完**是干净的**（末次机位数 == 基线机位数，"
       "且 15 次删除**逐次复验**都少了一台）⟹ ★ 探针不往 clone 里留垃圾",
       end.get("count") == base.get("count")
       and len(c_log) == 15 and all("✔" in line for line in c_log),
       {"基线机位": base.get("count"), "末次机位": end.get("count"),
        "删除日志条数": len(c_log),
        "删除日志全✔": all("✔" in line for line in c_log),
        "删除日志": c_log})

    # ── S9 新建机位的**名字**与源站逐字相同（只读名字）──
    s_names = [p.get(K_SRC_NEWNAME) for p in s_presets]
    c_names = []
    for c in c_items:
        names = c.get(K_CLONE_NAMES) or []
        c_names.append(names[-1] if names else None)
    ok("S9:★★★★★ clone 新建机位的**名字**与源站**逐字相同**（「机位2」）"
       "⟹ ★ 源站新建的机位叫 **「机位N」**（N = 现有机位数 + 1，无空格无后缀）"
       "⟹ ★ 旧名「机位 02 · 新镜头」是 batch 89 的**自拟**名 ⟹ 本批按实测改正",
       s_names == c_names and len(c_names) == 15
       and all(n == "机位2" for n in c_names),
       {"源站": s_names, "clone": c_names})

    # ── S10 读数器在**源站**上的自证：9 个 number（分组 vs DOM 顺序切片）──
    self_js = self_raw.get(K_SELF_JS) or {}
    self_sem = self_raw.get(K_SELF_SEM) or {}
    cross = self_raw.get(K_SELF_CROSS) or {}
    cross_nums = [float(v) for v in (cross.get("nums") or [])]
    ok("S10:★★★★★ **读数器在源站活体上自证**：规则 R 分组出的 位置/旋转/注视 "
       "与**另一次独立采集**（diag833）的 DOM 顺序切片**逐字相等**（9 个数）"
       "⟹ ★ 证明读数器**确实读到了东西** ⟹ 不是「两个空集相等」",
       len(cross_nums) == 9
       and _same(self_sem.get("位置"), cross_nums[0:3])
       and _same(self_sem.get("旋转"), cross_nums[3:6])
       and _same(self_sem.get("注视"), cross_nums[6:9]),
       {"规则R语义": self_sem,
        "独立采集的 number（DOM 顺序）": cross_nums,
        "vec 分组原文": self_js.get("vec")})

    # ── S11 读数器的 FOV 在源站活体上自证（range 值）──
    cross_ranges = [float(v) for v in (cross.get("ranges") or [])]
    ok("S11:★★★★★ **读数器的 FOV** 在源站活体上与独立采集的 range 值相等"
       "（67）⟹ ★ 证明「取 FOV 标题下第一个 range」这条规则在源站上成立",
       len(cross_ranges) == 1
       and _same(self_sem.get("FOV"), cross_ranges[0])
       and len(self_js.get("fov") or []) == 1,
       {"规则R的 FOV": self_sem.get("FOV"),
        "独立采集的 range": cross_ranges,
        "规则R的 fov 分组": self_js.get("fov")})

    # ── S12 两边是**同一套读数口径**（只读键集合）──
    # ★ 只比**语义键**：源站 raw 的每枚还带 idx / label / 新建机位名 三个**元数据**键
    #   ⟹ 那是「怎么找到这一枚」用的，不是语义 ⟹ 不能拿来比口径。
    s_keys = (set(s_presets[0].keys()) - META_KEYS) if s_presets else set()
    c_keys = set((c_items[0].get(K_CLONE_SEM) or {}).keys()) if c_items else set()
    ok("S12:★★★★★ 源站与 clone 的读数是**同一套口径**（语义键集合相同："
       "位置/旋转/注视/FOV）⟹ ★ 这是两边能直接比的前提"
       "⟹ ★★ 旧口径（number 序列切片）**不成立**——clone 多一行「缩放」",
       s_keys == c_keys and c_keys == set(FIELDS),
       {"源站语义键": sorted(s_keys), "clone语义键": sorted(c_keys),
        "★排除的元数据键": sorted(META_KEYS),
        "★为什么不能切 number 序列": "clone 的 Inspector 多一行「缩放」"
                                "⟹ [0:3]/[3:6]/[6:9] 会整体错位"})

    # ── S13 面板源码里的 15 枚**常量**与 raw 逐字相符 ──
    parsed = parse_panel_presets(panel_src)
    diff = []
    for i, p in enumerate(parsed[:15]):
        if i >= len(s_presets):
            diff.append((i, "面板多出一枚"))
            continue
        sp = s_presets[i]
        if p["label"] != sp.get("label"):
            diff.append((i, "label", p["label"], sp.get("label")))
        for key in FIELDS:
            if not _same(p[key], sp.get(key)):
                diff.append((i, key, p[key], sp.get(key)))
    ok("S13:★★★★★ clone 面板源码里那 15 枚的**常量**与源站 raw **逐字相符**"
       "（label ＋ 位置/旋转/注视/FOV，共 60 组）"
       "⟹ ★ 期望值来自 raw ⟹ 源码里不是手打的",
       len(parsed) == 15 and not diff,
       {"解析到几枚": len(parsed), "不一致": diff,
        "解析到的第 0 枚": parsed[0] if parsed else None})

    # ── S14 store 真的把这四组字段写进新建的机位 ──
    ok("S14:★★★★★ clone 的 store 动作 `addDirectorCameraWithPreset` "
       "**真的**把四组字段写进新建的机位"
       "（先 `addDirectorCamera()` 建机位 ⟹ 再 `updateObjectTransform` 写位置/旋转 "
       "⟹ 再 `updateCamera` 写注视坐标/FOV）",
       "addDirectorCameraWithPreset" in store_src
       and "const added = get().addDirectorCamera();" in store_src
       and 'updateObjectTransform(cameraId, "position"' in store_src
       and 'updateObjectTransform(cameraId, "rotation"' in store_src
       and "updateCamera(cameraId, { fov: preset.fov, target: preset.target })"
       in store_src,
       {"store 里的锚点": [ln.strip() for ln in store_src.splitlines()
                       if "addDirectorCameraWithPreset" in ln
                       or "preset.fov" in ln][:6]})

    # ── S15 Desk 把面板的 onPick 接到那个动作上 ──
    ok("S15:★★★★★ clone 的 `DirectorDesk` 把面板的 `onPick` 接到 "
       "`addDirectorCameraWithPreset` 上（并把整枚语义传进去）"
       "⟹ ★ 不接就等于「点了没反应」",
       "addDirectorCameraWithPreset" in desk_src
       and "onPick={(preset) => {" in desk_src
       and "position: preset.position" in desk_src
       and "rotation: preset.rotation" in desk_src
       and "target: preset.target" in desk_src
       and "fov: preset.fov" in desk_src,
       {"desk 里的锚点": [ln.strip() for ln in desk_src.splitlines()
                     if "addDirectorCameraWithPreset" in ln
                     or "preset." in ln][:8]})

    # ── S16 点完预设后，左侧**仍是预设面板**（源站 == clone）──
    s_after = panel_raw.get(K_PANEL_AFTER) or {}
    c_after = (c_items[0].get(K_CLONE_LEFT) or {}) if c_items else {}
    ok("S16:★★★★★ 点完一枚预设后，**左侧仍是机位预设面板**（源站 15 格 / "
       "clone 15 格）且**场景树都不在 DOM 里** ⟹ ★ 源站实测「面板不关」"
       "⟹ ★ 这条是本批**新测**的（832 的采集过程把它覆盖掉了）",
       s_after.get("presetCells") == 15
       and c_after.get("presetCells") == 15
       and s_after.get("treeInDom") is False
       and c_after.get("treeInDom") is False,
       {"源站点完后": s_after, "clone点完后": c_after})
    return C


# ── 阴性对照：每条**只**翻它自己那一条 ────────────────────────────────────────
def _negations():
    def n1(sr, cr, st, pr, ps, so, dk):
        c = copy.deepcopy(sr)
        c[K_SRC_COUNT] = 14
        return c, cr, st, pr, ps, so, dk

    def n2(sr, cr, st, pr, ps, so, dk):
        c = copy.deepcopy(cr)
        c[K_CLONE_ITEMS][3]["label"] = "别的小景"
        return sr, c, st, pr, ps, so, dk

    def n3(sr, cr, st, pr, ps, so, dk):
        # ★ 扰动**clone 的位置** ⟹ 只翻 S3
        #   ★ 为什么扰 clone 而不扰源站 raw：源站 raw 的四组值同时被 S13 读
        #     （S13 = 面板常量 vs 源站 raw）⟹ 扰源站 raw 会让 S13 一起翻 ⟹ 串门。
        #     ⟹ 源站 raw 那一侧由 **N13**（扰面板常量）覆盖 S13。
        c = copy.deepcopy(cr)
        c[K_CLONE_ITEMS][5][K_CLONE_SEM]["位置"][1] = 1.6
        return sr, c, st, pr, ps, so, dk

    def n4(sr, cr, st, pr, ps, so, dk):
        # ★ 扰动**clone 的旋转** ⟹ 只翻 S4
        c = copy.deepcopy(cr)
        c[K_CLONE_ITEMS][5][K_CLONE_SEM]["旋转"][0] = 0.01
        return sr, c, st, pr, ps, so, dk

    def n5(sr, cr, st, pr, ps, so, dk):
        # ★ 扰动**clone 的注视** ⟹ 只翻 S5（同 N3：源站 raw 那一侧留给 S13）
        c = copy.deepcopy(cr)
        c[K_CLONE_ITEMS][7][K_CLONE_SEM]["注视"][2] = 0.1
        return sr, c, st, pr, ps, so, dk

    def n6(sr, cr, st, pr, ps, so, dk):
        # ★ 扰动**clone 的 FOV** ⟹ 只翻 S6
        c = copy.deepcopy(cr)
        c[K_CLONE_ITEMS][2][K_CLONE_SEM]["FOV"] = 36
        return sr, c, st, pr, ps, so, dk

    def n7(sr, cr, st, pr, ps, so, dk):
        # ★ 扰动**机位数** ⟹ 只翻 S7（S8 读的是末次机位与删除日志）
        c = copy.deepcopy(cr)
        c[K_CLONE_ITEMS][8][K_CLONE_AFTER] = c[K_CLONE_ITEMS][8][K_CLONE_BEFORE]
        return sr, c, st, pr, ps, so, dk

    def n8(sr, cr, st, pr, ps, so, dk):
        c = copy.deepcopy(cr)
        c[K_CLONE_END]["count"] = 2
        return sr, c, st, pr, ps, so, dk

    def n9(sr, cr, st, pr, ps, so, dk):
        # ★ 扰动**名字** ⟹ 只翻 S9
        c = copy.deepcopy(cr)
        names = c[K_CLONE_ITEMS][0][K_CLONE_NAMES]
        names[-1] = "机位 02 · 新镜头"
        return sr, c, st, pr, ps, so, dk

    def n10(sr, cr, st, pr, ps, so, dk):
        # ★ 扰动**独立采集**里的一个数 ⟹ 只翻 S10（S11 读的是 range）
        c = copy.deepcopy(st)
        c[K_SELF_CROSS]["nums"][0] = "3.4"
        return sr, cr, c, pr, ps, so, dk

    def n11(sr, cr, st, pr, ps, so, dk):
        c = copy.deepcopy(st)
        c[K_SELF_CROSS]["ranges"][0] = "66"
        return sr, cr, c, pr, ps, so, dk

    def n12(sr, cr, st, pr, ps, so, dk):
        # ★ 扰动**源站 raw 的键集合**（加一个键）⟹ 只翻 S12
        #   （S3–S6 只读那四个键的值 ⟹ 不受影响）
        c = copy.deepcopy(sr)
        c[K_SRC_PRESETS][0]["缩放"] = [1, 1, 1]
        return c, cr, st, pr, ps, so, dk

    def n13(sr, cr, st, pr, ps, so, dk):
        # ★ 扰动**面板源码**里的一个常量 ⟹ 只翻 S13
        p = ps.replace('target: [0, 1.2, 0], fov: 50 }',
                       'target: [0, 1.3, 0], fov: 50 }', 1)
        return sr, cr, st, pr, p, so, dk

    def n14(sr, cr, st, pr, ps, so, dk):
        s = so.replace("updateCamera(cameraId, { fov: preset.fov, target: preset.target })",
                       "updateCamera(cameraId, {})")
        return sr, cr, st, pr, ps, s, dk

    def n15(sr, cr, st, pr, ps, so, dk):
        d = dk.replace("fov: preset.fov", "fov: 50")
        return sr, cr, st, pr, ps, so, d

    def n16(sr, cr, st, pr, ps, so, dk):
        # ★ 扰动**源站点完后的格数** ⟹ 只翻 S16
        c = copy.deepcopy(pr)
        c[K_PANEL_AFTER]["presetCells"] = 14
        return sr, cr, st, c, ps, so, dk

    return [
        ("N1 把源站的「预设项数」改成 14 ⟹ S1 翻红", "S1", n1),
        ("N2 把 clone 第 4 枚的标签改掉 ⟹ S2 翻红", "S2", n2),
        ("N3 改 clone 第 6 枚的「位置」⟹ S3 翻红", "S3", n3),
        ("N4 改 clone 第 6 枚的「旋转」⟹ S4 翻红", "S4", n4),
        ("N5 改 clone 第 8 枚的「注视」⟹ S5 翻红", "S5", n5),
        ("N6 改 clone 第 3 枚的「FOV」⟹ S6 翻红", "S6", n6),
        ("N7 把 clone 第 9 枚的机位数改成没增加 ⟹ S7 翻红", "S7", n7),
        ("N8 把 clone 的末次机位数改成 2 ⟹ S8 翻红", "S8", n8),
        ("N9 把 clone 新建机位的名字改回旧名 ⟹ S9 翻红", "S9", n9),
        ("N10 改独立采集里的一个数 ⟹ S10 翻红", "S10", n10),
        ("N11 改独立采集里的 range 值 ⟹ S11 翻红", "S11", n11),
        ("N12 给源站 raw 加一个键 ⟹ S12 翻红", "S12", n12),
        ("N13 改面板源码里第 1 枚的注视常量 ⟹ S13 翻红", "S13", n13),
        ("N14 把 store 的 updateCamera 写空 ⟹ S14 翻红", "S14", n14),
        ("N15 把 desk 里的 fov 写死 ⟹ S15 翻红", "S15", n15),
        ("N16 把源站点完后的格数改成 14 ⟹ S16 翻红", "S16", n16),
    ]


def main():
    src_raw = json.loads(SRC_RAW.read_text(encoding="utf-8"))
    clone_raw = json.loads(CLONE_RAW.read_text(encoding="utf-8"))
    self_raw = json.loads(SELFTEST_RAW.read_text(encoding="utf-8"))
    panel_raw = json.loads(PANELSTAYS_RAW.read_text(encoding="utf-8"))
    panel_src = SRC_PANEL.read_text(encoding="utf-8")
    store_src = SRC_STORE.read_text(encoding="utf-8")
    desk_src = SRC_DESK.read_text(encoding="utf-8")

    checks = build_checks(src_raw, clone_raw, self_raw, panel_raw,
                          panel_src, store_src, desk_src)
    neg = []
    for label, expect, builder in _negations():
        args = builder(src_raw, clone_raw, self_raw, panel_raw,
                       panel_src, store_src, desk_src)
        mc = build_checks(*args)
        turned = sorted({c["id"].split(":")[0] for c in mc if not c["ok"]})
        neg.append({"name": label, "期望翻红": expect, "实际翻红": turned,
                    "ok": turned == [expect]})

    passed = sum(1 for c in checks if c["ok"])
    report = {"batch": 833, "mode": "offline",
              "totals": {"passed": passed, "total": len(checks)},
              "阴性对照": {"passed": sum(1 for n in neg if n["ok"]),
                           "total": len(neg)},
              "checks": checks, "阴性": neg}
    (BATCH / "verify-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("主检查 %d/%d ｜ 阴性对照 %d/%d" % (
        passed, len(checks), report["阴性对照"]["passed"], len(neg)))
    for c in checks:
        print(("  ✔ " if c["ok"] else "  ✘ ") + c["id"][:92])
    for n in neg:
        print(("  ✔ " if n["ok"] else "  ✘ ") + n["name"][:50]
              + " → 实际翻红 " + ",".join(n["实际翻红"]))
    return 0 if passed == len(checks) and all(n["ok"] for n in neg) else 1


if __name__ == "__main__":
    sys.exit(main())
