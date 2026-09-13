# Batch 450 — VR-021 Slice A：纯 media-ingress 描述符/入口注册表/有序校验

> 状态：`IMPLEMENTATION_RECORDED`（media ingress/resource lifecycle 合同
> 首个 runtime 切片；纯模型、无 UI/store 集成；心跳批次）。
>
> 证据：`runtime-audit.json`、
> `docs/design-references/liblib-clone-batch450-ingress-registry-929-2026-09-13.png`、
> `scripts/verify-liblib-batch450.py`。

## 变更

- **`src/lib/libtvMediaIngress.ts`（新，纯模块）**：
  - §5 十项入口 profile 注册表（ADD_RESOURCE_MULTI …
    DIRECTOR_LOCAL_MODEL_IMPORT），每项声明基数（min/max，null=无上界）、
    目标与投影政策；
  - §6.2 LOCAL_FILE 描述符；§8.1 客户端有序校验（步骤 1–6：
    profile/基数 → 画布/世代 → 描述符形状 → 空文件 → 族分类 →
    克隆专用字节预算）；探针/物化（步骤 7–11）归 Slice B；
  - §8.3 稳定 reason 族（MEDIA_ENTRY_PROFILE_INVALID、
    MEDIA_CARDINALITY_EXCEEDED、MEDIA_EMPTY、MEDIA_CANVAS_STALE、
    MEDIA_TARGET_MISSING、MEDIA_SOURCE_DESCRIPTOR_INVALID、
    MEDIA_TYPE_AMBIGUOUS、MEDIA_TYPE_UNSUPPORTED、MEDIA_SIZE_EXCEEDED），
    按校验顺序全部报告、去重；
  - 族分类规范策略：MIME 前缀 → 扩展名回退（octet-stream）→ unknown；
    各族克隆专用预算显式标注非源站限制（§8.2）。
- **page.tsx**：只读 window 诊断暴露（注册表 + 校验器）。

## 验收（verify-liblib-batch450.py，SCRIPT_RECORDED_PASS）

- 注册表 10 项、GENERATED_HISTORY_ATTACH 基数上界 10；
- 合法 ADD_RESOURCE_MULTI 图片意图 → accepted（family=image、零 reason）；
- 空/未知 profile/超基数/世代过期/画布缺失/非法描述符/空文件/未知族/
  无预算族/超预算 —— 逐项命中稳定 reason；
- 多因场景按校验顺序报告
  [MEDIA_CANVAS_STALE, MEDIA_EMPTY, MEDIA_SOURCE_DESCRIPTOR_INVALID]；
- console/pageerror/requestfailed 为 0；无溢出。

## 后续（VR-021）

Slice B（instance 租约台账 + fake materializer）、Slice C（Add Resource
多文件纵切）。
