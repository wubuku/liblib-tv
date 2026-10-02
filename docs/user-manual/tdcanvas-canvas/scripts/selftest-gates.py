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

def mutate_probe_contract_drift(root: Path) -> None:
    """探针源码的白名单在 PUBLISH 纪律表里被删成「见脚本源码」（M144）。

    M144 查出的真实漂移：M143 新写的纪律表只写「白名单四项」而**没列出是哪四项**，
    维护者在这张表里查不到清单，必须去翻 `.js`。读者查手册查不到清单，
    就等于没有这道闸——所以新立 `check-probe-contracts.py` 守住「文档不能漏项」。
    """

    path = root / "PUBLISH.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace(
            "**移除节点 / 清空画布 / 删除当前画布 / 删除选中**",
            "**（清单见脚本源码）**",
            1,
        ),
        encoding="utf-8",
    )


def mutate_probe_contract_extra_context(root: Path) -> None:
    """文档比源码写得**更细**（多写背景）**不该被误报**（M144 的判据边界）。

    本门禁只守「文档不能漏项」，**不做双向全等**：文档的职责是「让人看懂」，
    源码的职责是「让机器跑」，两者本就该有详略。若误判「文档多写了就是不一致」，
    这道门禁会逼着维护者把文档删成源码的复述——反而更难读。

    阴性形态与 M133 的「未实测」是同一类：不加限制的判据必然误报。
    """

    path = root / "PUBLISH.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace(
            "**移除节点 / 清空画布 / 删除当前画布 / 删除选中**",
            "**移除节点 / 清空画布 / 删除当前画布 / 删除选中**"
            "（这四个都在画布工具条或顶栏上，前两个 M136 亲历过误删）",
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
    ("文档比源码写得更细不该被误报（不做双向全等）", mutate_probe_contract_extra_context, "probecontracts", EXPECT_PASS),
    ("出口行挂到章节标题下（位置错但门禁全绿过）", mutate_ownership_wrong, "ownership", "归属错误"),
    ("出口行挂在正确条目下不该被误报（不判该不该有）", mutate_ownership_ok, "ownership", EXPECT_PASS),
    ("门禁静默放行：ledger-pin 退回 M150 行为", mutate_gate_silence_reintroduced, "gatesilence", "仍 exit=0"),
    ("门禁静默放行：inventory-evidence 退回 M150 行为", mutate_gate_silence_ledger_evid_reintroduced, "gatesilence", "仍 exit=0"),
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
    elif which == "gatesilence":
        cmd = [sys.executable, str(root / "scripts/check-gate-silence.py"), str(root)]
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

    for name, mutate, which, expected in CASES:
        with tempfile.TemporaryDirectory(prefix="m42gate-") as tmp:
            work = Path(tmp) / "manual"
            shutil.copytree(source, work, ignore=shutil.ignore_patterns("dist", "cache", "node_modules"))
            mutate(work)
            code, output = run_gate(work, which)

        if expected == EXPECT_PASS:
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
        return 1
    print("门禁自检通过：所有注入的故障都被对应门禁以正确理由拦下")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
