# Batch 173 — 节点右键菜单 + 模型菜单选中态（源站 2026-09-07 CDP 补采）

## 源站事实（窗口 31fps 可渲染期，CDP 采样，JSON/截图已存档）

### 节点右键菜单（`source-node-context-menu-dom.json`）

- **勘误**：节点右键**不是**空白右键的同一菜单（Batch 172 记录中的
  「更早采样：节点右键为同一菜单」结论错误，该早样只看到部分状态）。
- 容器与 pane 菜单同款（min-width 196 / p-8 / gap-4 / rounded-16 /
  0.5px 边框 / #262626），位置同样锚定点击点（左上 ≈ 点击点）。
- 七项：保存到我的资产（disabled）、创建主体（disabled）｜复制节点⌘C、
  创建副本⌘D、粘贴⌘V、删除⌘⌫｜复制到剪贴板；两组 0.5px 分隔线
  （创建主体后、删除后）。
- 复制节点/创建副本标签后带 14px 圆形「?」提示图标（inline SVG，
  opacity .35，ml-4px）；快捷键 span 与 pane 菜单同款（12px/40%/ml-24）。
- 空图片节点上保存到我的资产/创建主体均禁用（含内容状态未采样）。
- 行为直证：菜单内「删除」直接删节点（图片/视频节点均无确认弹窗）。

### 模型菜单（`source-model-menu-dump.json` / `-container.json`）

- 菜单挂载成功（今日窗口 rAF ~31fps，非此前 0-2fps 冻结态）——
  「模型菜单不可采」仅适用于窗口被遮挡限流时。
- 行按钮 360×52、`h-[52px] rounded-xl p-2`；菜单列容器 360×1956
  （35 项全量、外层滚动）。
- **选中态标记 = 行背景 `rgba(255,255,255,0.15)`**（其余行透明）；
  未捕捉到选中行高度增长/常显描述（行内描述常驻 DOM、靠 hover 位移展示，
  hover 态未采样——行高系统整体校准留给后续批次）。

### 默认模型变异性（重要勘误）

- 今日新建视频节点：触发器「2.0」、选中行「Seedance 2.0 VIP」。
- 同日早间 Batch 158 受控复测：新建节点 2.5。
- 结论：源站默认模型随账号状态变化（推断=上次使用模型），非常量。
  clone 保持 2.5 现状，不随单点翻转；后续若再采得新数据点仅记录不迁移。

## 实施

- `CanvasContextMenu` 扩展 `variant: "pane" | "node"`（`data-canvas-context-variant`）：
  node 变体七项 + 双分隔线 + 「?」图标；保存到我的资产/创建主体禁用
  （与两处已采样状态一致；选中启用态未采样）。复制节点/粘贴/复制到剪贴板
  为点击关闭占位（clone 无内部剪贴板与系统序列化管线）；创建副本→
  `duplicateSelectedNodes()`、删除→`removeSelectedNodes()` 真实接线。
- `page.tsx`：`onNodeContextMenu` 以 node 变体打开；pane 菜单的
  保存到我的资产改为恒禁用（Batch 172 的 selection 门控是推断，两个已采样
  状态均禁用；batch172 验证器本就只测无选择态，无需再迁移）。
- `VideoGenerationPanel` 模型菜单选中行背景 `bg-white/[0.1]` →
  `bg-white/[0.15]`（行高/描述系统未动，batch22 合同完好）。
- 源站测试残留清理：采样的图片/视频节点均经菜单「删除」移除（0 残留）。

## 验收

- `verify-liblib-batch173.py`：11 checks（七项顺序/快捷键/禁用+问号图标/
  双分隔线/Escape/创建副本+1/删除-1/模型菜单选中背景；Tailwind 4 将
  `bg-white/[0.15]` 编译为 oklab 形式，断言按类名+alpha 校验）。
- `verify-liblib-batch172.py` 节点段迁移：节点右键断言改为 node 变体打开，
  撤销断言移至 pane 菜单（15 checks 仍全过）。
- 回归绿：batch22 / 160-171 相邻集全过；`npm run check` 0 errors；
  docs check 通过。
- 不证明：有内容节点的保存到我的资产/创建主体启用态；复制节点/粘贴/
  复制到剪贴板点击后的源站行为；「?」图标的 hover 提示文案；模型菜单
  hover 行展开描述；源站默认模型的取值规则。
