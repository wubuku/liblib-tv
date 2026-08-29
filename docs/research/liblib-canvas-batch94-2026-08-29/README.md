# Batch 94：Director 焦点 containment 与键盘边界

> 状态：`FOCUSED_RUNTIME_RECORDED_PASS`
>
> 日期：2026-08-29。

本批为 clone-owned Director UI/UX reliability slice。目标是让前景 Director
工作区、移动端对象树和 Inspector 抽屉具有可复现的焦点边界，并保持现有
Escape、编辑输入框和 Director command shortcut 的优先级。

## 导航

- [`PLAN.md`](PLAN.md)：计划、证据分层、范围、停止条件和执行记录。
- [`DIRECTOR_FOCUS_CONTAINMENT.spec.md`](DIRECTOR_FOCUS_CONTAINMENT.spec.md)：焦点
  containment、回焦、inert 和键盘 ownership 合同。
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：代码变更、验证结果和未完成重复回归
  的准确边界。
- [`runtime-audit.json`](runtime-audit.json)：Batch 94 fresh desktop/mobile
  结构化运行结果。
- [`current-gate-regression.json`](current-gate-regression.json)：本批专项、
  Director current gates、普通画布继承证据和本次回归停止边界。

## 实施结果

- Director workspace 使用动态 tabbable 集合执行正向和反向循环；
- 打开 Director 后焦点进入 workspace，关闭后优先返回原入口；
- 移动端 tree/Inspector 抽屉有局部焦点循环，非活动抽屉使用
  `aria-hidden` 与 `inert`；
- backdrop、Escape 和 close button 都回焦对应触发入口；
- 移动抽屉活动时，Escape 优先关闭抽屉；桌面编辑输入框仍保留原生编辑语义；
- 专项 verifier 覆盖桌面/移动端、动态面板、焦点回退、输入框边界、ARIA、
  inert、overflow 和浏览器诊断。

## 证据边界

本批通过只证明当前 clone 的焦点与键盘可靠性合同。当前没有足够的已认证
LibTV Director DOM/CSS/runtime 证据证明源站使用同样的 focus trap、`inert`
或选择器，因此不得把本批结果描述为 source parity。

## 验证入口

```bash
LIBLIB_BASE_URL=http://localhost:4317 \
  python3 scripts/verify-liblib-batch94.py
```

固定开发端口为 `4317`。本批不写截图，不执行截图识别；已有截图分析记录继续
作为唯一视觉复核入口。
