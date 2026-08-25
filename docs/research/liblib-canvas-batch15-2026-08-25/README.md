# Batch 15：添加节点菜单语义与音频入口

> 日期：2026-08-25
> 范围：LibTV clone 的“添加节点”菜单和音频/素材库入口。
> 目标：修复入口标签与实际创建行为不一致的问题，并复刻原站菜单的高置信结构。

## 当前缺口

- “音频”入口实际调用 `addNode("text")`，会创建文本节点。
- “素材库”入口实际调用 `addNode("image")`，会创建图片节点。
- 菜单中的脚本/素材库右箭头没有表达任何后续动作。
- 上传和从生成历史选择是死按钮，没有本地原型反馈。
- 当前 `AddNodePanel.spec.md` 仍是旧版 8 项网格合同，与已保存原站截图和当前 9 项竖向菜单不一致。

## 证据入口

- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：原站添加节点截图一次性识图。
- [`ADD_NODE_MENU.spec.md`](ADD_NODE_MENU.spec.md)：菜单与入口行为合同。
- [`../liblib-live-2026-08-25/README.md`](../liblib-live-2026-08-25/README.md)：原站入口面板总审计。
- [`../liblib-seedance-2.5-2026-08-25/live-script-string-evidence.json`](../liblib-seedance-2.5-2026-08-25/live-script-string-evidence.json)：音频、脚本、素材库和专用节点字符串证据。

## 边界

- 音频节点只实现前端原型卡片，不解析真实音频、不播放和不上传。
- 素材库子入口复用已有本地素材库面板，不假造账户资产。
- 导演台节点的深层视觉没有足够证据，本批不把现有导演台 renderer 重写成 3D 场景。
- 画布下拉和项目名元数据留到后续批次，不与本批混杂。

## 导航

- [`PLAN.md`](PLAN.md)
- [`ADD_NODE_MENU.spec.md`](ADD_NODE_MENU.spec.md)
- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)

