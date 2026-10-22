#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 839 验收：把「查看角色资产」从**死按钮**做成**角色资产视图**，几何对齐源站。

## 这批在还什么债

batch 826／827 已经在 clone 里重建了源站当前的「角色造型室」（我的角色库／官方角色库 页签、
筛选胶囊、横向角色条、三种底部 CTA），但：
  - 那枚悬停才显形的「**查看角色资产**」浮层**点了没反应**（它只是卡片里的一个 `<span>`）；
  - 而**源站**实测：点它 ⟹ 出现**角色资产视图**（4 张图 ＋「选择角色音色」＋ 角色名）。

⟹ 本批：① **先测源站**（点前/点后 DOM 差分 ＋ 绝对几何 ＋ 截图）⟹ ② 再在 clone 里实现 ⟹ ③ 逐像素对拍。

★ 本批最刺眼的三处（都写进了 README）：
  1. ★ **读数器的元素类型覆盖不全**：面板里的按钮文字（性别／年龄段／文化区域／创建新角色）
     全在 `<button>` 里 ⟹ 只扫 `span/div/p/label` 的读数器**会以为面板没开**（截图里明明开着）。
  2. ★ **前提不成立**：源站那枚浮层**只在「官方角色库」页签**里 ⟹ 在「我的角色库」里找它
     ⟹ 「找不到」≠「不存在」⟹ 必须先切页签。
  3. ★★★ **改完 CSS 立刻量 ⟹ 量到的是还没重建完的旧 chunk**（dev server 的 CSS 重建是异步的）
     ⟹ ⟹ 判据必须**先确认服务端已重建**再量。
     ★★★ **本批实测到一种更阴的形态**：Turbopack 的**持久缓存**会把**陈旧**的编译结果
     原样吐出来（磁盘已是 139px，服务端仍下发注入期的 100px ⟹ **重启也不生效**
     ⟹ 只有 `rm -rf .next/dev/cache/turbopack` 才恢复）⟹ ⟹ 光「等一会儿」**不够**，
     ⟹ ⟹ 门禁里加了一道**前置检查**：**抓服务端下发的 chunk 与磁盘对拍**
     ⟹ 不一致 ⟹ **显式失败**（而不是给出「像真的、其实是假的」红）。

## 判据（S1–S7）

S1 ★★★ **「查看角色资产」不再是死按钮**：clone 点它 ⟹ **资产视图**出现（4 张图 ＋ 音色按钮）；
    ★ 且源站同一动作**也**产生资产视图（点前/点后差分可证）
S2 ★★★ **几何与源站逐像素一致**：4 张图的盒 ＋ 音色按钮的盒 ⟹ **期望值从入库的源站 raw 机器提取**
    （★ 不是手打常量 ⟹ 且判据里有「★是否成功抽出期望值」这一条）
S3 ★★ **图源**：第 1 个角色的 4 张图是 **4 张不同**的 detail 图（立绘／近景／表情／三视图）；
    其余角色复用缩略图
S4 ★★★ **Esc 只关资产视图、面板留着** ⟹ 靠 `character-assets` 这个**前台阻塞面**（不是组件本地状态）
S5 ★★ **关掉之后还能再打开**（资产视图不是一次性）
S6 ★★ **悬停行为与源站同**：未悬停 `opacity:0` ＋ `pointer-events:none`；悬停后 `1` ＋ `auto`
S7 ★★★ **否定性结论的扫描器有效性 ＋ mock 如实标注**：
    ★ 源站点「选择角色音色」**没有任何可见变化** ⟹ ⟹ clone 的音色按钮是 **mock** ⟹
    ⟹ README **必须**写明这一点（否则就是把自拟行为说成源站事实）

## 纪律

