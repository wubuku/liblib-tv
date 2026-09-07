# Batch 154 — 全量回归扫描（124 个验证器）

## 结果

- **112 通过 / 12 老化失败（与 Batch 108/131 记录的清单完全一致：6、9、40、41、
  44、46、48、49、51、72、74、75）/ 0 个未解释失败。**
- 扫描中发现并修复 1 个真实回归：`verify-liblib-batch124.py`（回收站恢复）——
  Batch 150 将画布卡点击改为新标签页后，该验证器仍在原页断言节点数。
  已迁移为 `expect_page` 弹窗契约（restore:content-intact / canvas-2-active
  在 popup 内断言），迁移后通过（14 checks）。
- `verify-liblib-batch93.py`（导演台移动端）首跑失败、复跑通过 —— 场景对象
  面板 transition-transform 未完成时的点击拦截**时序 flake**，非回归；
  记录在案，暂不改等待策略。

## 运行注意事项（勘误）

`timeout`（coreutils）为 x86_64 二进制，会让 venv 内 CPython 在 Rosetta 下运行，
Pillow 的 arm64 `.so` 加载失败（`dlopen ... incompatible architecture`）——
33 个验证器因此误报失败。**全量扫描必须直接调用 venv python，不加 timeout 前缀。**
本轮已对 33 个受影响验证器直接复跑并按复跑结果归类。

## 验收

- 124/124 分类闭环；`npm run check`：0 errors、8 warnings（既有基线）。
- 代码变更仅 `verify-liblib-batch124.py` 迁移。
