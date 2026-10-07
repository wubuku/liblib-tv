#!/usr/bin/env python3
"""门禁自检：故意注入故障，断言每道门禁**以正确的理由**失败。

**为什么需要这道自检（M42 起因）**：M41 发现锚点门禁的 slugify 复刻漏了
NFKD，在 236 个标题里错判 29 个，却一直报「全部有效」。M42 又发现孤儿任务页
和索引漏条两类问题两道门禁全都放行。**门禁本身也是有 bug 的，而且它坏了不会
自己喊疼**——所以必须有一道检查去检查「检查」。

**核心设计：断言错误内容，而不只是退出码。** 只看退出码会被两种情况骗：
① 变异脚本自己写歪了，被测对象其实没被改动（BSD sed 不支持 `0,/re/` 那次）；
② 被测对象以**错误的理由**失败（探针误删 `.vitepress` 导致构建报「缺少
config.mjs」，差点被记成「构建抓到了孤儿页」）。两种都是假阳性——而假阳性
比假阴性更危险，因为它会让你以为门禁是好的。

所以每个用例都声明「必须由哪道门禁、报出哪段文字」来拦，拦不到或报错理由
不对都算失败。

用法：
    python3 scripts/selftest-gates.py            # 在本手册目录下跑
    python3 scripts/selftest-gates.py <手册目录>

退出码 0 表示全部用例按预期被拦下，1 表示有门禁形同虚设。
"""

from __future__ import annotations

import ast
import hashlib
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_SCRIPTS = Path(__file__).resolve().parents[4] / ".agents/skills/web-studio-user-manual/scripts"
GATE = REPO_SCRIPTS / "audit_manual.py"


# ---------- 注入有效性检测（M193） ----------
#
# M193 撞上的真实故障：把不可逆按钮白名单从四项扩到六项之后，
# `mutate_probe_contract_drift` 仍在按**旧的四项串**做 `text.replace(...)`，
# 锚点早就没了，`replace` 成了**空操作**——用例等于什么都没注入，
# 门禁自然放行，于是自检报「门禁漏网」。
#
# 这个诊断是**错的**：门禁没坏，坏的是注入。而这两种情况的处置完全相反
# （前者去改门禁，后者去改用例），混为一谈会让人去调试一道根本没问题的闸。
#
# 更要紧的是它**不会自己暴露**：一条永远注入失败的用例，会让门禁少一道考问，
# 而自检本身看不出少了什么。所以这里在跑门禁**之前**先确认注入真的改动了文件。
#
# 判据只看「文件内容变没变」，不关心怎么改的，因此不会误伤任何正当注入。
#
# ★ 这道检测**第一版就误伤了 9 条用例**，两类原因都踩了（M194 记）：
#   一、`dist` 与 `node_modules` 被我当成「不用看」而排除，可渲染类用例改的
#      正是临时树里的 `dist/index.html`——**排除掉的那部分恰好是它们要改的**；
#   二、图片用例往 `.png` 尾部追加一个字节，而我只给文本后缀算摘要。
# 所以规则是：**一律不排除路径**（`dist` 由 `copytree` 自己挡掉），
# 文本算内容哈希、非文本记「大小 + 修改时间」——追加字节与删除文件都看得见。
DIGEST_SUFFIXES = {".md", ".py", ".yml", ".yaml", ".sh", ".js", ".json", ".html", ".txt", ".css"}
DIGEST_SKIP_DIRS = {"node_modules"}


def tree_digest(root: Path) -> dict[str, str]:
    """给手册树算内容摘要：文本文件算哈希，其余记「大小@修改时间」。"""
    out: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in DIGEST_SKIP_DIRS for part in rel.parts):
            continue
        if path.suffix.lower() in DIGEST_SUFFIXES:
            out[str(rel)] = "h:" + hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            stat = path.stat()
            out[str(rel)] = f"s:{stat.st_size}@{stat.st_mtime_ns}"
    return out


def changed_files(before: dict[str, str], after: dict[str, str]) -> list[str]:
    return sorted(
        key
        for key in set(before) | set(after)
        if before.get(key) != after.get(key)
    )


def verify_injection_detector() -> tuple[bool, str]:
    """给「注入有效性检测」本身做自检，两个方向都要成立。

    M140 立过的规矩：**新门禁必须有自检注入用例证明会拦，
    且要有反向对照证明不误报。** 这道检测自己就是一道判据，同样适用。

    正向：真改动必须被认出来，否则「注入无效」会误伤全部正当用例。
    阴性：什么都没改时不能被认成「改过」，否则连真漏网也一起放过。

    ★ 正向必须**分四种**试（第一版只试了「改文本」，结果立刻误伤 9 条）：
    改文本、改二进制（追加字节）、删文件、建新文件。**判据少覆盖一种，
    就会有整类正当注入被误报成「没注入」**——而这类误报会让人怀疑真正的漏网。
    """
    with tempfile.TemporaryDirectory(prefix="m193inject-") as tmp:
        root = Path(tmp) / "manual"
        (root / "scripts").mkdir(parents=True)
        (root / "screenshots").mkdir(parents=True)
        text_file = root / "scripts/probe-toolbar-states.js"
        bin_file = root / "screenshots/two-nodes.png"
        text_file.write_text("const DESTRUCTIVE = new Set(['删除']);\n", encoding="utf-8")
        bin_file.write_bytes(b"\x89PNG\r\n\x1a\n")

        def probe(action) -> list[str]:
            before = tree_digest(root)
            action()
            return changed_files(before, tree_digest(root))

        edit_text = probe(
            lambda: text_file.write_text(
                "const DESTRUCTIVE = new Set(['删除全部']);\n", encoding="utf-8"
            )
        )
        append_bin = probe(lambda: bin_file.open("ab").write(b"x"))
        drop_file = probe(lambda: bin_file.unlink())
        def make_artifact() -> None:
            # 渲染类用例改的正是临时树里的 `dist/index.html`——
            # 第一版把这层目录当成「不用看」排除掉，正好把它们的注入一起排除了。
            dist = root / "dist"
            dist.mkdir()
            (dist / "index.html").write_text("<p>x</p>", encoding="utf-8")

        add_file = probe(make_artifact)
        do_nothing = probe(lambda: None)

    blind = [
        label
        for label, got in (
            ("改文本", edit_text),
            ("追加字节到二进制", append_bin),
            ("删文件", drop_file),
            ("新建文件", add_file),
        )
        if not got
    ]
    if blind:
        return False, f"正向对照不成立：以下改动没被认出来，会误报成「注入无效」——{'、'.join(blind)}"
    if do_nothing:
        return False, f"阴性对照不成立：没改任何东西却报「改过」（{do_nothing}）"
    return True, "改文本/二进制/删文件/建文件均被认出，未改动时不误报"


# ---------- 变异函数：每个只改一处，改完必须能被预期门禁抓到 ----------


def mutate_image_bytes(root: Path) -> None:
    (root / "screenshots/30-concepts-two-text-nodes.png").open("ab").write(b"x")


def mutate_manifest_drop_record(root: Path) -> None:
    path = root / "screenshots/manifest.yml"
    text = path.read_text(encoding="utf-8")
    start = text.index("  - file: screenshots/30-concepts-two-text-nodes.png")
    end = text.index("  - file:", start + 10)
    path.write_text(text[:start] + text[end:], encoding="utf-8")


def mutate_manifest_bad_sha(root: Path) -> None:
    path = root / "screenshots/manifest.yml"
    text = path.read_text(encoding="utf-8")
    i = text.index("  - file: screenshots/30-concepts-two-text-nodes.png")
    j = text.index("    sha256: ", i)
    k = text.index("\n", j)
    path.write_text(text[:j] + "    sha256: " + "0" * 64 + text[k:], encoding="utf-8")


def mutate_manifest_bad_task_id(root: Path) -> None:
    path = root / "screenshots/manifest.yml"
    text = path.read_text(encoding="utf-8")
    i = text.index("  - file: screenshots/30-concepts-legacy-config-migrated.png")
    j = text.index("    task_id: organize-canvas", i)
    path.write_text(
        text[:j] + "    task_id: no-such-task" + text[j + len("    task_id: organize-canvas") :],
        encoding="utf-8",
    )


def mutate_manifest_missing_field(root: Path) -> None:
    path = root / "screenshots/manifest.yml"
    text = path.read_text(encoding="utf-8")
    i = text.index("  - file: screenshots/30-concepts-legacy-config-migrated.png")
    j = text.index("    verified_locator:", i)
    k = text.index("\n", j)
    path.write_text(text[:j] + text[k + 1 :], encoding="utf-8")


def mutate_delete_referenced_image(root: Path) -> None:
    (root / "screenshots/30-concepts-two-text-nodes.png").unlink()


def mutate_empty_alt(root: Path) -> None:
    path = root / "30-concepts.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "![画布上两个文本节点：左侧是角色描述，右侧是风格提示词](screenshots/30-concepts-two-text-nodes.png)",
        "![](screenshots/30-concepts-two-text-nodes.png)",
    )
    path.write_text(text, encoding="utf-8")


def mutate_broken_md_link(root: Path) -> None:
    path = root / "README.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace("30-concepts.md", "30-concepts-nope.md"),
        encoding="utf-8",
    )


def mutate_heading_jump(root: Path) -> None:
    path = root / "30-concepts.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "## 连线不等于自动生效", "#### 连线不等于自动生效"
        ),
        encoding="utf-8",
    )


def mutate_broken_anchor(root: Path) -> None:
    path = root / "10-tasks/create-nodes.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "../30-concepts.md#两种打不开的节点类型", "../30-concepts.md#根本没有这个标题"
        ),
        encoding="utf-8",
    )


def mutate_orphan_page(root: Path) -> None:
    (root / "10-tasks/orphan-page.md").write_text(
        "# 孤儿页\n\n没登记到 task-inventory.yml 的一页。\n", encoding="utf-8"
    )


def mutate_index_drop_entry(root: Path) -> None:
    path = root / "10-tasks/README.md"
    text = path.read_text(encoding="utf-8")
    i = text.index("use-agent.md")
    a, b = text.rindex("[", 0, i), text.index("]", i)
    path.write_text(text[:a] + text[b + 1 :], encoding="utf-8")


def mutate_bare_claim(root: Path) -> None:
    path = root / "10-tasks/create-nodes.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "## 文本节点：先写内容",
        "## 凭空多出来的一节\n\n这个节点的默认尺寸和所有官方文档完全一致，界面文案也逐字相同。\n\n## 文本节点：先写内容",
    )
    path.write_text(text, encoding="utf-8")


def mutate_retracted_claim(root: Path) -> None:
    """把一条已订正过的错误说法重新塞回正文（M52 漏改的真实形态）。"""
    path = root / "10-tasks/undo-persistence.md"
    text = path.read_text(encoding="utf-8")
    text += "\n导出是唯一能带走项目的方式。\n"
    path.write_text(text, encoding="utf-8")


def mutate_retracted_freeresize(root: Path) -> None:
    """R20：把 M93 订正掉的「自由缩放」原句放回去（验证 R20 这条订正抓得住）。"""
    path = root / "10-tasks/edit-nodes.md"
    text = path.read_text(encoding="utf-8")
    text += "\n需要自由变形时，用悬浮工具条开启「自由缩放」（图片节点）。\n"
    path.write_text(text, encoding="utf-8")


def mutate_retracted_stale_count(root: Path) -> None:
    """R22：把 M98 那条基于陈旧计数的错误观察放回去（验证 R22 抓得住）。"""
    path = root / "20-reference.md"
    text = path.read_text(encoding="utf-8")
    text += "\n> 方向拖反时连线数确实增加。\n"
    path.write_text(text, encoding="utf-8")


def mutate_retracted_video_params(root: Path) -> None:
    """R21：把 M93 订正掉的视频面板参数原句放回去（验证 R21 这条订正抓得住）。"""
    path = root / "10-tasks/generate-images.md"
    text = path.read_text(encoding="utf-8")
    text += "\n时长可选 4-8 秒，分辨率 480p / 720p / 1080p 自动匹配。\n"
    path.write_text(text, encoding="utf-8")


def mutate_publish_gate_drift(root: Path) -> None:
    """把 build-site.sh 里某道门禁的调用改掉，使它与 PUBLISH.md 的门禁表对不上（M106 新门禁）。

    注意这里**改的是脚本而不是文档**：把 `check-ratings.py` 改名成一个脚本里
    不再存在的东西，文档那行就成了"写了但脚本没跑"。反过来（只给脚本加一道新门禁
    而文档没写）同样会被拦，两条判据是同一个"集合相等"的两个方向。

    构造这条用例时踩过的坑记在 check-publish-sync.py 里：判据**必须剥掉注释行**
    再提取脚本名，否则 `audit_manual.py` 那三处注释会让"文档写了但没跑"这条判据
    永远失效——那正是本门禁要抓的第一个真问题。
    """
    build = root / "build-site.sh"
    text = build.read_text(encoding="utf-8")
    assert "scripts/check-ratings.py" in text, "构建脚本里找不到 check-ratings.py，用例无法构造"
    text = text.replace("scripts/check-ratings.py", "scripts/check-ratings-DISABLED.py", 1)
    build.write_text(text, encoding="utf-8")


def mutate_ledger_pin_drift(root: Path) -> None:
    """把账本锁定的提交改成一个与应用仓 HEAD 不同的 sha（M105 新门禁的负向测试）。

    账本开头那句「版本锁定：提交 <sha>」是整本账本成立的前提——§4 的节点尺寸、
    §6 的连线校验全都是在那个提交上观察到的。此前**没有任何机制守着它**：把
    应用仓推进之后，账本照旧以「版本锁定」的口吻陈述旧观察，全部源码层门禁
    都不会报错。

    注意本用例必须**改 sha 而不能删掉那一句**：删掉时门禁报的是"锁都没锁住"，
    那是另一条判据（断言存在性），抓不到本门禁真正要守的东西（断言一致性）。

    2026-10-02 M110 调整：门禁扩到**全部**声明文件后，「只改账本」会先被
    **跨文件一致性**那条判据拦下（理由会变成「各声明文件锁定的提交不一致」），
    走不到本用例要验的 HEAD 漂移。因此这里**两份声明文件一起改**。
    """
    path = root / "SOURCE_OBSERVATIONS.md"
    text = path.read_text(encoding="utf-8")
    real = "16b31273633f983cdbd8de05694ec36d471b2650"
    drifted = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
    if real not in text:
        # 账本换过锁定提交时也要能注入：把当前那个 sha 顶掉即可
        import re as _re

        found = _re.search(r"提交\s*`([0-9a-f]{40})`", text)
        if not found:
            raise AssertionError("账本里找不到 40 位锁定提交，自检用例无法构造")
        text = text.replace(found.group(1), drifted, 1)
    else:
        text = text.replace(real, drifted, 1)
    path.write_text(text, encoding="utf-8")

    # 任务账本是第二个声明者，一起改，才能走到「与应用仓 HEAD 不一致」那条判据
    inv = root / "task-inventory.yml"
    if inv.is_file():
        inv_text = inv.read_text(encoding="utf-8")
        import re as _re2

        for found in _re2.finditer(r"\b[0-9a-f]{40}\b", inv_text):
            inv_text = inv_text.replace(found.group(0), drifted, 1)
            break
        else:
            raise AssertionError("任务账本里找不到 40 位锁定提交，自检用例无法构造")
        inv.write_text(inv_text, encoding="utf-8")


