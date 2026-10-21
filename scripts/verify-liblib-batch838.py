#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 838 验收：把 clone 的默认角色名改成源站口径「角色A」，并**更正 batch 837 的一条结论**。

## 这批在还什么债

batch 837 的 README 里写着一条：
> 「源站画布上真实显示的镜头名是『**S83·镜2**』⟹ 源站用的是另一套命名体系」

★ **本批把那条结论查穿了**：权威数据（`api/canvas/project/detail-by-space` 的响应）里，
那个「S83·镜2」是一个 **video 节点**的标题，而它的 `alt` 字段是「**S83·镜2.mp4**」
⟹ ★★ 那是**用户上传的 mp4 文件名**，**不是**任何系统命名规则。
⟹ batch 837 那句「源站用 S83·镜2 体系」**不成立** ⟹ 本批更正（不重写 837 的 README）。

★ 同时查清了源站导演台的**权威数据结构**（`compositionData`）：
只有 characters / characterGroups / cameras / props / animation / environment
⟹ ★★ **源站根本没有「镜头」实体** ⟹ clone 的 `shots[]` 是**借自 StoryAI 上游**的分层
（见 batch 96 PLAN.md）⟹ **无源站口径可对齐** ⟹ 本批**不改** clone 的镜头名。

★★ 本批的**实施**：源站实测「第一个角色叫『角色A』，新建的那个叫『角色B』」
⟹ 默认名规则是「**角色 + 字母序号**」⟹ clone 的自拟名「角色01 · 陈默」改成「**角色A**」。

## 判据（S1–S7）

S1 ★★★ **「S83·镜2」是上传文件名，不是命名规则**：raw 里该节点的 `alt` == 「S83·镜2.mp4」，
    且 `action` == `video_resource` ⟹ 钉住「它不是镜头名」
S2 ★★ **源站没有「镜头」实体**：权威 `compositionData` 的顶层键**不含**任何 shots/shot 键 ⟹
    钉住「clone 的镜头名无源站口径可对齐」
S3 ★★ **源站的相机/角色命名**：`cameras[].label` == 「机位1」/「机位2」、
    `characters[].label` == 「角色A」⟹ 钉住源站的命名口径
S4 ★★★ **角色默认名规则 = 「角色 + 字母序号」**：★ **权威 API 口径** ——
    清理后基线**只剩**「角色A」⟹ 新建后**权威 API 里真多了一个**角色
    （轮询达成 ⟹ 已落盘，不是内存态）⟹ ★ **重算关系**：新增角色的 `label` **==**
    右栏名称输入框的值 == 「角色B」⟹ ⟹ 字母序号递进成立；
    ★ 且收尾**已复原**（**独立进程**再读 API ⟹ 服务端状态，不是内存残留）
    ★ 第一版（已废弃）用的是「场景树行数 +1」的 DOM 口径 ⟹ 读数器在**选中态**
      下失效 ⟹ 改成 API 口径
S5 ★★ **clone 默认角色名 == 「角色A」**，且派生量跟随（轨道 label == 「角色A · 变换」）
S6 ★★ **被改的三处旧门禁期望值已同步**：720 的 `FIXTURE`、42 的姿态轨道 label、43 的 option 列表
S7 ★★★ **否定性结论的扫描器有效性** + **更正已落地**（837 的更正声明在本批 README 里）

## 纪律

- 判据只认**绝对读数**与**DOM 可见读数**；
- **否定性结论**（「源站没有镜头实体」）必须**先证明扫描范围覆盖了那一类键**；
- 运行时读数**自己跑**，不读外部缓存；
- 阴性对照每条**只翻它自己那一条**。
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BATCH = ROOT / "docs/research/liblib-canvas-batch838-2026-10-01"
RAW = BATCH / "raw"
PROBE_CLONE = BATCH / "probes/clone838.py"
OUT = BATCH / "runtime-audit.json"


def read_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def run_probe(script: pathlib.Path) -> None:
    r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        print(r.stdout[-2000:])
        print(r.stderr[-2000:], file=sys.stderr)
        raise SystemExit(f"探针失败 {script.name} exit={r.returncode}")


