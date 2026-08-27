# StoryAI 借鉴进展审计计划

> 状态：`COMPLETE / HISTORICAL_CONTRACT`
> 执行日期：2026-08-27
> 目标：形成当前 Director 借鉴进展的统一权威和下一步建议，不修改业务代码。

## 1. 问题定义

历史工作已经证明 StoryAI 是当前 Director Desk 的重要实现启发，但缺少一个
跨 Batch 34-50、59 的当前视图。本轮回答：

1. 固定上游版本目前具有什么能力和工程边界？
2. 当前 clone 已借鉴、扩展、代理或遗漏哪些能力？
3. 当前实现的产品成熟度、源站 fidelity、工程可靠性和 verifier maturity
   分别处于什么阶段？
4. 后续借鉴工作的价值顺序、研究闸门和编码授权边界是什么？

## 2. 执行顺序

- [x] 读取 `project-docs` skill、文档索引与维护规则；
- [x] 保护当前 `master` 工作区中的并行业务 WIP；
- [x] 确认 submodule SHA、remote freshness、许可证和目录；
- [x] 复核 StoryAI build/test，记录 `build PASS` 与 `304/312` test；
- [x] 盘点 StoryAI schema/store/io/loaders/panels/canvas；
- [x] 盘点 clone Director store、components、graph bridge 和历史 batch；
- [x] 对当前 clone 做只读 Playwright 运行态复核；
- [x] 建立 progress audit、evidence matrix、borrowing decisions 和 roadmap；
- [x] 规划文档索引、lifecycle、coverage 和 Big Picture 的可发现性同步；
- [x] 运行文档链接校验并只提交本轮文档。

## 3. 不在本轮做

- 不修改 `src/`、`scripts/`、测试夹具或 submodule pointer；
- 不修复固定 StoryAI 的 8 个失败测试；
- 不覆盖历史 screenshots 或 runtime audit；
- 不把 StoryAI 行为声明为 LibTV 原站行为；
- 不以本计划自动授权 roadmap 中的任何实现 batch。

## 4. 完成条件

- agent 可从 research hub 在两跳内找到本专题；
- 关键能力均标注事实来源和不可推出结论；
- 建议按价值、风险、依赖和授权状态排序；
- 当前 clone 的历史通过、当前静态事实和本轮运行事实不混写；
- 文档检查通过，提交只包含本轮文档变更。