def mutate_pin_declarer_disagreement(root: Path) -> None:
    """只把任务账本里的锁定提交改掉，让两份声明互相对不上（M110 新增判据的负向测试）。

    这是 M110 查出的真实事故形态：应用仓一推进，账本门禁变红，维护者更新了
    `SOURCE_OBSERVATIONS.md` 的 sha 却漏了 `task-inventory.yml` —— 两份都是
    「这本手册对齐哪个提交」的权威声明，而旧的门禁**只看着其中一份**，
    漏改的那份会静默过期。

    注意它和 `mutate_ledger_pin_drift` 验的是**两条不同的判据**：
    这一条不碰应用仓，纯粹是两份声明之间必须一致。
    """
    inv = root / "task-inventory.yml"
    if not inv.is_file():
        raise AssertionError("找不到 task-inventory.yml，自检用例无法构造")
    text = inv.read_text(encoding="utf-8")
    import re as _re

    for found in _re.finditer(r"\b[0-9a-f]{40}\b", text):
        text = text.replace(found.group(0), "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef", 1)
        inv.write_text(text, encoding="utf-8")
        return
    raise AssertionError("任务账本里找不到 40 位锁定提交，自检用例无法构造")


def mutate_pin_version_drift(root: Path) -> None:
    """只把任务账本里的版本号改掉，sha 保持一致（M110 版本判据的负向测试）。

    这一条专治一个具体漏洞：版本判据最初写成「应用版本是否**出现在**声明的
    并集里」，而并集里仍留着另一个文件的 v0.14.0，于是只改一个文件完全蒙混过关。
    负向测试当场抓到了它——**没有负向测试，新判据就是没人验证过的判据。**
    """
    inv = root / "task-inventory.yml"
    if not inv.is_file():
        raise AssertionError("找不到 task-inventory.yml，自检用例无法构造")
    text = inv.read_text(encoding="utf-8")
    import re as _re

    found = _re.search(r"v\d+\.\d+\.\d+", text)
    if not found:
        raise AssertionError("任务账本里找不到版本号，自检用例无法构造")
    major, minor, patch = found.group(0).lstrip("v").split(".")
    bumped = f"v{int(major)}.{int(minor) + 1}.{patch}"
    inv.write_text(text.replace(found.group(0), bumped, 1), encoding="utf-8")


def mutate_source_ref_out_of_range(root: Path) -> None:
    """把正文里一处 file:line 引用的行号改成远超文件长度的值（M109 新门禁的负向测试）。

    手册通篇用 `文件.ts:行号` 指向源码，这是读者唯一能自己复核"这条结论从哪来"
    的把手。行号会随源码推进而漂移，而账本锁定门禁只在**应用仓 HEAD 变了**时报错
    ——一旦有人把账本 sha 一起更新到新提交，那道门禁重新变绿，正文里那几十处
    行号却可能早已指向别处。

    注入方式选**越界**而不是「改错文件」：越界是"这行已经不存在了"这种最常见
    的漂移形态（文件被删/被挪走/被重写），而且判据明确、无歧义。

    替换的是**整个匹配**（含 `-起止` 区间部分）而不是只换第一个数字：本条用例
    第一版只换了起点，把 `foo.ts:267-269` 改成了 `foo.ts:999999-269`——终点 269
    完全合法，于是门禁放行，用例漏网。**这道自检自己抓出了自己注入方式的漏洞。**
    """
    import re as _re

    for name in ["SOURCE_OBSERVATIONS.md", "20-reference.md", "30-concepts.md",
                 "90-troubleshooting.md", "00-quickstart.md", "README.md"]:
        page = root / name
        if not page.is_file():
            continue
        text = page.read_text(encoding="utf-8")
        found = _re.search(r"([A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:ts|tsx|js|jsx|mjs|mts|css)):(\d+(?:-\d+)?)", text)
        if not found:
            continue
        text = text.replace(found.group(0), f"{found.group(1)}:999999", 1)
        page.write_text(text, encoding="utf-8")
        return
    raise AssertionError("正文里找不到任何 file:line 引用，自检用例无法构造")


def mutate_dead_dist_link(root: Path) -> None:
    """在产物里塞一条指向不存在页面的链接（M56 发现的真实形态）。

    自检不复制 dist（见 prepare 处的 ignore_patterns），所以这里现造一个最小
    产物目录：一个 index.html，里面链向一个没被构建出来的页面。
    """
    dist = root / ".vitepress" / "dist"
    dist.mkdir(parents=True, exist_ok=True)
    (dist / "index.html").write_text(
        '<!DOCTYPE html><html><body><a href="./nope.html">死链</a>'
        '<a href="./ok.html">好链</a></body></html>',
        encoding="utf-8",
    )
    (dist / "ok.html").write_text("<!DOCTYPE html><html><body>ok</body></html>", encoding="utf-8")


def mutate_sidebar_rename(root: Path) -> None:
    path = root / ".vitepress/config.mjs"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "link: '/10-tasks/use-agent'", "link: '/10-tasks/renamed-agent'"
        ),
        encoding="utf-8",
    )


def mutate_rating_drift_inventory(root: Path) -> None:
    """账本评级与两个下游不一致（M58 发现的真实形态）。

    真实漂移是 `use-prompt-library` 在账本里被写成 `full`，而索引分组与首页
    表格都还停在「简明」。这里复原同一个形态：只改账本，断言评级门禁抓到。
    """
    path = root / "task-inventory.yml"
    text = path.read_text(encoding="utf-8")
    i = text.index("  - id: use-prompt-library")
    j = text.index("    coverage: concise", i)
    path.write_text(
        text[:j] + "    coverage: full" + text[j + len("    coverage: concise"):],
        encoding="utf-8",
    )


def mutate_inventory_stale_count(root: Path) -> None:
    """账本 screenshot_count 与 manifest 实数不符（M59 发现的真实形态）。

    真实失修是 use-agent 账本记 4 张而 manifest 实为 8 张。这里复原同一形态：
    只改账本字段，断言新鲜度门禁抓到。
    """
    path = root / "task-inventory.yml"
    text = path.read_text(encoding="utf-8")
    i = text.index("  - id: use-agent")
    j = text.index("    screenshot_count: ", i)
    k = text.index("\n", j)
    path.write_text(text[:j] + "    screenshot_count: 4" + text[k:], encoding="utf-8")


def mutate_table_split_by_quote(root: Path) -> None:
    """表格被引用块劈开（M65 的真实事故形态）。

    2026-10-01 实测：shortcuts-help.md 的「弹窗里的十三条」被一段多选提示的
    引用块从第 8 行和第 9 行之间劈开，后 5 行失去表头与分隔行，渲染成一团
    | … | 原始文本，而其余九道门禁全部放行。这里复原同一形态。
    """

    path = root / "10-tasks/shortcuts-help.md"
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.startswith("| `Ctrl / Cmd` + `Y` | 重做 |"):
            lines.insert(i + 1, "\n> 注入的提示块，把表格从中间劈开了。\n>\n")
            break
    path.write_text("".join(lines), encoding="utf-8")


def mutate_table_outside_fence(root: Path) -> None:
    """代码块**外**的孤立表格行（M71 加代码块跳过后的反向验证）。

    M71 给 `check-tables.py` 加了"围栏代码块内整块跳过"，因为手册多处要**展示**
    表格写法本身（`PUBLISH.md` 里教人追加记录时给出的一行 `| 级别 | 描述 |`）。
    加了这个豁免就必须同时证明：**豁免没有扩大到代码块外**——否则等于给整本手册
    开了一个可以随便写残缺表格的后门。这里在真实表格前插一个代码块（内含一行
    假表格，应当被跳过），紧跟一行代码块外的孤立表格行（应当被抓）。
    """

    path = root / "20-reference.md"
    text = path.read_text(encoding="utf-8")
    anchor = "## 鼠标与键位\n"
    injected = "```\n| 假 | 表格 |\n```\n\n| 孤立 | 行 |\n\n"
    path.write_text(text.replace(anchor, injected + anchor, 1), encoding="utf-8")


def mutate_table_rows_after_list(root: Path) -> None:
    """表格行被追加到列表末尾，脱离任何表头（AUDIT.md 的真实事故形态）。

    2026-10-01 实测：AUDIT.md 里 M44–M47 追加的 61 行覆盖记录被直接接在
    一个列表项后面，既没有表头也没有 |---| 分隔行，整块渲染成原始管道文本。
    这里只注入 3 行，形态与判据一致即可。
    """

    path = root / "AUDIT.md"
    text = path.read_text(encoding="utf-8")
    anchor = "- ComfyUI 本地环境全流程、Agent（Codex/Claude）连接全流程：超出画布手册范围。\n"
    injected = (
        "| Major(注入) | 无表头的表格行 | 无分隔行 | 应当被拦下 |\n"
        "| Minor(注入) | 同样无表头 | 同样无分隔行 | 同样应当被拦下 |\n"
        "| Minor(注入) | 第三行 | 第三行 | 第三行 |\n"
    )
    path.write_text(text.replace(anchor, anchor + injected, 1), encoding="utf-8")


def mutate_unescaped_pipe_in_code_span(root: Path) -> None:
    """表格单元格里出现**未转义的竖线**——列数正确，但产物会丢内容（M84 加）。

    M84 给 `check-tables.py` 加了行内代码反引号平衡检查，理由是自己写崩了两处。
    这里注入的是**更狠的一类**：单元格里写 `` 收尾竖线 `|` ``，竖线没转义。
    GFM 是"先按竖线切单元格、再解析行内内容"，所以这个竖线**照样切**，
    该行从 3 格变成 4 格，而表格只有 3 列——**产物 HTML 里第 3 格的内容直接消失**
    （M84 已在 `90-troubleshooting.html` 产物上实测确认，不是推断）。

    关键点：这类错误的**列数校验查不出来**（行首行尾的竖线都还在），
    所以只能靠新的反引号奇偶判据拦。
    """

    path = root / "90-troubleshooting.md"
    text = path.read_text(encoding="utf-8")
    anchor = "## 相关页面\n"
    injected = (
        "| 列A | 列B | 列C |\n"
        "|---|---|---|\n"
        "| 正常 | 转义过 `\\|` | 收尾竖线写成 `\\|` |\n"
        "| 未转义 | 收尾竖线代码span `|` | 后面这段内容会被丢掉 |\n\n"
    )
    path.write_text(text.replace(anchor, injected + anchor, 1), encoding="utf-8")


def mutate_orphan_screenshot(root: Path) -> None:
    """孤儿截图：登记在 manifest 里，却没有任何页面引用它（M89 加）。

    M89 在临时副本上实测过：把图放进 `screenshots/`、manifest 补一条**字段齐全、
    sha256 正确**的记录、账本 `screenshot_count` 也对齐——**七道门禁全部通过**。
    也就是说这一类错误能完全静默地混进发布产物：账本写着"截图 N 张"，
    读者一张都看不到，而 manifest 里的 `verified_locator` 让它看起来像核对过。

    这里注入同一形态，并**同时把账本计数对齐**，确保拦下它的只能是新判据本身，
    而不是 `check-inventory-freshness` 顺手抓到的计数不符。
    """

    src = root / "screenshots/01-create-canvas-project-empty-home.png"
    dst = root / "screenshots/99-selftest-orphan.png"
    shutil.copyfile(src, dst)
    digest = hashlib.sha256(dst.read_bytes()).hexdigest()

    manifest = root / "screenshots/manifest.yml"
    text = manifest.read_text(encoding="utf-8")
    entry = (
        "\n  - file: screenshots/99-selftest-orphan.png\n"
        "    task_id: create-canvas-project\n"
        "    step: 自检用孤儿截图：没有任何页面引用它\n"
        "    route: '/canvas'\n"
        "    viewport: 1280x720\n"
        "    locale: zh-CN\n"
        "    captured_at: '2026-10-01'\n"
        "    verified_locator: '从一张画布开始'\n"
        "    visible_text: '从一张画布开始'\n"
        "    alt: 自检用孤儿截图\n"
        f"    sha256: {digest}\n"
    )
    manifest.write_text(text.rstrip("\n") + "\n" + entry, encoding="utf-8")

    inv = root / "task-inventory.yml"
    lines = inv.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("- id: create-canvas-project"):
            for j in range(i, min(i + 25, len(lines))):
                m = re.match(r"^(\s*)screenshot_count:\s*(\d+)", lines[j])
                if m:
                    lines[j] = f"{m.group(1)}screenshot_count: {int(m.group(2)) + 1}"
                    break
            break
    inv.write_text("\n".join(lines) + "\n", encoding="utf-8")


def mutate_broken_emphasis(root: Path) -> None:
    """`**` 紧邻标点导致加粗渲染失效，产物里留下字面量 `**`（M90 加）。

    M90 全站扫产物才发现 7 处这类写法，源文件看上去完全正常，其余门禁全部报 ok。
    注入的是真实命中的形态之一：`**` 后面紧跟全角引号 `「`，而 `**` 前面是实义字
    "的"——既不是空白也不是标点，2b 豁免条款不成立，开定界符无法 left-flanking。

    判据的精确性是这批的重点：**表格单元格里同样的写法必须放行**（单元格两侧有
    空格，2b 成立），否则就是 146 条假阳性。
    """

    path = root / "10-tasks/edit-nodes.md"
    text = path.read_text(encoding="utf-8")
    anchor = "工具条是**选中单个节点**后才出现的"
    injected = "自检注入：但它的**「读屏提示」**是「加入我的资产」。\n\n"
    path.write_text(text.replace(anchor, injected + anchor, 1), encoding="utf-8")


def mutate_same_page_anchor(root: Path) -> None:
    """**同页**锚点指向不存在的标题（M91 补的盲区）。

    M91 实测：`check-anchors.py` 此前对同页锚点（`[文字](#标题)`，不带文件路径）
    直接 `continue`，注释写"由 VitePress 保证"——**那个假设是假的**，标题里的
    `：` `，` `"` 会被 slugify 折成 `-`，手写链接少写连字符就点不动。
    全站仅 3 条同页锚点，**2 条是坏的**，而门禁当时报"44 个全部有效"。

    先前的 `mutate_broken_anchor` 只改**跨页**链接，覆盖不到这个分支。
    """

    path = root / "10-tasks/connect-references.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace("#连线时的常见限制", "#根本没有这个同页标题", 1), encoding="utf-8"
    )


def mutate_fenced_pseudo_anchor(root: Path) -> None:
    """锚点指向**代码块里的注释行**（M140 补的盲区）。

    M140 实测：`collect_ids` 此前逐行匹配标题、**不识别代码围栏**，把 bash 代码块里
    的 `# 注释` 当成真标题收进 id 集合。手册现存 4 处这样的"假标题"。按脚本自己的
    算法算出其 slug 写进链接后，`check-anchors.py` 报「全部有效」exit=0 **假通过**，
    而产物里那行是 `<span>` 着色代码、**没有这个 id**。

    与 M41（漏 NFKD）同族：都是**假通过**而非报错，所以更难发现。`mutate_broken_anchor`
    与 `mutate_same_page_anchor` 都指向真实标题，覆盖不到这个分支——需要一条
    「指向**不存在**的标题、但该 slug 恰好由代码块注释生成」的链接。
    """

    path = root / "README.md"
    fake = "启动一个静态服务器-浏览器打开-http-localhost-4173"
    path.write_text(
        path.read_text(encoding="utf-8")
        + f"\n自检注入：[对照](README.md#{fake})\n",
        encoding="utf-8",
    )


def mutate_vue_interpolation(root: Path) -> None:
    """正文里裸写 `{{count}}`，会被 Vue 当插值吞掉（M91）。

    源文件读起来完全正常，产物里那段**直接消失**：
    行内代码段里表现为空的 `<code></code>`，正文里表现为凭空少一句话。
    第二种**任何产物侧判据都测不出来**（不产生异常标签），所以只能源侧拦。
    """

    path = root / "10-tasks/connect-references.md"
    path.write_text(
        path.read_text(encoding="utf-8")
        + "\n自检注入：i18n 原文是「已导入 {{count}} 个画布」。\n",
        encoding="utf-8",
    )


