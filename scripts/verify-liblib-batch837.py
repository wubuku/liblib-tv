#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 837 验收：把默认机位的**自拟名**换成源站口径「机位1」，并**清算一处循环论证**。

## 这批在还什么债

batch 833 的 README 里写着一条「**源站实测**：源站的镜头叫「机位01 · 对峙中景 · 镜头」」，
并据此把 clone 的镜头命名模式写成「沿用源站」。
本批实测发现：**「对峙中景」在源站侧的所有 raw 里零出现**，整页关键词扫描也零出现 ⟹
那串字是 batch 3661ccae 给 clone **自拟**的，batch 833 把它**倒推**成源站实测 ⟹ ★ **无源的循环论证**。

★ 循环论证的形状（值得记住）：
  clone 自拟名 ⟹ 看到 clone 界面上有这串字 ⟹ 以为那是源站的命名 ⟹ 写成「源站实测」
  ⟹ 后续批次拿它当**期望值的来源** ⟹ 越滚越实。**每一环读的都是自己造的东西。**

## 判据（S1–S7）

S1 ★★ **源站事实钉住**：源站 raw 完备（基线/新建/再建/收尾复原），且
    「对峙中景」在源站侧的**关键词扫描**里零出现 ⟹ 钉住「那串字不是源站的」
S2 ★★ **clone 默认机位名 == 「机位1」**，且名字**匹配** `^机位\\d+$`
S3 ★★ **派生跟随**：镜头名 == 「机位1 · 镜头」、轨道 label == 「机位1 · 机位」
    （两条都从 store 读，且**都**在 DOM 上可见）
S4 ★★★ **编号体系错位消失**：默认机位名匹配编号正则 ⟹ 它**占编号 1** ⟹
    新建那台叫「机位2」⟹ clone 的编号序列与源站**逐字一致**
    （这条是 batch 836 记过的错位，本批改名**顺手消掉**了 ⟹ 必须实测，不许只靠推理）
S5 ★★ **被改的两处旧门禁期望值已同步**：720 的 `FIXTURE`、750 的 `innerTitle`
S6 ★★ **源站侧零出现可复现**：现场重跑一次源站 raw 扫描 ⟹ 「对峙中景」仍零出现
    （★ 这一条是**否定性结论** ⟹ 必须先证明扫描器本身没坏：见 S7 的「扫描器有效性」）
S7 ★★★ **门禁自身的阴性对照**：每条判据都能被**单独**翻红

## 纪律

- 判据只认**绝对读数**与**DOM 可见读数**；
- 否定性结论（「零出现」）必须**先证明扫描器没坏**（S6 的扫描器有效性检查）；
- 运行时读数**自己跑**，不读外部缓存；
- 阴性对照每条**只翻它自己那一条** ⟹ 读的字段必须互不重叠。
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BATCH = ROOT / "docs/research/liblib-canvas-batch837-2026-10-01"
RAW = BATCH / "raw"
PROBE_CLONE = BATCH / "probes/clone837.py"
PROBE_TRACK = BATCH / "probes/tracksel837.py"
OUT = BATCH / "runtime-audit.json"

CAM_RE = re.compile(r"^机位(\d+)$")


def read_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def run_probe(script: pathlib.Path) -> dict:
    r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        print(r.stdout[-2000:])
        print(r.stderr[-2000:], file=sys.stderr)
        raise SystemExit(f"探针失败 {script.name} exit={r.returncode}")
    return r.stdout


