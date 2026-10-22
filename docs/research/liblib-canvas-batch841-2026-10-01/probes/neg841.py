#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 841 阴性对照：每条臂**只翻它自己那一条**判据，改完**字节级复原**。

## 为什么要有这个

「对照轮全绿」**不能**证明某条断言有牙 —— 只能证明「现在这样是绿的」。
⟹ 要证明「这条断言真的有牙」，必须**故意破坏一个前提**，看它**精确地红在指定的那一条上**。

★ 三条纪律：
  1. **每条臂只翻它自己那一条** ⟹ 读的字段**互不重叠**
     ⟹ ⟹ 设计时逐条核对「这条臂会不会顺带把别的判据也翻了」。
  2. **改完必须字节级复原**（SHA-256 对拍）⟹ 否则后面的臂是在脏状态上跑的。
  3. **等 dev server 真的重建完**再跑门禁 ⟹ 否则读到的是旧 chunk
     ⟹ ⟹ 阴性会「没翻红」⟹ 而那不是「断言没牙」，是「环境没跟上」。

## 臂与它该翻红的那一条

| 臂 | 注入的缺陷 | 应当翻红 | 为什么**不会**顺带翻别的 |
| --- | --- | --- | --- |
| N1 | 「鼻梁」改成「鼻背」（**同字数** ⟹ 盒宽不变） | S1 | 只改**文案** ⟹ S2 比的是几何（宽度同字数 ⟹ 不变）⟹ S3/S4/S5/S6 不读滑杆文案 |
| N2 | 滑杆行的 top **整体 +6px** | S2 | 只动几何 ⟹ S1（文案）／S3（页签）不读它 |
| N3 | 页签**每枚都渲染文字**（不再是「只有选中那枚」） | S3 | 只动**文案有无** ⟹ S2 比页签盒（宽度写死 24/56 ⟹ 不变）⟹ S1/S4/S5/S6 不读页签文案 |
| N4 | 滑杆更新量 `Number(...) % 1` ⟹ 拖动后永远是 0 | S4 | 只动**状态更新** ⟹ S1/S2/S3 是读 DOM 几何与文案 ⟹ 不受影响 |
| N5 | 未实现的页签改成渲染一枚**假滑杆** | S5 | 只动**空态分支** ⟹ 皮肤/鼻子/嘴唇/脸部四页不走这条分支 ⟹ S1/S2/S3/S4 不受影响 |
| N6 | README 里的 **mock** 标注全部删掉 | S6 | 只动**文档** |

★ N3 之所以能「只翻 S3」，是因为 **S3 里补了一条**
  「★只有选中那枚带文字」—— 之前只钉了「选中那枚带文字」，
  **没钉**「其余五枚没有文字」 ⟹ ⟹ 「每枚都带文字」的实现本来能蒙混过关 ⟹ ⟹ 本批补上。

★ N1 之所以能「只翻 S1」，是因为 **S2 比的是盒宽** ⟹ ⟹ 换字必须**同字数**
  （「鼻梁」「鼻背」都是 2 个汉字 ⟹ 盒宽都是 28px）⟹ ⟹ 否则 S2 会一起红。

## 产物