def mutate_broken_render(root: Path) -> None:
    """产物里表格列数不一致（多出的格连同内容被丢弃，M84 那类）。

    自检不跑真实构建，所以现造一个最小产物目录，注入一个"表头 2 列、
    某行 3 格"的表格。这是 M84 真实事故的产物形态：源码里列数是对的，
    渲染器把多出来的格连同内容一起丢掉了。
    """

    dist = root / ".vitepress" / "dist"
    dist.mkdir(parents=True, exist_ok=True)
    (dist / "index.html").write_text(
        "<!DOCTYPE html><html><body><main>"
        "<table><thead><tr><th>甲</th><th>乙</th></tr></thead>"
        "<tbody><tr><td>1</td><td>2</td><td>多出来的一格，内容会被丢弃</td></tr></tbody>"
        "</table></main></body></html>",
        encoding="utf-8",
    )


def mutate_early_closed_code(root: Path) -> None:
    """行内代码段被提前截断（M92 补的缺口）。

    M92 查门禁覆盖度时发现：`check-tables.py` 的行内代码判据数的是**反引号总数的
    奇偶**，而嵌套反引号的总数是 4（偶数）——**判据形态上就抓不到**。实测注入后
    `check-tables.py` 报 ok，产物却是坏的：`` `title={a \\| \\`x\\`}` `` 被截成
    `<code>title={a \\| \\</code>x\`}`，后半截漏成正文。

    这条**只能从产物侧判**，判据是代码段内容以反斜杠结尾。
    """

    dist = root / ".vitepress" / "dist"
    dist.mkdir(parents=True, exist_ok=True)
    (dist / "index.html").write_text(
        "<!DOCTYPE html><html><body><main>"
        "<p>源码是 <code>title={a \\| \\</code>x`}` 这种嵌套反引号。</p>"
        "</main></body></html>",
        encoding="utf-8",
    )


def mutate_pipe_leak_render(root: Path) -> None:
    """本该渲染成表格的内容，在正文里留下了裸露的管道文本（M92 补的缺口）。"""

    dist = root / ".vitepress" / "dist"
    dist.mkdir(parents=True, exist_ok=True)
    (dist / "index.html").write_text(
        "<!DOCTYPE html><html><body><main>"
        "<p>| 甲 | 乙 | 这行本该是一张表格 |</p>"
        "</main></body></html>",
        encoding="utf-8",
    )


def mutate_dangling_anchor_render(root: Path) -> None:
    """产物里 `href="#x"` 指向本页不存在的 id（M92 补的缺口）。"""

    dist = root / ".vitepress" / "dist"
    dist.mkdir(parents=True, exist_ok=True)
    (dist / "index.html").write_text(
        '<!DOCTYPE html><html><body><main><h1 id="存在的标题">存在的标题</h1>'
        '<a href="#不存在的锚点">点我</a></main></body></html>',
        encoding="utf-8",
    )


# ---------- 用例表：(名称, 变异, 期望由谁拦下, 期望出现的错误文字) ----------

def mutate_inventory_yaml_broken(root: Path) -> None:
    """把账本改成**不是合法 YAML**（第十五道门禁的负向测试，M123）。

    这是**真实故障**的重放，不是假想：账本第 143 行第 340 列的 review_note 里
    嵌了 `{menu.type === "node" ? <复制> : null}`，第 163、263 行同理。
    YAML 的 plain scalar 一旦出现「半角冒号 + 空格」就被当成 key: value，
    整个文件随即不可解析。

    为什么这道负向测试不可省：M123 实测发现**此前的十四道门禁无一 import yaml**，
    全是按行正则读账本——正则读得动坏掉的 YAML，所以「门禁全绿」与「账本是合法
    YAML」一直是两件事。**没有这道用例，这道门禁自己也可能是形同虚设的。**
    """
    inv = root / "task-inventory.yml"
    text = inv.read_text(encoding="utf-8")
    # 注入一个带半角「冒号 + 空格」的 plain scalar 值——YAML 会把它当成 key: value
    marker = "    screenshot_count: 1"
    injected = "    injected_probe: a: b\n"
    text = text.replace(marker, injected + marker, 1)
    inv.write_text(text, encoding="utf-8")


def mutate_inventory_yaml_dup_id(root: Path) -> None:
    """让两个任务共用同一个 id（第十五道门禁的负向测试，M123）。

    重复 id 的危害是**静默**的：任何「按 id 查任务」的工具都会拿到第一条，
    后面的永远读不到，而文件本身看起来完全正常——没有一处会报错。
    """
    inv = root / "task-inventory.yml"
    text = inv.read_text(encoding="utf-8")
    ids = [ln for ln in text.split("\n") if ln.startswith("  - id: ")]
    if len(ids) < 2:
        return
    first = ids[0].split(": ", 1)[1].strip()
    text = text.replace(ids[1], f"  - id: {first}", 1)
    inv.write_text(text, encoding="utf-8")


def mutate_inventory_yaml_bad_type(root: Path) -> None:
    """把一条证据的 type 改成不存在的值（第十五道门禁的负向测试，M123）。

    这条用例还有个额外教训：门禁**第一版的已知集合是我按常见约定臆想的**
    （runtime/static/derived/source），而账本里实际用的是 runtime/static/**boundary**
    ——`derived` 与 `source` 根本不存在。门禁当场把自己顶红，逼我把集合改成
    从实际数据里数出来的。**判据集合必须数出来，不能照惯例编。**
    """
    inv = root / "task-inventory.yml"
    text = inv.read_text(encoding="utf-8")
    text = text.replace("      - type: boundary", "      - type: boundaryy", 1)
    inv.write_text(text, encoding="utf-8")


def mutate_inventory_evidence_drift(root: Path) -> None:
    """制造记账漂移：把 organize-canvas 的 runtime 证据删光，只留 static（第十七道门禁的负向测试，M133）。

    背景是 M133 查出的真实漏洞：那几个批次的运行时取证只写在 `review_note` 里，
    `evidence` 始终只有一条 `static`。本用例把这个状态重新造出来，
    断言门禁会以「记账漂移」为由拦下。

    ★ 注入用**行级删除**而不是字符串替换：第一次写这个用例时用了非贪婪正则
    `re.sub(r"...2026-10-02 M10\\d.*?\\n", "", ...)`，结果**只删掉一条**——
    organize-canvas 有两条 runtime（M101/M102 那条和 M103/M104 那条），
    非贪婪匹配在第一个换行就停手，另一条还在，门禁理所当然放行，
    **用例看起来跑了、结论却是假的**。所以这里按行删、并在删完时断言条数。
    """
    inv = root / "task-inventory.yml"
    lines = inv.read_text(encoding="utf-8").split("\n")
    out, i, removed = [], 0, 0
    start = out_len = None
    while i < len(lines):
        if lines[i].startswith("  - id: organize-canvas"):
            start = len(out)
            j = i + 1
            while j < len(lines) and not lines[j].startswith("  - id:"):
                j += 1
            drop = False
            for ln in lines[i:j]:
                if ln.strip() == "- type: runtime":
                    drop = True
                    removed += 1
                    continue
                if drop:
                    if ln.startswith("        note:"):
                        drop = False
                    continue
                out.append(ln)
            i = j
            continue
        out.append(lines[i])
        i += 1
    assert removed == 2, f"本该删掉 2 条 runtime，实际删了 {removed} 条——用例本身坏了"
    assert start is not None
    tail = out[start:start + 24]
    assert not any(x.strip() == "- type: runtime" for x in tail), "删完还有残留"
    inv.write_text("\n".join(out), encoding="utf-8")


def mutate_inventory_evidence_negation(root: Path) -> None:
    """把唯一的 runtime 证据换成 static，同时把 review_note 里的声称改成「未实测」——门禁**不得**拦下。

    这是本用例的另一半：**门禁不能只会说「是」。**
    「未实测」二字里也含「实测」，直接匹配会误报，把「明确写了没测」的任务
    判成记账漂移。修法是触发词前 3 字内出现「未」就不算触发——
    这个否定形态是从现有 15 个任务的真实数据里数出来的，不是照惯例编的。

    ★ 这条用例走的是自检框架新增的「期望通过」分支（EXPECT_PASS）：
    原来自检只有「期望拦下」一种，**把门禁整个关掉也能全绿**——
    与 M126 没有阳性对照是同一个漏洞。
    """
    inv = root / "task-inventory.yml"
    text = inv.read_text(encoding="utf-8")
    marker = "  - id: shortcuts-help"
    i = text.index(marker)
    j = text.index("  - id:", i + 10)
    block = text[i:j]
    nb = block.replace("      - type: runtime", "      - type: static")
    assert nb.count("      - type: static") >= 2, "runtime 没被换掉"
    text = text[:i] + nb + text[j:]
    # 再把 review_note 里的声称改成否定形态
    m = text.index("    review_note:", i)
    n = text.index("\n", m)
    note = text[m:n]
    # ★ 必须替换**全部**出现处，不是第一处。
    #   这个注入函数第一版写的是 `note.replace(w, "未" + w, 1)`（只换第一处），
    #   而 shortcuts-help 的 review_note 很长、后面还有好几处「实测」——
    #   于是门禁**理直气壮地报了**，差点被当成「门禁有 bug」而去改门禁。
    #   真实情况是**注入不彻底**。教训与前一个注入函数同源：
    #   **阴性测试自己设计错了，结论就会是假的**——先怀疑测试，再怀疑被测物。
    for w in ("实测", "运行时"):
        note = note.replace(w, "未" + w)
    text = text[:m] + note + text[n:]
    assert "实测" not in note.replace("未实测", "") or True
    inv.write_text(text, encoding="utf-8")


def mutate_encoding_mojibake(root: Path) -> None:
    """往正文里塞一个 U+FFFD 替换字符（第十六道门禁的负向测试，M131）。

    ★ **注入刻意用字节写法 `b"\\xef\\xbf\\xbd"`，不在源码里放 U+FFFD 字面量**——
    放字面量的话，**这个注入函数自己就带着乱码**，会被新门禁当场判为不合规。
    这正是 check-encoding.py 文件头里记的「判据自指」坑。

    ★ **另一个教训（M128 同族）**：注入完之后**必须验"撤回是否真的干净"**。
    M131 第一版注入的是「坏字 + 测 + U+FFFD + 试」，而撤回脚本找的是「坏字 + U+FFFD + 试」，
    **少算了一个「测」字，于是撤回失败、注入残留在工作区里**，差点被提交进去。
    """
    target = root / "10-tasks" / "edit-nodes.md"
    data = target.read_bytes()
    data += "\n\xe5\x9b\xbe\xef\xbf\xbd\n".encode("latin-1").decode("unicode_escape").encode("latin-1")
    target.write_bytes(data)



# 「期望门禁放过」的哨兵。★ 原来自检只有「期望拦下」一种用例，
# 于是**把门禁整个关掉也能自检全绿**——与 M126 没有阳性对照是同一个漏洞。
# 第十七道门禁的否定形态用例（写「未实测」不得被当成声称实测）本质上要求门禁放过，
# 原来的框架表达不了，所以补上这一类。
EXPECT_PASS = "__expect_pass__"

def mutate_probe_fuzzy_destructive(root: Path) -> None:
    """M193：探针用 `/删除/` 这种**子串**去选不可逆按钮——M192 正是栽在这一条上。

    当时的真实经过：清理测试画布时用子串匹配找删除按钮，**先命中了页面上的
    「删除全部」而不是卡片上的「删除」**，确认弹窗没读就点了「删除」，
    两张画布一起没了、不可恢复。而「删除」此前根本不在白名单里。

    注入的代码里**故意不含完整文案「删除全部」**——
    门禁的判据是「用了子串且没出现全名」，全名在场就该按精确匹配放行。
    """
    path = root / "scripts/probe-discoverability.js"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text + "\n// 注入的故障：用子串去选不可逆按钮\nif (/删除/.test(label)) { target.click(); }\n",
        encoding="utf-8",
    )


def mutate_probe_comment_fuzzy_destructive(root: Path) -> None:
    """**注释里**提到子串匹配，不该被判成「用子串去选不可逆按钮」（M194 反向对照）。

    M194 的真实经过：M193 新立的模糊匹配判据一上线，就把我新写的
    `probe-node-toolbars.js` 判成违规——**而那支探针根本没选任何删除按钮**，
    是**文件头的注释在描述这个坑**（写着「M192 用 `/删除/` 这类子串匹配」）。
    **注释里的话不是选择器。**

    根因与 M106 撞的是同一个坑：`audit_manual.py` 在 `build-site.sh` 里出现 3 次、
    **全部在注释里**，当年的解法就是剥掉注释再比对。**同一个坑，换个门禁又踩一次。**

    判据已改成先剥 `/* */` 块注释与「整行以 // 开头」的注释再扫。
    这一例守的是**不误报**：注释放进去，门禁必须放行。
    """

    path = root / "scripts/probe-discoverability.js"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text
        + "\n/* 历史教训：M192 曾用 /删除/ 这类子串去匹配按钮，\n"
          "   先命中了「删除全部」而不是卡片上的「删除」，两张画布一起没了。\n"
          "   这里只是**记录**这段教训，不是选择器。 */\n",
        encoding="utf-8",
    )


def mutate_probe_exact_destructive(root: Path) -> None:
    """反向：全名精确匹配**不该被误报**。

    这条纪律要的就是「写全名」，所以按全名匹配必须是放行的那一种。
    没有这个反向用例，这道新规则就可能变成「一律拦下子串」的粗暴门禁。
    """
    path = root / "scripts/probe-discoverability.js"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text
        + "\n// 注入的合规写法：全名精确匹配\n"
          "if (label === '删除全部') { target.click(); }\n",
        encoding="utf-8",
    )


DESTRUCTIVE_RE = re.compile(r"const\s+DESTRUCTIVE\s*=\s*new Set\(\[(.*?)\]\)", re.S)
STRING_RE = re.compile(r"'([^']+)'|\"([^\"]+)\"")


def destructive_from_probe(root: Path) -> list[str]:
    """从探针源码现算不可逆按钮白名单。

    ★ 这一段原来是**手写的四项字面量**（M194 记）。M193 把白名单扩到六项，
    锚点当场过期、`replace` 静默变成空操作，用例从此不再注入任何东西——
    而自检把它误报成「门禁漏网」。改成现算，锚点就再也追不上真实状态。
    """
    text = (root / "scripts/probe-toolbar-states.js").read_text(encoding="utf-8")
    match = DESTRUCTIVE_RE.search(text)
    if not match:
        raise AssertionError("读不出探针里的 DESTRUCTIVE 集合，用例无法构造注入")
    return [a or b for a, b in STRING_RE.findall(match.group(1))]


def case_count_from(root: Path) -> int:
    """数出自检自己的用例条数（用 `ast`，不靠数括号）。"""
    tree = ast.parse((root / "scripts/selftest-gates.py").read_text(encoding="utf-8"))
    for node in tree.body:
        targets = (node.targets if isinstance(node, ast.Assign)
                   else [node.target] if isinstance(node, ast.AnnAssign) else [])
        if any(getattr(t, "id", None) == "CASES" for t in targets):
            return len(node.value.elts)
    raise AssertionError("读不出 CASES，用例无法构造注入")


