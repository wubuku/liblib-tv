#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 836 的**阴性对照** ＋ **真实注入自检**。

## 阴性对照（每条只翻它自己那一条）

  N1 篡改 raw 里的「源站判为 count+1」 ⟹ 只有 **S2** 红
  N2 篡改 raw 里的「默认机位在有 3 台时删不掉」 ⟹ 只有 **S1** 红
  N3 把 clone 运行时读数里的「删主机位」改成 COMMITTED ⟹ 只有 **S4** 红
  N4 把 clone 运行时读数里的「删非主机位」改成失败 ⟹ 只有 **S5** 红
  N5 把 clone 运行时读数里的「只剩一台」的理由改成新增那条 ⟹ 只有 **S6** 红

## ★ 真实注入自检（改产品源码）

  I1 把 `DIRECTOR_PRIMARY_CAMERA_ID` 改成一个**不存在的 id** ⟹ 保护失效 ⟹
     clone 又能删主机位 ⟹ **S4 必须红** ⟹ ⟹ 这证明 S4 真的在测「产品代码」，
     而不是在读一份写死的 JSON。

★ 每条注入后**按字节复原**（sha256 复核）⟹ 不允许带着半恢复的树继续。
★ 注入**必须自校验打上了没打上**（锚点唯一 ／ 文本确实变了 ／ 语法可解析 ／ 读回验证）。
"""
import ast
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE = ROOT / "scripts/verify-liblib-batch836.py"
RAW = ROOT / "docs/research/liblib-canvas-batch836-2026-10-01/raw/source-836-camera-numbering.json"
RUNTIME = pathlib.Path("/tmp/b836-clone-836-runtime.json")
PLANNER = ROOT / "src/lib/directorDeletePlanner.ts"
BACKUP = pathlib.Path("/tmp/b836-neg-backup")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_gate():
    proc = subprocess.run([sys.executable, str(GATE)], cwd=str(ROOT),
                          capture_output=True, text=True, timeout=1800)
    out = (proc.stdout or "") + (proc.stderr or "")
    res = {}
    for line in out.splitlines():
        line = line.strip()
        if line.startswith(("PASS ", "FAIL ")):
            res[line.split()[1]] = line.startswith("PASS ")
    return res, proc.returncode, out


def expect(base, res, flip, name):
    diff = [k for k in base if base[k] != res.get(k)]
    ok = diff == [flip] and res.get(flip) is False
    print("  %s %s ⟹ 翻红的是 %s（期望只有 %s）" % ("✔" if ok else "✘", name, diff, flip))
    if not ok:
        print("      base:", base)
        print("      got :", res)
    return ok


def inject(path, old, new, label):
    txt = path.read_text(encoding="utf-8")
    if txt.count(old) != 1:
        raise SystemExit("★ %s：锚点出现 %d 次（应为 1）⟹ 注入没打上，**中止**"
                         % (label, txt.count(old)))
    cand = txt.replace(old, new)
    if cand == txt:
        raise SystemExit("★ %s：替换后文本没变 ⟹ 注入没打上，**中止**" % label)
    if path.suffix == ".py":
        try:
            ast.parse(cand)
        except SyntaxError as exc:
            raise SystemExit("★ %s：注入后语法坏了（line %s %s）⟹ **中止**"
                             % (label, exc.lineno, exc.msg))
    path.write_text(cand, encoding="utf-8")
    back = path.read_text(encoding="utf-8")
    if new not in back:
        raise SystemExit("★ %s：读回验证失败 ⟹ 注入没落盘，**中止**" % label)


def restore(path, backup_name):
    shutil.copy2(BACKUP / backup_name, path)
    if sha(path) != sha(BACKUP / backup_name):
        raise SystemExit("★ 复原后 sha256 不一致：%s" % path)


def main():
    BACKUP.mkdir(parents=True, exist_ok=True)
    shutil.copy2(GATE, BACKUP / "verify-liblib-batch836.py")
    shutil.copy2(RAW, BACKUP / "raw.json")
    shutil.copy2(PLANNER, BACKUP / "planner.ts")
    rt_backup = BACKUP / "runtime.json"
    if RUNTIME.exists():
        shutil.copy2(RUNTIME, rt_backup)

    print("=== 基线 ===")
    base, _, _ = run_gate()
    print("  ", base)
    if len(base) != 6:
        raise SystemExit("★ 基线不是 6 条判据（拿到 %r）⟹ 中止" % base)
    results = []

    # ---- N1 / N2：篡改 raw ----
    # ★ raw 是 JSON ⟹ ★ **不要用文本锚点**（缩进一变锚点就失效 ⟹ 第一版就是这么坏的）：
    #   改用 JSON 解析器改**值** ⟹ 改完**读回校验那个值确实变了** ⟹ 一样自校验，
    #   而且不受格式化影响。
    def raw_set(path, keys, value, label):
        """按**键路径**改 JSON 的一个值 ⟹ 改完读回校验 ⟹ 返回是否真的改了。"""
        data = json.loads(path.read_text(encoding="utf-8"))
        cur = data
        for k in keys[:-1]:
            if k not in cur:
                raise SystemExit("★ %s：键路径 %r 不存在 ⟹ 中止" % (label, keys))
            cur = cur[k]
        if keys[-1] not in cur:
            raise SystemExit("★ %s：键路径 %r 不存在 ⟹ 中止" % (label, keys))
        old = cur[keys[-1]]
        cur[keys[-1]] = value
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        back = json.loads(path.read_text(encoding="utf-8"))
        node = back
        for k in keys:
            node = node[k]
        if node != value:
            raise SystemExit("★ %s：读回校验失败 ⟹ 注入没落盘，**中止**" % label)
        return old

    raw_cases = [
        ("N1", "把 **clone** 侧的规则从 count+1 改成 max+1（源站那处不动）", "S2",
         ["clone_对照", "★判定"],
         {"前提_删后编号不连续": True, "删后已有的编号": [2, 4], "新机位编号": 4,
          "与已有编号重名": False, "规则": "max+1（不重名）"}),
        ("N2", "把 **v3** 的「默认机位在有 3 台时删不掉」改成删得掉", "S1",
         ["源站_v3_默认机位可删性", "机位1可删"], True),
    ]
    for cid, desc, flip, keys, value in raw_cases:
        try:
            raw_set(RAW, keys, value, cid)
            res, _, _ = run_gate()
            if not res:
                print("  ✘ %s：门禁没跑出判据行 ⟹ 不算阴性通过" % cid)
                results.append(False)
            else:
                results.append(expect(base, res, flip, "%s %s" % (cid, desc)))
        finally:
            restore(RAW, "raw.json")

    # ---- N3 / N4 / N5：篡改 clone 运行时读数（同样用 JSON 方式）----
    rt_cases = [
        ("N3", "把「删主机位」改成成功", "S4",
         "①删主机位_返回", "COMMITTED"),
        ("N4", "把「删非主机位」改成失败", "S5",
         "②删非主机位_成功", False),
        ("N5", "把「只剩一台」的理由改成新增那条", "S6",
         "③只剩一台_理由", "DIRECTOR_PRIMARY_CAMERA_REQUIRED"),
    ]
    for cid, desc, flip, key, value in rt_cases:
        try:
            data = json.loads(RUNTIME.read_text(encoding="utf-8"))
            if key not in data:
                raise SystemExit("★ %s：键 %r 不存在 ⟹ 中止" % (cid, key))
            data[key] = value
            RUNTIME.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            back = json.loads(RUNTIME.read_text(encoding="utf-8"))
            if back.get(key) != value:
                raise SystemExit("★ %s：读回校验失败 ⟹ 中止" % cid)
            res, _, _ = run_gate()
            if not res:
                print("  ✘ %s：门禁没跑出判据行 ⟹ 不算阴性通过" % cid)
                results.append(False)
            else:
                results.append(expect(base, res, flip, "%s %s" % (cid, desc)))
        finally:
            shutil.copy2(rt_backup, RUNTIME)

    # ---- I1：真实注入（改产品源码）----
    print("\n=== I1 真实注入自检：把主机位 id 改成不存在的 ⟹ 保护应失效 ⟹ S4 翻红 ===")
    before = PLANNER.read_bytes()
    try:
        inject(PLANNER,
               'export const DIRECTOR_PRIMARY_CAMERA_ID = "director-camera-main";',
               'export const DIRECTOR_PRIMARY_CAMERA_ID = "director-camera-NOT-EXIST";',
               "I1")
        # ★ 改了产品代码 ⟹ 必须**重跑 clone 侧探针**（读数是旧的，不能用）
        probe = subprocess.run(
            [sys.executable, str(ROOT / "docs/research/liblib-canvas-batch836-2026-10-01/probes/clone836c.py")],
            cwd=str(ROOT), capture_output=True, text=True, timeout=600)
        print("  注入后重跑 clone 探针：", (probe.stdout or "").strip().splitlines()[-1:] or "无输出")
        res, _, _ = run_gate()
        ok = res.get("S4") is False
        print("  %s I1 保护失效后 S4 应翻红 ⟹ 实际 S4=%s" % ("✔" if ok else "✘", res.get("S4")))
        if not ok:
            print("      got:", res)
        results.append(ok)
    finally:
        PLANNER.write_bytes(before)
        if sha(PLANNER) != sha(BACKUP / "planner.ts"):
            raise SystemExit("★ 复原后 sha256 不一致")
        # ★ 复原后必须**重跑** clone 探针，把读数换回「有保护」的版本
        subprocess.run(
            [sys.executable, str(ROOT / "docs/research/liblib-canvas-batch836-2026-10-01/probes/clone836c.py")],
            cwd=str(ROOT), capture_output=True, text=True, timeout=600)
        print("  已复原并重跑 clone 探针，读数已换回")

    print("\n阴性对照 + 注入自检 %d/%d" % (sum(results), len(results)))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
