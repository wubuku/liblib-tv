# Batch 504 — VR-018 catalog 收尾一致性：ProjectMenu 状态 disposition 化

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。项目菜单三个
> prototype-unavailable 项（回到主页/创建新项目/删除项目）→ rejected →
> diagnostic；全部项目 为导航项，静默关闭不产生命令反馈。catalog 增补
> project-menu surface。copy 与几何不变。

## 内容

- `src/lib/libtvCommandFeedback.ts`：catalog project-menu surface；
- `src/components/TopNavBar.tsx`：ProjectMenu 状态对象化 +
  `data-status-tone` 投影（batch 106 的 `本地原型` 文案断言兼容）；
- `scripts/verify-liblib-batch504.py`：诊断 tone ×2 + 静默导航 两场景；
- `runtime-audit.json`：本目录。