def mutate_publish_gate_count_drift(root: Path) -> None:
    """文档里「几道门禁」这个数字漂了，必须被拦下（M193）。

    M193 查出的真实漂移：**标题写「十二道」、正文写「十六道」、实际二十一**，
    而专门守这张表的 `check-publish-sync.py` 一直是绿的——
    因为它数的是「哪几个门禁」，数不到「几个字」。

    这类漂移比漏一个门禁更隐蔽：门禁表是**维护者排查的唯一索引**，
    照着「十六道门禁」去理解构建流程的人，拿到的是一份几批之前的快照。
    """

    path = root / "PUBLISH.md"
    text = path.read_text(encoding="utf-8")
    # ★ **锚点现算，不写死。** M199 把门禁数从二十一道加到二十二道之后，
    #   这个用例的 `replace("二十一道门禁", …)` 立刻变成空操作、自检报「注入无效」——
    #   **和 M193 撞的是同一个坑**：写死的锚点会随被测对象一起长大，然后静默失效。
    #   现在从标题里读出当前数字再改写，以后每加一道门禁都不用回来动这里。
    import re

    m = re.search(r"### 构建时的门禁：([零一二三四五六七八九十]+)道", text)
    assert m, "注入失败：PUBLISH.md 里找不到门禁数量标题"
    current = m.group(1)
    patched = text.replace(f"{current}道门禁", "十六道门禁", 1)
    assert patched != text, f"注入失败：正文里没找到「{current}道门禁」"
    path.write_text(patched, encoding="utf-8")


def mutate_publish_selftest_count_drift(root: Path) -> None:
    """文档里「注入几类故障」与自检实际用例数对不上，必须被拦下（M193）。

    这个数字此前写的是 38，而实际已经 68 以上——**差几十条用例没人发现**。
    文档里的自检规模也是排查依据（「自检只考 38 类」会让人以为覆盖面没那么宽）。

    ★ 注入的数字**从被测系统现算**，不写死：这条用例要能在「用例总数本身
    变了」之后继续成立。写死的话每加一条用例就得改三处，而**其中一处漏改
    会静默地把这条用例变成假通过**。
    """

    path = root / "PUBLISH.md"
    text = path.read_text(encoding="utf-8")
    n = case_count_from(root)
    patched = text.replace(f"注入 {n} 类故障", f"注入 {n - 8} 类故障", 1)
    assert patched != text, f"注入失败：没找到「注入 {n} 类故障」"
    path.write_text(patched, encoding="utf-8")


def mutate_batch_date_in_future(root: Path) -> None:
    """批次标题自述的日期晚于「今天」，必须被拦下（M227）。

    M226 实测过这个病：M193–M199 明明是 10-03 傍晚落库的，标题却写着 10-04，
    而且同样的错日期另有 9 处漏进了 6 个正文页 —— **没有任何一道门禁会看日期**。

    这道门禁的判据是**单向**的：只报「晚于今天」。所以本例注入的是一个
    **明显晚于任何一天**的日期（从标题里现算「今天 + 一年」），
    **不写死具体日子**——写死日期的锚点会随被测对象一起过期然后静默失效
    （M199 已把 `mutate_publish_gate_count_drift` 的锚点改成现算，正是同一个坑）。

    顺带注入一处**正文内联标注**（`2026-10-04 Mxxx` 那种语序），
    因为 M226 的 17 处里有 9 处就是这种写法，**只测标题会漏掉一大半**。
    """

    import datetime as _dt
    import re as _re

    path = root / "PROGRESS.md"
    text = path.read_text(encoding="utf-8")
    future = (_dt.date.today() + _dt.timedelta(days=365)).isoformat()
    # ★ 注入**最后一个**（最新那个）标题：那才是真实会犯的错——新批次刚写好就填了日期。
    m = None
    for cand in _re.finditer(r"^(#{2,4} M\d+（)(\d{4}-\d{2}-\d{2})", text, _re.M):
        m = cand
    assert m, "注入失败：PROGRESS.md 里找不到带日期的批次标题"
    batch = m.group(0).split("（")[0].replace("#", "").strip()
    text = text.replace(m.group(0), f"{m.group(1)}{future}", 1)

    # 正文内联标注：从「今天 + 一年」造一个不存在的日期，挂在 PROGRESS 末尾
    tail = f"\n> 自检注入：{future} {batch}\n"
    path.write_text(text.rstrip("\n") + tail + "\n", encoding="utf-8")


def mutate_publish_historical_gate_count(root: Path) -> None:
    """历史陈述里的门禁数不该被当成当前数量而误报（M193 的反向对照，两条路径）。

    **路径一：门禁表的「由来」列。** 那列里满是「七道门禁下全部通过」
    「此前的十六道门禁无一扫它」这类**描述当时**的话。数量判据若扫到这些，
    会把整张表的历史全判成错——判据一上线就全线误报。

    **路径二：引号里的举例。** 这条是**判据打回作者自己**之后才发现的：
    那段专门解释「历史陈述不该被判错」的文字本身要举例，引号里于是也出现了
    「七道门禁」，判据把作者的说明判成了错。**排除引号是有依据的**——
    真正声明当前数量的地方（标题、导语、构建步骤表）都不在引号里。

    所以这一例守的是**不误报**：两条路径各注入一个明显不对的当前数量，必须放行。
    """

    path = root / "PUBLISH.md"
    text = path.read_text(encoding="utf-8")
    in_table = "M89 实测孤儿图在七道门禁下全部通过"
    in_quotes = "满是「七道门禁下全部通过」"
    assert in_table in text and in_quotes in text, "注入失败：反例锚点已变"
    text = text.replace(in_table, in_table + "（当时仓库里只有九道门禁）", 1)
    text = text.replace(in_quotes, "满是「十二道门禁」", 1)
    path.write_text(text, encoding="utf-8")


def mutate_probe_contract_drift(root: Path) -> None:
    """探针源码的白名单在 PUBLISH 纪律表里被删成「见脚本源码」（M144）。

    M144 查出的真实漂移：M143 新写的纪律表只写「白名单四项」而**没列出是哪四项**，
    维护者在这张表里查不到清单，必须去翻 `.js`。读者查手册查不到清单，
    就等于没有这道闸——所以新立 `check-probe-contracts.py` 守住「文档不能漏项」。
    """

    path = root / "PUBLISH.md"
    text = path.read_text(encoding="utf-8")
    listed = "**" + " / ".join(destructive_from_probe(root)) + "**"
    if listed not in text:
        raise AssertionError(f"PUBLISH.md 里找不到按探针现算的白名单串：{listed}")
    path.write_text(
        text.replace(listed, "**（清单见脚本源码）**", 1),
        encoding="utf-8",
    )


def mutate_probe_marker_undocumented(root: Path) -> None:
    """探针用了**没登记进标记表**的 data-* 时，必须被拦下（M178）。

    M177 连续栽在「找错元素」上：按 class 找 data-* 承载的右键菜单，
    一个都找不到，连查三轮读出「产品不响应右键」。而三支已提交探针里
    **全都在用 data-* 标记定位**——这意味着这类标记会不断新增。

    若新标记可以静默进入探针，下一个维护者就会拿它去定位，
    然后在文档里查不到它是什么、什么时候引入的、是不是已经废弃。
    **读者查不到这张表，等于没有这道闸。**
    """

    path = root / "scripts/probe-toolbar-states.js"
    text = path.read_text(encoding="utf-8")
    patched = text.replace("'[data-node-id]'", "'[data-node-id]', '[data-selftest-ghost]'", 1)
    assert patched != text, "注入失败：没找到 data-node-id 那一处"
    path.write_text(patched, encoding="utf-8")


def mutate_probe_marker_ghost_in_table(root: Path) -> None:
    """标记表里列了**应用源码中并不存在**的 data-* 时，必须被拦下（M178）。

    反向那一向不能省：**表过期比表缺失更坏**——缺项只是查不到，
    过期则是照着它去找一个根本不存在的元素，浪费一轮排查，
    还会怀疑「是不是这个版本删掉了」。

    M178 实测这道反向检查真能拦下（在临时副本里往表里塞一个假标记，
    门禁 exit=1 并指名道姓报出来）。
    """

    path = root / "PUBLISH.md"
    text = path.read_text(encoding="utf-8")
    patched = text.replace("| 节点 | `data-node-id` |",
                           "| 节点 | `data-node-id` / `data-selftest-ghost` |", 1)
    assert patched != text, "注入失败：没找到标记表里 data-node-id 那一格"
    path.write_text(patched, encoding="utf-8")


def mutate_probe_contract_extra_context(root: Path) -> None:
    """文档比源码写得**更细**（多写背景）**不该被误报**（M144 的判据边界）。

    本门禁只守「文档不能漏项」，**不做双向全等**：文档的职责是「让人看懂」，
    源码的职责是「让机器跑」，两者本就该有详略。若误判「文档多写了就是不一致」，
    这道门禁会逼着维护者把文档删成源码的复述——反而更难读。

    阴性形态与 M133 的「未实测」是同一类：不加限制的判据必然误报。
    """

    path = root / "PUBLISH.md"
    text = path.read_text(encoding="utf-8")
    listed = "**" + " / ".join(destructive_from_probe(root)) + "**"
    if listed not in text:
        raise AssertionError(f"PUBLISH.md 里找不到按探针现算的白名单串：{listed}")
    path.write_text(
        text.replace(
            listed,
            listed + "（这六项都在画布工具条、顶栏或资产页上，前两项 M136 亲历过误删）",
            1,
        ),
        encoding="utf-8",
    )


def mutate_ownership_wrong(root: Path) -> None:
    """出口行挂到 `##` 章节标题下，而不是 `###` 条目下（M146）。

    M145 第一版的真实错位。**症状极隐蔽**：条目数不变、其余门禁全绿，
    但读者点那条出口到的是另一个问题。
    """

    path = root / "90-troubleshooting.md"
    lines = path.read_text(encoding="utf-8").splitlines()
    idx = next(i for i, l in enumerate(lines) if "→ **相关任务页**" in l)
    line = lines.pop(idx)
    while lines and lines[idx].strip() == "":
        lines.pop(idx)
    sec = next(i for i, l in enumerate(lines) if l.startswith("## "))
    lines[sec + 1 : sec + 1] = ["", line]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def mutate_ownership_ok(root: Path) -> None:
    """出口行挂在正确的条目下**不该被误报**（M146 的判据边界）。

    本门禁只判「归属哪个条目」，**不判「这条出口该不该有」**。
    若误判「同一章节下出现两次出口就是重复」，正常内容会被当成缺陷。
    """

    path = root / "90-troubleshooting.md"
    text = path.read_text(encoding="utf-8")
    # 在一个已有出口的条目里再加一行普通说明文字（位置仍属该条目）
    lines = text.splitlines()
    idx = next(i for i, l in enumerate(lines) if "→ **相关任务页**" in l)
    lines.insert(idx, "")
    lines.insert(idx + 1, "补充说明：这一段仍属于上一条条目，出口位置不应被判为错误。")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def mutate_gate_silence_reintroduced(root: Path) -> None:
    """把 `check-ledger-pin` 退回 M150 的行为（静默少收一份声明，M151）。

    这条用例验的不是「某个门禁坏了」，而是**第二十道门禁本身有没有效**：
    撤掉修复后，它必须重新抓到 `check-ledger-pin` 的静默放行。
    **没有这条，第二十道门禁就只是一段没人验证过的新代码。**
    """

    import re

    path = root / "scripts/check-ledger-pin.py"
    text = path.read_text(encoding="utf-8")
    patched = re.sub(r"    # M151 订正：.*?\n        return 1\n\n", "", text, flags=re.S)
    assert patched != text, "注入失败：没找到 M151 那段修复"
    path.write_text(patched, encoding="utf-8")


def mutate_gate_silence_ledger_evid_reintroduced(root: Path) -> None:
    """把 `check-inventory-evidence` 退回 M150 的行为（账本缺失时 exit=0）。

    M150 抓到的那一处。**两道一起验**，因为它们形态相同、位置不同：
    一个是「文件不存在就 continue」，一个是「账本不存在就 return 0」。
    """

    path = root / "scripts/check-inventory-evidence.py"
    text = path.read_text(encoding="utf-8")
    patched = text.replace(
        '        print(\n            f"证据一致性校验未执行：账本不存在（{inv}）。"\n'
        '            "这不是通过——请确认账本是否被误删或改名。"\n        )\n        return 1',
        '        print("[skip] 账本不存在，跳过证据一致性校验")\n        return 0',
        1,
    )
    assert patched != text, "注入失败：没找到 M150 修复后的那段"
    path.write_text(patched, encoding="utf-8")


def mutate_retracted_m132_dock(root: Path) -> None:
    """M132 订正的「Dock 认不出 9 个」复现（R25，M152 补登记）。

    M152 查出 `RETRACTIONS` 表只覆盖 **M39–M108**——
    **M109 到 M151 这四十三批的订正一条都没进表**，
    而这张表是「防止已订正说法复现」的唯一机制。**表外的订正等于没被守住。**
    """

    path = root / "README.md"
    path.write_text(
        path.read_text(encoding="utf-8") + "\n自检注入：Dock 认不出 9 个按钮。\n",
        encoding="utf-8",
    )


def mutate_retracted_allowlist_too_broad(root: Path) -> None:
    """`allow_in` 豁免写成**只给文件名**时，必须被门禁拒绝（M152）。

    M152 加 `allow_in` 是为了让订正说明块能引述原错误说法，
    但**豁免一旦放宽到整页，这条门禁就形同虚设**——
    这正是 M140 查出的「文档可以比源码写得细」的反面教训：
    **豁免要窄到无法滥用**。
    门禁若不校验豁免的形状，加机制的人就会顺手写宽。
    """

    import re

    path = root / "scripts/check-retractions.py"
    text = path.read_text(encoding="utf-8")
    # M154 给 R27 的 allow_in 加了第二处，这一行不再只有一处——
    # 注入要按**前缀**匹配，不能写死整行。
    # M173 起这一处也改成了内容锚点形态（行号形态已退役），
    # 所以匹配的是锚点前缀，不是 `:\d+`。
    patched = re.sub(
        r'"allow_in": \["10-tasks/edit-nodes\.md#[^"]*"[^\]]*\]',
        '"allow_in": ["10-tasks/edit-nodes.md"]', text, count=1)
    assert patched != text, "注入失败：没找到 allow_in 那一行"
    path.write_text(patched, encoding="utf-8")


def mutate_anchor_exemption_wrong_fragment(root: Path) -> None:
    """内容锚点豁免的**锚点对不上那一行**时，必须仍然报出（M160）。

    M160 给 `allow_in` 加了「内容锚点」形态（`文件#行内稳定片段`），
    解决 M152 那条「豁免必须精确到行号」判据的另一半缺陷：
    **行号精确但不稳定**——在文件上方插入几行，登记的 357 就漂到 360，
    豁免静默失效，门禁开始报一条根本没变的行（M160 亲历）。

    但新机制必须守住同一条底线：**锚点必须真的指向那一行**。
    把锚点改成一个该行里并不存在的片段，门禁必须照样抓得到复现，
    否则「锚点」就退化成了「随便写个字符串就能豁免整页」——
    那比 M152 修掉的「只写文件名」还宽。
    """

    import re

    path = root / "scripts/check-retractions.py"
    text = path.read_text(encoding="utf-8")
    patched = re.sub(
        r'"SOURCE_OBSERVATIONS\.md#三处按钮区的顺序固定"',
        '"SOURCE_OBSERVATIONS.md#这里放一个该行里根本不存在的锚点片段"',
        text, count=1)
    assert patched != text, "注入失败：没找到内容锚点豁免（载具已从 R31 迁到 R26，见下）"
    path.write_text(patched, encoding="utf-8")


def mutate_anchor_exemption_too_short(root: Path) -> None:
    """内容锚点**短于 8 字**时必须判非法（M160）。

    没有长度下限的话，锚点可以退化成两三个字，实质等于按内容模糊匹配整页。
    8 字是 M160 实测挑的：够长到能唯一指认一行，够短到还能手写出来。
    """

    import re

    path = root / "scripts/check-retractions.py"
    text = path.read_text(encoding="utf-8")
    patched = re.sub(
        r'"SOURCE_OBSERVATIONS\.md#三处按钮区的顺序固定"',
        '"SOURCE_OBSERVATIONS.md#像素值"', text, count=1)
    assert patched != text, "注入失败：没找到内容锚点豁免（载具已从 R31 迁到 R26，见下）"
    path.write_text(patched, encoding="utf-8")


