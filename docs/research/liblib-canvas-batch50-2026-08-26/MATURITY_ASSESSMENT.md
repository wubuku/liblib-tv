# Batch 50 成熟度评估

## 结论

Batch 50 已达到 **Director workspace shell 的 clone-owned 有界成熟原型**：

- 侧栏折叠/恢复与 viewport 扩展有真实 UI 状态和几何断言；
- mobile drawer 互斥、collapsed recovery 和无溢出有真实浏览器断言；
- workspace focus owner、page keyboard isolation、editable-target guard 和
  Escape 层级有 focused Playwright 覆盖；
- 相关对象、选中态、时间轴、active camera、capture payload 不因 shell
  collapse 改变；
- desktop/mobile 截图、一次性视觉识别、实施记录和成熟度文件已闭环。

这不是 LibTV source-exact 的结论。Batch 50 的 LibTV authenticated source
证据仍是 `UNKNOWN`，本批主要借鉴固定上游
`storyai-3d-director-desk@8c8bd36` 的 shell/keyboard 结构，并将其收敛为
当前 clone 可验证的 bounded contract。

## 已达成

| 能力 | 结论 | 证据 |
|---|---|---|
| desktop collapse | 达成 | `aria-hidden`、`display:none`、viewport `932 -> 1440` |
| desktop restore | 达成 | viewport x/width 恢复到 `220/932` |
| mobile drawer ownership | 达成 | tree/Inspector 单一 open，Escape 关闭 |
| collapsed mobile recovery | 达成 | 打开 drawer 自动恢复 expanded |
| focus ownership | 达成 | workspace root `role=dialog` + activeElement |
| keyboard isolation | 达成 | Tab/Space/Delete/Ctrl+Z 不穿透普通画布 |
| editable target guard | 达成 | Inspector input 不触发普通画布行为 |
| Escape layering | 达成 | drawer/export/workspace 分层关闭 |
| visual evidence | 达成 | 四态截图 + contact sheet + screenshot ledger |

## 保留风险

1. **Source parity risk**：未重新取得 LibTV Director shell 的 exact DOM/CSS；
   不能把“全屏”、ARIA role、rail 尺寸或动画写成源站事实。
2. **Focus trap risk**：workspace root 是 focus owner，但没有实现完整 modal
   focus trap，也没有声明已达到源站 focus management parity。
3. **Mobile reachability risk**：drawer 打开时覆盖部分 viewport toolbar；验证
   和交互路径要求先 Escape 收起 drawer，再操作被覆盖的工具栏命令。
4. **Persistence risk**：collapsed flag 是 session-local Director UI state，
   没有写入普通 canvas graph、history 或远端 project persistence。
5. **Regression risk**：Batch 9/10 等图片浮层历史合同仍未被本批更新；Director
   shell 稳定不等于普通 LibTV canvas parity 已完成。

## 是否可以转回普通画布

可以开始规划下一批普通画布任务，但不应宣布 Director 全域完成。建议保留
Director 的后续队列：

- source freshness 复核 Director shell 的“全屏”真实语义；
- 若有新 source evidence，再补 focus trap、drawer layering 和 exact CSS；
- Director 其它新能力只有在具备 source/clone/fixture/verifier 四层入口时
  才继续扩展。

当前最高价值的跨路线下一项，是回到普通画布图片节点的上下双浮层定位和
selected-node overlay parity；它直接对应用户此前指出的“上面工具条、下面
面板位置乱”的核心问题，但应另立 batch，不得把 Batch 50 的 Director
合同当成普通画布合同。
