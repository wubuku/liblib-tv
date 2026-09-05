# Batch 112：角色筛选面板对齐 2026-09-05 补采样

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-05。
>
> 上一批 checkpoint：Batch 111（`batch/111-character-modal-source`）。

按 2026-09-05 补采样把 `角色筛选` 实现为源站同构筛选面板：`清空筛选` +
五组芯片（性别 男/女/中性；年龄段 儿童/少年/青年/中年/老年；种族
人类/精灵/兽人/机械/其他；时代 先秦/古代/近代/现代/未来；文化区域 选项
被卡片条遮挡，`SOURCE_UNKNOWN`），面板锚定按钮向上展开。

## 导航

- [PLAN.md](PLAN.md)：采样事实、过滤语义与证据边界。
- [runtime-audit.json](runtime-audit.json)：结构化运行时证据。

## 证据边界

| 标签 | 本批含义 |
|---|---|
| `SOURCE_FACT` | 面板存在、向上展开、组名、芯片集合、清空筛选 |
| `CLONE_DECISION` | 组内多选组间 AND 的标签匹配（`古代`→`古风` 别名）、无标签数据组选中即空结果、霸总性别推断 |
| `SOURCE_UNKNOWN` | 文化区域选项、芯片选中态源站样式、与真实筛选服务的关系 |

## 实施结果

- `CharacterLibraryPanel`：`data-character-filter-toggle/panel/clear/chip`；
  组内多选、组间 AND，按 tagsFor 标签匹配（`古代` 别名 `古风`）；
  无匹配时卡片条回退全量（与清空后可见性一致）。
- 修复重名角色导致的 React duplicate key（按索引渲染卡片条）。
- 「霸总/精英大佬」名字无性别字，加 `inferredGender` 推断（`CLONE_DECISION`）。

## 完成定义

1. `verify-liblib-batch112.py` 32 checks、`0/0/0` diagnostics 通过。
2. 相邻 `verify-liblib-batch111/11.py` 通过。
3. `npm run check`、`npm run docs:check` 通过。
4. 特性分支 commit/push。

通过结果只证明 clone-owned 筛选面板展示与本地过滤合同；文化区域选项与
真实筛选服务仍是 `SOURCE_UNKNOWN`。
