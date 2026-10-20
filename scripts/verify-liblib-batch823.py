#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 823 验收器 —— **纯 UI 可达性审查**

## 验收什么

过去 800+ 批的探针，**起点状态几乎全靠 `window.__libtv_store` /
`window.__director_store` 这两个后门造**（`canvasStore.ts:4344`、
`directorStore.ts:8721` —— 那是**我给测试挂的**，源站产品里根本不存在）。
本批把「用户能不能纯 UI 走到那个状态」逐条量出来。

## ★ 三条硬纪律在本文件里的落点

1. ★ **零 store 写调用**：由 **S1** 用**正则扫探针源码**自证 ——
   不是靠我口头保证。探针里所有 store 访问只允许经 `RO()` / `RO_D()`
   两个只读入口。
2. ★ **否定性读数必须两侧都堵死**：S7（两句同屏纯 UI 不可达）要求
   **两条顺序相反的臂**都给出证据，**外加**一个对照臂
   （B9 程序化 vs B10 真实鼠标）——★ 否则「不可达」可能只是没找对方法。
3. ★ **前提写死**：S1 把 18 个时刻**按顺序**写死，探针少读一个就判红。
"""
import copy
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
BATCH = ROOT / "docs" / "research" / "liblib-canvas-batch823-2026-10-01"
RAW = BATCH / "raw" / "vb823a.json"
PROBE = BATCH / "probes" / "dbg823a.py"

# ★ 顶层键与「dom 里的键」写成**分开的常量**（821 的教训）
K_N = "★ 节点数"
K_POS = "★ 节点位置"
K_SEL = "★ 选中节点"
K_EDGES = "★ 边数"
K_TRACK = "选中轨道"
K_OBJ = "★ 选中对象"
K_OTYPE = "★ 选中对象类型"
K_LOCK = "★ 相机锁定"
K_FOLLOW = "★ 跟随目标"
K_KF = "★ 关键帧数"
K_TRACKS = "★ 轨道清单"
K_LASTMS = "★ 末关键帧毫秒"
K_DURMS = "总时长毫秒"

MSG_DUR = "当前时间轴没有可追加的时长"
MSG_FOLLOW = "跟随目标时不可使用预设运镜"

EXPECTED_MOMENTS = [
    "A0·刚打开画布（**纯 UI 起点**）",
    "A2·点节点中心（纯 UI 选中）",
    "A3·真实鼠标拖拽 +108px/+72px",
    "A4·按 Delete 键",
    "A5·按 Cmd+Z 撤销",
    "A6·按 Cmd+Shift+Z 重做",
    "A7·纯 UI 从 source handle 拖到 target handle",
    "B1·点「打开导演台」",
    "B2·★ 点时间轴上的相机对象行（纯 UI 选相机）",
    "B3·在检查器里选跟随目标（纯 UI）",
    "B4·点检查器里的锁定按钮（纯 UI）",
    "B5·点预设运镜开关",
    "B6a·append 被拒（★ 面板内应有提示）",
    "B6b·★★ 纯 UI 点跟随 select 之后",
    "B7·★ 点跟随横幅上的取消（纯 UI 清跟随）",
    "B8·★★ 无跟随时开面板 + append ⟹ 面板内应有「没有可追加的时长」",
    "B9·★★★ 纯 UI 点跟随 select 之后（★ 面板还开着吗）",
    "B10·★★★ **真实鼠标**点跟随 select（★ 面板被点关了吗）",
]


def at(raw, name):
    """★ 按名字取一个时刻，取不到就**炸**而不是静默返回空。"""
    for r in raw.get("画布", []) + raw.get("导演台", []):
        if r["步骤"] == name:
            return r
    raise KeyError("raw 里没有这个时刻：" + name)


def ok(name, why, cond, evidence):
    return {"id": name, "why": why, "ok": bool(cond), "evidence": evidence}


def build_checks(raw):
    C = []

    # ── S1 前提：18 个时刻按顺序齐 + 探针零 store 写调用
    got = [r["步骤"] for r in raw.get("画布", []) + raw.get("导演台", [])]
    src = PROBE.read_text(encoding="utf-8")
    # ★ 扫探针源码：找 store 访问点，只允许 `getState()`（只读）
    store_refs = re.findall(r"__libtv_store|__director_store", src)
    # ★ 允许的写调用：探针里**不该**出现任何 action 形式的调用
    action_calls = re.findall(
        r"\bS\.(?!getState\b)\w+\s*\(", src)
    # ★ 再扫一遍：任何 `.getState()` 之后的链式调用
    chained = re.findall(r"getState\(\)\s*\.\s*(\w+)", src)
    zero_write = (len(action_calls) == 0
                  and all(c == "getState" for c in chained))
    C.append(ok(
        "S1:★★ **前提**：18 个时刻**按顺序一个不缺**、探针源码里**零 store 写调用**（正则自证）",
        "★★ 807 起立的规矩：**前提不满足的臂显式作废**。★ 时刻写死**顺序**而不是索引 ⟹ 探针中途少读一个就判红、而不是让后面的读数悄悄错位。★★ 「零 store 写调用」是**本批的立身之本** ⟹ 靠**扫源码**自证，不靠口头保证：允许 `getState()`，**禁止任何 action 形式的调用**",
        got == EXPECTED_MOMENTS and zero_write,
        {"时刻": got, "★ 与写死的顺序一致": got == EXPECTED_MOMENTS,
         "★ 扫到的 store 引用次数": len(store_refs),
         "★ 扫到的 action 形式调用": action_calls,
         "★ getState 之后的链式调用": chained,
         "★ 零写调用": zero_write}))

    # ── S2 画布：点节点中心 → 真的选中了
    a2 = at(raw, "A2·点节点中心（纯 UI 选中）")
    C.append(ok(
        "S2:★ 画布·纯 UI 选中：点节点中心 ⟹ `selectedNodeIds` 里出现那个节点 id",
        "★ 判据只认**绝对读数**（选中的 id），不靠「看起来有高亮」。★ 这是本批最基础的一条：**如果连点都点不中，后面所有画布结论都无从谈起**",
        len(a2["读数"][K_SEL]) == 1
        and a2["读数"][K_SEL][0] == "v-UGQZzZOpbv",
        {"★ 选中节点": a2["读数"][K_SEL],
         "★ 节点数": a2["读数"][K_N]}))

    # ── S3 画布：真实鼠标拖拽 → 坐标真的变了
    a3 = at(raw, "A3·真实鼠标拖拽 +108px/+72px")
    before = {n["id"]: (n["x"], n["y"]) for n in a3["★ 拖之前"]}
    after = {n["id"]: (n["x"], n["y"]) for n in a3["★ 拖之后"]}
    moved = {k: (before[k], after[k]) for k in before
             if k in after and before[k] != after[k]}
    C.append(ok(
        "S3:★ 画布·纯 UI 拖拽：**至少一个节点的坐标真的变了**",
        "★ 用**逐节点的前后坐标**判，而不是「列表不一样」⟹ 后者可能只是顺序变了。★ 画布节点的坐标是**画布坐标**（不是屏幕坐标）⟹ 拖拽真生效的话它必然变",
        len(moved) >= 1,
        {"★ 动了的节点": {k: {"从": v[0], "到": v[1]}
                          for k, v in moved.items()},
         "★ 拖之前": a3["★ 拖之前"][:3], "★ 拖之后": a3["★ 拖之后"][:3]}))

    # ── S4 画布：Delete → 撤销 → 重做，三步都靠绝对节点数
    a4 = at(raw, "A4·按 Delete 键")
    a5 = at(raw, "A5·按 Cmd+Z 撤销")
    a6 = at(raw, "A6·按 Cmd+Shift+Z 重做")
    n0 = a4["★ 删除前节点数"]
    n1 = a4["★ 删除后节点数"]
    n2 = a5["★ 撤销后节点数"]
    n3 = a6["★ 重做后节点数"]
    C.append(ok(
        "S4:★★ 画布·删除／撤销／重做：**节点数 10→9→10→9**",
        "★ 判据只认**节点数**这一条绝对读数，三步各自成立。★ 这一条同时排除了「撤销只是把选中态清了」这种假象（809/810 的老坑：**读数对不上先怀疑自己**）",
        (n0, n1, n2, n3) == (10, 9, 10, 9),
        {"删除前": n0, "删除后": n1, "撤销后": n2, "重做后": n3}))

    # ── S5 导演台起点：默认选中的**不是**相机轨道
    b1 = at(raw, "B1·点「打开导演台」")
    d0 = b1["读数"]
    cam_track = None
    for t in d0[K_TRACKS]:
        if t["kind"] == "camera":
            cam_track = t["id"]
    C.append(ok(
        "S5:★★★ **起点**：导演台打开后默认选中的是**角色轨道**（`transform`），**不是相机轨道**",
        "★★★ 这是本批**最要紧的一条反省**：821/822 全部导演台读数的起点「相机轨道已选中」是**后门替用户选好的** ⟹ 而纯 UI 下默认是角色 ⟹ ⟹ ★ **「用户第一次打开导演台看到什么」之前从没量过**。★ 判据要求**显式断言它是 transform** —— 判「不是相机」太弱（可能什么都没选中）",
        d0[K_TRACK] == "director-track-character-lead-transform"
        and cam_track == "director-track-camera-main"
        and d0[K_OTYPE] != "camera",
        {"★ 默认选中轨道": d0[K_TRACK],
         "★ 相机轨道 id": cam_track,
         "★ 默认选中对象": d0[K_OBJ],
         "★ 默认选中对象类型": d0[K_OTYPE],
         "★ 轨道清单": d0[K_TRACKS]}))

    # ── S6 导演台三个纯 UI 功能
    b2 = at(raw, "B2·★ 点时间轴上的相机对象行（纯 UI 选相机）")
    b3 = at(raw, "B3·在检查器里选跟随目标（纯 UI）")
    b4 = at(raw, "B4·点检查器里的锁定按钮（纯 UI）")
    d1, d2, d3 = b2["读数"], b3["读数"], b4["读数"]
    C.append(ok(
        "S6:★★★ 导演台三个功能**纯 UI 可达**：① 点**对象名**选中相机轨道 ② 检查器 select 设跟随目标 ③ 检查器按钮锁相机",
        "★★ 枢纽问题：「用户能不能纯 UI 选中相机轨道？」—— **能**，但**要点对地方**：★ 行首那个位置是**展开/收起箭头**（aria「展开属性」）⟹ 点它只 toggle、不选轨道；★ 真入口是 `[data-director-timeline-object-name]`（`DirectorTimeline.tsx:1664`，onClick → `selectTimelineTrack(group.tracks[0].id)`）。★ 我第一、二版探针点的是行首 ⟹ 读数「没变」⟹ ★ **差点把「纯 UI 选不中」写成结论**",
        d1[K_TRACK] == "director-track-camera-main"
        and d1[K_OBJ] == "director-camera-main"
        and d1[K_OTYPE] == "camera"
        and d2[K_FOLLOW] is not None
        and d3[K_LOCK] is True,
        {"B2 选中轨道": d1[K_TRACK], "B2 选中对象": d1[K_OBJ],
         "B2 对象类型": d1[K_OTYPE],
         "B3 跟随目标": d2[K_FOLLOW],
         "B4 相机锁定": d3[K_LOCK],
         "★ 用的入口": {
             "选轨道": "data-director-timeline-object-name",
             "跟随": "data-director-camera-follow-target",
             "锁定": "data-director-inspector-lock"}}))

    # ── S7 ★★★ 决定性：两句同屏**纯 UI 造不出来**
    b8 = at(raw, "B8·★★ 无跟随时开面板 + append ⟹ 面板内应有「没有可追加的时长」")
    b9 = at(raw, "B9·★★★ 纯 UI 点跟随 select 之后（★ 面板还开着吗）")
    b10 = at(raw, "B10·★★★ **真实鼠标**点跟随 select（★ 面板被点关了吗）")
    tips8 = b8["★ 屏幕上的提示"]
    tips9 = b9["★ 屏幕上的提示"]
    tips10 = b10["★ 屏幕上的提示"]
    C.append(ok(
        "S7:★★★ ★★ **「两句同屏」纯 UI 造不出来** —— B9（`select_option()`）能造出来、B10（**真实鼠标**）造不出来",
        "★★★ 本批最重要的发现。★ 两条纯 UI 路径都被堵死：① 先让 append 被拒、再设跟随 ⟹ 设跟随要点**检查器**的 select ⟹ 那一下 pointerdown **落在面板外** ⟹ `:576` **当场关掉面板** ⟹ 面板内那句随之消失；② 先设跟随 ⟹ 开关 **disabled** ⟹ 面板根本开不了。★★ 而 **B9 与 B10 的差别只有「有没有产生 pointerdown」** ⟹ ⟹ ★★ **「用了 Playwright 的 API」不等于「纯 UI」**：`select_option()` 是**程序化设值**、**不产生 pointerdown** ⟹ 它**绕过了**外部点击关闭",
        (b8["★ 面板开着"] is True
         and any(t["文本"] == MSG_DUR and t["在面板内"] for t in tips8)
         and b9["★ 两句同屏了吗"] is True
         and b10["★ 点击前面板开着"] is True
         and b10["★ 点击后面板开着"] is False
         and b10["★ 面板被真实点击关掉了"] is True
         and b10["★ 两句同屏了吗"] is False
         and b10["★ 面板内那句还在吗"] is False),
        {"B8 面板开着": b8["★ 面板开着"], "B8 提示": tips8,
         "B9 两句同屏": b9["★ 两句同屏了吗"], "B9 提示": tips9,
         "B10 点击前面板开着": b10["★ 点击前面板开着"],
         "B10 点击后面板开着": b10["★ 点击后面板开着"],
         "B10 面板被真实点击关掉了": b10["★ 面板被真实点击关掉了"],
         "B10 两句同屏": b10["★ 两句同屏了吗"],
         "B10 提示": tips10}))

    # ── S8 跟随横幅的取消按钮纯 UI 点得动
    b7 = at(raw, "B7·★ 点跟随横幅上的取消（纯 UI 清跟随）")
    C.append(ok(
        "S8:★★ 跟随横幅上的「退出跟随」按钮**纯 UI 点得动**（清掉了跟随目标）",
        "★ `DirectorDesk.tsx:1390` 的注释说：源站那枚按钮**继承了 `pointer-events: none`**（源站本身点不动），clone 是**有意偏离**。★ 本条只判 **clone 自身**的点得动，★ **不声称源站点得动**（未对照）",
        b7["★ 跟随目标清了吗"] is True,
        {"★ 跟随目标清了吗": b7["★ 跟随目标清了吗"],
         "★ 按钮": raw["操作"].get("B7 跟随横幅取消按钮"),
         "★ 矩形": raw["操作"].get("B7 取消按钮矩形")}))

    # ── S9 静态锚点：读数依赖的那几处源码
    tl = (ROOT / "src" / "components" / "director" /
          "DirectorTimeline.tsx").read_text(encoding="utf-8")
    desk = (ROOT / "src" / "components" / "director" /
            "DirectorDesk.tsx").read_text(encoding="utf-8")
    store = (ROOT / "src" / "store" / "canvasStore.ts").read_text(encoding="utf-8")
    anchors = {
        "DirectorTimeline.tsx: 对象名带 data-director-timeline-object-name":
            "data-director-timeline-object-name" in tl,
        "DirectorTimeline.tsx: 对象名 onClick 选的是 group.tracks[0]":
            "selectTimelineTrack(group.tracks[0].id)" in tl,
        "DirectorTimeline.tsx: 面板的 pointerdown 外部点击关闭":
            "presetPanelRef.current?.contains(target)" in tl,
        "DirectorDesk.tsx: 跟随横幅上的取消按钮":
            "data-director-follow-cancel" in desk,
        "canvasStore.ts: 后门是我挂的（不是源站产品的一部分）":
            "window.__libtv_store = useCanvasStore" in store,
    }
    C.append(ok(
        "S9:★ 静态锚点：对象名的标记与 onClick、面板的外部点击关闭、跟随横幅取消按钮、以及**后门是我自己挂的**",
        "★ 静态锚点与运行时读数**互为独立来源**。★ 特别把「`window.__libtv_store` 是 clone 源码里挂的」这条**写进锚点** ⟹ 因为它是**本批全部反省的根据**：源站产品里根本没有这个全局 ⟹ 任何依赖它的探针**都不能**证明「用户能走到那里」",
        all(anchors.values()), anchors))

    return C


# ══════════════════════ 阴性对照 ══════════════════════

def n9_fake_reachable(raw):
    """把 B10 的「面板被真实点击关掉了」改成 True ⟹ S7 必须翻红。"""
    r = copy.deepcopy(raw)
    row = at(r, "B10·★★★ **真实鼠标**点跟随 select（★ 面板被点关了吗）")
    row["★ 点击后面板开着"] = True
    row["★ 面板被真实点击关掉了"] = False
    return r


def n10_fake_order(raw):
    """把 B5 的默认选中轨道改成相机轨道 ⟹ S5 必须翻红。"""
    r = copy.deepcopy(raw)
    row = at(r, "B1·点「打开导演台」")
    row["读数"][K_TRACK] = "director-track-camera-main"
    return r


def n11_fake_select_write(raw):
    """把 B6b（第一次 select_option 之后）的跟随目标改掉 ⟹ S6 必须翻红。"""
    r = copy.deepcopy(raw)
    row = at(r, "B3·在检查器里选跟随目标（纯 UI）")
    row["读数"][K_FOLLOW] = None
    return r


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    checks = build_checks(raw)

    neg = []
    for label, mut, expect in [
        ("N9 把 B10「面板被真实点击关掉了」改成 False ⟹ S7 翻红",
         n9_fake_reachable, "S7"),
        ("N10 把 B5 的默认选中轨道改成相机 ⟹ S5 翻红",
         n10_fake_order, "S5"),
        ("N11 把 B3 的跟随目标抹成 null ⟹ S6 翻红",
         n11_fake_select_write, "S6"),
    ]:
        mutated = mut(raw)
        mc = build_checks(mutated)
        turned = [c["id"].split(":")[0] for c in mc if not c["ok"]]
        neg.append({"name": label, "期望翻红": expect, "实际翻红": turned,
                    "ok": expect in turned})

    passed = sum(1 for c in checks if c["ok"])
    report = {"batch": 823,
              "totals": {"passed": passed, "total": len(checks)},
              "阴性对照": {"passed": sum(1 for n in neg if n["ok"]),
                            "total": len(neg)},
              "checks": checks, "阴性": neg}
    out = BATCH / "verify-report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print("主检查 %d/%d ｜ 阴性对照 %d/%d" % (
        passed, len(checks), report["阴性对照"]["passed"], len(neg)))
    for c in checks:
        print(("  ✔ " if c["ok"] else "  ✘ ") + c["id"][:66])
    for n in neg:
        print(("  ✔ " if n["ok"] else "  ✘ ") + n["name"][:58]
              + " → 实际翻红 " + ",".join(n["实际翻红"]))
    return 0 if passed == len(checks) and all(n["ok"] for n in neg) else 1


if __name__ == "__main__":
    sys.exit(main())