def mutate_table_row_too_many_cells(root: Path) -> None:
    """表格行**格子数多于表头**时必须被拦下（M184）。

    多出来的格子会被渲染器**连同里面的内容一起丢弃**——
    源文件里每一行都还在，坏掉的只是产物，**其余门禁一律报 ok**。
    最常见的成因是**把两行拼成了一行**（相邻两行各以竖线结尾又以竖线开头）。
    写在**发布页**上才拦（读者看得见），内部账本另有基线口径。
    """

    import re

    path = root / "20-reference.md"
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    def cells(line: str) -> int:
        return len(re.split(r"(?<!\\)\|", line.strip().strip("|")))

    # 找到第一个表格块的**表头**列数，并记下表头所在行
    head_cols = None
    head_at = -1
    for idx, line in enumerate(lines):
        if line.strip().startswith("|") and not set(line.strip()) <= set("|-: "):
            head_cols, head_at = cells(line), idx
            break
    if head_cols is None:
        raise AssertionError("注入失败：20-reference.md 里没有表格")

    # ★ 必须挑一个**正文行**，不能碰表头——
    # 给表头加一格会让全表正文行都变成「少格」，而少格在 CommonMark 里合法，
    # 结果这道注入**反而造出了一个不报错的场景**（M184 第一版注入就栽在这儿）。
    for i, line in enumerate(lines):
        # ★ 表头本身（head_at）与其下一行的分隔行都要跳过——
        # 改表头会让整表正文行都变成「少格」，而少格合法，于是**这道注入自己造出了一个不报错的场景**
        if i <= head_at + 1:
            continue
        if not line.strip().startswith("|"):
            continue
        if set(line.strip()) <= set("|-: "):
            continue
        if cells(line) != head_cols:
            continue
        lines[i] = line.rstrip() + " 多出来的一格 |"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return
    raise AssertionError("注入失败：20-reference.md 里没找到列数与表头一致的正文行")


def mutate_table_internal_backlog_grows(root: Path) -> None:
    """**内部账本的表格欠账不许增长**（M184）。

    这四份内部页由 srcExclude 排除、读者看不到，且表里早有 M65 就在册的历史欠账，
    一次性清完不现实——所以给它们设了**基线**。
    但基线的意义是「不许再长」：**新增一处必须当场报错**，
    否则「已知不管」就会变成「谁都往里加」。

    ★★ **这一例栽过两次，两次都是同一个病：注入依赖了会变的字面量。**

    第一次（M185 之后）：基线从 48 清到 0，注入还在靠「把基线改成 1」越线，
    目标没了、assert 直接崩。改成**真的制造一处新增欠账**。

    第二次（M199）：第一版是「复制 AUDIT.md 最后一条合法表格行、在末尾再接一格」。
    当时那行有 **4 个格子**（表头也是 4），接一格变成 5 > 4，越线成功。
    **M199 给 AUDIT 追加的 8 行是 3 格的**（这批内部页的既有常态就是少格），
    于是「最后一行」变成 3 格、接一格是 4 格，**刚好等于表头、不算欠账**，用例当场漏网。
    **「最后一行」是个移动靶。** 现在改成**先回溯找到那张表的表头、按表头格子数 +1 现造一行**，
    无论末尾那行有几格都成立。
    """

    path = root / "AUDIT.md"
    text = path.read_text(encoding="utf-8")
    lines = text.rstrip("\n").split("\n")
    # 找最后一条合法表格行
    last = None
    for i, line in enumerate(lines):
        t = line.rstrip()
        if t.startswith("| ") and t.endswith(" |"):
            last = i
    assert last is not None, "注入失败：AUDIT.md 里没有合法表格行"
    # ★ 回溯到它所属那张表的表头，按**表头**的格子数 +1 现造一行——
    #   末尾那行有几格与「制造一处超出的欠账」无关，依赖它就是依赖移动靶。
    sep = None
    for j in range(last, -1, -1):
        if lines[j].lstrip().startswith("|---"):
            sep = j
            break
    assert sep is not None and sep > 0, "注入失败：没找到这张表的分隔行与表头"
    header_cells = lines[sep - 1].count("|") - 1
    assert header_cells >= 1, "注入失败：表头格子数算不出来"
    injected = "| " + " | ".join(["注入"] * (header_cells + 1)) + " |"
    lines.insert(last + 1, injected)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def mutate_retraction_missing_kind(root: Path) -> None:
    """新订正**不写 kind** 时必须被拦下（M183）。

    M182 出现过「改了事实、计数却没动」：那次订正改的是描述不是结论，
    按老口径不算「订正」，于是「已订正 N 条」这个数字**没有反映出手册被改过**——
    审计的人看不出这一批动过什么。
    所以每条订正都必须声明它改的是 `conclusion` 还是 `wording`。
    **不写等于没分类，门禁不许它悄悄过。**
    """

    import re

    path = root / "scripts/check-retractions.py"
    text = path.read_text(encoding="utf-8")
    patched = re.sub(r'("id": "R37",\n)\s*"kind": "conclusion",\n', r"\1", text, count=1)
    assert patched != text, "注入失败：没找到 R37 的 kind 字段"
    path.write_text(patched, encoding="utf-8")


def mutate_retraction_bad_kind(root: Path) -> None:
    """`kind` 取值写错时必须被拦下（M183）。

    取值拼错等于没分类，而分类失效时门禁只会「安静地少拦一类」——
    这是最容易被放过的一种坏状态，必须当场报错而不是当没看见。
    """

    path = root / "scripts/check-retractions.py"
    text = path.read_text(encoding="utf-8")
    patched = text.replace('"kind": "conclusion",', '"kind": "conclustion",', 1)
    assert patched != text, "注入失败：没找到 kind 字段"
    path.write_text(patched, encoding="utf-8")


def mutate_anchor_exemption_back_to_lineno(root: Path) -> None:
    """把豁免写回**已退役的行号形态**时，必须被明确拦下（M173）。

    M172 把 6 个行号豁免迁成了内容锚点，并做了严格 A/B 对照：
    同一份插了 2 行的内容，行号形态 exit=1（5 条假阳性），锚点形态 exit=0。
    M173 迁完最后 2 处后行号形态**一个使用者都不剩**，于是正式退役。

    这一例守的是**退役本身**：如果有人（或未来的我）顺手写回行号，
    门禁必须点名说「这是已退役的写法」，而不是继续默默接受——
    默默接受等于退役从来没发生过，下一批就会有人再写一个行号豁免。
    """

    import re

    path = root / "scripts/check-retractions.py"
    text = path.read_text(encoding="utf-8")
    patched = re.sub(
        r'"SOURCE_OBSERVATIONS\.md#三处按钮区的顺序固定"',
        '"SOURCE_OBSERVATIONS.md:357"', text, count=1)
    assert patched != text, "注入失败：没找到内容锚点豁免（载具已从 R31 迁到 R26，见下）"
    path.write_text(patched, encoding="utf-8")


def mutate_coverage_drop_body_page(root: Path) -> None:
    """从某道声明式门禁的 `BODY_PAGES` 里删掉一页，该页必须被判为漏网（M162）。

    这是 M162 那个**真实穿透**的最小复现：根目录新增页面、或有人从清单里删掉一页，
    **21 道门禁会全绿**。本门禁存在的全部理由就是把这种静默变成 exit=1。
    """

    # ★ 三道门禁**都要**删：本门禁的判据是**并集**——一页被任意一道内容门禁扫到就算覆盖。
    #   M162 第一版只删了 check-claims 一道，README.md 仍被另外两道扫着，用例红了。
    #   **这是用例写错了，不是门禁坏了**（M151 的老教训：先问是工具坏了还是用例写错了）。
    import re

    for name in ("check-claims.py", "check-retractions.py", "check-source-refs.py"):
        path = root / "scripts" / name
        text = path.read_text(encoding="utf-8")
        # 三个门禁的 BODY_PAGES 排版不同：有的多行、有的单行——**按格式写死会漏**。
        patched = re.sub(r'"README\.md",\s*', "", text, count=1)
        assert patched != text, f"注入失败：{name} 的 BODY_PAGES 里没找到 README.md"
        path.write_text(patched, encoding="utf-8")


def mutate_coverage_reason_too_short(root: Path) -> None:
    """`KNOWN_EXCLUDED` 里的排除理由过短时必须判非法（M162）。

    没有理由的排除等于漏网——所以「排除」这件事本身也必须被守。
    少了这一条，加排除的人就会写一个 `AUDIT.md` 光秃秃地躺在表里。
    """

    import re

    path = root / "scripts/check-page-coverage.py"
    text = path.read_text(encoding="utf-8")
    patched = re.sub(
        r'"AUDIT\.md": "[^"]{12,}"', '"AUDIT.md": "不用扫"', text, count=1)
    assert patched != text, "注入失败：没找到 KNOWN_EXCLUDED 里 AUDIT.md 那条理由"
    path.write_text(patched, encoding="utf-8")


def mutate_coverage_stale_exclusion(root: Path) -> None:
    """`KNOWN_EXCLUDED` 里登记了已不存在的文件时必须报过期（M162）。

    排除表会随手册演进而失真：文件被删了、登记还留着，
    于是**那一行看起来像一个正当的排除，其实什么也没排除**。
    """

    import re

    path = root / "scripts/check-page-coverage.py"
    text = path.read_text(encoding="utf-8")
    patched = re.sub(
        r'KNOWN_EXCLUDED: dict\[str, str\] = \{',
        'KNOWN_EXCLUDED: dict[str, str] = {\n    "99-ghost.md": "这一页早就不存在了，登记留着",',
        text, count=1)
    assert patched != text, "注入失败：没找到 KNOWN_EXCLUDED 的定义行"
    path.write_text(patched, encoding="utf-8")


def mutate_retracted_ledger_repro(root: Path) -> None:
    """已订正的说法复现到**账本**里（正文之外，M153 补的覆盖范围）。

    M153 实测盲区：把「Dock 认不出 9 个」写进 `task-inventory.yml`，
    `check-retractions.py` 报 ok——**它只扫 5 个固定页 + `10-tasks/*.md`，
    账本根本不在扫描范围里**。M152 补登记 R25 时也只扫了正文三页，
    **「补登记」这件事自己就有覆盖不全**。

    ★ **注入位置必须避开 `allow_in` 登记的行**（M153 第一版阳性对照就踩了这个：
    注入恰好落在 R25 豁免的那一行，于是被如实放行、exit=0——
    **那是判据行为正确，是对照设计错了**）。
    """

    path = root / "task-inventory.yml"
    lines = path.read_text(encoding="utf-8").splitlines()
    exempt = {47, 126, 237, 257}
    for i, line in enumerate(lines, 1):
        if i in exempt:
            continue
        if "review_note:" in line or "note:" in line:
            lines[i - 1] = line + " 另外 Dock 认不出 9 个按钮。"
            break
    else:
        raise AssertionError("没找到可注入的行")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def mutate_retracted_manifest_repro(root: Path) -> None:
    """已订正的说法复现到**截图清单**里（M203 补的覆盖范围）。

    `screenshots/manifest.yml` 有 112 条目，每条都带 `verified_locator`（当时量到了什么）、
    `alt`、`visible_text`。它是**唯一一份逐条记取证读数的清单**，而从前不在订正门禁的
    扫描面里——**正文改了、清单里那条过期读数不会自己知道**。

    ★ **注入位置从被测对象现算**（本轮已栽过四次锚点事故）：不复用任何写死的行号，
      直接找 R26 needle「三处按钮区」**当前**不存在的那个字段值并改回去。
    """

    path = root / "screenshots/manifest.yml"
    text = path.read_text(encoding="utf-8")
    needle = "四处按钮区的位置距离"
    assert needle in text, "注入失败：清单里已找不到该字段值（上一批已经订正过？）"
    path.write_text(text.replace(needle, "三处按钮区的位置距离", 1), encoding="utf-8")


def mutate_ledger_phrase_rewritten(root: Path) -> None:
    """台账里的重述位置短语被改写（= 有人改了正文却没同步台账）时必须拦下。

    这是 M199 立这道闸的全部理由：同一句断言散在 52 处，改一处漏一处时
    **没有任何东西会报错**——图还是对的，链接还是通的，只有那句话悄悄变成了错的。
    """

    path = root / "SOURCE_OBSERVATIONS.md"
    text = path.read_text(encoding="utf-8")
    patched = text.replace("`10-tasks/edit-nodes.md`「13 个按钮立刻齐了」",
                           "`10-tasks/edit-nodes.md`「13 个按钮立刻就齐了」", 1)
    assert patched != text, "注入失败：没找到 F01 的重述位置短语"
    path.write_text(patched, encoding="utf-8")


def mutate_ledger_number_drift(root: Path) -> None:
    """正文上的数字被改了、台账里的实测值没跟着改时必须拦下。

    ★★ **这一例写了两遍才对，记下来免得下一个人再栽一遍。**

    第一版只改 `20-reference.md` 长度速查表里组节点那一行的 `**2**` → `**3**`，
    门禁放行。查下来是：**F05 的第二处重述位置在 `edit-nodes.md` 的对照句上，
    那一行本来就有「长度从 2 到 13」「（2 / 4 / 5 / 6 / 8 / 13」这些顺带出现的 2**，
    于是「至少一处所在行含实测值 2」照样成立。**只改一行，会被另一行救回来。**

    第二版把 F05 两处重述位置所在行里的 2 全部换掉。顺带确认过这不会误伤：
    F02（值 2/4/5/6/8/13）在同一行仍读到 6 与 4/5/8/13，判据照常成立。

    **结论**：这条判据的实际作用面比预想的窄——**只有当某条事实的每一处重述
    所在行都不含它的值时，它才真正起作用**。这不是缺陷，是「逐字短语」判据
    的固有性质，写在这里以免有人以为它能覆盖所有数字漂移。
    """

    ref = root / "20-reference.md"
    text = ref.read_text(encoding="utf-8")
    patched = text.replace("| 组 | **2** | 只剩", "| 组 | **3** | 只剩", 1)
    assert patched != text, "注入失败：没找到长度速查表里组节点那一行"
    ref.write_text(patched, encoding="utf-8")

    # ★ M208 第三次修这一处：这一段原来按**整句字面量**替换，而 M208 把那句
    #   改成了「默认配置下共 6 种」，字面量当场失效、注入静默变成空操作，
    #   自检报「注入无效」——**门禁没坏，是用例坏了**（M193、M203 已各犯过一次）。
    #   现改成**在被测对象上现算**：先找出含那串档位的行，再改行内的 2。
    #   措辞再怎么变都不会哑，**只有档位本身变了才会**——而那本来就该让用例响。
    edit = root / "10-tasks/edit-nodes.md"
    lines = edit.read_text(encoding="utf-8").splitlines()
    #   ★ 还要再挑一层：那一串档位在**同一页出现两处**（F02 的「按上表逐个数是 6 种」
    #   与 F05 的「长度从 2 到 13…」），**取第一处会改到 F02 那一行**，
    #   而 F02 的值里本来就有 2/4/5/8/13，判据照常成立 → 门禁不响、注入白做。
    #   所以在匹配行里**挑含「长度从 2 」的那一行**（F05 的重述位置）。
    for i, line in enumerate(lines):
        if "2 / 4 / 5 / 6 / 8 / 13" in line and "长度从 2 " in line:
            # ★ 必须把**行内所有的 2** 都换掉，不能只换「长度从 2」。
            #   这正是该判据已记录的窄面（见本函数 docstring）：只要**任何一处**
            #   重述所在行还留着值，判据就当没漂。M208 往这行补的说明里
            #   有一句「默认勾 **12** 项」，那个 2 就足以让整条注入白做。
            #   F05 的两处重述短语（「只剩「信息 · 删除」，最简的一种」
            #   与「选中组节点则只剩最左边的两个」）都不含数字，逐字匹配不受影响。
            lines[i] = line.replace("2", "3")
            break
    else:
        raise AssertionError("注入失败：找不到同时含档位串与「长度从 2 」的那一行（F05 的重述位置）")
    patched = "\n".join(lines)
    assert "长度从 3 " in patched and "2" not in lines[i], "注入失败：行内还留着 2"
    edit.write_text(patched, encoding="utf-8")


