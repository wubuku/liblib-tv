#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1032-②d：探针级变异 —— 把 `onConnect` 从页面源码拿掉 ⇒ 门必须红。

⭐⭐⭐⭐⭐ **为什么要有这个脚本**：前面所有门都是「产品改了就红」。
   而「门自己能不能被证伪」这件事**没人证明过** ⇒ ⇒ 一道永远绿的门，
   和一个「证明自己会被证伪」的门，在外面看起来一模一样。
   ⇒ ⇒ 所以本脚本**真的去把产品改坏**，看门会不会红。

纪律（每一条都对应一个已踩过的坑）：
 ① **变异必须自证「我确实改动了东西」** ⇒ 记 sha256 前后值，且断言不同。
 ② **还原必须逐字还原** ⇒ 还原后 sha256 必须回到原值。
 ③ **即使中途异常也必须还原** ⇒ 还原放在 `finally` 里。
 ④ **不许覆盖别人的并发改动** ⇒ 若期间文件被别人动过 ⇒ 只把那一行插回去，
    不写回整份备份，并在产物里**明写**「期间有他人改动，已保留」。
 ⑤ **不许靠「等几秒」猜编译时序** ⇒ 用**运行时判据 P1 变红**当「变异已生效到浏览器」
    的凭据（静态判据 P6 会立刻红，但那只是「源码被改了」）。
 ⑥ **产物里只留布尔与计数** ⇒ 不许出现时间戳 / pid / 耗时。

⚠️ 本脚本会**真的改 `src/`** ⇒ 跑它的时候别同时改同一份源码。
"""
import hashlib
import io
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, "src", "components", "jimeng", "JimengWorkspace.tsx")
GATE = os.path.join(ROOT, "scripts", "jimeng_probe1032a_connect_contract.py")
CONTRACT = os.path.join(ROOT, "docs", "research", "jimeng-canvas",
                        "connect-contract-1032a.json")
OUT = os.path.join(ROOT, "docs", "research", "jimeng-canvas",
                   "inputs", "mutation-1032d.json")

LINE = "        onConnect={onConnectHandler}\n"
ANCHOR = "        onConnectEnd={onConnectEndHandler}\n"
MAX_ATTEMPTS = 8
PY = sys.executable


def sha(b):
    return hashlib.sha256(b).hexdigest()


def read(p):
    with io.open(p, "rb") as f:
        return f.read()


def write(p, b):
    with io.open(p, "wb") as f:
        f.write(b)


def run_gate():
    r = subprocess.run([PY, GATE], cwd=ROOT, capture_output=True, timeout=900)
    try:
        prod = json.loads(read(CONTRACT).decode("utf-8"))
    except Exception:
        prod = {}
    crit = prod.get("criteria") or {}
    return {
        "rc": r.returncode,
        "P1_runtime": crit.get("P1"),
        "P6_static": crit.get("P6"),
        "false_criteria": prod.get("false_criteria"),
        "p6_static_detail": prod.get("p6_static"),
        "n_false": prod.get("n_false"),
    }


def main():
    orig = read(TARGET)
    orig_sha = sha(orig)
    text = orig.decode("utf-8")
    assert text.count(LINE) == 1, "变异点不唯一：%d" % text.count(LINE)
    mut = text.replace(LINE, "", 1).encode("utf-8")
    assert sha(mut) != orig_sha, "变异没有改变任何字节"

    res = {
        "generated_by": "jimeng_probe1032d_mutation.py",
        "target": "jimeng-canvas-connect-onConnect",
        "mutation": "删除 JimengWorkspace.tsx 里的 onConnect={onConnectHandler} 那一行",
        "self_test_mutation_changed_bytes": True,
        "attempts": 0,
    }

    try:
        write(TARGET, mut)
        res["mutated_sha"] = sha(read(TARGET))
        res["mutated_sha_differs"] = res["mutated_sha"] != orig_sha
        best = None
        for i in range(1, MAX_ATTEMPTS + 1):
            g = run_gate()
            res["attempts"] = i
            best = g
            res["mutated_gate_rc"] = g["rc"]
            res["mutated_P1_runtime_red"] = (g["P1_runtime"] is False)
            res["mutated_P6_static_red"] = (g["P6_static"] is False)
            res["mutated_false_criteria"] = g["false_criteria"]
            res["mutated_p6_static_detail"] = g["p6_static_detail"]
            if g["P1_runtime"] is False and g["P6_static"] is False and g["rc"] != 0:
                break
            time.sleep(15)
        res["mutated_gate_turned_red"] = bool(
            res.get("mutated_P1_runtime_red")
            and res.get("mutated_P6_static_red")
            and res.get("mutated_gate_rc", 0) != 0)
    finally:
        # ── 还原（finally：哪怕上面抛异常也必须还原）────────────────────
        now = read(TARGET)
        if now == mut:
            write(TARGET, orig)
            res["restored_by"] = "full_restore"
            res["other_edits_during_mutation"] = False
        else:
            # ⚠️ 期间有人动过这个文件 ⇒ **不写回整份备份**（那会覆盖别人的改动）
            cur = now.decode("utf-8")
            if LINE not in cur:
                assert ANCHOR in cur, "找不到还原锚点"
                write(TARGET, cur.replace(ANCHOR, LINE + ANCHOR, 1).encode("utf-8"))
            res["restored_by"] = "line_insert_only"
            res["other_edits_during_mutation"] = True
        res["restored_sha_matches_original"] = (sha(read(TARGET)) == orig_sha)
        res["restored"] = True

    # ── 还原后必须再跑一次门 ⇒ 必须绿 ────────────────────────────────
    g2 = run_gate()
    res["restored_gate_rc"] = g2["rc"]
    res["restored_P1_runtime_green"] = (g2["P1_runtime"] is True)
    res["restored_P6_static_green"] = (g2["P6_static"] is True)
    res["restored_false_criteria"] = g2["false_criteria"]

    res["all_ok"] = bool(
        res.get("mutated_gate_turned_red")
        and res.get("restored_sha_matches_original")
        and g2["rc"] == 0
        and g2["P1_runtime"] is True
        and g2["P6_static"] is True)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    write(OUT, json.dumps(res, ensure_ascii=False, indent=1).encode("utf-8"))
    print(json.dumps({k: res[k] for k in (
        "attempts", "mutated_gate_rc", "mutated_P1_runtime_red",
        "mutated_P6_static_red", "mutated_gate_turned_red",
        "restored_by", "restored_sha_matches_original",
        "restored_gate_rc", "restored_P1_runtime_green", "all_ok")},
        ensure_ascii=False))
    print("PROBE_1032D_MUTATION_DONE ->", OUT)
    return 0 if res["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
