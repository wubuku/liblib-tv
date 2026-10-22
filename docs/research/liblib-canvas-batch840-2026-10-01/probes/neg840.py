#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 840 阴性对照：每条臂**只翻它自己那一条**判据，改完**字节级复原**。

## 为什么要有这个

「对照轮全绿」**不能**证明某条断言有牙 —— 只能证明「现在这样是绿的」。
⟹ 要证明「这条断言真的有牙」，必须**故意破坏一个前提**，看它**精确地红在指定的那一条上**。

★ 三条纪律：
  1. **每条臂只翻它自己那一条** ⟹ 读的字段**互不重叠**
     （例如 N3 动滑杆的 `onChange`、N4 动开关的 `onClick` ⟹ 都翻 S3，
       但它们读的是**不同**的字段 ⟹ 不会互相掩盖）；
  2. **改完必须字节级复原**（SHA-256 对拍）⟹ 否则后面的臂是在脏状态上跑的；
  3. **等 dev server 真的重建完**再跑门禁 ⟹ 否则读到的是旧 chunk
     ⟹ 阴性会「没翻红」⟹ 而那不是「断言没牙」，是「环境没跟上」。

## 臂与它该翻红的那一条

| 臂 | 注入的缺陷 | 应当翻红 |
| --- | --- | --- |
| N1 | `.ce-preview-tools` 的间隙 9px ⟹ 0px（半身/全身 贴在一起） | S2 |
| N2 | 「返回」按钮从 rel 16 ⟹ 20 | S2 |
| N3 | 滑杆 `onChange` 不再更新 state（控件成了摆设） | S3 |
| N4 | 祛斑祛痘开关 `onClick` 不再翻转 | S3 |
| N5 | 阻塞面 union 里的 `"character-editor"` 改名 ⟹ 全局契约认不出它 | S4 |
| N6 | 「保存」改成传**原名**（名字不再落回角色） | S5 |
| N7 | 未实测的页签渲染一枚**假控件**（而不是空态说明） | S7 |
| N8 | README 里的 **mock** 标注全部删掉 | S6 |

★ N1/N2 打的是**几何** ⟹ 翻 S2；
  N3/N4 打的是**交互** ⟹ 翻 S3；
  N5 打的是**阻塞面** ⟹ 翻 S4；
  N6 打的是**保存链路** ⟹ 翻 S5；
  N7 打的是**空态** ⟹ 翻 S7；
  N8 打的是**文档** ⟹ 翻 S6。
"""
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[4]  # probes→batch→research→docs→仓库根
BATCH = ROOT / "docs/research/liblib-canvas-batch840-2026-10-01"
GATE = ROOT / "scripts/verify-liblib-batch840.py"
AUDIT = BATCH / "runtime-audit.json"
DEV_ORIGIN = "http://localhost:4317"

CSS = ROOT / "src/components/character-studio.css"
PANEL = ROOT / "src/components/CharacterEditorPanel.tsx"
CTX = ROOT / "src/lib/libtvSelectionCommandContext.ts"
README = BATCH / "README.md"

# ── 臂的定义：每条只动**一个**文件（README 那条除外，只动文档） ─────────
ARMS = [
    {
        "id": "N1",
        "expect": "S2",
        "files": [CSS],
        "mutate": (lambda s: s.replace(
            "  gap: 9px;\n  height: 32px;",
            "  gap: 0px;\n  height: 32px;",
            1)),
        "note": "半身/全身 的间隙 9px ⟹ 0px",
    },
    {
        "id": "N2",
        "expect": "S2",
        "files": [CSS],
        "mutate": (lambda s: s.replace(
            ".ce-back {\n  position: absolute;\n  left: 16px;",
            ".ce-back {\n  position: absolute;\n  left: 20px;",
            1)),
        "note": "「返回」按钮从 rel 16 ⟹ 20",
    },
    {
        "id": "N3",
        "expect": "S3",
        "files": [PANEL],
        "mutate": (lambda s: s.replace(
            "                          onChange={(event) =>\n"
            "                            setValues((prev) => ({\n"
            "                              ...prev,\n"
            "                              [item.id]: Number(event.target.value),\n"
            "                            }))\n"
            "                          }",
            "                          data-neg840=\"neg840n3\"\n"
            "                          onChange={() => undefined}",
            1)),
        "marker": "neg840n3",
        "note": "滑杆 onChange 不再更新 state",
    },
    {
        "id": "N4",
        "expect": "S3",
        "files": [PANEL],
        "mutate": (lambda s: s.replace(
            "                      data-character-editor-switch=\"spot\"\n"
            "                      onClick={() => setSpot((prev) => !prev)}",
            "                      data-character-editor-switch=\"spot\"\n"
            "                      data-neg840=\"neg840n4\"\n"
            "                      onClick={() => undefined}",
            1)),
        "marker": "neg840n4",
        "note": "祛斑祛痘开关 onClick 不再翻转",
    },
    {
        "id": "N5",
        "expect": "S4",
        "files": [CTX],
        "mutate": (lambda s: s.replace('"character-editor"', '"character-editor-N5"')),
        "marker": "character-editor-N5",
        "note": "阻塞面改名 ⟹ 全局契约认不出大编辑器",
    },
    {
        "id": "N6",
        "expect": "S5",
        "files": [PANEL],
        # ★ 标记必须放在 **JSX 属性位置** ⟹ 放进函数体会变成**无效 JSX** ⟹ 编译失败
        "mutate": (lambda s: s.replace(
            "              data-character-editor-save\n"
            "              onClick={() => {\n"
            "                onSave(name);",
            "              data-character-editor-save\n"
            "              data-neg840=\"neg840n6\"\n"
            "              onClick={() => {\n"
            "                onSave(characterName);",
            1)),
        "marker": "neg840n6",
        "note": "「保存」传原名 ⟹ 名字不再落回角色",
    },
    {
        "id": "N7",
        "expect": "S7",
        "files": [PANEL],
        "mutate": (lambda s: s.replace(
            "                <p className=\"ce-empty\" data-character-editor-empty>\n"
            "                  「{TABS.find((item) => item.id === tab)?.label}」这一页签的控件\n"
            "                  本批未实测（源站 2026-10-22 那趟只采了「皮肤」页签）。\n"
            "                  ⟹ 这里不编造控件，只如实说明。\n"
            "                </p>",
            "                <div data-character-editor-empty data-neg840=\"neg840n7\">\n"
            "                  <input type=\"range\" min={0} max={100} defaultValue={0}\n"
            "                    aria-label=\"编造的滑杆\" />\n"
            "                </div>",
            1)),
        "marker": "neg840n7",
        "note": "未实测页签改成渲染一枚假控件",
    },
    {
        "id": "N8",
        "expect": "S6",
        "files": [README],
        "mutate": (lambda s: re.sub(r"[Mm][Oo][Cc][Kk]", "占位", s)),
        "note": "README 里的 mock 标注全部删掉",
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


def wait_for_marker(marker: str, timeout: int = 120) -> bool:
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
                       text=True, timeout=1200)
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
                ok = wait_for_marker(arm["marker"])
                if not ok:
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
                                             ensure_ascii=False)[:1500])
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
    print("\n%d/%d 通过" % (passed, len(results)))
    out_path = BATCH / "negative-audit.json"
    out_path.write_text(json.dumps({
        "batch": 840,
        "verdict": "%d/%d" % (passed, len(results)),
        "arms": results,
        "note": "每条臂只翻它自己那一条判据；改完按 SHA-256 字节级复原",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", out_path)
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
