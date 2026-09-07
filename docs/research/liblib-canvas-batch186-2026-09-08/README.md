# Batch 186 — 视频面板 footer 图标按钮组对齐（源站 2026-09-08 直采）

## 源站事实（窗口 rAF ~32fps；`source-footer-icons.json` / 截图已存档）

- params 触发器之后依次 4 枚 32×32 图标按钮（均无 aria/title，点击语义
  未采样）：
  1. **doc-sparkle**（libtv，viewBox `0 0 20 20`，文档行 + 星芒）；
  2. **文A 翻译**（libtv，`0 0 19.71 18`）；
  3. **settings2 滑杆**（**源站自身用 lucide**，`0 0 24 24`）；
  4. 生成上箭头（libtv，`0 0 18 18`，反白 `text-btn-invert-text`）。
- credits 块位于 settings2 与生成按钮之间。

## 实施

- footer 顺序对齐：params → doc-sparkle（新增，`data-footer-icon`）→
  翻译 → settings2（新增，lucide Settings2——与源站同源）→ credits
  （ml-auto 位置不变）→ 生成。
- 字形替换：翻译 Languages → 直采文A path；生成 ArrowUp → 直采上箭头
  path（Loading/Check 状态保留）。
- 新按钮无 onClick（源站点击语义未采样，占位）；翻译按钮保留既有
  aria-label（clone 无障碍先例）。

## 验证器迁移

- `verify-liblib-batch125.py`：attempts:deselect →
  attempts:reclick-stays-selected（Batch 177 非 toggle 合同的漏迁移补齐）。
- `verify-liblib-batch21.py`：新增按钮后 footer flex 重排 + 参数触发器
  文字宽度随字体加载抖动（面板相对 x 在 119/124.16 双峰）→ 普通/长两相
  均改断言 **CSS 保证的触发器相对偏移**（普通 -68 / 长 -60，字体无关）；
  y 偏移 -245/-196.5 保持面板相对（底锚稳定）。

## 验收

- `verify-liblib-batch186.py`：8 checks（三枚图标按钮顺序/viewBox×2/
  settings2/credits 位于 settings2 与生成之间/生成箭头 viewBox/生成
  title）。
- 全量回归绿：21（三连跑）/ 22 / 26 / 33 / 125 / 128 / 149 / 155 / 160 /
  161 / 164 / 165 / 166 / 169 / 172-180 / 185。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 不证明：doc-sparkle/settings2 按钮的点击语义（源站未采样，点击可能开
  弹层或触发 AI 动作）；credits 块在源站该状态下的精确宽度。
- 源站测试残留清理：采样节点已删（0 残留）。
