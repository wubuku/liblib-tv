# Batch 440 — Batch History 索引补全（追溯债清偿）

> 状态：`DOCS_RECORDED`（无代码变更；心跳批次）。
>
> 证据：`docs/research/README.md` Batch History 表（本批 +173 行）、
> freshness §10.2b 第四十八次重测行。

## 变更

- `docs/research/README.md` Batch History 表补入 **173 个缺失批次行**
  （121–439 区间的未索引档案，含 146b 变体目录之外的全部缺口）：
  每行批次号 + 档案 README 标题派生的 focus + 相对链接；按批次号
  升序插入表尾。此前索引只覆盖到 ~234，332–439 等近期批次仅存在于
  git 提交链与档案目录，表内无入口。
- 行内容由脚本从各档案 `README.md` 首标题生成（剥离「Batch NNN：」
  前缀），未手写不改写任何历史记录；docs check 全部 173 个新链接
  通过（4178 → 4351 targets）。

## 验收

- docs check：956 Markdown / 4351 本地链接通过；
- `npm run check` exit 0；维护集 52 项 + jimeng batch 1 全 PASS
  （本批无代码变更，绿自 batch 439 的运行基线）。

## 备注

- VGP「generic generation/host epoch」在合同 §3.3 为 MAY 级可选
  adapter（separately gated），其行为不变量已由 batch 435–439 的
  owner 守卫闭环；不做无验证对象的实现。
- 并行 jimeng 路线 batch 39（group-drag）WIP 进行中，落库后下一
  对照批同步 §7。
