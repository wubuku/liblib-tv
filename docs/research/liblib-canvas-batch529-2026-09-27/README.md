# Batch 529 — 素材库风格库/特效库大版面浮层

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。第六/七/八轮源站采样
> （liblib-source-exploration-2026-09-25 NOTES §132-145 + 截图 31/32/34/35）：
> 素材库启动器的两入口各自打开居中大版面浮层。此前 batch 98 只克隆了
> 启动器卡面，入口点击仅关闭面板。

## 行为合同

- 素材库入口「风格库」→ `primary:style-library` 浮层：页签
  风格广场|我的收藏|最近使用、搜索框（本地过滤标题/作者）、分类页签
  （推荐/摄影写真/电商营销/动漫游戏/风格插画/平面设计/建筑及室内设计/
  创意玩法/文创周边/小说推文）、「仅看可商用」勾选 +「全部」、16 张
  商用风格卡（标题+商用徽标+作者+热度；Seedream 5.0 pro 等，截图 31
  前两行转录，低分辨率作者名为近似）；
- 素材库入口「特效库」→ `primary:effects-library` 浮层：页签
  特效广场|我的收藏|最近使用、推荐+全部筛选行、24 张运镜预设效果卡
  （小蜜蜂运镜/穿云而入/飞跃地平线…截图 32 三行转录；前 7 张对应源站
  已加载封面，其余为源站本身的灰色未加载块）；
- 「我的收藏/最近使用」页签 → 空态「暂无素材」（新账号，截图 34/35 一致）；
- 关闭按钮与 Escape（primary-panel 分支）均可退出；原 primary:material
  启动器被替换，非叠加。

## CLONE_DECISION / SOURCE 边界

- 卡片缩略图为确定性渐变占位（源站缩略图不可下载且禁止热链）；
- 分类页签仅本地图形态——无逐卡分类映射采样，不做过滤语义；
- 仅看可商用：采样卡全为商用，勾选为无过滤的可视状态；
- 风格卡「✕」推荐消除角标未复刻（仅个别卡出现，hover 归属 SOURCE_UNCERTAIN）；
  特效卡「···」角标 + hover 收藏星已复刻。

## 附带：aged verifier 再对齐（batch 462 先例）

- 回归中发现 verify-liblib-batch15/98 的「生成历史未连接」断言自
  batch 478（2026-09-15 恢复 fixture 选择器接线）起漂移失效（两者不在
  78 项维护集内，12 天未被发现）；
- 按 batch 462 的 aged-verifier 重写先例迁移到 478 合同：history 点击 →
  `data-add-node-submenu="history"` 可见（batch 15 另需收起子菜单避免
  遮挡后续 material 入口点击）；batch 478 契约源 verifier 复跑绿。

## 内容

- `scripts/verify-liblib-batch529.py`（2 面板 24 检查）；
- `src/components/LibraryShowcasePanel.tsx`（新组件，variant 双态）；
- `src/components/MaterialLibraryPanel.tsx`（入口改为 onOpenLibrary）；
- `src/components/LeftSidebar.tsx`（挂载两浮层）；
- `src/store/uiStore.ts`（PrimaryPanel 联合类型 +style-library/effects-library）；
- `scripts/verify-liblib-batch15.py`、`scripts/verify-liblib-batch98.py`
  （aged 断言迁移，见上）；
- 回归：batch 11/15/98/116/478 全绿；`npm run lint` 0 error；
  `npm run typecheck` 此刻的 8 个错误全部位于并行开发者未提交的
  JimengGenPanel WIP（frameos/jimeng 业务逻辑在途编辑，与本批无关）。
- `runtime-audit.json`：本目录。
