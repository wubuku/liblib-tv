#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 manifest 的 `visible_text` 与截图 OCR 结果做全量比对，列出可疑条目。

★ **它是分析工具，不是门禁，退出码恒为 0。**
  按 M195 那条「判据必须窄到能全对，窄不到就别假装是门禁」——
  OCR 认不出 placeholder、认不出极小文字、还会把简体认成繁体，
  **「没匹配上」有可能是 OCR 不行，不是清单写错**。所以只出候选，不下结论。

它抓到的东西（M225）：
  · R76 / R77 —— 两条 `visible_text` 登的是「发生了什么」而不是「图上写着什么」；
  · 另证掉 3 条报警，其中「新建」放大 5 倍后确认就在图上（**第 152 次否证**）。

用法：
    python3 scripts/audit-visible-text.py .
    python3 scripts/audit-visible-text.py . --keep-ocr    # 复用上次的 OCR 结果

依赖：需要 swiftc（本机实测 v1.148.6）。没有就如实跳过，不报错。
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# 繁简归一：Vision 实测会把简体认成繁体（頻/題/節…）。这里只收实测撞到过的，
# 目的是**消除已知的假阴性**，不是做完整的简繁转换。
TRAD2SIMP = str.maketrans({
    "頻": "频", "題": "题", "節": "节", "圖": "图", "傳": "传", "優": "优",
    "樣": "样", "個": "个", "為": "为", "對": "对", "點": "点", "線": "线",
    "開": "开", "關": "关", "設": "设", "網": "网", "選": "选", "單": "单",
    "產": "产", "業": "业", "項": "项", "態": "态", "顏": "颜", "應": "应",
})

# 相似度阈值。三档是**给人看的候选分层**，不是通过/不通过。
NEAR = 0.70   # ≥ 这个值：多半是 OCR 认错了字
WEAK = 0.45   # ≥ 这个值：大概是 OCR 没读全
                 # <  这个值：值得打开图看一眼


def norm(s: str) -> str:
    """去掉全部空白 + 繁简归一。OCR 会在词里插空格（`Q 搜 节点` ← `搜索节点`）。"""
    return re.sub(r"\s+", "", s or "").translate(TRAD2SIMP)


