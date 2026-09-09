# Batch 245 — 全量稳定性确认（178 脚本全量跑 + 差分定位 + batch125 合同迁移 WIP）

> 状态：`STABILITY_RECORDED`（batch125 迁移为 WIP：一个 check 未过，见下）。

## 全量跑（178 个 verify 脚本）三类信号

1. **工具链伪故障**：以 coreutils `timeout` 前缀批量执行导致 venv CPython
   走 Rosetta、arm64 `.so` dlopen 失败（约 45 个脚本的 ImportError 全部
   属此类——已知陷阱再次确认：**禁止 timeout 前缀**）。
2. **输出格式误报**：batch69–96 等脚本打印 JSON（`"status": "PASS"` /
   `SCRIPT_RECORDED_PASS`），与脚本的通过判别 glob（*passed*/*OK*）不匹配，
   非真失败。
3. **真实失败 11 个**：batch6 / 14 / 19 / 57 / 61 / 64 / 67 / 83 / 97 /
   125（+90 的 audit 副作用已还原）。

## 差分定位（checkout 到 batch 235 提交点 8206c9a 热载对比）

- batch6 / 14 / 19 / 57 / 61 / 64 / 97：**在 batch 235 时同样失败**——
  先于本会话（236–244）的老化门，非本会话回归；
- **batch125：235 通过、当前失败**——本会话改动的真回归，已定位：
  batch 239 源站事实（首帧态无提示词输入框）演进后，batch125 的
  「首帧芯片后断言 textarea」合同失效。

## batch125 合同迁移（WIP）

已重写流程：attempts 行/芯片断言 → 首帧面板断言（槽/说明文案/无
textarea，batch 239 合同）→ 经 batch 244 销毁按钮回退 → 再做提示词
placeholder / 工具行 / 生成流断言（默认态）。

**未决**：`firstframe:destroy-reverts` check 仍失败（batch244 验证器同
流程通过；batch125 差异 = 使用 `.react-flow__node-video` **first** 选择——
预设画布含多个视频节点，`.first` 可能命中预设节点、其图状态含既有
image→video 边，销毁目标的歧义待查）。下会话继续：先验证 `.first`
选择的节点身份，必要时改为新建节点定位。

## 其余验收

- `npm run check`：0 errors（8 warnings 基线）；docs check 通过
  （806 Markdown / 4175 链接）；
- 工作树仅余本批变更（batch125 迁移 + 全量跑再生成的 audit/截图），
  master 与远端同步，无额外分支/worktree；
- 源站画布 0 残留。

## 后续候选

- batch125 destroy-reverts 根因（`.first` 节点歧义）收尾；
- OmniHuman 1.5 模式名与芯片上下文补采；
- 首帧态紧凑页脚分布采样（Happy Horse 系 vs 2.5 对照）。
