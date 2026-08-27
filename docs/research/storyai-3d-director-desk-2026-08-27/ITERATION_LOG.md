# StoryAI 借鉴专题迭代记录

## 2026-08-27：建立当前权威

### 输入

- 固定 StoryAI submodule `8c8bd36`；
- Batch 34 的源码考古与借鉴判断；
- Batch 35-50、59 的 Director specs、implementation、maturity、screenshots 和
  verifier records；
- 当前 `src/components/director/`、`src/store/directorStore.ts`、React Flow
  entry/result bridge；
- 2026-08-27 fixed upstream build/test、remote freshness 和 clone runtime smoke。

### 新增

- 统一专题 README 和阅读顺序；
- 30+ 项能力进展矩阵；
- 主张级 evidence matrix；
- 15 张借鉴模式卡和拒绝直接复制清单；
- research-only 与待授权 implementation roadmap；
- project/history/resource/current-verifier/source-reinspection 五个研究包。

### 关键判断变化

旧批次主要按“下一个 Director 功能”排序。本专题将当前最高优先级调整为：

```text
project/session identity
  -> command/history/reference repair
  -> resource/persistence lifecycle
  -> panorama/real asset
  -> multi-camera/source calibration
```

原因是 clone 的 timeline/path/pose/export/vcam breadth 已经明显超过固定上游，
继续增加 feature 的边际价值低于补齐 durable authoring core。

### 维护触发器

以下事件发生时追加新记录：

- StoryAI remote SHA 或 submodule pointer 改变；
- Director project/store/resource/history runtime 改变；
- 新增 authenticated LibTV Director evidence；
- 建立 current verifier manifest 或全量 Director gate；
- roadmap 中任何实施 batch 获得授权、开始或完成。
