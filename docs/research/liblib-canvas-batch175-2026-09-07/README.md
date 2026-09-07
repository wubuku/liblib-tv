# Batch 175 — 模式菜单 + 参数菜单源站对齐（2026-09-07 可渲染窗口直采）

## 源站事实（窗口 rAF ~31fps，弹层可挂载，JSON/截图已存档）

### 模式菜单（`source-mode-menu-rows.json` / `-container.json`）

- Mantine Popover：161×229、radius 16、深底 95% alpha、锚在触发器上方；
  标题「视频生成模式」存在；5 行各带 1 图标。
- 行：h-8（32px，行距 36）、`rounded-lg px-2 gap-2 transition-colors`。
- **仅 5 项**：文生视频（选中，bg white/15）/ 全能参考 / 图生视频 /
  首尾帧 / 图片参考——**超长视频与视频编辑不在菜单中**（长视频入口在
  节点卡尝试芯片，与 Batch 128/160 一致）。
- 空白新建节点上**只有文生视频可用**，其余四项全部 disabled。

### 参数菜单（`source-params-menu-rows.json` / 截图）

- 比例网格 **6 格无 Auto**：16:9/4:3/1:1/3:4/9:16/21:9，57×62 瓦片、
  每行 4 格（间距 8px）；选中标记 bg white/10。
- 清晰度 480P/720P/1080P（73×32）；生成音频 开启/关闭（154×32）；
  数量 1个/2个/4个（100×32）。
- 时长是**滑杆行**：「视频时长」标签 + 滑杆 + 48×20 数值输入（s 后缀），
  非离散按钮组（与 clone 现实现一致）。

## 实施

- `ModeMenu`：7 项 → 菜单只渲染 5 项（`modeItems` 加 `inMenu: false`
  标记保留 超长视频/视频编辑 作标签查找项——超长视频触发器文案与
  batch21/33/128/160 合同不受影响）；禁用态对齐空节点实采（仅 text
  可用）；行 h-9→h-8；选中 bg-white/[0.08]→white/15；容器 w-52→w-[161px]
  rounded-2xl p-2。
- `ParamsMenu`：比例网格 7 格（含 Auto）→ **6 格无 Auto**、grid-cols-5
  →grid-cols-4、瓦片 52→62 高；Auto 保留为尝试联动的内部状态。
- clone 默认 mode 维持 omnireference（触发器显示 文生视频，与源站一致）；
  源站默认模式的账号态变异性同模型默认（Batch 173 勘误），只记录不翻转。

## 验证器迁移（当前源站合同）

- `verify-liblib-batch21.py`：模式菜单断言改为 5 项/仅 text 可用/无
  long-video 项；长模式入口改走尝试芯片（比例 Auto 无格子按下、时长
  初值 300——batch128 联动合同）；比例格 7→6。
- `verify-liblib-batch33.py`：`select_long_mode` 改走芯片（toggle 有界
  重试）；移除入长模式前的普通 submit 点击（芯片路径下 submitted 置位
  会提前创建过程图）；过程节点 ratio 断言 16:9→Auto。

## 验收

- `verify-liblib-batch175.py`：13 checks（五项顺序/禁用态/行高 32/无
  long-video/比例 6 格顺序与 62 高/无 Auto/清晰度/音频数量/0 error）。
- 回归绿：21 / 22 / 26 / 33 / 128 / 149 / 155 / 160 / 165 / 166 / 172 /
  173 / 174。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 不证明：有引用/图片节点上各模式的启用规则；非 2.0 模型的菜单项差异
  （超长视频是否对部分模型出现在菜单）；长模式下参数菜单的源站形态；
  滑杆轨道视觉细节。
- 源站测试残留清理：采样用视频节点已删（0 残留）。