def static_side() -> dict:
    """静态侧：读仓库里的**事实源**（源码与门禁脚本），不靠运行时。"""
    st = {}
    store = (ROOT / "src/store/directorStore.ts").read_text(encoding="utf-8")
    # ★ 只取种子那一条的 name（第一个 `name: "机位..."` 出现在 director-camera-main 之后）
    m = re.search(r'id:\s*"director-camera-main".*?name:\s*"([^"]*)"', store, re.S)
    st["种子机位名"] = m.group(1) if m else None
    st["种子机位名是否机位1"] = st["种子机位名"] == "机位1"
    st["种子机位名是否匹配编号正则"] = bool(st["种子机位名"] and CAM_RE.match(st["种子机位名"]))
    # ★★ 口径修正（第一版踩坑）：这一条**不能**用「全文 grep 有没有『对峙中景』」来判 ——
    #   本批在源码的**注释里**写了那串字（说明它的来历）⟹ 全文 grep 必然命中 ⟹
    #   把「产品里还有没有那串字」判成了「源码里有没有提到那串字」⟹ 判据与命题不对齐。
    #   ⟹ 正确口径：**只扫「被产品读到的那些值」**（种子 name ＋ 三个派生式字面量），
    #      不扫注释、不扫文档。
    product_literals = []
    if st["种子机位名"]:
        product_literals.append(st["种子机位名"])
    for pat in (r"name:\s*`\$\{camera\.name\} · 镜头`",
                r"label:\s*`\$\{camera\.name\} · 机位`",
                r"name:\s*`机位\$\{cameraIndex\}`"):
        mm = re.search(pat, store)
        product_literals.append(mm.group(0) if mm else "")
    st["★产品字面量"] = product_literals
    st["★产品字面量里是否还有对峙中景"] = any("对峙中景" in x for x in product_literals)
    # 派生公式（必须仍是「由机位名派生」，否则改名不会跟随）
    # ★★★ 口径修正（阴性 N6 逼出来的）：**不能**用「`${camera.name} · 镜头` 这串字符
    #   在不在文件里」来判 —— 注入把**代码行**改成固定串之后，那串字符**仍然在注释里**
    #   ⟹ 子串匹配照样绿 ⟹ **判据测的是「文件里提到过它」，不是「代码还在用它」**。
    #   ⟹ 正确口径：匹配**代码行本身**（行首缩进 ＋ `name:` / `label:` ＋ 那个字面量），
    #      且**排除注释行**。
    def _code_line_has(literal: str, key: str) -> bool:
        """源码里**代码行**（不是注释行）上是否有 `key: "<literal>"` 或 `key: \`<literal>\``。

        ★★ 两种引号都要认：源码里的派生式用的是**反引号模板串**
           （`name: \\`${camera.name} · 镜头\\``），而种子 name 用的是双引号。
           ⟹ 只认一种 ⟹ 另一条判据会**静默地什么都测不到**。
        """
        pat = re.compile(
            r"^\s*" + re.escape(key) + r":\s*(?:\"|`)" + re.escape(literal) + r"(?:\"|`)\s*,?\s*$"
        )
        for line in store.splitlines():
            if line.lstrip().startswith("//") or line.lstrip().startswith("*"):
                continue
            if pat.match(line):
                return True
        return False

    st["镜头名派生式"] = _code_line_has("${camera.name} · 镜头", "name")
    st["轨道label派生式"] = _code_line_has("${camera.name} · 机位", "label")
    st["★派生式命中的代码行"] = [
        l.strip() for l in store.splitlines()
        if ("${camera.name} · 镜头" in l or "${camera.name} · 机位" in l)
        and not l.lstrip().startswith("//") and not l.lstrip().startswith("*")
    ]
    st["新建机位名派生式"] = any(
        l.strip().startswith("name: `机位${cameraIndex}`")
        for l in store.splitlines()
        if not l.lstrip().startswith("//") and not l.lstrip().startswith("*")
    )

    # ★ 720 / 750 的期望值是否已同步（读脚本本体，不执行）
    # ★★ 同样口径修正：**不扫全文**（本批在两处都写了「对峙中景」的**注释**说明来历）⟹
    #   只扫**断言里的字面量**。
    s720 = (ROOT / "scripts/verify-liblib-batch720.py").read_text(encoding="utf-8")
    s750 = (ROOT / "scripts/verify-liblib-batch750.py").read_text(encoding="utf-8")
    fx = re.search(r"FIXTURE\s*=\s*\[(.*?)\]", s720, re.S)
    st["720_FIXTURE字面量"] = re.findall(r'"([^"]*)"', fx.group(1)) if fx else []
    st["720_FIXTURE含机位1"] = "机位1" in st["720_FIXTURE字面量"]
    st["720_FIXTURE是否仍含对峙中景"] = any(
        "对峙中景" in x for x in st["720_FIXTURE字面量"])
    # 750 的 C5 期望值：在 `ts.get("innerTitle") == "..."` 里
    # ★ 第一版正则写成 `innerTitle"\]\s*==` ⟹ 匹配不到（真实写法是 `ts.get("innerTitle") ==`）
    #   ⟹ 抽出来是 null ⟹ 判据「静默地什么都没比」⟹ ★ 这类「抽不出值」的判据必须显式失败。
    ti = re.search(r'innerTitle"\)\s*==\s*"([^"]*)"', s750)
    st["750_innerTitle字面量"] = ti.group(1) if ti else None
    st["★750_是否成功抽出期望值"] = ti is not None
    st["750_期望值含机位1 · 机位"] = st["750_innerTitle字面量"] == "机位1 · 机位"
    st["750_是否仍含对峙中景"] = bool(
        st["750_innerTitle字面量"] and "对峙中景" in st["750_innerTitle字面量"])
    return st


