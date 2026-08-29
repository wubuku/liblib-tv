# Batch 91：Director 对象、相机与分组 command/history 收口

- [`PLAN.md`](PLAN.md)：本批范围、合同和验收矩阵。
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实施结果、证据边界和验证命令。
- [`runtime-audit.json`](runtime-audit.json)：fresh-page Playwright 结构化结果。

> 本批只处理 clone-owned Director reliability slice；不把上游 StoryAI 或
> 当前 clone 的实现推断为 LibTV 原站 source-exact 行为。

## 本批证据边界

| 主张 | 等级 |
|---|---|
| clone 对象/相机/分组 command、persistence、history | `CLONE_STATIC_FACT` + `RECORDED_RUNTIME` |
| 对象/分组名称 draft + Enter/blur | `CLONE_DECISION` + `RECORDED_RUNTIME` |
| LibTV 原站 Director 的 exact object/camera/group command、history 和 persistence 语义 | `SOURCE_UNKNOWN` |

## 结果

`FOCUSED_RUNTIME_RECORDED_PASS`。对象/相机/分组的高频 direct writer 已接入
project/session、persistence 和 Director-local history 边界；对象名和分组名
不会因逐字符输入而制造 history。专项结果与限制见 [`IMPLEMENTATION.md`](IMPLEMENTATION.md)。