`negative-audit.json`（每条臂的红/绿与期望）
"""
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[4]  # probes→batch→research→docs→仓库根
BATCH = ROOT / "docs/research/liblib-canvas-batch841-2026-10-01"
GATE = ROOT / "scripts/verify-liblib-batch841.py"
AUDIT = BATCH / "runtime-audit.json"
DEV_ORIGIN = "http://localhost:4317"

PANEL = ROOT / "src/components/CharacterEditorPanel.tsx"
README = BATCH / "README.md"

# ── 臂的定义 ─────────────────────────────────────────────────────────
ARMS = [
    {
        "id": "N1",
        "expect": "S1",
        "files": [PANEL],
        "mutate": (lambda s: s.replace(
            '{ id: "nose-bridge", label: "鼻梁", info: false },',
            '{ id: "nose-bridge", label: "鼻背", info: false },', 1)
            .replace(
            '          data-character-editor-slider-label={item.id}\n',
            '          data-character-editor-slider-label={item.id}\n'
            '          data-neg841="neg841n1"\n', 1)),
        "marker": "neg841n1",
        "note": "「鼻梁」改成「鼻背」（同字数 ⟹ 盒宽不变 ⟹ 只翻 S1）",
    },
    {
        "id": "N2",
        "expect": "S2",
        "files": [PANEL],
        "mutate": (lambda s: s.replace(
            "    const top = 20 + index * SLIDER_STEP;",
            "    const top = 20 + index * SLIDER_STEP + 6;", 1)
            .replace(
            '          data-character-editor-slider={item.id}\n',
            '          data-character-editor-slider={item.id}\n'
            '          data-neg841="neg841n2"\n', 1)),
        "marker": "neg841n2",
        "note": "滑杆行整体下移 6px ⟹ 几何与源站差 6px（>±1 容差）",
    },
    {
        "id": "N3",
        "expect": "S3",
        "files": [PANEL],
        # ★ 标记必须放在 **JSX 属性位置** ⟹ 放进函数体会变成无效 JSX ⟹ 编译失败
        "mutate": (lambda s: s.replace(
            '                  data-character-editor-tab={item.id}\n',
            '                  data-character-editor-tab={item.id}\n'
            '                  data-neg841="neg841n3"\n', 1)
            .replace(
            '                  {tab === item.id ? (\n'
            '                    <span className="ce-tab-text">{item.label}</span>\n'
            '                  ) : null}',
            '                  {tab === item.id ? (\n'
            '                    <span className="ce-tab-text">{item.label}</span>\n'
            '                  ) : (\n'
            '                    <span className="ce-tab-text">{item.label}</span>\n'
            '                  )}', 1)),
        "marker": "neg841n3",
        "note": "页签每枚都渲染文字 ⟹ 「只有选中那枚带文字」这条红",
    },
    {
        "id": "N4",
        "expect": "S4",
        "files": [PANEL],
        "mutate": (lambda s: s.replace(
            "              [item.id]: Number(event.target.value),",
            "              [item.id]: Number(event.target.value) % 1,", 1)
            .replace(
            '          data-character-editor-slider={item.id}\n',
            '          data-character-editor-slider={item.id}\n'
            '          data-neg841="neg841n4"\n', 1)),
        "marker": "neg841n4",
        "note": "滑杆更新量取模 ⟹ 拖动后 state 永远是 0 ⟹ 控件成了摆设",
    },
    {
        "id": "N5",
        "expect": "S5",
        "files": [PANEL],
        # ★ 假控件必须带 `data-character-editor-slider` ⟹ 否则探针数出来还是 0 ⟹ S5 不会红
        "mutate": (lambda s: s.replace(
            '                <p className="ce-empty" data-character-editor-empty>\n'
            '                  「{TABS.find((item) => item.id === tab)?.label}」这一页签的控件\n'
            '                  **已实测**（源站 raw 入库在 batch 841），\n'
            '                  但它除了滑杆还含**预设网格**（76×96 的卡片，带缩略图）\n'
            '                  ⟹ ⟹ 属后续批次 ⟹ ⟹ 这里不编造控件，只如实说明。\n'
            '                </p>',
            '                <p className="ce-empty" data-character-editor-empty data-neg841="neg841n5">\n'
            '                  <input type="range" min={0} max={100} defaultValue={0} aria-label="编造的滑杆" data-character-editor-slider="fake" />\n'
            '                  「{TABS.find((item) => item.id === tab)?.label}」这一页签的控件\n'
            '                  **已实测**（源站 raw 入库在 batch 841），\n'
            '                  但它除了滑杆还含**预设网格**（76×96 的卡片，带缩略图）\n'
            '                </p>', 1)),
        "marker": "neg841n5",
        "note": "未实现的页签渲染一枚假滑杆 ⟹ 「0 控件」这条红",
    },
    {
        "id": "N6",
        "expect": "S6",
        "files": [README],
        "mutate": (lambda s: re.sub(r"[Mm][Oo][Cc][Kk]", "占位", s)),
        "note": "README 里的 mock 标注全部删掉 ⟹ 「mock 出现次数 >= 3」这条红",
    },
]


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def served_chunks() -> str:
    html = urllib.request.urlopen(DEV_ORIGIN + "/", timeout=60).read().decode("utf-8", "replace")
    urls = sorted(set(re.findall(r'/_next/static/chunks/[^"]+\.(?:js|css)', html)))
    out = []
    for u in urls:
        try:
            out.append(urllib.request.urlopen(DEV_ORIGIN + u, timeout=60)
                       .read().decode("utf-8", "replace"))
        except Exception:  # noqa: BLE001
            pass
    return "\n".join(out)


def wait_for_marker(marker: str, timeout: int = 180) -> bool:
    """等 dev server **真的重建完**（在服务端下发的 chunk 里看到标记）。"""
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            if marker in served_chunks():
                return True
        except Exception:  # noqa: BLE001
            pass
        time.sleep(3)
    return False


def run_gate() -> dict:
    r = subprocess.run([sys.executable, str(GATE)], capture_output=True,
                       text=True, timeout=1800)
    if not AUDIT.exists():
        print(r.stdout[-3000:])
        print(r.stderr[-3000:], file=sys.stderr)
        raise SystemExit("门禁没有产出 runtime-audit.json")
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    return {"rc": r.returncode, "audit": audit}


def failed_checks(audit: dict) -> list:
    return [c["label"].split(" ")[0] for c in audit.get("checks", [])
            if not c.get("pass")]


def main() -> int:
    results = []
    for arm in ARMS:
        aid = arm["id"]
        backups = {}
        before_sha = {}
        for f in arm["files"]:
            backups[f] = f.read_bytes()
            before_sha[f] = sha(f)
        try:
            for f in arm["files"]:
                src = f.read_text(encoding="utf-8")
                dst = arm["mutate"](src)
                if dst == src:
                    raise SystemExit("%s 变异没有生效（源串没匹配上）" % aid)
                f.write_text(dst, encoding="utf-8")
            # ★ 等 dev server 真的重建完 ⟹ 否则阴性会「没翻红」，
            #   而那不是「断言没牙」，是「环境没跟上」
            if arm.get("marker"):
                if not wait_for_marker(arm["marker"]):
                    raise SystemExit("%s 等不到标记 %r" % (aid, arm["marker"]))
            else:
                time.sleep(6)
            out = run_gate()
            reds = failed_checks(out["audit"])
            ok = (reds == [arm["expect"]])
            print("%s %s ⟹ 红的是 %s（期望 %s）%s"
                  % ("PASS" if ok else "FAIL", aid, reds or "无",
                     arm["expect"], "" if ok else "  ★ 不符合预期"))
            if not ok:
                print("   判据明细：", json.dumps(out["audit"].get("checks"),
                                             ensure_ascii=False)[:2000])
            results.append({"臂": aid, "红": reds, "期望": arm["expect"],
                            "通过": ok, "说明": arm["note"]})
        finally:
            # ★ 字节级复原（SHA-256 对拍）
            for f, data in backups.items():
                f.write_bytes(data)
            for f in arm["files"]:
                if sha(f) != before_sha[f]:
                    raise SystemExit("%s 复原失败：%s 的 SHA-256 对不上" % (aid, f))
            time.sleep(4)

    print("\n=== 阴性对照汇总 ===")
    for r in results:
        print("  %s  %s ⟹ %s" % ("PASS" if r["通过"] else "FAIL", r["臂"], r["说明"]))
    passed = sum(1 for r in results if r["通过"])

    # ★ 全部复原之后，门禁必须**回到全绿** ⟹ ⟹ 否则「复原」本身有问题
    print("\n复原后再跑一次门禁（必须回到 6/6）……")
    out = run_gate()
    reds = failed_checks(out["audit"])
    back_green = (not reds) and out["rc"] == 0
    print("  %s 复原后门禁：%s（红的是 %s）"
          % ("PASS" if back_green else "FAIL", out["audit"].get("verdict"), reds or "无"))

    print("\n%d/%d 通过" % (passed, len(results)))
    out_path = BATCH / "negative-audit.json"
    out_path.write_text(json.dumps({
        "batch": 841,
        "verdict": "%d/%d" % (passed, len(results)),
        "arms": results,
        "复原后门禁回到全绿": back_green,
        "note": "每条臂只翻它自己那一条判据；改完按 SHA-256 字节级复原；"
                "复原后重跑门禁必须回到 6/6",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", out_path)
    return 0 if (passed == len(results) and back_green) else 1


if __name__ == "__main__":
    sys.exit(main())