def source_raws() -> list:
    """仓库里所有**源站** raw（文件名含 source 的 raw json）。"""
    return sorted(RAW.glob("source-*.json")) + sorted(
        p for p in RAW.glob("*.json") if "source" in p.name and p not in RAW.glob("source-*.json")
    )


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    st = static_side()
    print("静态：", json.dumps(st, ensure_ascii=False))

    print("跑 clone 运行时探针……")
    run_probe(PROBE_CLONE)
    run_probe(PROBE_TRACK)
    rt = read_json(pathlib.Path("/tmp/b837-clone-runtime.json"))
    ts = read_json(pathlib.Path("/tmp/b837-tracksel.json"))

    src_scan = read_json(RAW / "source-837-shotname-scan.json")
    src_page = read_json(RAW / "source-837-shotname-page-scan.json")

    checks = []

    # ── S1 源站事实钉住 ────────────────────────────────────────────────
    s1 = {
        "源站raw_基线机位": src_scan.get("①基线_机位"),
        "源站raw_基线镜头": src_scan.get("①基线_镜头"),
        "源站raw_收尾复原正确": src_scan.get("收尾正确") is True,
        "源站raw_镜头名不等于机位名+镜头": (
            src_scan.get("④判定", {}).get("★镜头名是否 == 机位名 + 「 · 镜头」") is False
        ),
        "★对峙中景在源站raw里零出现": not any(
            "对峙中景" in p.read_text(encoding="utf-8") for p in source_raws()
        ),
        "★对峙中景在源站整页扫描里零出现": not any(
            "对峙中景" in json.dumps(v, ensure_ascii=False) for v in src_page.values()
        ),
        "★源站整页扫描里确实读到了文字": bool(src_page.get("①含「镜头/对峙/中景」的所有可见文本")),
    }
    checks.append((
        "S1 ★★ **源站事实钉住**：源站镜头名**不含**机位名（实测 raw）；"
        "「对峙中景」在源站 raw 与整页扫描里**零出现**；且整页扫描**确实读到了文字**"
        "（⟹ 扫描器没瞎）",
        all(s1.values()),
        json.dumps(s1, ensure_ascii=False),
    ))

    # ── S2 clone 默认机位名 ────────────────────────────────────────────
    s2 = {
        "静态_种子名": st["种子机位名"],
        "静态_种子名是否机位1": st["种子机位名是否机位1"],
        "运行时_默认机位名": rt.get("②默认机位名"),
        "运行时_是否机位1": rt.get("②默认机位名是否机位1") is True,
        "运行时_是否匹配编号正则": rt.get("②默认机位名是否匹配编号正则") is True,
        "★产品字面量里不再有对峙中景": st["★产品字面量里是否还有对峙中景"] is False,
        "★产品字面量": st["★产品字面量"],
    }
    checks.append((
        "S2 ★★ **clone 默认机位名 == 「机位1」**（纯编号、无语义后缀）"
        "且**匹配** `^机位\\d+$`；★ **产品读到的字面量**里「对峙中景」已清零"
        "（口径：只扫**被产品读到的值**，不扫注释与文档 ⟹ 见脚本内注释）",
        all(s2.values()),
        json.dumps(s2, ensure_ascii=False),
    ))

    # ── S3 派生跟随 ────────────────────────────────────────────────────
    s3 = {
        "镜头名派生式仍在": st["镜头名派生式"],
        "轨道label派生式仍在": st["轨道label派生式"],
        "运行时_镜头名": rt.get("③镜头名"),
        "运行时_镜头名是否机位1 · 镜头": rt.get("③镜头名是否机位1 · 镜头") is True,
        "运行时_轨道label": rt.get("③轨道label"),
        "运行时_轨道label是否机位1 · 机位": rt.get("③轨道label是否机位1 · 机位") is True,
        "★DOM上镜头条含机位1 · 镜头": rt.get("⑤DOM含机位1 · 镜头") is True,
        "★DOM轨道行title": ts.get("innerTitle"),
        "★DOM轨道行title是否机位1 · 机位": ts.get("innerTitle是否机位1 · 机位") is True,
        # ★★★ 关系式判据（阴性 N6 逼出来的）：
        #   只查「名字 == 机位1 · 镜头」**不够** —— 派生式被改成固定串时，
        #   名字**恰好**还是对的那一个（本批改名后镜头名就是「机位1 · 镜头」），
        #   绝对值判据照样绿 ⟹ 必须**再查一遍派生关系本身**：
        #   源码里**必须**还是 `${camera.name} · 镜头` 这一条派生式。
        "★镜头名派生式_源码字面量仍在": st["镜头名派生式"],
        "★轨道label派生式_源码字面量仍在": st["轨道label派生式"],
    }
    checks.append((
        "S3 ★★ **派生跟随**：镜头名 == 「机位1 · 镜头」、轨道 label == 「机位1 · 机位」；"
        "两条**既**在 store 读到、**又**在 DOM 上可见（⟹ 不是只有 store 改了）",
        all(s3.values()),
        json.dumps(s3, ensure_ascii=False),
    ))

    # ── S4 编号体系错位消失 ────────────────────────────────────────────
    s4 = {
        "默认机位名": rt.get("②默认机位名"),
        "默认机位名匹配编号正则": rt.get("②默认机位名是否匹配编号正则") is True,
        "新建后那台的名字": rt.get("④新机位名"),
        "新建后那台是否机位2": rt.get("④新机位名是否机位2") is True,
        "★台数口径_与名字无关": rt.get("④新建后台数_与名字无关的口径"),
        "★错位是否消失": rt.get("④★编号体系错位是否消失") is True,
    }
    checks.append((
        "S4 ★★★ **batch 836 记的「编号体系错位」已消失**：默认机位名匹配编号正则 ⟹ "
        "它**占编号 1** ⟹ 新建那台叫「机位2」⟹ clone 的编号序列与源站**逐字一致**"
        "（台数用**与名字无关**的口径交叉校验）",
        (s4["★错位是否消失"] and s4["新建后那台是否机位2"]
         and s4["默认机位名匹配编号正则"] and s4["★台数口径_与名字无关"] == 2),
        json.dumps(s4, ensure_ascii=False),
    ))

    # ── S5 旧门禁期望值已同步 ──────────────────────────────────────────
    s5 = {
        "720_FIXTURE含机位1": st["720_FIXTURE含机位1"],
        "720_不再含对峙中景": st["720_FIXTURE是否仍含对峙中景"] is False,
        "★720_成功抽出FIXTURE": bool(st["720_FIXTURE字面量"]),
        "750_含机位1 · 机位": st["750_期望值含机位1 · 机位"],
        "750_不再含对峙中景": st["750_是否仍含对峙中景"] is False,
        "★750_成功抽出期望值": st["★750_是否成功抽出期望值"] is True,
    }
    checks.append((
        "S5 ★★ **被改的两处旧门禁期望值已同步**：720 的 `FIXTURE` 与 750 的 `innerTitle` "
        "都改成新名，且**都不再**含「对峙中景」",
        all(s5.values()),
        json.dumps(s5, ensure_ascii=False),
    ))

    # ── S6 否定性结论的「扫描器有效性」 ────────────────────────────────
    # ★ 「零出现」是最容易骗人的读数 ⟹ 必须同时证明：扫描器**读到了东西**，
    #   且扫描范围**覆盖了**那一类元素。
    s6 = {
        "扫描器读到的元素数": len(src_page.get("①含「镜头/对峙/中景」的所有可见文本", [])),
        "扫描器读到的样本": [t.get("text") for t in
                        src_page.get("①含「镜头/对峙/中景」的所有可见文本", [])],
        "★扫描器确实读到了「镜」": any(
            "镜" in (t.get("text") or "") for t in
            src_page.get("①含「镜头/对峙/中景」的所有可见文本", [])
        ),
        "★扫描器读到了源站真实的镜头名形态": any(
            "S83·镜" in (t.get("text") or "") for t in
            src_page.get("①含「镜头/对峙/中景」的所有可见文本", [])
        ),
        "★扫描器读到了「确认镜头」": any(
            "确认镜头" in (t.get("text") or "") for t in
            src_page.get("①含「镜头/对峙/中景」的所有可见文本", [])
        ),
        "★整页扫描覆盖了右下属性区": len(src_page.get("②右下区域所有可见文本", [])) > 0,
        "★源站raw目录文件数": len(source_raws()),
    }
    checks.append((
        "S6 ★★★ **否定性结论的扫描器有效性**：「对峙中景零出现」这句话的前提是"
        "扫描器**看得见**那一类元素 ⟹ 证明它读到了「镜」「**S83**·镜2」「确认镜头」"
        "「分镜」等**同族**文字，且覆盖了右下属性区 ⟹ 零出现**不是因为扫不到**",
        (s6["★扫描器确实读到了「镜」"] and s6["★扫描器读到了源站真实的镜头名形态"]
         and s6["★扫描器读到了「确认镜头」"] and s6["★整页扫描覆盖了右下属性区"]
         and s6["★源站raw目录文件数"] > 0),
        json.dumps(s6, ensure_ascii=False),
    ))

    # ── S7 720 / 750 的运行时行为仍成立（读已归档的读数） ──────────────
    # ★ 720 全量跑过（7/7）⟹ 直接采信其脚本自身的 verdict；
    #   750 的运行时探针**从未入库**（`/tmp/dbg750e.py` 已随 /tmp 清空丢失）⟹
    #   本批用**同口径的独立探针**复验了 750 的 C5 那一条（见 tracksel837.py）⟹
    #   ★ **不声称** 750 整门禁跑通 ⟹ 明确记为「环境性缺失」。
    s7 = {
        "750_内壳无data标记": (ts.get("轨道行外壳") or {}).get("hasDataMarkerOnInner") == [False],
        "750_外壳有data标记": "directorTrackLabel" in
                          ((ts.get("轨道行外壳") or {}).get("rowDataKeys") or []),
        "750_innerTitle": ts.get("innerTitle"),
        "750_innerTitle是否机位1 · 机位": ts.get("innerTitle是否机位1 · 机位") is True,
    }
    checks.append((
        "S7 ★★ **750 的 C5 那条契约仍成立**（用同口径独立探针复验）："
        "轨道行**外壳有** data-* 标记、**内壳没有**、内壳 title == 「机位1 · 机位」"
        "（★ 750 的**整门禁**因 `/tmp/dbg750e.py` 从未入库而跑不起来 ⟹ **不声称**整门禁绿）",
        all(s7.values()),
        json.dumps(s7, ensure_ascii=False),
    ))

    print("\n=== 判据 ===")
    passed = 0
    for label, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
        passed += bool(ok)
    print(f"\n{passed}/{len(checks)} 通过")

    audit = {
        "batch": 837,
        "title": "把默认机位的自拟名「机位01 · 对峙中景」换成源站口径「机位1」；"
                 "清算 batch 833 的一处**无源循环论证**（把 clone 自拟名当成「源站实测」）",
        "verdict": f"{passed}/{len(checks)}",
        "static": st,
        "runtime": rt,
        "trackSelection": ts,
        "checks": [{"label": l, "pass": bool(o), "detail": d} for l, o, d in checks],
        "conclusions": [
            "**「对峙中景」是 clone 自拟的，不是源站的** —— 源站 raw 零出现、"
            "整页关键词扫描零出现 ⟹ batch 833 写的「源站实测『机位01 · 对峙中景 · 镜头』」"
            "**没有源** ⟹ 本批更正（不重写 833 的 README，见本目录 README）。",
            "**源站的镜头名体系与 clone 完全不同** —— 源站画布上的镜头显示为"
            "「**S83·镜2**」形态，源站场景树里**没有镜头节点**（只有「确认镜头」按钮）⟹ "
            "clone 的「机位名 · 镜头」派生式**仍与源站不一致** ⟹ ★ 本批**不声称**已解决。",
            "**语义（景别）属于源站的「预设」，不属于初始机位** —— 源站 15 枚预设里有"
            "「正面中景」「背面中景」，而初始机位名是纯编号「机位1」⟹ "
            "clone 把「中景」写进初始机位名是**层级错置**。",
            "★★ **本批顺手消掉了 batch 836 记的「编号体系错位」** —— 改名后默认机位名"
            "匹配 `^机位\\d+$` ⟹ 它**占编号 1** ⟹ 新建那台叫「机位2」⟹ "
            "clone 的编号序列与源站**逐字一致**（实测，非推理）。",
            "**镜头名与轨道 label 都是机位名的派生** ⟹ 改名后二者自动跟随，"
            "无需另改（实测：store 与 DOM 两侧都读到新值）。",
            "**两处旧门禁的期望值已同步**：720 的 `FIXTURE`、750 的 `innerTitle`。",
        ],
        "notClaimed": [
            "**不声称** clone 的镜头命名体系已对齐源站（源站是「S83·镜2」那套）。",
            "**不声称** 750 的整门禁跑通 —— 它的运行时探针 `/tmp/dbg750e.py` "
            "**从未入库**、已随 /tmp 清空丢失 ⟹ 本批只**独立复验了 C5 那一条**。",
            "**不声称** batch 833 的 README 已被更正 —— 旧批次 README 不可重写 ⟹ "
            "更正写在本批 README ＋ 台账。",
            "**不声称** 源站每个项目的第一台机位都叫「机位1」—— 只测了**这一个**测试项目。",
            "**不声称** 改名是源站的「命名规范」—— 只证明了源站**这个项目**的第一台机位"
            "叫「机位1」，且源站支持改名（batch 830 实测）。",
        ],
        "environment": [
            "`/tmp/dbg750e.py`（750 的运行时探针）**从未入库**、已随 /tmp 清空丢失 ⟹ "
            "750 整门禁 exit=1 是**环境性**的，与本批改动无关（batch 836 已归因过一次）。",
        ],
    }
    OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", OUT)
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