def mutate_ledger_count_drift(root: Path) -> None:
    """表体上方声明的条数与表体行数不一致时必须拦下（M106 门禁表的教训同族）。"""

    import re

    path = root / "SOURCE_OBSERVATIONS.md"
    text = path.read_text(encoding="utf-8")
    patched = re.sub(r"本表共 \*\*\d+ 条事实", "本表共 **20 条事实", text, count=1)
    assert patched != text, "注入失败：没找到条数声明"
    path.write_text(patched, encoding="utf-8")


def mutate_ledger_duplicate_id(root: Path) -> None:
    """台账里出现重复的事实 ID 时必须拦下——重复 ID 意味着两处声称同一件事。"""

    path = root / "SOURCE_OBSERVATIONS.md"
    text = path.read_text(encoding="utf-8")
    patched = text.replace("\n| F02 |", "\n| F01 |", 1)
    assert patched != text, "注入失败：没找到 F02 那一行"
    path.write_text(patched, encoding="utf-8")


def mutate_ledger_evidence_placeholder(root: Path) -> None:
    """依据被写成占位词时必须拦下。

    M196 立的规矩：**只给数字不给方法的断言，读者只能选择相信或不相信。**
    「依据」这一列就是方法的落点，把它清空等于把那条断言退回不可复核的状态。

    ★ **整格替换，不是替换其中一段。** 第一版只把依据末尾的探针名换成「待补」，
      那一格仍然是「运行时实测 M136 / M137 / M194；待补」——**有据可查的批次还在**，
      门禁放行是对的。**判据没坏，是注入没注入到位**（M193 的老教训换了个马甲）。
    """

    path = root / "SOURCE_OBSERVATIONS.md"
    text = path.read_text(encoding="utf-8")
    # ★ **M250 改：按行定位 + 整格替换，不再靠一句固定原文当锚点。**
    #   上一版替换的是「运行时实测 M136 / M137 / M194；`scripts/probe-node-toolbars.js` 逐项读可见文字」
    #   这一句——**而 M250 给 F01 的依据追加了源码第三条读数，那句后面又跟了一大段**，
    #   于是「替换那一段」只换掉了前半截，依据格变成「待补 + 一整段方法」，
    #   **门禁放行是对的，坏的是注入**（M193 的老教训第三次换马甲）。
    #   修法与本函数文档里写的一样：**整格替换**，且**按行定位**，
    #   这样以后往依据里追加任何内容都不会再让这个用例悄悄失效。
    lines = text.split("\n")
    hit = 0
    for i, line in enumerate(lines):
        if not line.startswith("| F01 |"):
            continue
        cells = line.split("|")
        if len(cells) < 5:
            continue
        cells[3] = " 待补 "
        lines[i] = "|".join(cells)
        hit += 1
        break
    assert hit, "注入失败：没找到 F01 那一行"
    path.write_text("\n".join(lines), encoding="utf-8")


def mutate_absolute_qualifier_deleted(root: Path) -> None:
    """绝对断言的限定词被删掉时必须拦下（M254）。

    R103 / R104 是同一种病：把带条件的结论写成了不带条件的。
    本用例删掉**正文里那句限定词**，而登记表还指着它——
    **这正是「订正块被误删」在现实里的样子**。
    """

    path = root / "10-tasks" / "shortcuts-help.md"
    text = path.read_text(encoding="utf-8")
    patched = text.replace("全部落在遮罩上", "全都不见了", 1)
    assert patched != text, "注入失败：没找到那段限定词"
    path.write_text(patched, encoding="utf-8")


def mutate_absolute_row_ok(root: Path) -> None:
    """限定词还在时不该误报（M254 的不误报对照）。

    ★ **正向那一侧必须有对照**：只测「删掉会被抓到」，那道闸可能只是**永远报错**。

    ★ **M296 改过一次注入方式**：★ **第一版把锚点短语 `一律不变（仍可见）` 改成
    ★ `一律不变（依旧可见）`，★ **而那正好把 A27 的锚点片段也一起改坏了——
    ★ **于是 M296 新加的「锚点片段也要校验」把这条不误报用例拦下了，**
    ★ **自检 99 个里死了 1 个（错在我，不在判据）。**
    ★ **★ 现在改成在锚点短语**前面**加字：★ **锚点片段作为子串仍然完整，
    ★ **限定词也仍然在，★ **而门禁确实读到了一个被改写的正文句子。**
    ★ **★ 这样它同时守住新判据的不误报侧**：★ **锚点片段还在就该放过。**
    """

    path = root / "10-tasks" / "shortcuts-help.md"
    text = path.read_text(encoding="utf-8")
    patched = text.replace("一律不变（仍可见）", "前后一律不变（仍可见）", 1)
    assert patched != text, "注入失败：锚点短语没找到"
    assert "一律不变（仍可见）" in patched, "注入失败：★ **锚点片段被弄丢了，★ **这条用例就名存实亡了"
    path.write_text(patched, encoding="utf-8")


def mutate_absolute_anchor_rotten(root: Path) -> None:
    """登记表里的锚点片段指着一句已经不存在的话时必须拦下（M296）。

    ★ **M296 撞上的就是这个洞**：★ **那一格明明写着「文件#行内片段」，
    ★ **而脚本只拿 `#` 前半段去找文件、后半段 `strip_markup` 之后就直接丢弃——
    ★ **所以改了正文之后锚点会静默腐化，★ **而门禁一路报 ok。**

    ★ **本用例改的是登记表那一格**（而不是正文），★ **模拟的正是现实里的形态：
    ★ **正文被改了、台账没跟着改，于是「#」后面那截指着一句不存在的话。**
    """

    path = root / "SOURCE_OBSERVATIONS.md"
    text = path.read_text(encoding="utf-8")
    good = "`10-tasks/shortcuts-help.md#一律不变（仍可见）`"
    bad = "`10-tasks/shortcuts-help.md#这句锚点被故意改坏了`"
    patched = text.replace(good, bad, 1)
    assert patched != text, "注入失败：没找到 A27 的锚点"
    path.write_text(patched, encoding="utf-8")


def mutate_multiple_ratio_wrong(root: Path) -> None:
    """正文里显式算式的结论被改错时必须拦下（M297）。

    ★ **M296 订正的那处算术错的形态**：★ **左边两个乘数一个没动，
    ★ **只有除完之后的结论被写错了**——★ **而按「值」建的判据全都看不见这件事**
    （★ **它们问的是「这个数对不对」，★ **而这里错的是「算出来对不对」**）。
    """

    path = root / "30-concepts.md"
    text = path.read_text(encoding="utf-8")
    patched = text.replace("8 ÷ 2 = 4", "8 ÷ 2 = 8", 1)
    assert patched != text, "注入失败：没找到那条显式算式"
    path.write_text(patched, encoding="utf-8")


def mutate_multiple_unlisted_ok(root: Path) -> None:
    """不在台账里的「N 倍」不该被误报（不误报对照，M297）。

    ★ **正向那一侧必须有对照**：★ **只测「算错会抓到」，★ **那道闸可能只是永远报错。**
    ★ **而这一条钉住的是判据二的边界**：★ **它守的是「那 7 条不许悄悄改」，
    ★ **不是「所有倍数句都要进表」**——★ **正文里本就有一处「把那一行裁出来放大 4 倍」，
    ★ **那是操作建议、不是测量断言，★ **而它一直没被报过。**
    """

    path = root / "10-tasks" / "manage-assets.md"
    text = path.read_text(encoding="utf-8")
    probe = "\n- 探针注入句：把这块区域放大 6 倍就能看清差别。\n"
    assert "放大 4 倍" in text, "注入失败：★ **那处既有的不误报对照已经不在了**"
    path.write_text(text + probe, encoding="utf-8")


def mutate_ledger_points_to_progress(root: Path) -> None:
    """重述位置指向内部账本而不是对外发布页时必须拦下。

    本表索引的是**读者能查到的出处**。指到 `PROGRESS.md` 等于把
    「我在内部账本里写过」当成「读者查得到」——那解决不了它要解决的问题。
    """

    path = root / "SOURCE_OBSERVATIONS.md"
    text = path.read_text(encoding="utf-8")
    patched = text.replace("`10-tasks/use-agent.md`「从左到右共 7 个」",
                           "`PROGRESS.md`「从左到右共 7 个」", 1)
    assert patched != text, "注入失败：没找到 F15 的重述位置"
    path.write_text(patched, encoding="utf-8")


def mutate_ledger_pipe_in_phrase(root: Path) -> None:
    """重述位置短语里带了字面竖线时必须被指名报错，而不是安静地少一行。

    表格单元格不能出现 `|`，这是全手册的硬约束；抄进台账的短语若带了竖线，
    那一行会被拆成两列，**少算一条事实却一声不吭**。
    """

    path = root / "SOURCE_OBSERVATIONS.md"
    text = path.read_text(encoding="utf-8")
    patched = text.replace("`10-tasks/use-agent.md`「从左到右共 7 个」",
                           "`10-tasks/use-agent.md`「从左到右共 7 个 | 面板顶端」", 1)
    assert patched != text, "注入失败：没找到 F15 的重述位置"
    path.write_text(patched, encoding="utf-8")


def mutate_ledger_rich_phrase_ok(root: Path) -> None:
    """反向对照：短语里带加粗、箭头、反引号、全角括号，**不该**被误报（不误报）。

    判据用的是**逐字子串**，不是分词也不是正则 token。
    这条用例守的是「别把它改窄」：手册正文大量使用 `**加粗**`、`→`、反引号，
    一旦有人把匹配收紧成「纯文字」，**正确的台账会全线变红**——
    那是把真信号淹掉，比漏网更坏（M195）。

    ★ 两处替换都取**原文中确实存在的连续片段**，不是自己拼的。
      第一版把 F09 的短语接到了「→ Cmd+A」后面，而原文的 `**` 是在「也是 9 个」
      之后才闭合的——拼出来的短语根本不存在，门禁当然报错。**注入必须先确认锚点。**
    """

    path = root / "SOURCE_OBSERVATIONS.md"
    text = path.read_text(encoding="utf-8")
    a_old = "`10-tasks/create-canvas-project.md`「未选中 8 个 → 单选 9 个 → Shift 真多选仍是 9 个」"
    a_new = ("`10-tasks/create-canvas-project.md`「**未选中 8 个 → 单选 9 个 → "
             "Shift 真多选仍是 9 个 → Cmd+A 全选 3 个也是 9 个**」")
    b_old = "`10-tasks/shortcuts-help.md`「缩放条那 4 个按钮的 `visibility` / `opacity` 一律不变」"
    b_new = ("`10-tasks/shortcuts-help.md`「缩放条那 4 个按钮的 `visibility` / `opacity` "
             "一律不变（仍可见），但逐个用 `elementFromPoint` 打点」")
    patched = text.replace(a_old, a_new, 1).replace(b_old, b_new, 1)
    assert patched != text and a_new in patched and b_new in patched, "注入失败：没找到 F08 / F09 的重述位置"
    path.write_text(patched, encoding="utf-8")


def mutate_duplicate_line_in_prose(root: Path) -> None:
    """正文里连续两行一模一样时必须被拦下（M201 实测事故）。

    起因不是假想故障：`edit-nodes.md` 里 M137 那段引用块的**同一行真的连续出现了两遍**，
    而**二十一道门禁全绿**。它躲过了全部既有判据——表格对、链接对、锚点对、
    强断言有证据、不是已订正说法的复活、也不在可数断言台账里。
    """

    path = root / "20-reference.md"
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    for i, line in enumerate(lines):
        t = line.strip()
        # 拿一行**有实质内容**的散文行来重复，避免重复的是空行或分隔线
        if t.startswith("TDCanvas 是一个") :
            lines.insert(i + 1, line)
            break
    else:
        raise AssertionError("注入失败：没找到用来重复的散文行")
    path.write_text("\n".join(lines), encoding="utf-8")


def mutate_duplicate_line_in_code_fence_ok(root: Path) -> None:
    """反向对照：围栏代码块里连续两行相同**不该**被误报（不误报）。

    示例输出连打两行 `OK` 是完全正常的写法（控制台日志、网络重试日志都长这样）。
    判据若不排除围栏内部，就是一个「总有一天会误报」的假门禁——
    **那种闸会把真正的错一起淹掉**（M195）。这一例守的就是别把它改严。

    ★ **锚点现算，且要插在围栏「内部」**：① 第一版把文件写死成 `90-troubleshooting.md`，
      而那个文件**压根没有围栏代码块**，注入空转、自检报「注入无效」——
      **写死文件名的锚点会随被测对象变化而静默失效**（这一批第三次撞上同一个病）。
      ② 第二版用 `replace("```\\n", …)` 插「OK\\nOK」，**插到了收尾那道围栏的后面**——
      也就是插进了散文里，门禁立刻报重复行。**````` 后面紧跟换行的是「收尾」那道，不是「开头」那道。**
      现在先按行判定哪一道是开围栏，再插到它**后面一行**。
    """

    target = None
    for p in sorted((root).rglob("*.md")):
        if "node_modules" in str(p) or ".vitepress" in str(p):
            continue
        if any(l.strip().startswith("```") for l in p.read_text(encoding="utf-8").split("\n")):
            target = p
            break
    assert target is not None, "注入失败：手册里一个围栏代码块都没有"
    lines = target.read_text(encoding="utf-8").split("\n")
    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            lines[i + 1 : i + 1] = ["OK", "OK"]      # 插进围栏内部
            break
    else:
        raise AssertionError("注入失败：没找到围栏开头")
    target.write_text("\n".join(lines), encoding="utf-8")


def mutate_duplicate_blank_lines_ok(root: Path) -> None:
    """反向对照：连续两个空行**不该**被算成重复行（不误报）。

    Markdown 用空行分段，连续空行是正常的排版；判据只看**非空**行。
    """

    path = root / "30-concepts.md"
    text = path.read_text(encoding="utf-8")
    patched = text.replace("\n\n## ", "\n\n\n## ", 1)
    assert patched != text, "注入失败：没找到可插入空行的小节标题"
    path.write_text(patched, encoding="utf-8")


def mutate_internal_list_hardcoded(root: Path) -> None:
    """有人又手抄了一份「内部资料」名单，且与 `srcExclude` 不一致（M240）。

    ★ **这正是 M240 抓到的真实病**：三道门禁各抄一份，其中 `check-emphasis.py`
    那份把**正在发布的 `README.md`（站点首页）**当成了内部资料。
    注入到 `check-fact-ledger.py` 是为了证明**判据不看脚本名**——
    只要名字形如 `INTERNAL` / `INTERNAL_PAGES` 且是模块级字面量，就会被抓。
    """

    path = root / "scripts" / "check-fact-ledger.py"
    path.write_text(
        path.read_text(encoding="utf-8")
        + '\nINTERNAL = {"AUDIT.md", "PROGRESS.md"}\n',
        encoding="utf-8",
    )


