# Batch 179 — canvas token 收割对齐 + 素材库门重探（源站 2026-09-08 直采）

## 源站事实（窗口 rAF ~31fps；`source-canvas-tokens.json` / 截图已存档）

### :root token 直采

| token | 值 | clone 现状 |
|---|---|---|
| `--canvas-controls-hover` | `#ffffff1a`（白 10%） | 芯片 hover 原为 white/9% → 已对齐 |
| `--canvas-controls-bg` | `#262626` | 与 fallback 一致 |
| `--canvas-controls-border` | `#363636` | 与 fallback 一致 |
| `--canvas-controls-text` | `#fff` | 右键菜单原 #eeeeee → 已对齐 |
| `--canvas-shadow-menu` | `0 8px 32px #00000026, 0 2px 8px #0000001a` | globals.css 逐字一致 |
| `--canvas-shadow-dropdown` | `0px 4px 10px #00000040, 0px 2px 4px #0000004d` | 一致 |
| `--canvas-shadow-panel` | `0px 2px 5px #00000026` | 一致 |
| `--z-panel` / `--z-modal` | `400` / `500` | clone 映射 z-62/63（Batch 172 决策，记录不翻转） |
| `--fg-default` / `--fg-muted` | `#f7f7f7` / `#919191` | 新增定义 |
| `--panel-background` | `#262626` | 已有 --color-background-normal |

芯片 hover 背景实测 = `rgba(255,255,255,0.1)`，与 token 值吻合。

### 素材库承诺书门重探（伦理约束维持）

- 角色库弹窗默认 公共角色库；切到 Seedance2.0&2.5合规素材库 页签时
  承诺书门（不同意 / 同意并使用）仍然拦截——与 Batch 169 的 clone 实现
  一致。**未代用户同意**，门后内容仍未采样。

## 实施

- `globals.css` 新增 token 块：`--canvas-controls-bg/-border/-text/-hover`、
  `--z-panel/--z-modal`、`--fg-default/--fg-muted`（值=源站直采）。
- 尝试芯片 hover 背景 `hover:bg-white/[0.09]` →
  `hover:bg-[var(--canvas-controls-hover)]`。
- 右键菜单项文字 `text-[#eeeeee]` → `text-[var(--canvas-controls-text,#fff)]`。

## 验收

- `verify-liblib-batch179.py`：10 checks（9 项 token 定义与值/芯片 hover
  alpha 0.1/右键菜单文字 #fff/0 console error）。
- 回归绿：21 / 22 / 26 / 33 / 128 / 149 / 155 / 160 / 165 / 166 / 169 /
  172-178（含 batch169 承诺书门合同复验）。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 不证明：`--z-header`（源站未定义/未取到）；clone z 映射切到源站真实
  z 值（涉及全站层级重构，另行立项）；承诺书门后内容。
- 源站测试残留清理：采样节点已删（0 残留）。
