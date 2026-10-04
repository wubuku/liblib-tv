#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 35 `verify-shot-version-source.py` 的反向验证（Batch 241 新增）。

**必须成对**：既有「能抓到」的用例，也有「不该误伤」的用例。
只测前者，判据可以靠恒真通过全部用例（纪律 152）。

**本闸的输入是 git 提交历史，所以反验必须造一个真的临时 git 仓**——
先 `git init`，再按「版本区间」分三批提交，然后用 `BEEFTV_SHOT_SPAN_ANCHOR`
把锚点指到临时仓里那一次提交。生产路径不读这个环境变量（真实锚点 `570d6579`
写死在闸里），它只为让临时仓能被同一段代码判定。

## 临时仓的四张图各代表一种归属（缺一张就有一条判据测不到）

| 文件 | 加入 | 之后再被改动 | 期望版本 |
|---|---|---|---|
| `pre.png` | 锚点前 | **没有** | v1.6.6 |
| `mid.png` | 锚点那批 | 没有 | v1.6.13 |
| `post.png` | 锚点后 | 没有 | v1.6.14 |
| `reshot.png` | 锚点前 | **有**（锚点后重拍） | v1.6.14 |

`reshot.png` 是**本闸最重要的样本**：真实 67 张里 `01-home.png` 正是这样
（Batch 6 首拍、Batch 51 在 v1.6.14 重拍）。**判据若锚「这张图是哪一批新增的」，
就会把它错判成 v1.6.6**——所以判据锚的是**最后一次改动**，不是**第一次出现**。

## 十三例

**能抓 5 条**（1–3 三条方向一 + 10 免检表反向核；**下面 rc=2 那组里的 11 / 12 也是能抓的**）
  1. `pre.png`（锚点前）登记成 v1.6.14 → 方向一必报。
     **这一条正是本批在真图上实测过的那个洞**：真实 67 张里有 27 张
     （首批 12 张、v1.6.6 补拍、真实上传轮）就是这么错的。
  2. `post.png`（锚点后）登记成 v1.6.6 → 方向一必报。**与 1 必须成对**：
     只钉 1 的话，判据可能只是「比锚点新的都放行」；这一条证明它是**双向**的。
  3. `mid.png`（锚点那批）登记成 v1.6.6 → 方向一必报（第三段也不能落到第一段）。
  4. 锚点提交根本不存在 → **必须 rc=2**，不能按一张对不上的区间表继续判。
  5. 锚点提交的**信息里没有那个版本号** → **必须 rc=2**。
     **这一条是本闸的自我保护**：锚点信息里的版本号是区间表唯一的书面依据，
     依据没了还继续判，判出来的结论没有任何出处。

**rc=2 五条**（4 锚点提交不存在 / 5 锚点提交信息里没有那个版本号 /
  6 空 manifest / 7 不在 git 仓库里 / **11 与 12 区间表没有覆盖 manifest 里出现的版本**）

  11. 登记里出现一个**比 `SPAN_AFTER` 更新**的版本（v1.6.22）→ **必须 rc=2**。
      **这一条正是闸 35 文件头里写了三个批次的那句能力上限**：
      「方向二能发现锚点自身失效，**发现不了末端该换版本了**」。
      不拦的后果不是「漏报」而是**报出一个错的诊断**——
      方向一会说那些图「落在 v1.6.14 区间」，**照着改登记会把数据改成错的**。
  12. 登记里出现一个**比 `SPAN_BEFORE` 更老**的版本（v1.6.5）→ **也必须 rc=2**。
      **11 与 12 必须成对**：只钉 11 的话，实现可能只是「查有没有比末端更新的」，
      **而表里少了一段更老的同样是表过期**。
      **而 case 8（三个版本都在表里 → 放行）与 11 / 12 一起构成「能抓 + 不误伤」这一对。**

**不误伤 2 条**（用例 10 是「能抓」那一组的另一半，**成对的两条按能抓计**，而它同时也是本闸「不把免检表当成永久有效」的那一半）
  8. 四张图全部登记正确（含 `reshot.png`）→ 必须放行。
  9. 归属任务在账本里**没有版本声明** → 不得因此报错
     （现场有 54 张是这样，**「账本没写」不等于「核对过没问题」，但也不是缺陷**）。
  10. `OFF_TASK` 登记的产出提交与该图**最后一次被改动的提交**不符 → 方向三必报。
     **免检表只减不增就会变成一张没人敢碰的清单**（与闸 16/23 的反向检查同一条纪律）。
     ⚠️ 登记表写死在闸里，而临时仓的提交号必然不同于生产仓，
     所以本例只能测「登记失效会报」这一侧；**「登记仍然有效」那一侧由用例 11 在真仓上验**。