def mutate_internal_list_derivation_removed(root: Path) -> None:
    """把 `check-emphasis.py` 的推导悄悄改回「不推导」（M240 判据 2）。

    ★ **与上一例是两种不同的病**：那里的名单**是错的**，
    而这里名单**可能恰好是对的**——**只有「必须真的 import 共享模块」才抓得到**。
    """

    path = root / "scripts" / "check-emphasis.py"
    text = path.read_text(encoding="utf-8")
    patched = text.replace(
        "from _site_exclude import is_excluded, read_src_exclude  # noqa: E402",
        "# 假装还在推导（M240 自检注入）",
    )
    assert patched != text, "注入失败：没找到 _site_exclude 的 import 行"
    path.write_text(patched, encoding="utf-8")


def mutate_src_exclude_removed(root: Path) -> None:
    """事实源 `srcExclude` 被改坏时，**推导它的门禁必须判失败而不是默默换覆盖面**（M240）。

    ★ **这一例守的是 F42**：「没查」与「查了没问题」在输出里必须长得不一样。
    **默默退回硬编码名单或默默当成空集，都属于「门禁自己骗自己」。**
    """

    path = root / ".vitepress" / "config.mjs"
    text = path.read_text(encoding="utf-8")
    patched = text.replace("srcExclude:", "srcExcludeX:")
    assert patched != text, "注入失败：config.mjs 里没找到 srcExclude"
    path.write_text(patched, encoding="utf-8")


def mutate_page_list_runtime_mutation(root: Path) -> None:
    """页面清单在**运行时**被改，覆盖面当场缩小而覆盖门禁看不见（M241）。

    ★ **阳性对照是两道门禁同时失明**：加一行 `BODY_PAGES.remove("20-reference.md")` 之后，
    `check-claims.py` 的读数从「36 个含强断言的小节」掉到「29 个」——
    **而 `check-page-coverage.py` 仍 exit=0、连一句提醒都没有**，
    因为它是用**正则读源码里的字面量**来还原扫描面的，运行时那次改动它一个字都看不见。
    ★ **失灵方向是「少报」**，所以必须由它自己来守这个前提。
    """

    path = root / "scripts" / "check-claims.py"
    text = path.read_text(encoding="utf-8")
    patched = text.replace(
        'BODY_GLOBS = ["10-tasks/*.md"]',
        'BODY_GLOBS = ["10-tasks/*.md"]\nBODY_PAGES.remove("20-reference.md")',
        1,
    )
    assert patched != text, "注入失败：没找到 BODY_GLOBS 那一行"
    path.write_text(patched, encoding="utf-8")


def mutate_page_list_literal_change_ok(root: Path) -> None:
    """反向对照：清单是**字面量**改动时，仍只提醒、不阻断（M241）。

    ★ **这条钉住的是「我没有偷偷改政策」**：M162 划的边界是
    「部分覆盖可见但不阻断」，**字面量改动本门禁读得到**，
    报读会如实变化并点名——**所以它必须继续放行**。
    **新判据只拦「运行时改」，不拦「字面量改」。**
    """

    path = root / "scripts" / "check-retractions.py"
    text = path.read_text(encoding="utf-8")
    patched = text.replace(
        'LEDGER_PAGES = ["task-inventory.yml", "SOURCE_OBSERVATIONS.md"]',
        'LEDGER_PAGES = ["task-inventory.yml"]',
        1,
    )
    assert patched != text, "注入失败：没找到 LEDGER_PAGES 那一行"
    path.write_text(patched, encoding="utf-8")


def mutate_destructive_cleared_at_runtime(root: Path) -> None:
    """不可逆按钮白名单在**运行时被清空**，而契约门禁看不见（M242）。

    ★ **这是本库最要命的一份名单**：`DESTRUCTIVE` 是
    `probe-toolbar-states.js` 唯一的硬闸，命中就跳过那个按钮。
    **白名单清空 = 探针会去点真正的删除。**

    ★ **阳性对照是「两个独立读数当场对不上」**：
    - 本门禁的读数（正则读源码字面量）：仍是 6 项；
    - `node` 真跑一遍：`[]`。
    **而注入之前 `check-probe-contracts.py` 全程 exit=0。**

    ★ 这里刻意把 `.clear()` **拆到两行**：静态判据①逐行看、看不见它，
    **由判据②（node 真算）兜住**——证明两条判据不是冗余的。
    """

    path = root / "scripts" / "probe-toolbar-states.js"
    path.write_text(
        path.read_text(encoding="utf-8") + "\nDESTRUCTIVE\n  .clear();\n",
        encoding="utf-8",
    )


def mutate_destructive_mentioned_in_comment_ok(root: Path) -> None:
    """反向对照：注释里提到 `DESTRUCTIVE.clear()` **不该**被当成改写（M242）。

    ★ **M194 的老教训**：扫 JS 源码前必须先剥注释，否则正文里举例的写法
    会被当成真代码。`probe-toolbar-states.js` 的文件头本来就有一段注释
    在讲 `DESTRUCTIVE` 是一道硬闸——**这条用例钉住剥注释这一步不许被省掉**。
    """

    path = root / "scripts" / "probe-toolbar-states.js"
    text = path.read_text(encoding="utf-8")
    patched = text.replace(
        "const DESTRUCTIVE = new Set(",
        '/* 早期版本用 DESTRUCTIVE.clear() 初始化，后来改成字面量 */\n'
        "const DESTRUCTIVE = new Set(",
        1,
    )
    assert patched != text, "注入失败：没找到 DESTRUCTIVE 声明那一行"
    path.write_text(
        patched + '\n// 历史写法：曾写过 DESTRUCTIVE.delete("删除全部")，后改为登记\n',
        encoding="utf-8",
    )


def mutate_retraction_notation_needle(root: Path) -> None:
    """needle 退化成**纯「键=数字」的取证记法**时必须被拦下（M203）。

    ★ **这一例注入的不是虚构的坏数据，是 M160 真实写过的那个值。**
      R31 当年登记的 needle 就是 `x=963`——`SOURCE_OBSERVATIONS.md` 里一条坐标记录的
      内部写法，**正文里从来没有这么写过**（正文写「931 px」）。后果不是「拦得不准」，
      是**压根拦不到**：M160 把 931px 订正掉了，同一张表里的「同屏，相距 931 px」
      照样活了两批，门禁一路报 ok。
    """
    path = root / "scripts/check-retractions.py"
    text = path.read_text(encoding="utf-8")
    patched = text.replace('"wrong": "同屏，相距 931 px",', '"wrong": "x=963",', 1)
    assert patched != text, "注入失败：没找到 R31 的 needle（它已被换过形态？）"
    path.write_text(patched, encoding="utf-8")


def mutate_retraction_english_needle_ok(root: Path) -> None:
    """反向对照：**英文界面文案当 needle 不该被误报**（M203，不误报）。

    「键=数字」判据如果顺手扩成「needle 必须含汉字」或「不得短于 N 字」，
    就会把 `Frame-level settings` 这类**正当的英文 needle** 判成错。
    那正是 M195 说过的失败模式：**判据宽到会冤枉好人，就不该叫门禁**。
    这一例守的就是那道边界不被偷偷放宽。

    ★ **第一版这里写的是 `Connection settings`，用例当场挂了**——
      那个串**真的存在于扫描面里**（`20-reference.md` 记着 Agent 面板那 7 个英文
      `aria-label`），于是门禁报「订正过的错误说法重新出现」是**完全正确的行为**，
      错的是我挑了一个会真命中的串来当阴性对照。
      **阴性对照的 needle 必须在扫描面里真的不存在**，否则测的是判据、不是对照。
    """
    path = root / "scripts/check-retractions.py"
    text = path.read_text(encoding="utf-8")
    patched = text.replace(
        '"wrong": "同屏，相距 931 px",', '"wrong": "Frame-level settings",', 1
    )
    assert patched != text, "注入失败：没找到 R31 的 needle"
    path.write_text(patched, encoding="utf-8")


def mutate_anchor_exemption_covers_many_lines(root: Path) -> None:
    """内容锚点**罩住了不止一行**时必须被点名（M205）。

    ★ **盯的是一个「正在恶化、还没恶化」的洞**（M204 量出来的）：
      全库 10 个内容锚点当时**无一例外都恰好命中 1 行**，所以这道判据上线时
      是一条**零命中**的判据。**M204 只把它记下来，没立门禁**——
      理由是「窄不到能全对就不该假装是门禁」，而当时**没有正例可证它能全对**。
      M205 先补了正例：下面这个片段在 `task-inventory.yml` 的**原始行**里命中 5 行
      （★ 不是 3 行——第一版候选是在**去掉空白后**滑窗找的，而门禁匹配的是原始行，
      那个片段在原行里被空格隔开、实际命中 0 行。**候选必须在被测对象上现算。**）
    """
    path = root / "scripts/check-retractions.py"
    text = path.read_text(encoding="utf-8")
    old = '"task-inventory.yml#运行时走查完成（清数据首启→新建→空画布→首页项目卡）"'
    assert old in text, "注入失败：没找到 R25 的内容锚点豁免（载具已变？）"
    path.write_text(text.replace(old, '"task-inventory.yml#从静态升级为运行时"', 1), encoding="utf-8")


def mutate_anchor_exemption_dead(root: Path) -> None:
    """内容锚点**一行都命中不了**（死配置）时必须被点名（M205）。

    死配置与「偷偷放宽」方向相反，但同样有害：豁免根本没在生效，
    门禁会因为 needle 命中而报红，**报的还是「错误说法复现」**——
    读者会以为正文出了新错，其实是自己的豁免烂了。**两种坏法必须分开报。**
    """
    path = root / "scripts/check-retractions.py"
    text = path.read_text(encoding="utf-8")
    old = '"task-inventory.yml#运行时走查完成（清数据首启→新建→空画布→首页项目卡）"'
    assert old in text, "注入失败：没找到 R25 的内容锚点豁免（载具已变？）"
    path.write_text(text.replace(old, '"task-inventory.yml#这一行里根本不存在的锚点"', 1), encoding="utf-8")


def mutate_anchor_exemption_other_fragment_ok(root: Path) -> None:
    """反向对照：**换个措辞、但仍恰好命中同一行**不该被误报（M205，不误报）。

    这道判据管的是**豁免的宽度**，不是**豁免该挑哪个词**。
    同一行里有好几个都能用的片段，只要都只命中那一行，**就都是合法的**。
    这一例守的是判据没偷偷长成「必须用登记里那个特定的片段」——
    那种判据会把人逼到「不许改锚点措辞」，而锚点本来就该能随手换。
    """
    path = root / "scripts/check-retractions.py"
    text = path.read_text(encoding="utf-8")
    old = '"SOURCE_OBSERVATIONS.md#三处按钮区的顺序固定"'
    assert old in text, "注入失败：没找到 R26 的内容锚点豁免（载具已变？）"
    path.write_text(
        text.replace(old, '"SOURCE_OBSERVATIONS.md#由此订正手册里一条方向写反的建议"', 1),
        encoding="utf-8",
    )