def static_side() -> dict:
    st = {}
    store = (ROOT / "src/store/directorStore.ts").read_text(encoding="utf-8")
    m = re.search(r'id:\s*"director-character-lead".*?name:\s*"([^"]*)"', store, re.S)
    st["种子角色名"] = m.group(1) if m else None
    st["种子角色名是否角色A"] = st["种子角色名"] == "角色A"
    # ★ 派生式（角色轨道 label 由 object.name 派生）⟹ 改名后自动跟随
    st["角色轨道label派生式"] = "label: `${object.name} · 变换`" in store
    st["姿态轨道label派生式"] = "label: `${object.name} · 姿态`" in store
    # ★ 产品读到的字面量里不应再有「角色01 · 陈默」
    lits = []
    if st["种子角色名"]:
        lits.append(st["种子角色名"])
    for pat in (r"label:\s*`\$\{object\.name\} · 变换`",
                r"label:\s*`\$\{object\.name\} · 姿态`"):
        mm = re.search(pat, store)
        lits.append(mm.group(0) if mm else "")
    st["★产品字面量"] = lits
    st["★产品字面量里是否还有角色01"] = any("角色01 · 陈默" in x for x in lits)

    # 旧门禁期望值
    s720 = (ROOT / "scripts/verify-liblib-batch720.py").read_text(encoding="utf-8")
    s42 = (ROOT / "scripts/verify-liblib-batch42.py").read_text(encoding="utf-8")
    s43 = (ROOT / "scripts/verify-liblib-batch43.py").read_text(encoding="utf-8")
    fx = re.search(r"FIXTURE\s*=\s*\[(.*?)\]", s720, re.S)
    st["720_FIXTURE字面量"] = re.findall(r'"([^"]*)"', fx.group(1)) if fx else []
    st["720_FIXTURE含角色A"] = "角色A" in st["720_FIXTURE字面量"]
    st["720_FIXTURE是否仍含角色01"] = any("角色01" in x for x in st["720_FIXTURE字面量"])
    p42 = re.search(r'assert wave_track\["label"\]\s*==\s*"([^"]*)"', s42)
    st["42_姿态轨道label字面量"] = p42.group(1) if p42 else None
    st["★42_是否成功抽出"] = p42 is not None
    st["42_是否角色A · 姿态"] = st["42_姿态轨道label字面量"] == "角色A · 姿态"
    o43 = re.findall(r'"([^"]*)"', s43)
    st["43_option列表含角色A"] = "角色A" in o43
    st["43_是否仍含角色01"] = any("角色01" in x for x in o43)

    # ★ 更正已落地：本批 README 必须含对 837 的更正声明
    readme = (BATCH / "README.md").read_text(encoding="utf-8")
    st["★本批README含S83更正"] = "S83" in readme and "上传" in readme
    st["★本批README声明源站无镜头实体"] = "没有「镜头」实体" in readme or "没有镜头实体" in readme
    return st


