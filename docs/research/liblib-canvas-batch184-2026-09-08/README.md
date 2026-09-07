# Batch 184 — 剩余 6 个老化验证器逐个核对（全部确认 AGED_GATE，零代码改动）

## 核对方法与裁决

对 batch6 / 40 / 41 / 44 / 46 / 48 逐一取当前失败形态，对照
`LIBTV_VERIFIER_REPLACEMENT_MAP.md §4.z` 的取代关系与现行门状态裁决。
**全部确认维持 AGED_GATE，不做合同迁移**，理由：六个的表面均已被
Batch 59 / 67-96 现行门（全绿）取代；迁移意味着按当前文档 schema 重写
整套 fixture，等于重造已被取代映射废弃的验证器，违反台账规则
（"修改断言需记录当前源站合同"——它们没有当前源站合同）。

## 逐个失败形态（2026-09-08 实测）

| 验证器 | 当前失败 | 裁决 |
|---|---|---|
| batch6 | marquee 选择框不出现 | Batch 77 源站运行时证据取代 marquee 语义（AGENTS.md 导航权威）；superseded |
| batch40 | HTMLMediaElement.currentTime 赋非有限值 | fixture 视频元数据未加载的媒体伪影，非源站合同差异 |
| batch41 | export/import 回路 selection/camera 断言 | Batch 96 后 schema 收紧的旧 fixture 契约 |
| batch44 | run_desktop 断言 | 同上 |
| batch46 | run_desktop 断言 | 同上 |
| batch48 | run_desktop 断言 | 同上 |

## 落地

- 六个验证器头部各加 Batch 184 核对注记（失败形态 + 取代门引用 + 维持
  AGED_GATE），让脚本自文档化。
- 零源代码改动；batch9/21/51/75/89/96 抽样回归绿；`npm run check`
  0 errors（8 warnings 基线）；docs check 通过。
- **老化名单终态：剩余 6 个为「确认历史合同」，不再有未归因失败。**
  batch72/74/75/49/9/51 已于 181-183 复活。
- 源站画布保持 0 残留（本批无源站采样）。
