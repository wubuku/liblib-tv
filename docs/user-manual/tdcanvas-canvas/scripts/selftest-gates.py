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
    ("孤儿任务页（未登记账本）", mutate_orphan_page, "structure", "孤儿页"),
    ("任务索引漏一条", mutate_index_drop_entry, "structure", "索引缺少"),
    ("侧边栏条目被改名", mutate_sidebar_rename, "structure", "侧边栏缺少"),
    ("小节里的裸强断言（无证据）", mutate_bare_claim, "claims", "裸断言"),
    ("已订正的错误说法复现", mutate_retracted_claim, "retractions", "订正过的错误说法重新出现"),
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

        if code != 0 and expected in output:
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