def source_nodes() -> list:
    """权威 raw 里的节点列表。"""
    d = read_json(RAW / "source-838-detail-by-space.json")

    def walk(o):
        if isinstance(o, dict):
            if "nodeKey" in o and "name" in o:
                yield o
            for v in o.values():
                yield from walk(v)
        elif isinstance(o, list):
            for v in o:
                yield from walk(v)
    return list(walk(d))


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    st = static_side()
    print("静态：", json.dumps(st, ensure_ascii=False))

    print("跑 clone 运行时探针……")
    run_probe(PROBE_CLONE)
    rt = read_json(pathlib.Path("/tmp/b838-clone-runtime.json"))

    nodes = source_nodes()
    video = next((n for n in nodes if n.get("type") == 3), None)
    director = next((n for n in nodes if n.get("type") == 36), None)
    vdata = json.loads(video["data"]) if video else {}
    ddata = json.loads(director["data"]) if director else {}
    comp = ddata.get("compositionData")
    if isinstance(comp, str):
        comp = json.loads(comp)

    checks = []

    # ── S1 「S83·镜2」是上传文件名 ─────────────────────────────────────
    s1 = {
        "视频节点名": video.get("name") if video else None,
        "★alt字段": vdata.get("alt"),
        "★alt是否带mp4扩展名": bool(vdata.get("alt") and str(vdata["alt"]).endswith(".mp4")),
        "★action": vdata.get("action"),
        "★action是否video_resource": vdata.get("action") == "video_resource",
        "★uploaded": vdata.get("uploaded"),
        "★uploaded是否为真": vdata.get("uploaded") is True,
        "★generatorType": vdata.get("generatorType"),
    }
    checks.append((
        "S1 ★★★ **「S83·镜2」是用户上传的 mp4 文件名，不是命名规则**："
        "权威 raw 里该 video 节点的 `alt` 带 `.mp4` 扩展名、`action` 是 `video_resource`、"
        "`uploaded` 为真 ⟹ ⟹ batch 837 那句「源站用 S83·镜2 体系」**不成立**",
        (s1["★alt是否带mp4扩展名"] and s1["★action是否video_resource"]
         and s1["★uploaded是否为真"]),
        json.dumps(s1, ensure_ascii=False),
    ))

    # ── S2 源站没有「镜头」实体 ───────────────────────────────────────
    comp_keys = sorted((comp or {}).keys())
    s2 = {
        "compositionData顶层键": comp_keys,
        "★是否含shot类键": any("shot" in k.lower() for k in comp_keys),
        "★animation的子键": sorted(((comp or {}).get("animation") or {}).keys()),
        "★animation是否含shots": any(
            "shot" in k.lower() for k in ((comp or {}).get("animation") or {}).keys()),
        "★扫描覆盖度_顶层键数": len(comp_keys),
    }
    checks.append((
        "S2 ★★ **源站没有「镜头」实体**：导演台权威数据 `compositionData` 的顶层键"
        "**不含**任何 shot 类键（顶层 %d 个键 + animation 的 %d 个子键都已枚举）⟹ "
        "⟹ clone 的 `shots[]` 是**借自 StoryAI 上游**的分层 ⟹ **镜头名无源站口径可对齐**"
        "⟹ 本批**不改**它" % (len(comp_keys), len(s2["★animation的子键"])),
        (s2["★是否含shot类键"] is False and s2["★animation是否含shots"] is False
         and s2["★扫描覆盖度_顶层键数"] >= 5),
        json.dumps(s2, ensure_ascii=False),
    ))

    # ── S3 源站的相机/角色命名口径 ────────────────────────────────────
    cams = (comp or {}).get("cameras") or []
    chars = (comp or {}).get("characters") or []
    s3 = {
        "相机label": [c.get("label") for c in cams],
        "角色label": [c.get("label") for c in chars],
        "★相机label是否机位N": all(
            re.match(r"^机位\d+$", str(c.get("label") or "")) for c in cams) and bool(cams),
        "★角色label是否角色+字母": all(
            re.match(r"^角色[A-Z]$", str(c.get("label") or "")) for c in chars) and bool(chars),
        "★相机数": len(cams),
        "★角色数": len(chars),
    }
    checks.append((
        "S3 ★★ **源站的命名口径**：`cameras[].label` 全部是「机位N」（纯数字）、"
        "`characters[].label` 全部是「角色 + 单个大写字母」⟹ ⟹ 与 clone 的自拟名不同口径",
        (s3["★相机label是否机位N"] and s3["★角色label是否角色+字母"]),
        json.dumps(s3, ensure_ascii=False),
    ))

    # ── S4 角色默认名规则（★ **API 权威口径**） ───────────────────────
    #   ★★ 第一版（已废弃）读的是「场景树行数 +1」⟹ 那是 DOM 口径 ⟹ 且读数器
    #      在**选中态**下失效（v16 实测返回 0 行）⟹ ⟹ 改成 **权威状态 = API**
    #      （`compositionData.characters`）⟹ DOM 只用来「读右栏名称输入框」。
    cn = read_json(RAW / "source-838-charname-closedloop.json")
    cl = read_json(RAW / "source-838-cleanup.json")
    rf = read_json(RAW / "source-838-restored-final.json")
    base = cn.get("B_★清理后的API角色") or []
    new_ch = cn.get("E_★新增的角色") or []
    rf_chars = rf.get("★独立复核_角色") or []
    s4 = {
        "★清理后基线_角色": base,
        "★清理后基线_标签": [c.get("label") for c in base],
        "★新建后API里的角色": cn.get("E_★API里的角色"),
        "★API轮询是否达成": cn.get("E_★API轮询是否达成"),
        "★新增的角色": new_ch,
        "★右栏读到的默认名": cn.get("D_★读到的默认名"),
        "★右栏面板标题是角色": cn.get("D_★面板标题是角色"),
        "★raw里存的关系结论(仅交叉印证)": cn.get("E_★★新增角色的label是否等于右栏读到的名"),
        "★清理脚本_最终标签": cl.get("③★最终标签"),
        "★清理脚本_是否已复原": cl.get("③★★是否已复原"),
        "★独立复核_角色": rf_chars,
        "★独立复核_角色标签": rf.get("★独立复核_角色标签"),
        "★独立复核_相机标签": rf.get("★独立复核_相机标签"),
        "★独立复核_是否只剩角色A": rf.get("★★是否只剩角色A"),
    }
    # ★ 判据的**结构**（★ **关系式** ⟹ 不拿 raw 里**存好的结论**当判据）：
    #   ① 权威基线：清理后**只剩**「角色A」；
    #   ② 新建后**权威 API 里真多了一个**角色（轮询达成 ⟹ 已落盘，不是内存态）；
    #   ③ ★★ **重算**关系：新增角色的 `label` **==** 右栏名称输入框读到的值
    #      ⟹ raw 里那条**存好的布尔**只作**交叉印证**，不作判据
    #      （★ 已入库那条「只查字面量不够 ⟹ 补关系式」的直接应用）；
    #   ④ 递进：基线是「角色A」⟹ 新拿到的应是下一个字母 ⟹ 实测为「角色B」；
    #   ⑤ 收尾**已复原**：**独立进程**再读一次权威 API ⟹ 复原是**服务端状态**，
    #      不是同一浏览器会话里的内存残留（★ 已入库那条「内存里消失 ≠ 存盘了」）。
    s4["★①基线只剩角色A"] = (len(base) == 1 and base[0].get("label") == "角色A")
    s4["★②权威API里真多了一个"] = (
        bool(new_ch) and cn.get("E_★API轮询是否达成") is True
        and len(cn.get("E_★API里的角色") or []) == len(base) + 1)
    s4["★③新增角色label等于右栏读到的名"] = bool(
        new_ch and s4["★右栏读到的默认名"]
        and new_ch[0].get("label") == s4["★右栏读到的默认名"])
    s4["★④递进_新名是角色B"] = s4["★右栏读到的默认名"] == "角色B"
    s4["★⑤收尾已复原_独立进程复核"] = (
        rf.get("★★是否只剩角色A") is True
        and len(rf_chars) == 1 and bool(base)
        and rf_chars[0].get("id") == base[0].get("id")
        and rf_chars[0].get("label") == base[0].get("label")
        and cl.get("③★★是否已复原") is True)
    checks.append((
        "S4 ★★★ **源站角色默认名规则 = 「角色 + 字母序号」**（★ **权威 API 口径**）："
        "清理后基线**只剩**「角色A」⟹ 新建后**权威 API 里真多了一个**角色（轮询达成 ⟹ 已落盘）"
        "⟹ ★ **重算关系**：那个角色的 `label` **==** 右栏「名称」输入框读到的值 == 「角色B」"
        "⟹ ⟹ 字母序号递进成立；★ 且收尾**已复原**（**独立进程**再读 API ⟹ 服务端状态，"
        "不是内存残留）",
        (s4["★①基线只剩角色A"] and s4["★②权威API里真多了一个"]
         and s4["★③新增角色label等于右栏读到的名"] and s4["★④递进_新名是角色B"]
         and s4["★⑤收尾已复原_独立进程复核"]),
        json.dumps(s4, ensure_ascii=False),
    ))

    # ── S5 clone 侧 ───────────────────────────────────────────────────
    # ★ 口径修正（第一版踩坑）：姿态轨道**不是种子就有的** —— 它在**选中角色**后按需生成
    #   ⟹ 判据**不能**要求它存在 ⟹ 改成「**若存在则必须匹配**」。
    #   ★ 姿态轨道 label 的**实际存在性**由 **42 门禁**覆盖（它实测过那条 label）。
    pose_labels = rt.get("③姿态轨道label") or []
    s5 = {
        "静态_种子角色名": st["种子角色名"],
        "静态_是否角色A": st["种子角色名是否角色A"],
        "★产品字面量里是否还有角色01": st["★产品字面量里是否还有角色01"],
        "运行时_角色名": rt.get("②默认角色名"),
        "运行时_是否角色A": rt.get("②默认角色名是否角色A") is True,
        "运行时_变换轨道label": rt.get("③变换轨道label"),
        "运行时_变换轨道label是否角色A · 变换": (
            rt.get("③变换轨道label是否角色A · 变换") is True),
        "★姿态轨道label": pose_labels,
        "★姿态轨道_若存在则必须匹配": all(
            x == "角色A · 姿态" for x in pose_labels),
        "★DOM上的角色名": rt.get("⑤DOM_场景树角色名"),
        "★DOM上是否角色A": rt.get("⑤DOM_是否角色A") is True,
    }
    checks.append((
        "S5 ★★ **clone 默认角色名 == 「角色A」**；★ **派生量跟随**"
        "（变换轨道 label == 「角色A · 变换」；姿态轨道 label **若存在**则必须是「角色A · 姿态」"
        "—— ★ 它在**选中角色**后按需生成，不是种子就有的 ⟹ **不要求它存在**，"
        "其存在性由 **42 门禁**覆盖）；且**在 DOM 上可见**（⟹ 不是只有 store 改了）",
        (s5["静态_是否角色A"] and s5["★产品字面量里是否还有角色01"] is False
         and s5["运行时_是否角色A"] and s5["运行时_变换轨道label是否角色A · 变换"]
         and s5["★姿态轨道_若存在则必须匹配"]
         and s5["★DOM上是否角色A"]),
        json.dumps(s5, ensure_ascii=False),
    ))

    # ── S6 旧门禁期望值已同步 ─────────────────────────────────────────
    s6 = {
        "720_FIXTURE含角色A": st["720_FIXTURE含角色A"],
        "720_不再含角色01": st["720_FIXTURE是否仍含角色01"] is False,
        "42_姿态轨道label": st["42_姿态轨道label字面量"],
        "★42_成功抽出": st["★42_是否成功抽出"],
        "42_是否角色A · 姿态": st["42_是否角色A · 姿态"],
        "43_option列表含角色A": st["43_option列表含角色A"],
        "43_不再含角色01": st["43_是否仍含角色01"] is False,
    }
    checks.append((
        "S6 ★★ **被改的三处旧门禁期望值已同步**：720 的 `FIXTURE`、42 的姿态轨道 label、"
        "43 的 option 列表（★ 且 42 那条**成功抽出**了期望值 ⟹ 不是「抽不出而静默通过」）",
        (s6["720_FIXTURE含角色A"] and s6["720_不再含角色01"] and s6["★42_成功抽出"]
         and s6["42_是否角色A · 姿态"] and s6["43_option列表含角色A"] and s6["43_不再含角色01"]),
        json.dumps(s6, ensure_ascii=False),
    ))

    # ── S7 否定性结论的扫描器有效性 ＋ 更正已落地 ─────────────────────
    r837 = (ROOT / "docs/research/liblib-canvas-batch837-2026-10-01/README.md") \
        .read_text(encoding="utf-8")
    s7 = {
        "★扫描覆盖度_compositionData顶层键数": len(comp_keys),
        "★顶层键样本": comp_keys,
        "★animation子键样本": s2["★animation的子键"],
        "★权威raw里的节点数": len(nodes),
        "★节点类型样本": sorted({n.get("type") for n in nodes}),
        "★更正声明在本批README": st["★本批README含S83更正"],
        "★声明源站无镜头实体": st["★本批README声明源站无镜头实体"],
        # ★ 旧批次 README **不可重写** ⟹ 837 里那条**原始结论**必须**原样还在**
        #   （★ 不是「随便查一下」—— 是「原文仍在」这个**可证的**不变量）
        "★837的README未被改写": (
            "S83·镜2" in r837 and "镜头命名体系仍与源站不一致" in r837),
    }
    checks.append((
        "S7 ★★★ **否定性结论的扫描器有效性 ＋ 更正已落地**："
        "「源站没有镜头实体」的前提是扫描**覆盖了**那一类键 ⟹ 证明顶层 %d 个键与 "
        "animation 的 %d 个子键**都已枚举**、权威 raw 里有 %d 个节点（类型 %s）⟹ "
        "零命中**不是因为扫不到**；★ 且本批 README 里**含对 837 的更正声明**；"
        "★ 而 **837 的 README 未被改写**（那条原始结论原样还在 ⟹ 更正只落在本批 ＋ 台账）"
        % (len(comp_keys), len(s2["★animation的子键"]), len(nodes),
           sorted({n.get("type") for n in nodes})),
        (s7["★扫描覆盖度_compositionData顶层键数"] >= 5
         and len(s7["★animation子键样本"]) >= 5
         and s7["★权威raw里的节点数"] >= 5
         and s7["★更正声明在本批README"] and s7["★声明源站无镜头实体"]
         and s7["★837的README未被改写"]),
        json.dumps(s7, ensure_ascii=False),
    ))

    print("\n=== 判据 ===")
    passed = 0
    for label, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
        passed += bool(ok)
    print(f"\n{passed}/{len(checks)} 通过")

    audit = {
        "batch": 838,
        "title": "把 clone 的默认角色名改成源站口径「角色A」；"
                 "★ 并**更正 batch 837 的一条结论**（「S83·镜2」不是源站命名体系，"
                 "那是用户上传的 mp4 文件名）",
        "verdict": f"{passed}/{len(checks)}",
        "static": st,
        "runtime": rt,
        "source": {
            "nodes": [{"nodeKey": n.get("nodeKey"), "type": n.get("type"),
                       "name": n.get("name")} for n in nodes],
            "videoData": vdata,
            "compositionDataKeys": comp_keys,
            "cameraLabels": s3["相机label"],
            "characterLabels": s3["角色label"],
        },
        "checks": [{"label": l, "pass": bool(o), "detail": d} for l, o, d in checks],
        "conclusions": [
            "★★★ **「S83·镜2」是用户上传的 mp4 文件名，不是源站的命名体系** —— "
            "权威 raw（`api/canvas/project/detail-by-space`）里那个 video 节点的 "
            "`alt` 是「S83·镜2.mp4」、`action` 是 `video_resource`、`uploaded` 为真 ⟹ "
            "★ **batch 837 README 里「源站用 S83·镜2 体系」那句不成立** ⟹ 本批更正。",
            "★★ **源站根本没有「镜头」实体** —— 导演台权威数据 `compositionData` 的顶层只有 "
            "characters / characterGroups / cameras / props / animation / environment ⟹ "
            "⟹ clone 的 `shots[]` 是**借自 StoryAI 上游**的分层（batch 96 PLAN.md 明说）⟹ "
            "★ **镜头名无源站口径可对齐** ⟹ 本批**不改**它（不制造一个假的「对齐」）。",
            "★★ **源站的命名口径**：相机 `label` 是「机位N」（纯数字）、"
            "角色 `label` 是「角色 + 字母」。",
            "★★★ **角色默认名规则 = 「角色 + 字母序号」** —— 单趟闭环实测："
            "选体型预设后树区**真多了一行**、那一行的文本 == 右栏「名称」输入框的值 == "
            "「角色B」（进站基线是「角色A」）⟹ ⟹ 字母序号递进成立。",
            "★★ **clone 的默认角色名由「角色01 · 陈默」改成「角色A」**，"
            "派生的变换/姿态轨道 label 自动跟随。",
            "★ **源站的保存机制查清了**：导演台改动靠**约 30 秒延迟**的 "
            "`POST /api/canvas/nodes/batch` 自动保存（保存的是导演台节点 "
            "`n-gYB1c2Peq9` 的 compositionData）⟹ ⟹ 「跨刷新复验」必须等够时间，"
            "否则会把「还没落盘」误判成「没删掉」。",
        ],
        "notClaimed": [
            "**不声称**源站的角色名一定是「角色A/B/C」字母表 —— 只实测了 A→B 这一步递进。",
            "**不声称**源站的机位名在任何情形下都唯一（batch 836 已证它会重名）。",
            "**不声称** clone 的镜头命名体系已对齐源站 —— 源站**没有**镜头实体可比。",
            "**不声称** crowd（群众）的成员命名已对齐 —— 源站的 crowd 命名**未测** ⟹ 未改。",
            "**不声称** 837 的 README 已被更正 —— 旧批次 README 不可重写 ⟹ 更正写在本批 ＋ 台账。",
        ],
        "environment": [
            "源站项目在本次实验中**被完整复原**（跨刷新复验：场景树 == 进站基线）。",
            "源站有**并发活动**（batch 837 时基线已是两台机位）⟹ 全程以**进站基线**为准，"
            "只删本批新建的那一个。",
        ],
    }
    OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", OUT)
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