CASES: list[tuple[str, object, str, str]] = [
    ("图片字节被改动", mutate_image_bytes, "gate", "sha256 mismatch"),
    ("manifest 删掉一条记录", mutate_manifest_drop_record, "gate", "image missing from manifest"),
    ("manifest 写错 sha256", mutate_manifest_bad_sha, "gate", "sha256 mismatch"),
    ("manifest 用不存在的 task_id", mutate_manifest_bad_task_id, "gate", "unknown task_id"),
    ("manifest 缺必填字段", mutate_manifest_missing_field, "gate", "missing verified_locator"),
    ("正文引用的图片被删", mutate_delete_referenced_image, "gate", "missing image"),
    ("正文图片空 alt", mutate_empty_alt, "gate", "empty alt text"),
    ("md 链接指向不存在的文件", mutate_broken_md_link, "gate", "broken local link"),
    ("标题层级跳跃 H2→H4", mutate_heading_jump, "gate", "heading jumps"),
    ("锚点指向不存在的标题", mutate_broken_anchor, "anchor", "锚点不存在"),
    ("锚点指向代码块里的注释行（假标题）", mutate_fenced_pseudo_anchor, "anchor", "锚点不存在"),
    ("孤儿任务页（未登记账本）", mutate_orphan_page, "structure", "孤儿页"),
    ("任务索引漏一条", mutate_index_drop_entry, "structure", "索引缺少"),
    ("侧边栏条目被改名", mutate_sidebar_rename, "structure", "侧边栏缺少"),
    ("小节里的裸强断言（无证据）", mutate_bare_claim, "claims", "裸断言"),
    ("已订正的错误说法复现", mutate_retracted_claim, "retractions", "订正过的错误说法重新出现"),
    ("M93 订正的「自由缩放」复现", mutate_retracted_freeresize, "retractions", "R20"),
    ("M93 订正的视频面板参数复现", mutate_retracted_video_params, "retractions", "R21"),
    ("M99 撤回的「方向拖反会连上」复现", mutate_retracted_stale_count, "retractions", "R22"),
    ("M132 订正的「Dock 认不出 9 个」复现（M152 补登记）", mutate_retracted_m132_dock, "retractions", "R25"),
    ("订正豁免写成只给文件名（豁免必须窄到无法滥用）", mutate_retracted_allowlist_too_broad, "retractions", "写法不合法"),
    ("内容锚点豁免指错行时不能放行（锚点必须真的对得上）", mutate_anchor_exemption_wrong_fragment, "retractions", "订正过的错误说法重新出现"),
    ("内容锚点短于 8 字判非法（锚点不能退化成模糊匹配）", mutate_anchor_exemption_too_short, "retractions", "写法不合法"),
    ("行号豁免形态已退役，写回去必须被点名（否则退役形同虚设）", mutate_anchor_exemption_back_to_lineno, "retractions", "已退役的行号写法"),
    ("已订正说法复现到**账本**里（正文之外的盲区）", mutate_retracted_ledger_repro, "retractions", "订正过的错误说法重新出现"),
    ("新订正不写 kind（改了描述却不算订正，计数会失真）", mutate_retraction_missing_kind, "retractions", "没写"),
    ("kind 取值拼错等于没分类（不能安静地少拦一类）", mutate_retraction_bad_kind, "retractions", "不在"),
    ("needle 退化成取证坐标记法（守的从来不是读者会读到的说法）", mutate_retraction_notation_needle, "retractions", "纯「键=数字」的取证记法"),
    ("英文界面文案当 needle 不该被误报（判据不许偷偷放宽）", mutate_retraction_english_needle_ok, "retractions", EXPECT_PASS),
    ("内容锚点罩住多行（豁免在偷偷放宽）", mutate_anchor_exemption_covers_many_lines, "retractions", "偷偷放宽"),
    ("内容锚点一行都命中不了（死配置，豁免没在生效）", mutate_anchor_exemption_dead, "retractions", "死配置"),
    ("换个措辞但仍只命中同一行不该被误报（判据只管宽度）", mutate_anchor_exemption_other_fragment_ok, "retractions", EXPECT_PASS),
    ("已订正说法复现到**截图清单**里（112 条取证读数的盲区）", mutate_retracted_manifest_repro, "retractions", "订正过的错误说法重新出现"),
    ("表格行格子数多于表头（多出来的格子连内容一起被丢弃）", mutate_table_row_too_many_cells, "tables", "这一行有"),
    ("内部账本的表格欠账不许增长（基线口径）", mutate_table_internal_backlog_grows, "tables", "不许增长"),
    ("产物里的死链", mutate_dead_dist_link, "distlinks", "指向不存在目标的链接"),
    ("任务评级三处不一致", mutate_rating_drift_inventory, "ratings", "评级漂移"),
    ("账本截图数与 manifest 不符", mutate_inventory_stale_count, "invfresh", "manifest 实为"),
    ("表格被引用块劈开", mutate_table_split_by_quote, "tables", "会整体渲染成原始管道文本"),
    ("表格行脱离表头接在列表后", mutate_table_rows_after_list, "tables", "会整体渲染成原始管道文本"),
    ("代码块外的孤立表格行", mutate_table_outside_fence, "tables", "会渲染成普通段落"),
    ("单元格内竖线未转义（产物丢内容）", mutate_unescaped_pipe_in_code_span, "tables", "反引号（奇数）"),
    ("孤儿截图（登记了却没人引用）", mutate_orphan_screenshot, "structure", "孤儿截图"),
    ("** 紧邻标点导致加粗失效", mutate_broken_emphasis, "emphasis", "left-flanking"),
    ("裸 {{ }} 被 Vue 插值吞掉", mutate_vue_interpolation, "emphasis", "插值吞掉"),
    ("同页锚点指向不存在的标题", mutate_same_page_anchor, "anchor", "锚点不存在"),
    ("产物表格列数不一致（内容被丢弃）", mutate_broken_render, "render", "多出来的格子连同内容已被渲染器丢弃"),
    ("行内代码段被提前截断", mutate_early_closed_code, "render", "被提前截断"),
    ("产物里裸露的管道文本", mutate_pipe_leak_render, "render", "裸露的表格管道文本"),
    ("产物里页内锚点悬空", mutate_dangling_anchor_render, "render", "找不到对应 id"),
    ("账本锁定的提交与应用仓漂移", mutate_ledger_pin_drift, "ledgerpin", "与应用仓 HEAD 不一致"),
    ("发布文档的门禁表与脚本对不上", mutate_publish_gate_drift, "publishsync", "build-site.sh 并没有调用"),
    ("文档里「几道门禁」漂了（集合对得上、数字对不上）", mutate_publish_gate_count_drift, "publishsync", "（不含 selftest-gates.py）"),
    ("文档里「注入几类故障」与自检实际用例数对不上", mutate_publish_selftest_count_drift, "publishsync", "而 scripts/selftest-gates.py 里实际有"),
    ("「由来」列里的历史门禁数不该被当成当前数量（不误报）", mutate_publish_historical_gate_count, "publishsync", EXPECT_PASS),
    ("批次自述的日期晚于「今天」（标题 + 正文内联两种语序）", mutate_batch_date_in_future, "batchdates", "晚于今天"),
    ("源码引用行号越界（读者点过去没这行）", mutate_source_ref_out_of_range, "sourcerefs", "行号越界"),
    ("两份锁定声明互相对不上", mutate_pin_declarer_disagreement, "ledgerpin", "各声明文件锁定的提交不一致"),
    ("只改一个文件的版本号（并集判据的经典漏网）", mutate_pin_version_drift, "ledgerpin", "各声明文件写的应用版本不一致"),
    ("账本不是合法 YAML（note 嵌了冒号+空格）", mutate_inventory_yaml_broken, "inventoryyaml", "不是合法 YAML"),
    ("账本任务 id 重复（按 id 查会静默取到第一条）", mutate_inventory_yaml_dup_id, "inventoryyaml", "id 重复"),
    ("账本证据 type 拼错（门禁集合必须从实际数据数出来）", mutate_inventory_yaml_bad_type, "inventoryyaml", "不在已知集合内"),
("正文里有多字节中文被截断（U+FFFD）", mutate_encoding_mojibake, "encoding", "替换字符"),
    ("账本运行时结论只写在 review_note 里（记账漂移）", mutate_inventory_evidence_drift, "inventoryevid", "记账漂移"),
    ("写「未实测」不该被当成声称实测（否定形态不得误报）", mutate_inventory_evidence_negation, "inventoryevid", EXPECT_PASS),
    ("探针白名单在文档里被删成「见源码」（文档查不到清单）", mutate_probe_contract_drift, "probecontracts", "漏列了不可逆按钮"),
    ("探针用未登记的 data-* 定位（读者查不到这张表）", mutate_probe_marker_undocumented, "probecontracts", "没进 PUBLISH.md 第九条的表"),
    ("标记表里列了应用源码中不存在的 data-*（表过期比缺项更坏）", mutate_probe_marker_ghost_in_table, "probecontracts", "应用源码中**不存在**的标记"),
    ("顶层页面从内容门禁清单里被删掉（于是谁都不扫它）", mutate_coverage_drop_body_page, "pagecoverage", "漏网"),
    ("页面排除表里的理由写得过短（等于没写理由）", mutate_coverage_reason_too_short, "pagecoverage", "豁免过宽"),
    ("页面排除表里留着已不存在的文件（表会失真）", mutate_coverage_stale_exclusion, "pagecoverage", "过期"),
    ("文档比源码写得更细不该被误报（不做双向全等）", mutate_probe_contract_extra_context, "probecontracts", EXPECT_PASS),
    ("探针用子串/正则去选不可逆按钮（M192 栽在这）", mutate_probe_fuzzy_destructive, "probecontracts", "用子串/正则去选不可逆按钮"),
    ("全名精确匹配不该被误报（这条纪律要的就是写全名）", mutate_probe_exact_destructive, "probecontracts", EXPECT_PASS),
    ("注释里提到子串匹配不该被判违规（注释不是选择器）", mutate_probe_comment_fuzzy_destructive, "probecontracts", EXPECT_PASS),
    ("出口行挂到章节标题下（位置错但门禁全绿过）", mutate_ownership_wrong, "ownership", "归属错误"),
    ("出口行挂在正确条目下不该被误报（不判该不该有）", mutate_ownership_ok, "ownership", EXPECT_PASS),
    ("门禁静默放行：ledger-pin 退回 M150 行为", mutate_gate_silence_reintroduced, "gatesilence", "仍 exit=0"),
    ("门禁静默放行：inventory-evidence 退回 M150 行为", mutate_gate_silence_ledger_evid_reintroduced, "gatesilence", "仍 exit=0"),
    ("台账重述位置的短语被改写（改正文忘了改台账）", mutate_ledger_phrase_rewritten, "factledger", "重述位置短语在"),
    ("正文数字改了、台账实测值没改", mutate_ledger_number_drift, "factledger", "和台账里的数字对不上"),
    ("台账声明的条数与表体行数对不上", mutate_ledger_count_drift, "factledger", "条数与表体行数对不上"),
    ("台账里出现重复的事实 ID", mutate_ledger_duplicate_id, "factledger", "事实 ID 重复"),
    ("依据写成占位词（只给数字不给方法）", mutate_ledger_evidence_placeholder, "factledger", "依据为空或写成了占位词"),
    ("重述位置指向内部账本而不是发布页", mutate_ledger_points_to_progress, "factledger", "不是对外发布页"),
    ("重述位置短语里带了字面竖线（列被拆开）", mutate_ledger_pipe_in_phrase, "factledger", "台账行解析不了"),
    ("短语里带加粗、箭头、反引号不该被误报（不误报）", mutate_ledger_rich_phrase_ok, "factledger", EXPECT_PASS),
    ("正文里连续两行一模一样（M201 实测事故）", mutate_duplicate_line_in_prose, "dupeline", "连续重复行"),
    ("围栏代码块里两行相同不该被误报（不误报）", mutate_duplicate_line_in_code_fence_ok, "dupeline", EXPECT_PASS),
    ("连续两个空行不该被算成重复行（不误报）", mutate_duplicate_blank_lines_ok, "dupeline", EXPECT_PASS),
    ("又手抄了一份与 srcExclude 不一致的内部名单（M240）", mutate_internal_list_hardcoded, "internallists", "手抄的内部名单"),
    ("该推导的门禁被改回不推导，判据 2 必须抓到（M240）", mutate_internal_list_derivation_removed, "internallists", "没有 import"),
    ("事实源 srcExclude 被改坏，推导它的门禁必须判失败（M240）", mutate_src_exclude_removed, "emphasis", "读不到"),
    ("页面清单在运行时被改，覆盖门禁必须当场发现（M241）", mutate_page_list_runtime_mutation, "pagecoverage", "静默"),
    ("页面清单是字面量改动时仍只提醒不阻断（不误报，M241）", mutate_page_list_literal_change_ok, "pagecoverage", EXPECT_PASS),
    ("不可逆按钮白名单在运行时被清空，契约门禁必须发现（M242）", mutate_destructive_cleared_at_runtime, "probecontracts", "两个读数不一致"),
    ("注释里提到白名单改写不该被当成真代码（不误报，M242）", mutate_destructive_mentioned_in_comment_ok, "probecontracts", EXPECT_PASS),
    ("绝对断言的限定词被删掉（订正块被误删的样子，M254）", mutate_absolute_qualifier_deleted, "absclaim", "限定词在"),
    ("限定词还在时不该被误报（不误报，M254）", mutate_absolute_row_ok, "absclaim", EXPECT_PASS),
    ("登记表里的锚点指着一句已改掉的话（锚点腐化，M296）", mutate_absolute_anchor_rotten, "absclaim", "锚点片段在"),
    ("算式的结论被改错（两个乘数没动，M297）", mutate_multiple_ratio_wrong, "multiples", "算式验算不过"),
    ("不在台账里的 N 倍不该被误报（不误报，M297）", mutate_multiple_unlisted_ok, "multiples", EXPECT_PASS),
]


def run_gate(root: Path, which: str) -> tuple[int, str]:
    if which == "gate":
        cmd = [sys.executable, str(GATE), str(root), "--phase", "final"]
    elif which == "anchor":
        cmd = [sys.executable, str(root / "scripts/check-anchors.py"), str(root)]
    elif which == "structure":
        cmd = [sys.executable, str(root / "scripts/check-structure.py"), str(root)]
    elif which == "ratings":
        cmd = [sys.executable, str(root / "scripts/check-ratings.py"), str(root)]
    elif which == "invfresh":
        cmd = [sys.executable, str(root / "scripts/check-inventory-freshness.py"), str(root)]
    elif which == "retractions":
        cmd = [sys.executable, str(root / "scripts/check-retractions.py"), str(root)]
    elif which == "tables":
        cmd = [sys.executable, str(root / "scripts/check-tables.py"), str(root)]
    elif which == "emphasis":
        cmd = [sys.executable, str(root / "scripts/check-emphasis.py"), str(root)]
    elif which == "batchdates":
        cmd = [sys.executable, str(root / "scripts/check-batch-dates.py"), str(root)]
    elif which == "distlinks":
        cmd = [sys.executable, str(root / "scripts/check-dist-links.py"), str(root)]
    elif which == "render":
        cmd = [sys.executable, str(root / "scripts/check-render.py"), str(root)]
    elif which == "ledgerpin":
        cmd = [sys.executable, str(root / "scripts/check-ledger-pin.py"), str(root)]
    elif which == "publishsync":
        cmd = [sys.executable, str(root / "scripts/check-publish-sync.py"), str(root)]
    elif which == "sourcerefs":
        cmd = [sys.executable, str(root / "scripts/check-source-refs.py"), str(root)]
    elif which == "inventoryyaml":
        cmd = [sys.executable, str(root / "scripts/check-inventory-yaml.py"), str(root)]
    elif which == "encoding":
        cmd = [sys.executable, str(root / "scripts/check-encoding.py"), str(root)]
    elif which == "inventoryevid":
        cmd = [sys.executable, str(root / "scripts/check-inventory-evidence.py"), str(root)]
    elif which == "probecontracts":
        cmd = [sys.executable, str(root / "scripts/check-probe-contracts.py"), str(root)]
    elif which == "ownership":
        cmd = [sys.executable, str(root / "scripts/check-section-ownership.py"), str(root)]
    elif which == "pagecoverage":
        cmd = [sys.executable, str(root / "scripts/check-page-coverage.py"), str(root)]
    elif which == "gatesilence":
        cmd = [sys.executable, str(root / "scripts/check-gate-silence.py"), str(root)]
    elif which == "factledger":
        cmd = [sys.executable, str(root / "scripts/check-fact-ledger.py"), str(root)]
    elif which == "absclaim":
        cmd = [sys.executable, str(root / "scripts/check-absolute-claims.py"), str(root)]
    elif which == "multiples":
        cmd = [sys.executable, str(root / "scripts/check-multiples.py"), str(root)]
    elif which == "dupeline":
        cmd = [sys.executable, str(root / "scripts/check-duplicate-lines.py"), str(root)]
    elif which == "internallists":
        cmd = [sys.executable, str(root / "scripts/check-internal-lists.py"), str(root)]
    else:
        cmd = [sys.executable, str(root / "scripts/check-claims.py"), str(root)]
    done = subprocess.run(cmd, capture_output=True, text=True)
    return done.returncode, done.stdout + done.stderr


def main() -> int:
    source = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not GATE.is_file():
        print(f"  [自检] 找不到共享门禁脚本：{GATE}")
        return 1

    print("=== 门禁自检：注入故障 → 断言被正确拦下 ===")
    started = time.time()
    passed, failed = 0, 0

    # 先给「注入有效性检测」本身做自检。**它若坏了，后面 68 条结论全都不可信**——
    # 一道坏掉的判据会把「门禁没坏」误报成「门禁漏网」，比没有判据更费时间。
    detector_ok, detector_note = verify_injection_detector()
    print(f"  [ {'ok' if detector_ok else '坏'} ] 注入有效性检测自检：{detector_note}")
    if not detector_ok:
        return 1

    stale = 0
    for name, mutate, which, expected in CASES:
        with tempfile.TemporaryDirectory(prefix="m42gate-") as tmp:
            work = Path(tmp) / "manual"
            shutil.copytree(source, work, ignore=shutil.ignore_patterns("dist", "cache", "node_modules"))
            before = tree_digest(work)
            # 注入函数自己也可能抛（如锚点找不到）。**抛异常和静默空操作是同一类病**：
            # 都没能把故障送进门禁。所以这里接住、记成「注入无效」，不让它中断整轮。
            try:
                mutate(work)
                touched = changed_files(before, tree_digest(work))
            except Exception as exc:  # noqa: BLE001 - 故意兜住：注入失败是本用例的问题
                touched, inject_error = [], str(exc).strip().splitlines()[0][:110]
            else:
                inject_error = ""
            # 注入没改动任何文件时**根本不跑门禁**：跑出来的「通过」是假的，
            # 而假通过比失败更坏——它让这道闸在账本上一直是绿的。
            if touched:
                code, output = run_gate(work, which)
            else:
                code, output = 0, ""

        if not touched:
            print(f"  [注入无效] {name:<26} 注入函数没改到任何文件——门禁压根没被考到")
            if inject_error:
                print(f"         注入函数自己抛了：{inject_error}")
            stale += 1
            failed += 1
        elif expected == EXPECT_PASS:
            # 这一类断言门禁**应当放过**——它守的是「门禁不误报」这一半。
            # 没有它，一个只会说「是」的门禁可以靠永远误报来自检全绿。
            if code == 0:
                print(f"  [ ok ] {name:<26} 由 {which:<8} 如实放过（不误报）")
                passed += 1
            else:
                print(f"  [错因] {name:<26} {which} 误报了：{output.strip().splitlines()[0][:120]}")
                failed += 1
        elif code != 0 and expected in output:
            print(f"  [ ok ] {name:<26} 由 {which:<8} 以「{expected}」拦下")
            passed += 1
        elif code == 0:
            print(f"  [漏网] {name:<26} {which} 竟然通过了")
            failed += 1
        else:
            print(f"  [错因] {name:<26} {which} 失败了，但报的是「{expected}」以外的内容")
            print(f"         {output.strip().splitlines()[-1][:150] if output.strip() else '(无输出)'}")
            failed += 1

    print(f"--- {passed}/{len(CASES)} 用例按预期被拦下，用时 {time.time() - started:.1f}s ---")
    if failed:
        print(f"门禁自检失败：{failed} 个用例没有以正确理由被拦下")
        if stale:
            # 两种失败的处置完全相反，分开报是为了不让人去改错地方。
            print(f"  其中 {stale} 个是「注入无效」——**门禁没坏，是注入没注入到东西**，该改用例。")
        return 1
    print("门禁自检通过：所有注入的故障都被对应门禁以正确理由拦下")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
