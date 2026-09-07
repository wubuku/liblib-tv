# Batch 207 — script-v2 节点类型实装 + 芯片成对创建

## 源站事实（Batch 206 采样；`source-scriptv2-pair.json`）

- 「故事脚本生成」芯片成对创建：`text` 节点（350×200，预填「剧本」）
  + `script-v2` 节点（350×350，标题「脚本生成器」），二者无连线。
- 会话发送语义（Agent 抽屉发送按钮）采样尝试两次均挂起共享页面且有
  账号侧会话残留风险——**搁置**，维持不采样。

## 实施

- 新增 `src/components/nodes/ScriptV2Node.tsx`：350×350 卡片、标题
  「脚本生成器」、双侧 Handle；内部编辑器/面板未采样，主体为最小占位
  （记录）。
- store：`getDefaultNodeDimensions`/`getDefaultNodeData` 增加 script-v2
  分支（350×350 / title 脚本生成器）；新增 `createStoryScriptPair()`——
  **单条历史**原子成对创建（text 预填「剧本」+ script-v2），选中两节点。
- `page.tsx` nodeTypes 注册 `"script-v2"`。
- `CanvasEmptyState`：story-script 芯片点击 → `createStoryScriptPair()`
  （替换本地提示占位）；其余芯片维持占位。

## 验收

- `verify-liblib-batch207.py`：8 checks（成对 +2/text 预填剧本/
  script-v2 存在且 zoom 折算 350/标题/无连线/undo 单次移除两节点/
  0 console error）。
- 回归绿：100（空态 20 checks）/ 102 / 114 / 22 / 172 / 205。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 不证明：script-v2 内部编辑器与面板；会话发送语义（挂起风险搁置）；
  卡片内部细节（源站采样仅到标题级）。
- 源站测试残留清理：0 残留。