- 期望值**来自入库的源站 raw**（机器提取），不手打；
- 运行时读数**自己跑**，不读外部缓存；
- 否定性结论必须**先证明扫描范围覆盖了那一类东西**；
- 阴性对照每条**只翻它自己那一条**。
"""
import json
import pathlib
import re
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
BATCH = ROOT / "docs/research/liblib-canvas-batch839-2026-10-01"
RAW = BATCH / "raw"
PROBE_CLONE = BATCH / "probes/clone839.py"
OUT = BATCH / "runtime-audit.json"

# ── 前置检查用的常量 ────────────────────────────────────────────────
DEV_ORIGIN = "http://localhost:4317"
CSS_FILE = ROOT / "src/components/character-studio.css"
# ★ 只查**几何关键**的这几个属性 ⟹ 避开纯装饰属性（颜色/圆角…）的无关差异
CRITICAL_PROPS = ("left", "top", "width", "height")
CRITICAL_SELECTORS = (".cs-asset-strip", ".cs-asset-img", ".cs-voice-row", ".cs-voice-btn")


def read_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def run_probe(script: pathlib.Path) -> None:
    r = subprocess.run([sys.executable, str(script)], capture_output=True,
                       text=True, timeout=900)
    if r.returncode != 0:
        print(r.stdout[-2000:])
        print(r.stderr[-2000:], file=sys.stderr)
        raise SystemExit(f"探针失败 {script.name} exit={r.returncode}")


def src_detail_images(src: dict) -> list:
    """★ 源站资产视图里的那 **4 张**详情图。

    ★ 怎么从 raw 里认出来（**不手打坐标**）：详情图的 class **只有两种**
    （`size-full object-contain` / `size-full object-cover`），
    而**背景 carousel** 的卡片图是 `h-full w-auto max-w-none object-contain`，
    右上角那个 92×92 的头像是 `size-full **rounded-xl** object-cover`
    ⟹ ⟹ **按 class 精确匹配**挑出那 4 张，并断言**恰好挑到 4 张**
    （★ 第一次写成「class 以 `size-full` 开头」⟹ 多挑了那个头像 5 张 ⟹ 判据红了
    ⟹ ⟹ **过滤器太宽也是缺陷**）。
    """
    want = {"size-full object-contain", "size-full object-cover"}
    imgs = src.get("A_资产视图_imgs") or []
    detail = [i for i in imgs if (i.get("cls") or "").strip() in want]
    return detail


def box_close(a: dict, b: dict, tol: int = 1) -> bool:
    """两个盒「算相等」。

    ★ 为什么允许 **±1px** 的位置容差：源站与 clone 的音色药丸都**居中**在 921 宽的容器里
    ⟹ 算式给的是同一个**半像素**位置（139 + (921−128)/2 = 535.5 ⟹ 绝对 896.5）
    ⟹ 两侧浏览器的**取整方向**差 1px ⟹ ⟹ 位置容差 ±1，
    ★ 但**宽高必须逐像素全等**（宽高是布局算出来的确定值，不该有容差）。
    """
    if not a or not b:
        return False
    if a.get("w") != b.get("w") or a.get("h") != b.get("h"):
        return False
    return (abs((a.get("x") or 0) - (b.get("x") or 0)) <= tol
            and abs((a.get("y") or 0) - (b.get("y") or 0)) <= tol)


def src_voice_button(src: dict) -> dict | None:
    btns = src.get("A_资产视图_btns") or []
    hits = [b for b in btns if (b.get("text") or "").strip() == "选择角色音色"]
    return hits[0] if hits else None


# ── 前置检查：服务端 CSS chunk 必须**已经**跟磁盘一致 ──────────────────
def parse_css(css: str) -> dict:
    """`选择器 → 声明字典`。

    ★ 为什么只认**精确等于**该选择器的规则体：分组规则
    `.cs-assets-stage .cs-asset-strip, .cs-assets-stage .cs-voice-row
    { pointer-events: auto; }` 里的两个选择器**都不是** `.cs-asset-strip`
    ⟹ 若按「子串包含」去挑，就会把这条分组规则的声明算到 `.cs-asset-strip` 头上 ⟹ 假红。

    ★★ 为什么**先剥注释**（第一版就栽在这）：磁盘的 CSS 里，选择器**上面**常有注释 ⟹
    不剥的话，正则抓到的「选择器」是 `/* 注释 */\\n.cs-voice-row` ⟹ 精确匹配**永远对不上**
    ⟹ ⟹ 报成「磁盘上找不到这个选择器」（第一版实测：等满 92 秒后误报）。
    """
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out: dict = {}
    for sel_raw, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        decls: dict = {}
        for d in body.split(";"):
            if ":" in d:
                k, v = d.split(":", 1)
                decls[k.strip()] = v.strip()
        for sel in (s.strip() for s in sel_raw.split(",")):
            if not sel:
                continue
            merged = out.get(sel, {})
            merged.update(decls)
            out[sel] = merged
    return out


def served_css() -> str:
    """把 dev server **正在下发**的 CSS chunk 全量抓下来。"""
    html = urllib.request.urlopen(DEV_ORIGIN + "/", timeout=60).read().decode("utf-8", "replace")
    urls = sorted(set(re.findall(r'/_next/static/chunks/[^"]+\.css', html)))
    chunks = []
    for u in urls:
        try:
            chunks.append(urllib.request.urlopen(DEV_ORIGIN + u, timeout=60)
                          .read().decode("utf-8", "replace"))
        except Exception as exc:  # noqa: BLE001
            print(f"  ★ chunk 抓取失败 {u}: {exc}")
    return "\n".join(chunks)


def css_drift() -> dict:
    """磁盘 vs 服务端 chunk 的**关键几何**差异（**空字典 ＝ 一致**）。"""
    disk = parse_css(CSS_FILE.read_text(encoding="utf-8"))
    live = parse_css(served_css())
    drift: dict = {}
    for sel in CRITICAL_SELECTORS:
        d = disk.get(sel) or {}
        l = live.get(sel) or {}
        if not d:
            drift[sel] = {"error": "磁盘上找不到这个选择器"}
            continue
        if not l:
            drift[sel] = {"error": "服务端 chunk 里找不到这个选择器"}
            continue
        diff = {p: {"disk": d.get(p), "served": l.get(p)}
                for p in CRITICAL_PROPS if p in d and d.get(p) != l.get(p)}
        if diff:
            drift[sel] = diff
    return drift


def preflight_css(timeout: int = 90) -> tuple:
    """等 dev server 的 CSS chunk **追平磁盘** ⟹ 超时则**显式失败**。

    ★★ 为什么必须先过这一关：dev server 的 CSS 重建是**异步**的 ⟹ 改完源码立刻量，
      量到的可能是**上一版** chunk ⟹ ⟹ 判据会给出「像真的、其实是假的」红。
    ★★ 更阴的一种：Turbopack 的**持久缓存**可以把**陈旧**的编译结果原样吐出来
      （本批实测：磁盘已是 139px，服务端仍然下发注入期的 100px ⟹ 连重启都不生效
      ⟹ 只有 `rm -rf .next/dev/cache/turbopack` 才恢复）⟹ ⟹ 这一关必须**比对**，
      不能只靠「我等了一会儿」。
    """
    t0 = time.time()
    drift = css_drift()
    while drift and time.time() - t0 < timeout:
        time.sleep(3)
        drift = css_drift()
    waited = round(time.time() - t0, 1)
    if drift:
        return False, {"等了几秒": waited, "不一致": drift}
    return True, {"等了几秒": waited, "不一致": {}}


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    # ── 前置检查：先确认服务端 chunk 已经跟磁盘一致 ──────────────────
    print("前置检查：等 dev server 的 CSS chunk 追平磁盘……")
    pf_ok, pf_detail = preflight_css()
    if not pf_ok:
        print("PREFLIGHT-FAIL 服务端 CSS chunk 与磁盘不一致 ⟹ **本轮读数不可信**")
        print(json.dumps(pf_detail, ensure_ascii=False, indent=1))
        OUT.write_text(json.dumps({
            "batch": 839,
            "verdict": "preflight-failed",
            "preflight": pf_detail,
            "note": "服务端 chunk 还没重建（或 Turbopack 持久缓存陈旧）⟹ "
                    "需要 `rm -rf .next/dev/cache/turbopack` 并重启 dev server",
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print("写入", OUT)
        return 2
    print(f"  ✔ chunk 已追平磁盘（等了 {pf_detail.get('等了几秒')}s）")

    src = read_json(RAW / "source-839-editor.json")
    src_diff = read_json(RAW / "source-839-assets.json")
    noop = read_json(RAW / "source-839-voice-noop.json")

    print("跑 clone 运行时探针……")
    run_probe(PROBE_CLONE)
    rt = read_json(pathlib.Path("/tmp/b839-clone-assets.json"))

    opened = rt.get("C_点开后") or {}
    after_esc = rt.get("E_Esc后") or {}
    reopened = rt.get("F1_第一次点后") or {}
    hovered = rt.get("B_悬停后") or {}
    before = rt.get("A_点开前") or {}

    checks = []

    # ── S1 「查看角色资产」不再是死按钮 ────────────────────────────────
    clone_imgs = opened.get("资产图") or []
    clone_voice = opened.get("音色按钮") or {}
    s1 = {
        "clone_点开后_有资产视图": opened.get("资产视图容器") is not None,
        "clone_资产图数": len(clone_imgs),
        "clone_有音色按钮": bool(clone_voice.get("text")),
        "★源站_差分_新增文本数": len(src_diff.get("D_★新增的可见文本") or []),
        "★源站_差分_新增图片数": len(src_diff.get("D_★新增的图片") or []),
        "★源站_点开后含选择角色音色": src.get("A_★资产视图是否含选择角色音色"),
    }
    checks.append((
        "S1 ★★★ **「查看角色资产」不再是死按钮**：clone 点它 ⟹ **资产视图**出现"
        "（%d 张图 ＋ 音色按钮「%s」）⟹ ★ 且源站同一动作**也**产生资产视图"
        "（点前/点后差分：新增 %d 条文本 ＋ %d 张图）⟹ ⟹ 两者**同构**"
        % (s1["clone_资产图数"], (clone_voice.get("text") or "")[:8],
           s1["★源站_差分_新增文本数"], s1["★源站_差分_新增图片数"]),
        (s1["clone_点开后_有资产视图"] and s1["clone_资产图数"] == 4
         and s1["clone_有音色按钮"] and s1["★源站_差分_新增文本数"] >= 2
         and s1["★源站_差分_新增图片数"] == 4
         and s1["★源站_点开后含选择角色音色"] is True),
        json.dumps(s1, ensure_ascii=False),
    ))

    # ── S2 几何与源站逐像素一致（期望值从 raw 提取） ───────────────────
    s_detail = src_detail_images(src)
    s_voice = src_voice_button(src)
    s2 = {
        "★是否成功抽出源站的4张详情图": len(s_detail) == 4,
        "★是否成功抽出源站的音色按钮": s_voice is not None,
        "源站_详情图盒": [i.get("box") for i in s_detail],
        "clone_详情图盒": [i.get("box") for i in clone_imgs],
        "源站_音色按钮盒": (s_voice or {}).get("box"),
        "clone_音色按钮盒": clone_voice.get("box"),
    }
    s2["★4张图逐张盒全等"] = (
        len(s_detail) == 4 and len(clone_imgs) == 4
        and all(box_close(s_detail[i].get("box") or {},
                          clone_imgs[i].get("box") or {})
                for i in range(4)))
    s2["★音色按钮盒全等"] = box_close((s_voice or {}).get("box") or {},
                                      clone_voice.get("box") or {})
    s2["★宽高必须逐像素全等"] = (
        len(s_detail) == 4 and len(clone_imgs) == 4
        and all((s_detail[i].get("box") or {}).get("w")
                == (clone_imgs[i].get("box") or {}).get("w")
                and (s_detail[i].get("box") or {}).get("h")
                == (clone_imgs[i].get("box") or {}).get("h")
                for i in range(4))
        and (s_voice or {}).get("box", {}).get("w") == clone_voice.get("box", {}).get("w")
        and (s_voice or {}).get("box", {}).get("h") == clone_voice.get("box", {}).get("h"))
    checks.append((
        "S2 ★★★ **几何与源站逐像素一致**：4 张详情图（立绘 164×220／近景 165×220／表情 165×220／"
        "三视图 391×220）＋「选择角色音色」128×36 ⟹ **期望值从入库的源站 raw 机器提取**"
        "（★ 按 class **精确**匹配挑出那 4 张 ⟹ 并断言「★是否成功抽出」）"
        "⟹ ⟹ **宽高逐像素全等**、位置 ±1px（★ 两侧都居中在同一半像素位置，取整方向差 1）",
        (s2["★是否成功抽出源站的4张详情图"] and s2["★是否成功抽出源站的音色按钮"]
         and s2["★4张图逐张盒全等"] and s2["★音色按钮盒全等"]
         and s2["★宽高必须逐像素全等"]),
        json.dumps(s2, ensure_ascii=False),
    ))

    # ── S3 图源 ───────────────────────────────────────────────────────
    srcs = [((i.get("src") or "").split("/")[-1]) for i in clone_imgs]
    store = (ROOT / "src/components/CharacterLibraryPanel.tsx").read_text(encoding="utf-8")
    s3 = {
        "clone_四张图的src": srcs,
        "★四张是否互不相同": len(set(srcs)) == 4,
        "★是否都是character-detail-N": all(
            re.fullmatch(r"character-detail-\d\.webp", s or "") for s in srcs),
        "★源码里对首个角色特判": (
            'character.id === characters[0].id' in store),
        "★源码里其余角色复用缩略图": (
            "return [character.imageUrl, character.imageUrl, character.imageUrl, character.imageUrl];"
            in store),
        "★资源确实存在": all(
            (ROOT / "public/images/liblib-panels" / s).exists() for s in srcs),
    }
    checks.append((
        "S3 ★★ **图源**：第 1 个角色的 4 张图是 **4 张不同**的 detail 图"
        "（立绘／脸部近景／表情参考／三视图）⟹ ★ 其余角色**复用缩略图**（仓库里只有一张角色的 4 张详情图）"
        "⟹ ★ 且 4 个资源文件**确实存在**",
        (s3["★四张是否互不相同"] and s3["★是否都是character-detail-N"]
         and s3["★源码里对首个角色特判"] and s3["★源码里其余角色复用缩略图"]
         and s3["★资源确实存在"]),
        json.dumps(s3, ensure_ascii=False),
    ))

    # ── S4 Esc 只关资产视图、面板留着 ─────────────────────────────────
    ctx_src = (ROOT / "src/lib/libtvSelectionCommandContext.ts").read_text(encoding="utf-8")
    ui_src = (ROOT / "src/store/uiStore.ts").read_text(encoding="utf-8")
    s4 = {
        "★Esc后_面板还在": after_esc.get("模态盒") is not None,
        "★Esc后_资产视图已关": after_esc.get("资产视图容器") is None,
        "★阻塞面表里有character-assets": '"character-assets"' in ctx_src,
        "★解析顺序在primary-panel之前": bool(re.search(
            r'if \(snapshot\.characterAssetsId\) return "character-assets";\s*'
            r'if \(snapshot\.activePrimaryPanel\) return "primary-panel";',
            ctx_src)),
        "★store有characterAssetsId": "characterAssetsId" in ui_src,
        "★store有对应分支": 'case "character-assets":' in ui_src,
        "★面板用的是store而不是本地state": (
            "useUIStore((state) => state.characterAssetsId)" in store),
    }
    checks.append((
        "S4 ★★★ **Esc 只关资产视图、面板留着**：靠把资产视图登记成**前台阻塞面**"
        "`character-assets`（★ 它必须排在 `primary-panel` **之前**）⟹ ⟹ 宿主页那个"
        "**全局捕获阶段**的 Escape 处理会先关它；★ 且状态**放在 store** 里"
        "（组件本地状态那一层**看不见**）",
        all(v for k, v in s4.items() if k.startswith("★")),
        json.dumps(s4, ensure_ascii=False),
    ))

    # ── S5 关掉之后还能再打开 ─────────────────────────────────────────
    s5 = {
        "★Esc后资产视图关着": after_esc.get("资产视图容器") is None,
        "★再点浮层后资产视图回来了": reopened.get("资产视图容器") is not None,
        "★面板始终在": (after_esc.get("模态盒") is not None
                        and reopened.get("模态盒") is not None),
    }
    checks.append((
        "S5 ★★ **关掉之后还能再打开**（资产视图不是一次性）⟹ 且**面板始终在**",
        all(s5.values()),
        json.dumps(s5, ensure_ascii=False),
    ))

    # ── S6 悬停行为与源站同 ───────────────────────────────────────────
    src_before = (src_diff.get("A_★资产元素") or [])
    src_btn_before = next((e for e in src_before if e.get("tag") == "BUTTON"), {})
    src_after = (src_diff.get("B_★悬停后_资产元素") or [])
    src_btn_after = next((e for e in src_after if e.get("tag") == "BUTTON"), {})
    clone_float_before = (before.get("浮层") or {})
    clone_float_after = (hovered.get("浮层") or {})
    s6 = {
        "★源站_悬停前": {"opacity": src_btn_before.get("opacity"),
                        "pointerEvents": src_btn_before.get("pointerEvents")},
        "★源站_悬停后": {"opacity": src_btn_after.get("opacity"),
                        "pointerEvents": src_btn_after.get("pointerEvents")},
        "★clone_悬停前": {"opacity": clone_float_before.get("opacity"),
                         "pointerEvents": clone_float_before.get("pointerEvents")},
        "★clone_悬停后": {"opacity": clone_float_after.get("opacity"),
                         "pointerEvents": clone_float_after.get("pointerEvents")},
        "★clone浮层盒": clone_float_before.get("box"),
    }
    s6["★悬停前都是0/none"] = (
        clone_float_before.get("opacity") == "0"
        and clone_float_before.get("pointerEvents") == "none")
    s6["★悬停后都是1/auto"] = (
        clone_float_after.get("opacity") == "1"
        and clone_float_after.get("pointerEvents") == "auto")
    s6["★源站也是0/none→1/auto"] = (
        src_btn_before.get("opacity") == "0"
        and src_btn_before.get("pointerEvents") == "none"
        and src_btn_after.get("opacity") == "1"
        and src_btn_after.get("pointerEvents") == "auto")
    checks.append((
        "S6 ★★ **悬停行为与源站同**：未悬停 `opacity:0` ＋ `pointer-events:none` ⟹ "
        "悬停后 `1` ＋ `auto`（★ 源站与 clone **两侧**都实测过）⟹ ⟹ "
        "这正是「必须**先悬停**才点得到」的原因",
        (s6["★悬停前都是0/none"] and s6["★悬停后都是1/auto"]
         and s6["★源站也是0/none→1/auto"]),
        json.dumps(s6, ensure_ascii=False),
    ))

    # ── S7 否定性结论的扫描器有效性 ＋ mock 如实标注 ──────────────────
    readme = (BATCH / "README.md").read_text(encoding="utf-8")
    # ★★ **定位到 §2.4 那一节**（记录「选择角色音色」实测结果的那一节）⟹
    #   为什么不能只看「全文里有没有 mock」：那是**弱存在式** ⟹ README 里有**三处** mock ⟹
    #   删掉其中一处 ⟹ 判据照样绿 ⟹ ⟹ 负控 N7 第一版就是**这样没翻红的**（真发现，不是噪声）。
    sec24 = ""
    m24 = re.search(r"^###\s*2\.4\b(.*?)(?=^###\s|\Z)", readme, flags=re.S | re.M)
    if m24:
        sec24 = m24.group(1)
    s7 = {
        "★源站_音色点击后新增文本数": noop.get("B_音色_新增文本条数"),
        "★源站_音色点击后URL是否变化": noop.get("B_音色_URL是否变化"),
        # ★ 差分覆盖度**从独立 raw 读**（不是从 S1 读的那份）⟹ ⟹ 阴性注入**互不串门**
        "★源站_差分_新增文本数": noop.get("★差分_新增文本条数"),
        "★源站_差分_新增文本内容": noop.get("★差分_新增文本内容"),
        "★源站_差分_新增图片数": noop.get("★差分_新增图片数"),
        "★README里mock出现次数": readme.lower().count("mock"),
        "★README写明音色按钮是mock": ("mock" in readme.lower()
                                     and "选择角色音色" in readme),
        "★§2.4这一节存在": bool(sec24.strip()),
        "★§2.4这一节里就写明了mock": "mock" in sec24.lower(),
        "★README写明源站音色点击无可见变化": ("无可见变化" in readme
                                          or "没有可见变化" in readme),
        "★README写明资产视图几何来自源站实测": ("源站实测" in readme),
    }
    checks.append((
        "S7 ★★★ **否定性结论的扫描器有效性 ＋ mock 如实标注**："
        "★ 源站点「选择角色音色」**新增 0 条文本、URL 不变** ⟹ ⟹ **不知道**它会打开什么 "
        "⟹ ⟹ clone 的音色按钮**只能**是 mock ⟹ ⟹ README **必须**写明这一点"
        "（否则就是把自拟行为说成源站事实）；★ 差分读数**确实**只多出 %s ⟹ "
        "⟹ 覆盖度可证，不是「扫不到」"
        "；★★ 且这条标注必须落在**§2.4 记录实测结果的那一节**里"
        "（★ 全文弱存在式「有没有 mock」太松 ⟹ 负控 N7 第一版就是那样漏过去的）"
        % (s7["★源站_差分_新增文本内容"],),
        (s7["★源站_音色点击后新增文本数"] == 0
         and s7["★源站_音色点击后URL是否变化"] is False
         and s7["★源站_差分_新增文本数"] == 2
         and s7["★源站_差分_新增图片数"] == 4
         and s7["★README写明音色按钮是mock"]
         and s7["★§2.4这一节存在"]
         and s7["★§2.4这一节里就写明了mock"]
         and s7["★README写明源站音色点击无可见变化"]
         and s7["★README写明资产视图几何来自源站实测"]),
        json.dumps(s7, ensure_ascii=False),
    ))

    print("\n=== 判据 ===")
    passed = 0
    for label, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
        passed += bool(ok)
    print(f"\n{passed}/{len(checks)} 通过")

    audit = {
        "batch": 839,
        "title": "把「查看角色资产」从死按钮做成角色资产视图，几何逐像素对齐源站",
        "verdict": f"{passed}/{len(checks)}",
        "preflight": pf_detail,
        "source": {
            "详情图盒": [i.get("box") for i in s_detail],
            "音色按钮盒": (s_voice or {}).get("box"),
            "差分_新增文本": src_diff.get("D_★新增的可见文本"),
            "差分_新增图片数": len(src_diff.get("D_★新增的图片") or []),
            "音色点击无可见变化": noop,
        },
        "clone": {
            "C_点开后": opened, "E_Esc后": after_esc, "F1_第一次点后": reopened,
        },
        "checks": [{"label": l, "pass": bool(o), "detail": d} for l, o, d in checks],
        "conclusions": [
            "★★★ **「查看角色资产」以前是死按钮**（卡片里的一个 `<span>`，点了只会选中卡片）"
            "⟹ 本批把它做成**角色资产视图**：4 张图 ＋「选择角色音色」＋ 角色名。",
            "★★★ **几何与源站逐像素一致**：4 张详情图（164/165/165/391 × 220，x=500/676/853/1030，"
            "y=393）＋「选择角色音色」128×36 @896,646 ⟹ **期望值从入库的源站 raw 机器提取**。",
            "★★ **悬停行为两侧同构**：未悬停 opacity 0 ＋ pointer-events none ⟹ 悬停后 1 ＋ auto。",
            "★★★ **Esc 只关资产视图、面板留着** ⟹ 靠把资产视图登记成**前台阻塞面** "
            "`character-assets`（排在 `primary-panel` 之前）⟹ ⟹ 组件本地状态那一层**看不见**。",
            "★★ **源站点「选择角色音色」没有任何可见变化** ⟹ ⟹ clone 的音色按钮**是 mock** ⟹ "
            "⟹ README 如实标注，不假装成源站行为。",
        ],
        "notClaimed": [
            "**不声称**源站的「选择角色音色」会打开什么 —— 实测**无可见变化** ⟹ 不知道。",
            "**不声称**源站资产视图里点「选择角色音色」的行为已复刻（clone 是 mock）。",
            "**不声称**源站「编辑角色」的大编辑器已复刻 —— ★ 它**实测过**（脸部精修／"
            "脸部&身体特征／身材塑形／服装造型／音色音调 ＋ 皮肤滑杆 ＋ ⚡44 积分的「保存时生成角色资产」），"
            "但**本批没做** ⟹ 属下一批。",
            "**不声称**每个角色都有 4 张不同详情图 —— 仓库里只有**一张角色**的 4 张 ⟹ 其余复用缩略图。",
        ],
    }
    OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", OUT)
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
