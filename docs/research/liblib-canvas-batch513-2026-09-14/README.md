# Batch 513 — VR-010 Slice A：纯 graph-document codec + §9.2 确定性 corpus

> 状态：`PURE_CODEC_RECORDED_PASS`（commit 本批）。`src/lib/libtvGraphDocument.ts`
> 实现 Portable Document V1（§4 schema、§5 字段分类、§7 解析管线与 14 个
> 稳定拒绝 reason、§7.3 显式迁移链——V1 无迁移、高于 1 即
> UNSUPPORTED_FUTURE_VERSION 不降级）；写侧 runtime 白名单（selected/
> dragging/measured/style 等永不出现在 round-trip）；edge policy、
> embedded-media byte budget、document limits 全部注入式——不虚构产品数字。
> §9.2 纯 corpus 10/10 经 verify-liblib-batch513.py 驱动全绿。

## 内容

- `src/lib/libtvGraphDocument.ts`：codec + 严格读侧 + corpus runner；
- `src/app/page.tsx`：window 暴露（corpus + parse，dev-only，含对称
  cleanup）；
- `scripts/verify-liblib-batch513.py`：corpus 断言 + MALFORMED_JSON 直检；
- FIXTURE_CATALOG GRAPH-DOCUMENT 状态升级；
- `runtime-audit.json`：本目录。

## 边界

- Slice B/C/D（history isolation browser 层、import-as-new-canvas、
  export/clipboard 复用）仍未建；
- limits/budget 的产品默认值等待实测后的 clone-only 决定，当前全部
  由调用方注入。