**真实数据 1 条**
  11. 真实 67 张 → rc=0（顺带把 `OFF_TASK` 仍然有效那一侧验掉）。

退出码：0 全部通过；1 有用例失败。
"""

import io
import os
import shutil
import subprocess
import sys
import tempfile
from stagedeps import stage_gate

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE = "verify-shot-version-source.py"

# 临时仓里的三段版本（与生产同名，便于读输出）
V_BEFORE, V_ANCHOR, V_AFTER = "v1.6.6", "v1.6.13", "v1.6.14"

#: (文件名, 任务 id, 期望版本) —— 期望版本就是本闸该判出来的答案
SHOTS = [("pre.png", "t-pre", V_BEFORE), ("mid.png", "t-mid", V_ANCHOR),
         ("post.png", "t-post", V_AFTER), ("reshot.png", "t-reshot", V_AFTER)]

MANIFEST_TMPL = "screenshots:\n\n{recs}"
REC_TMPL = "  - file: screenshots/{fn}\n    task_id: {tid}\n    captured_version: '{ver}'\n\n"
LEDGER_TMPL = "tasks:\n{recs}"
LEDGER_REC = "  - id: {tid}\n    title: 任务 {tid}\n    review_note: 走查（{ver}）\n"
LEDGER_REC_NOVER = "  - id: {tid}\n    title: 任务 {tid}\n    review_note: 走查，**没有任何版本声明**\n"


def sh(d, *args):
    return subprocess.run(("git",) + args, cwd=d, capture_output=True, text=True)


import re as _re


def copy_gate(d, drop_offtask=False):
    """把闸复制到临时仓；`drop_offtask` 时**清空它的 OFF_TASK 免检表**。

    ── 为什么需要这一步 ──
    `OFF_TASK` 是**生产仓的**事实（`24-video-process-menu.png` 的产出提交是 `761106b9`），
    临时仓里那张图要么不在 manifest 里（→ 触发「登记的对象已消失」）、
    要么在但提交号对不上（→ 触发「登记过期了」）。
    **两条都是闸的正确行为，而它们与本组用例要验的方向一无关。**
    所以这里造一份**免检表为空的闸副本**给方向一用例用，
    而**免检表的两个方向由用例 10（临时仓、不清空）与用例 11（真仓）单独验**。

    `str.replace` 静默空转是纪律 240 点名的坑，**所以每次替换都必须 assert 真的发生了**。
    """
    src = io.open(os.path.join(HERE, GATE), encoding="utf-8").read()
    if drop_offtask:
        new_src, n = _re.subn(r"OFF_TASK = \{.*?\n\}\n", "OFF_TASK = {}\n",
                              src, count=1, flags=_re.S)
        assert n == 1, "没能从闸里找到 OFF_TASK 表——注入空转（纪律 240）"
        assert new_src != src and "761106b9" not in new_src
        src = new_src

    #: **Batch 264：这里原来只写闸自己，于是闸加一个本地 import 就会整份崩**——
    #: 实测本批把 `REC_RE` 收敛进 `shotmanifest.py` 之后，**12 例里 11 例转红**，
    #: 症状是子进程里 `ModuleNotFoundError: No module named 'shotmanifest'`。
    #:
    #: **修法是 `stage_gate()` 而不是自己写循环**——理由有两条，缺一条都不够：
    #: **①它自动算闭包，人不用再记**（纪律 279 推论三：手写清单每加一个本地 import 就得人记一次，
    #: **而 Batch 178/181/197/251/252 五次漏搬全部发生在手写清单这一类上**）。
    #: **②闸 17 认它**：`copies_gate_into_tmp()` 的第二个分支就是 `stage_(?:all|gate)\s*\(`。
    #: **第一版改成了 `for dep in sorted(local_closure(…)): shutil.copy(…, dep + ".py", …)`，
    #: 那是一次「修好了却在闸上更红」的改动**——
    #: **闸 17 核搬运时认的是「模块级常量的元素里写着这个模块名」**（Batch 239 修的），
    #: **而 `local_closure(…)` 是一个函数调用，它认不出来**，
    #: 于是闸从「整份跳过」变成「认出了搬闸、却认为依赖没搬齐」——**漏报变成了误报**。
    #: **同一个缺口的两面，而两次都是绿的。**
    #: **闸名写成字面量而不是 `GATE[:-3]`**——`staged_gates()` 的 docstring 写着
    #: 「**只认实参里的字符串字面量**：变量、拼接、推导出来的闸名一律不认——
    #: **判不出来的事不许当通过**」。**那是它有意保守，而写死反而是这里能过的那条路。**
    #: **代价是同一个闸名出现在两处**，所以用 `assert` 机器守住
    #: （抄一份必然漂移，**而机器守得住的那一份不算抄**，纪律 224）。
    assert GATE == "verify-shot-version-source.py", \
        "字面量与 GATE 不一致——**同一个闸名两份真值，而没人会来对**"
    stage_gate(d, "verify-shot-version-source")   # **闭包自动搬齐（含闸自己）**
    with open(os.path.join(d, "scripts", GATE), "w", encoding="utf-8") as f:
        f.write(src)   # **覆盖 `stage_gate` 搬来的那份——它没改过内容**


def build_repo(d, anchor_ver_in_msg=True, drop_offtask=True):
    """造一个三段版本的小仓（见文件头那张表）。"""
    os.makedirs(os.path.join(d, "screenshots"), exist_ok=True)
    os.makedirs(os.path.join(d, "scripts"), exist_ok=True)
    copy_gate(d, drop_offtask=drop_offtask)
    sh(d, "init", "-q")
    sh(d, "config", "user.email", "selftest@example.invalid")
    sh(d, "config", "user.name", "selftest")
    sh(d, "config", "commit.gpgsign", "false")

    def touch(name, body, msg):
        with open(os.path.join(d, "screenshots", name), "w", encoding="utf-8") as f:
            f.write(body)
        sh(d, "add", "-A")
        sh(d, "commit", "-q", "-m", msg)

    # 锚点之前：pre / reshot / off-task 那张，全都是 v1.6.6 时期的图
    for n in ("pre.png", "reshot.png", "24-video-process-menu.png"):
        touch(n, n + "-v1", "batch A: shots captured on v1.6.6")
    # 锚点那一批
    msg = ("batch anchor: runtime walkthrough on v1.6.13, screenshot mid"
           if anchor_ver_in_msg else "batch anchor: screenshot mid")
    touch("mid.png", "mid-v1", msg)
    anchor = sh(d, "rev-parse", "HEAD").stdout.strip()
    # 锚点之后：新图 + 把 reshot.png 重拍一遍（**它的版本因此从 v1.6.6 变成 v1.6.14**）
    touch("post.png", "post-v1", "batch C: new shot on v1.6.14")
    touch("reshot.png", "reshot-v2", "batch C: reshot reshot.png on v1.6.14")
    return anchor


def write_manifest(d, overrides=None, extra_files=()):
    overrides = overrides or {}
    recs = ""
    for fn, tid, ver in SHOTS:
        recs += REC_TMPL.format(fn=fn, tid=tid, ver=overrides.get(fn, ver))
    for fn in extra_files:
        recs += REC_TMPL.format(fn=fn, tid="t-pre", ver=V_BEFORE)
    with open(os.path.join(d, "screenshots", "manifest.yml"), "w", encoding="utf-8") as f:
        f.write(MANIFEST_TMPL.format(recs=recs))


def write_ledger(d, with_version=True):
    tmpl = LEDGER_REC if with_version else LEDGER_REC_NOVER
    recs = "".join(tmpl.format(tid=tid, ver=ver) for _fn, tid, ver in SHOTS)
    with open(os.path.join(d, "task-inventory.yml"), "w", encoding="utf-8") as f:
        f.write(LEDGER_TMPL.format(recs=recs))


def run(root, anchor):
    env = dict(os.environ)
    env["BEEFTV_SHOT_SPAN_ANCHOR"] = anchor
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    p = subprocess.run([sys.executable, os.path.join(root, "scripts", GATE)],
                       capture_output=True, text=True, env=env)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main():
    failures = []
    tmp = tempfile.mkdtemp(prefix="shotsrc-selftest-")
    try:
        def case(name, want_rc, want_in, overrides=None, with_version=True,
                 anchor_missing=False, no_ver_in_msg=False, empty_manifest=False,
                 no_git=False, extra_files=(), real=False):
            d = os.path.join(tmp, name)
            os.makedirs(d, exist_ok=True)
            if real:
                rc, out = run(ROOT, "570d6579")
            elif no_git:
                os.makedirs(os.path.join(d, "screenshots"), exist_ok=True)
                os.makedirs(os.path.join(d, "scripts"), exist_ok=True)
                copy_gate(d, drop_offtask=True)
                write_manifest(d, overrides, extra_files)
                write_ledger(d, with_version)
                rc, out = run(d, "0" * 40)
            else:
                anchor = build_repo(d, anchor_ver_in_msg=not no_ver_in_msg,
                                    drop_offtask="24-video-process-menu.png" not in extra_files)
                if empty_manifest:
                    with open(os.path.join(d, "screenshots", "manifest.yml"),
                              "w", encoding="utf-8") as f:
                        f.write("screenshots:\n")
                else:
                    write_manifest(d, overrides, extra_files)
                write_ledger(d, with_version)
                use = "deadbeef" * 5 if anchor_missing else anchor
                rc, out = run(d, use)
            ok = (rc == want_rc) and (want_in in out)
            print("  %s %-24s rc=%d（期望 %d）%s"
                  % ("✓" if ok else "✗", name, rc, want_rc,
                     "" if ok else "\n      " + out.strip().replace("\n", "\n      ")))
            if not ok:
                failures.append(name)

        # 1 —— 能抓：锚点之前的图登记成锚点之后（本批在真图上实测过的那个洞）
        case("old-shot-claims-new", 1, "落在 **v1.6.6** 区间", {"pre.png": V_AFTER})
        # 2 —— 能抓：锚点之后的图登记成锚点之前（与 1 成对，证明判据是双向的）
        case("new-shot-claims-old", 1, "落在 **v1.6.14** 区间", {"post.png": V_BEFORE})
        # 3 —— 能抓：锚点那批登记成 v1.6.6
        case("anchor-shot-claims-old", 1, "落在 **v1.6.13** 区间", {"mid.png": V_BEFORE})
        # 4 —— rc=2：锚点提交不存在
        case("anchor-missing", 2, "锚点提交", anchor_missing=True)
        # 5 —— rc=2：锚点提交信息里没有那个版本号
        case("anchor-no-ver", 2, "唯一的书面依据", no_ver_in_msg=True)
        # 6 —— rc=2：空 manifest
        case("empty-manifest", 2, "一个都没检查", empty_manifest=True)
        # 7 —— rc=2：不在 git 仓库里
        case("no-git", 2, "不在 git 仓库里", no_git=True)
        # 8 —— 不误伤：四张全对（含 reshot.png —— 判据锚的是「最后一次改动」）
        case("all-correct", 0, "核对通过")
        # 9 —— 不误伤：账本里没有版本声明（现场 54 张是这样）
        case("ledger-no-version", 0, "核对通过", with_version=False)
        # 10 —— 能抓：OFF_TASK 登记的产出提交与该图最后一次被改动的提交不符
        case("offtask-stale", 1, "登记过期了",
             extra_files=("24-video-process-menu.png",))
        # 11 —— 能抓：区间表没有覆盖的版本（**较新的一侧**，也就是文件头里那条能力上限）
        case("span-tail-stale", 2, "区间表的末端已经过期", {"pre.png": "v1.6.22"})
        # 12 —— 能抓：**较旧的一侧**也必须拦。
        # **11 与 12 必须成对**：只钉 11 的话，实现可能只是「查有没有比 SPAN_AFTER 更新的」，
        # **而「表里少了一段更老的」同样是表过期**——那种情况下方向一照样会给出错的诊断。
        # 而 case 8（三个版本都在表里 → 放行）与 11 / 12 一起构成「能抓 + 不误伤」这一对。
        case("span-unknown-older", 2, "区间表的末端已经过期", {"post.png": "v1.6.5"})
        # 13 —— 真实 67 张
        case("real-67", 0, "67 张", real=True)

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("=" * 70)
    if failures:
        print("反验失败 %d 例：%s" % (len(failures), "、".join(failures)))
        return 1
    print("✅ 13/13 例通过（能抓 5 / rc=2 5 / 不误伤 2 / 真实 1）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