def best_ratio(token: str, hay: str) -> tuple[float, str]:
    """滑窗找最像的一段，返回 (相似度, 那段文字)。"""
    n = len(token)
    if n == 0:
        return 1.0, ""
    if token in hay:
        return 1.0, token
    best, where = 0.0, ""
    step = max(1, n // 6)
    for i in range(0, max(1, len(hay) - n + 1), step):
        w = hay[i : i + n]
        sc = difflib.SequenceMatcher(None, token, w).ratio()
        if sc > best:
            best, where = sc, w
    return best, where


def build_ocr(script_dir: Path, shots: list[Path], cache: Path | None):
    """编译并运行 swift OCR 程序；返回 {文件名: [文本行]}。失败返回 None。"""
    if cache and cache.is_file():
        try:
            return json.loads(cache.read_text(encoding="utf-8"))
        except Exception:
            pass

    swiftc = shutil.which("swiftc")
    if not swiftc:
        print("[skip] 本机没有 swiftc，无法做 OCR。如实跳过，不报错。")
        return None

    src = script_dir / "ocr-visible.swift"
    if not src.is_file():
        print(f"[skip] 找不到 {src.name}，如实跳过。")
        return None

    outdir = Path(tempfile.mkdtemp(prefix="tdcanvas-ocr-"))
    binary = outdir / "ocr-visible"
    print(f"[build] {src.name} -> {binary}")
    r = subprocess.run([swiftc, "-O", "-o", str(binary), str(src)],
                       capture_output=True, text=True)
    if r.returncode != 0 or not binary.is_file():
        print("[skip] swiftc 编译失败，如实跳过：")
        print((r.stderr or r.stdout)[-800:])
        return None

    print(f"[ocr] 识别 {len(shots)} 张（首次全量较慢，约十几秒到几分钟）…")
    r = subprocess.run([str(binary), *[str(p) for p in shots]],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("[skip] OCR 运行失败，如实跳过：")
        print((r.stderr or r.stdout)[-800:])
        return None
    try:
        data = json.loads(r.stdout)
    except Exception as exc:  # pragma: no cover
        print(f"[skip] OCR 输出不是合法 JSON（{exc}），如实跳过。")
        return None
    shutil.rmtree(outdir, ignore_errors=True)
    if cache:
        cache.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description="visible_text × OCR 对账（分析工具，非门禁）")
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--keep-ocr", action="store_true",
                    help="复用 /tmp/m225-ocr-cache.json 里的 OCR 结果，跳过重新识别")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    script_dir = Path(__file__).resolve().parent
    manifest = root / "screenshots/manifest.yml"

    try:
        import yaml
    except ImportError:
        print("[skip] 没有 pyyaml，无法读 manifest，如实跳过。")
        return 0
    if not manifest.is_file():
        print(f"[skip] 找不到 {manifest}")
        return 0

    entries = yaml.safe_load(manifest.read_text(encoding="utf-8"))["screenshots"]
    shots = sorted((root / "screenshots").glob("*.png"))
    if not shots:
        print("[skip] screenshots/ 下没有图")
        return 0

    cache = Path("/tmp/m225-ocr-cache.json")
    ocr = build_ocr(script_dir, shots, cache if args.keep_ocr else None)
    if ocr is None:
        return 0
    ocr_by_name = {Path(k).name: v for k, v in ocr.items()}

    rows = []
    for e in entries:
        name = Path(str(e.get("file", ""))).name
        lines = ocr_by_name.get(name) or []
        if lines and (lines[0].startswith("__LOAD_FAIL__") or lines[0].startswith("__ERR__")):
            rows.append((name, "OCRFAIL", [], ""))
            continue
        hay = norm("".join(lines))
        vt = str(e.get("visible_text", "") or "").strip()
        if not vt:
            rows.append((name, "EMPTY", [], "（清单里就是空的）"))
            continue
        tokens: list[str] = []
        for seg in vt.split("/"):
            for t in re.split(r"[\s·、，,]+", seg.strip()):
                if len(t) >= 2:
                    tokens.append(t)
        missing = []
        for t in tokens:
            r, _ = best_ratio(norm(t), hay)
            if r < WEAK:
                missing.append(t)
        rows.append((name, "OK" if not missing else "MISS", missing, vt))

    n_ok = sum(1 for r in rows if r[1] == "OK")
    n_miss = sum(1 for r in rows if r[1] == "MISS")
    n_emp = sum(1 for r in rows if r[1] == "EMPTY")
    n_fail = sum(1 for r in rows if r[1] == "OCRFAIL")

    print("=" * 78)
    print(f"[读数] {len(rows)} 条：词元全命中 {n_ok}　有缺词 {n_miss}　空值 {n_emp}　OCR 失败 {n_fail}")
    print("=" * 78)

    buckets = {"OCR 认错字": [], "OCR 没读全": [], "值得打开图看": []}
    for name, st, missing, _ in rows:
        if st != "MISS":
            continue
        lines = ocr_by_name.get(name) or []
        hay = norm("".join(lines))
        for t in missing:
            r, w = best_ratio(norm(t), hay)
            line = f"  {name[:40]:42s} 缺「{t[:24]}」 最接近 {r:.2f} =「{w[:24]}」"
            key = "OCR 认错字" if r >= NEAR else ("OCR 没读全" if r >= WEAK else "值得打开图看")
            buckets[key].append(line)

    for k, v in buckets.items():
        print(f"\n--- {k}（{len(v)}）---")
        for line in v:
            print(line)

    print(
        "\n★ 这三桶都不是判决：\n"
        "  · 「OCR 认错字」多半是 Vision 的问题（它会把简体认成繁体，见 ocr-visible.swift 的注释）；\n"
        "  · 「值得打开图看」是**唯一值得花时间的一桶**，但**仍要人眼看图才算定论**；\n"
        "  · 判一条 visible_text 到底算不算错，要用 M211 定的三档：\n"
        "      ① 图上可见的文字　② 正文明确写成悬停提示的（合规）　③ 两者都不是却登记了（才是错）"
    )
    print("[info] 本工具退出码恒为 0，不参与 build-site.sh 的门禁序列。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
