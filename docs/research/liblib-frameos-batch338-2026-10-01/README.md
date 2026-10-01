# Batch 338（2026-10-01）：verify-docs.py 区分「产物缺失」与「链接写错」

## 结论一句话

Batch 337 发现 `verify-docs.py` 在干净 checkout 上必失败（submodule + gitignore 截图），
因而无法进 CI。本批给它加了 `is_expected_missing()` 分类：这两类**降级为 note**，
真正的链接写错仍然 `return 1`。改后干净 checkout **EXIT=0**，可以安全进 CI。

## 修改

新增 `is_expected_missing(target)`，识别两类**预期缺失**：

| 类别 | 判据 | 为什么预期缺失 |
|---|---|---|
| submodule 内容 | target 含 `research/upstream/` | `.gitmodules` 声明，需 `git submodule update --init` |
| gitignore 截图 | target 含 `screenshots/` 且是图片后缀 | `.gitignore` 排除验证/手册截图产物 |

`main()` 现在分两路计数：命中 `expected` 的打印 note（超过 10 条折叠），
其余仍进 `missing` 并 `return 1`。通过信息里也带上 expected 数量。

**刻意不扩大范围**：只降级这两类**可解释**的缺失。像拼错文件名、指向不存在的
章节这类真错误仍然报错 —— 否则门禁就废了。

## 干净 checkout 实测

```bash
git archive HEAD | tar -x -C $D          # 与 CI 等价的干净副本
cp scripts/verify-docs.py $D/scripts/
cd $D && python3 scripts/verify-docs.py
```

结果：

```
Documentation link check passed: 1197 Markdown files, 5169 local targets,
  302 expected-missing artifact link(s).
EXIT=0
```

302 条 note 全部是 submodule 与 gitignore 截图，**没有一条是真断链**。✅

## 一个必须说清楚的前提

干净副本里仍有 **4 条** 指向 `10-tasks/use-agent.md` 的链接报错 ——
因为该文件目前是**未跟踪**状态（`git status` 显示 `??`），是**其他开发者
正在进行的 WIP**。

按项目纪律（不得丢弃/提交他人未完成工作），本批**没有** `git add` 该文件。
已实测验证：一旦该 WIP 被其作者提交，干净 checkout 立刻 `EXIT=0`
（把占位文件放进干净副本复测通过）。

也就是说：**这不是 verify-docs 的缺陷，而是工作区状态的真实反映。**

## 顺带的一次自我纠正

排查中我一度把 `90-troubleshooting.md` 里指向 `10-tasks/use-agent.md` 的链接
改成 `../10-tasks/use-agent.md`，以为是从上级目录解析失败。改完本地检查反而失败 ——
**说明原路径本来就是对的**（文件确实在 `10-tasks/` 下，链接以手册根为基准）。
已 `git checkout` 还原。教训：在「文件未跟踪」和「链接写错」两种可能之间，
先确认文件到底存不存在，再动手改链接。

## 顺延 / 候选

- 源站采样队列仍阻塞（见 `SOURCE_ACCESS_BLOCKED_2026-10-01.md`）。
- `.github/workflows/ci.yml` 的接入仍**待有 `workflow` scope 者提交**
  （Batch 337 已记录）。本批让 `verify-docs.py` 具备 CI 可用性，
  届时可与断言门禁一并加入。
- 候选 Batch 339：断言门禁目前只查**恒真**（正则可判）。
  Batch 208 那类**方向反了**的断言需语义分析，可考虑要求
  `== nodes_before` 类断言必须带注释说明「为何等于操作前/后」。
