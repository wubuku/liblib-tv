# Batch 453 — VR-021 Slice C：Add Resource 多文件纵切（provisional cohort + 单次图事务）

> 状态：`IMPLEMENTATION_RECORDED`（media ingress/resource lifecycle 合同
> Slice C；本地 fixture 物化器，无 provider/存储/网络；心跳批次）。
>
> 证据：`runtime-audit.json`、
> `docs/design-references/liblib-clone-batch453-add-resource-cohort-929-2026-09-13.png`、
> `scripts/verify-liblib-batch453.py`。

## 变更

- **`canvasStore.addResourceCohort(descriptors, expectedGeneration)`
  （新动作）**：ADD_RESOURCE_MULTI 意图经 Slice A 有序校验（含世代
  过期 → MEDIA_CANVAS_STALE）；通过后逐文件走 fixture 物化器取
  SESSION_RESULT_URL locator，**一次 set() 内**创建全部节点 + 恰好
  一条 graph 历史（单次 accepted-success 图事务）；节点携带共享
  `ingressCohortId`/`ingressIndex`，File 字节从不入图状态（§6.2）。
  rejected = 稳定 reason + 零变更。
- **`AddNodePanel` 上传入口**：`data-add-node-resource="upload"` 现在
  打开真实文件选择器（隐藏多选 input，accept 图片三类）；File 在组件
  内即归约为 LOCAL_FILE 描述符；拒绝时面板以稳定 reason 文案反馈
  （如 `MEDIA_TYPE_AMBIGUOUS`），接受时显示计数并延迟关闭。

## 验收（verify-liblib-batch453.py，SCRIPT_RECORDED_PASS —— 真实文件输入）

- **accepted_cohort**：两个 PNG → 两个节点共享同一 cohortId、
  `blob:fixture-*` locator、**恰好 +1 历史**，面板反馈「已添加 2 个资源」；
- **rejected_reason_surfaces**：`application/x-unknown` 文件 → 面板
  显示 `MEDIA_TYPE_AMBIGUOUS`、节点数与历史零变更；
- **stale_generation_zero_mutation**：旧世代提交 →
  `MEDIA_CANVAS_STALE`、零产物；
- console/pageerror/requestfailed 为 0；无溢出。

## 后续（VR-021）

Slice D（生成历史/注册资产引用 attach）、Slice E（Shot 源生命周期）、
Slice F（Director data/blob 收敛）。
