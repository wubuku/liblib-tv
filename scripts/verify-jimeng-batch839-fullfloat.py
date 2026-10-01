#!/usr/bin/env python3
"""Jimeng clone batch 839 verifier —— 把「按几何的浮层普查」钉成**常备契约**。

## 批 837 留下的那句范围说明，本批兑现

§54 写死过：`jimeng_floating_layer_audit.py` 当时只枚举 2 个状态，
「3 个候选 / 0 缺锚点」**不能**读成「全站浮层都干净」。本批把状态扩到全量
（21 个状态 / 26 个候选层），并把覆盖面本身写成判据。

## 为什么不直接信工具的退出码

工具自己会判「缺锚点 0 个」并退出 0。但**范围**没人守：明天谁把状态从 21 个
删到 3 个，工具照样退出 0、照样打印「0 个缺锚点」。所以本 verifier 额外断言
两件工具自身无法保证的事：

  ① **覆盖面下限**：枚举到的**不同锚点**数量 ≥ 20，且 §二 逐个列出的
     21 个锚点**全部**出现过。少一个就红 —— 缩小范围会**被发现**。
  ② **三种"没结果"必须分开且都为空**：`skipped`（前置态没成立）、
     `empty`（打开了却枚举不到 = 判据盲区）、`expected_empty`（本来就该 0）。
     其中前两个必须都是 0；`expected_empty` 只允许是白名单里那 3 个。

再叠一条**反向自检**：审计器自己在活页面上摘掉一个锚点的 `data-testid`、**重跑整段
几何枚举**，必须报出缺锚点。不这么做，「0 个缺锚点」就只是运气好。

而「内建」也不等于「可信」——它同样可能被改成一个恒真的样子，所以 §E 一半取它
**运行时**的输出，一半对它的**源码**下防阉割契约（豁免表不许出现 `"": ...`
万能钥匙、退出码不许写死、自检不许只查标记元素在不在）。
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "scripts" / "jimeng_floating_layer_audit.py"
OUT = Path("/tmp/jimeng-floating-layers-b839.json")

# 覆盖面下限清单：每个都必须在普查结果里出现过
EXPECTED_TIDS = [
    "video-toolbar-capture-menu", "video-toolbar-tools-menu",
    "gen-model-listbox", "gen-video-size-listbox",
    "gen-mode-listbox", "gen-duration-listbox",
    "text-bg-palette", "image-tools-menu",
    "audio-music-model-listbox", "audio-music-duration-listbox",
    "audio-voice-model-listbox", "audio-gen-mode-listbox",
    "audio-all-voices-listbox", "audio-voice-filter-listbox",
    "canvas-context-menu", "canvas-zoom-menu",
    "video-fullscreen-preview",        # 批 840 新增（全屏模态）
    "topbar-share-panel", "canvas-user-menu", "topbar-more-menu",
    "jimeng-search-overlay", "topbar-history-menu",
]

# 只有这三个状态允许「枚举到 0 个候选」，且必须写明理由
# 状态名 → **必须逐字一致**的理由。批 840 把工具输出改成结构化
# {state, reason} 之后，这里可以逐字钉住理由，而不只是"有理由"（见 B.4）。
ALLOWED_EMPTY = {
    "空态": "画布上本来就没有任何浮层",
    "视频工具条": "工具条本身是 React Flow 的宿主架，判定为不是浮层；"
                  "它带出来的两个下拉由下面两个状态各自枚举",
    "视频生成面板": "生成面板是工具条里的一块板，本身没有独立锚点；"
                    "它内部的 4 个下拉由下面 4 个状态各自枚举",
    # 批 840 补：839 那轮它报出的那 1 个候选是**漏过来**的工具下拉
    # （TID2TRIG 当时缺了视频那两个下拉），补上之后 0 才是真值。
    "图片节点产出（截帧）": "截帧只产出图片节点，本身不打开任何浮层；"
                          "它的工具菜单由下面那个状态各自枚举",
}

failures: list[str] = []
checks = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global checks
    checks += 1
    if ok:
        print(f"  PASS  {name}" + (f"  ({detail})" if detail else ""))
    else:
        print(f"  FAIL  {name}  {detail}")
        failures.append(name)


def run_audit(env_extra: dict | None = None) -> tuple[int, str, dict]:
    env = dict(os.environ)
    env["SNAP_OUT"] = str(OUT)
    env.update(env_extra or {})
    r = subprocess.run(
        [sys.executable, str(AUDIT)],
        capture_output=True, text=True, env=env, cwd=str(ROOT), timeout=600)
    data = {}
    if OUT.exists():
        try:
            data = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            data = {"_parse_error": str(e)}
    return r.returncode, (r.stdout or "") + (r.stderr or ""), data


def main() -> int:
    # ── A. 跑一遍普查（正常状态）─────────────────────────────────
    print("— A. 按几何的浮层普查（全量状态）—")
    rc, out, data = run_audit()
    rows = data.get("rows", [])
    skipped = data.get("skipped", [])
    empty = data.get("empty", [])
    expected_empty = data.get("expected_empty", [])

    check("A.0 普查工具跑完且退出码 0（= 缺锚点 0 且自检通过）", rc == 0,
          f"rc={rc}；末尾：{out.strip().splitlines()[-1][:70] if out.strip() else ''}")
    check("A.1 结果文件可解析", not data.get("_parse_error"),
          str(data.get("_parse_error"))[:80])
    seen_tids = {r["tid"] for r in rows if r["tid"]}
    check(f"A.2 枚举到 {len(rows)} 个候选 / {len(seen_tids)} 个不同锚点",
          len(rows) > 0, f"rows={len(rows)} distinct={len(seen_tids)}")

    # ── B. 三种"没结果"必须分开记账，且前两种为空 ────────────────
    print("\n— B. 「没结果」的三种形态必须分开（沉默的漏报最贵）—")
    check(f"B.1 skipped（前置态没成立）= 0 —— 实测 {len(skipped)}",
          not skipped, "; ".join(skipped[:3]))
    check(f"B.2 empty（打开了却枚举不到 = 判据盲区）= 0 —— 实测 {len(empty)}",
          not empty, "; ".join(empty[:3]))
    # 批 840：工具输出已是 {state, reason}，直接取字段 —— 旧写法是
    # `e.split("（")[0]`，而状态名**本身带括号**（`图片节点产出（截帧）`），
    # 拼一拆就错，且错得像"工具有 bug"。
    got = {e.get("state"): e.get("reason", "") for e in expected_empty}
    check(f"B.3 expected_empty 的状态集合 = 白名单那 {len(ALLOWED_EMPTY)} 个 —— "
          f"实测 {len(expected_empty)}",
          set(got) == set(ALLOWED_EMPTY),
          f"实际={sorted(x for x in got if x)} 期望={sorted(ALLOWED_EMPTY)}")
    wrong = {k: (got.get(k), v) for k, v in ALLOWED_EMPTY.items()
             if got.get(k) != v}
    check("B.4 每个 expected_empty 的理由都逐字对得上（不许含糊成'同上'）",
          not wrong, f"对不上={list(wrong)[:2]}")

    # ── C. 覆盖面下限：缩小范围会被发现 ───────────────────────────
    print("\n— C. 覆盖面下限（工具自己无法保证的那部分）—")
    missing = [t for t in EXPECTED_TIDS if t not in seen_tids]
    check(f"C.1 契约列出的 {len(EXPECTED_TIDS)} 个锚点全部被枚举到",
          not missing, f"没看到={missing}")
    check(f"C.2 不同锚点数 ≥ 20（防悄悄缩小范围）", len(seen_tids) >= 20,
          f"实际={len(seen_tids)}")
    # 状态数下限
    states = {r["state"] for r in rows}
    check(f"C.3 状态数 ≥ 20（防把状态列表砍掉；批 840 后实测 21）", len(states) >= 20,
          f"实际={len(states)}")

    # ── D. 无 role 的两处必须**仍然**被枚举到 ─────────────────────
    #    它们是这条通道存在的理由（§52/§54）。哪天枚举不到了，
    #    说明有人把判据改回按 role 筛了。
    print("\n— D. 这条通道存在的理由：无 role 的两处仍被枚举到 —")
    for tid in ("video-toolbar-capture-menu", "video-toolbar-tools-menu"):
        hit = [r for r in rows if r["tid"] == tid]
        # f-string 里不能直接嵌同种引号（Python 3.12 仍限制），先算好再拼
        role_seen = hit[0]["role"] if hit else "n/a"
        check(f"D.{tid} 被枚举到、且 role 确实为空（判据没退回按 role 筛）",
              bool(hit) and role_seen == "",
              f"命中 {len(hit)} 次 role={role_seen!r}")

    # ── E. 反向自检：审计器**自己**已经做了，而且必须是真做 ───────
    #    第一版这里想"改源码摘锚点再跑一遍"，已经改掉了 —— 两个理由：
    #      ① 那要求临时改 `JimengGenPanel.tsx`，并行会话可能正在编辑同一个文件，
    #         `finally` 还原会把别人的改动一起抹掉（违反"绝不丢弃他人修改"）。
    #      ② 审计器内建的自检**在活页面上**摘 testid 再重扫，比改源码更贴近真实。
    #    但"内建"不等于"可信"：它有可能被改成一个恒真的样子。所以这里
    #    既取它**运行时**的输出，又对它的**源码**做几条防阉割契约。
    print("\n— E. 反向自检：真跑过、且没被改成恒真 —")
    m_cand = re.search(r"仍把它当候选=(\w+)", out)
    m_miss = re.search(r"并报成缺锚点=(\w+)", out)
    check("E.1 重跑几何枚举后，探针**仍被当候选**（几何判据不依赖锚点）",
          bool(m_cand) and m_cand.group(1) == "True",
          f"实测={m_cand.group(1) if m_cand else '没输出'}")
    check("E.2 探针随即**被报成缺锚点**（判据能失败，不是恒真）",
          bool(m_miss) and m_miss.group(1) == "True",
          f"实测={m_miss.group(1) if m_miss else '没输出'}")

    asrc = AUDIT.read_text(encoding="utf-8")
    # ③ 万能钥匙式豁免：历史上这里被塞过 `"": "..."`，空 tid 于是全部豁免、
    #    「缺锚点」恒为 0。这条断言专门防它再回来。
    m_exempt = re.search(r"^NO_TID_EXEMPT\s*:\s*dict\[str,\s*str\]\s*=\s*(\{.*?\})\s*$",
                         asrc, re.M)
    check("E.3 豁免表必须是**字面空字典**（不许出现 `\"\": ...` 万能钥匙）",
          bool(m_exempt) and m_exempt.group(1) == "{}",
          f"实际={m_exempt.group(1) if m_exempt else '没找到该行'}")
    check("E.4 退出码必须由 missing 推出（不许把 0 写死）",
          "return 1 if missing else 0" in asrc)
    # ④ 自检必须**重跑整段枚举**。只查 `[data-selfcheck]` 还在不在的话，
    #    `still_candidate = bool(rows2)` 恒真 —— 哪怕枚举被改成
    #    "只挑带 data-testid 的"，它照样报 ✓。
    tail = asrc.split("selfcheck: dict = {}")[-1]
    check("E.5 自检里必须 `page.evaluate(ENUM_JS)` 真重扫枚举",
          "page.evaluate(ENUM_JS)" in tail,
          "只查标记元素在不在 = 恒真" if "page.evaluate(ENUM_JS)" not in tail else "")

    print(f"\n{checks - len(failures)}/{checks}")
    if failures:
        print("FAILED: " + ", ".join(failures))
        return 1
    print("batch 839-fullfloat OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
