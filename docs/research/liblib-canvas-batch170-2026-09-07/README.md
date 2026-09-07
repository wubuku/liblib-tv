# Batch 170 — 画布顶栏工作区重命名输入（源站 2026-09-07 顶栏采样）

## 源站事实（画布顶栏 DOM）

画布芯片左侧存在**工作区名内联输入**：`min-w-[30px] max-w-[100px]
cursor-text truncate border`（13px，透明底、hover 描边高亮），实拍值
「未命名工作区」。右列（开通会员/积分/Agent）与此前采样一致。

## 实施

- `TopNavBar` 左组在 ProjectMenu 与画布芯片之间插入
  `input[data-workspace-name]`，绑定 store 的 projectName/setProjectName。
- store 默认项目名「未命名项目」→「未命名工作区」（源站实拍）；
  batch16/17 的 4 处断言同步迁移。

## 源站重探（同期）

模型菜单仍不挂载（遮挡限流间歇出现，窗口可见期与点击时机未重叠）；
菜单选中态/300s 参数展开继续阻塞。

## 验收

- `verify-liblib-batch170.py`：8 checks（默认值/透明底/cursor-text/max-w/
  位于芯片左侧/重命名生效/0 diagnostics）。
- 相邻回归绿：16 / 17 / 100 / 103。
- `npm run check`：0 errors、8 warnings（既有基线）。
