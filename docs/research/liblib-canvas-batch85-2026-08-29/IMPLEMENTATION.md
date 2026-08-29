# Batch 85 实施与验证记录

> 状态：`RECORDED_PASS`。
>
> 实施日期：2026-08-29。
>
> 本批为 clone-owned Director 选择与对象树 CRUD 可发现性，不是 LibTV 原站
> Director source-exact 结论。

## 1. 实施内容

### 1.1 Selection action bar

`DirectorObjectTree` 在存在对象或分组选择时显示紧凑的 selection action bar：

- 当前选择数量；
- 复制当前选择；
- 删除当前选择；
- 清除当前选择。

分组选择显示成员数量，删除分组仍使用既有“解组并保留成员”策略；对象多选
删除仍使用既有 `DELETE_OBJECTS` reference-aware command。

### 1.2 Command authority

本批没有新增第二套 mutation。按钮分别复用：

- `copyDirectorSelection`；
- `deleteDirectorEntity`；
- `selectObject(null)`；
- 已有 Shift 多选、`groupSelectedCharacters` 和 `ungroupSelectedCharacters`。

清除选择只改变 selection/临时路径选择，不修改 portable Director document，
不会增加 history。复制继续使用 project-scoped clipboard，删除继续保留
reference closure、selection repair 和一条 history。

## 2. 验证

### 2.1 Pure verifier

```bash
node --experimental-strip-types scripts/verify-liblib-batch85.mjs
```

结果：`PASS`。验证 selection bar selectors、数量投影、copy/delete/clear command
连接、group context 和 source boundary 记录。

### 2.2 Fresh-page Playwright

```bash
LIBLIB_BASE_URL=http://localhost:4317 \
  python3 scripts/verify-liblib-batch85.py
```

结果：`SCRIPT_RECORDED_PASS`。

覆盖：

- 单选 selection bar 与单对象计数；
- 清除选择后 bar 卸载且 history 不变；
- 复制按钮写入 project clipboard 且 committed feedback 保持隐藏；
- 通过临时 crowd fixture 解组后进行 Shift 多选；
- 批量删除减少两个对象并产生一条 history；
- mobile 对象树仍可访问；
- console/page/request diagnostics 均为 0。

结构化结果见 [`runtime-audit.json`](runtime-audit.json)。

## 3. 证据边界

| 标签 | 结论 |
|---|---|
| `CLONE_FACT` | 当前 clone 已有对象选择、Shift 多选、分组、复制和 reference-aware 删除命令 |
| `CLONE_DECISION` | 用 selection action bar 作为统一的 clone-owned 发现入口 |
| `SOURCE_UNKNOWN` | LibTV 原站 Director 是否有同样的 selection bar、数量文案、快捷键和 exact placement |

## 4. 当前限制

- 本批没有重新读取截图，也没有新增 screenshot artifact；
- 未改变普通 LibTV React Flow、FrameOS 或 Batch 84 locked-target 语义；
- 多选仍限于角色对象，因为既有分组合同只允许角色；
- 没有引入系统剪贴板、拖框选择或远端资源操作。
