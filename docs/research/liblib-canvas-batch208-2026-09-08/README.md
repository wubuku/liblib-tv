# Batch 208 — script-v2 选中态卡片内部对齐

## 源站事实（选中态 DOM 采样，`source-scriptv2-selected.json` 存档）

- **悬浮标题条**：卡片上方 -28px 处，文档图标（`0 0 20 20` 四行文档）
  + 「脚本生成器」13px 文本（ellipsis、title 属性）；宽度随流缩放
  （源样式 scale 0.461×zoom 补偿，max-width 反缩放 759px）。
- **卡壳**：`node-shell rounded-xl overflow-hidden`，350×350，
  `background: var(--Surface-Panel-background, #171717)`，
  边框 `var(--canvas-node-border)`，选中 outline
  `2px solid var(--canvas-node-border-selected)`。
- 左 target handle：零尺寸 + 80px 不可见连接区 + 20px 圆形 handle。
- 选中 script-v2 **不打开视频生成面板**（panel count 0）。

## 实施

- `ScriptV2Node` 重写：悬浮标题条（DocGlyph + 标题，top-[-28px]）、
  卡壳 `rounded-xl bg-[#171717] border-[#363636]`（对齐 Surface-Panel-
  background）；标题自卡内移到悬浮条。
- batch207 验证器：floating-header 断言加入（9 checks）。

## 验收

- `verify-liblib-batch207.py`：9 checks 全绿。
- 回归绿：205 / 22 / 100 / 172。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 不证明：script-v2 内部编辑器/面板（选中不开面板，编辑器入口未采样）；
  标题条的 zoom 补偿实现（clone 由流变换自然缩放）。
- 源站测试残留清理：采样节点已删（0 残留；text 节点需 Escape 退出编辑态
  再 Backspace——删除方法学补充）。
