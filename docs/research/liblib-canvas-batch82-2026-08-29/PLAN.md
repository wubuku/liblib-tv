# Batch 82 计划：Director 本地资源生命周期纵切

> 状态：`COMPLETED` / `RECORDED_PASS`。
>
> 建档日期：2026-08-29。
>
> 实施 checkpoint：`8c959de`；实施结果见本目录 `IMPLEMENTATION.md`。

## 1. 任务排序

| 优先级 | Slice | 价值 | 风险 |
|---|---|---|---|
| P0 | descriptor/provenance/status authority | 让资源状态可观察、可验证、可恢复 | 低 |
| P0 | loader/materialization lease | 让本地 OBJ/FBX 不再永远是假 proxy | 中 |
| P0 | failure/retry/cancel/release | 防止失败资源和延迟结果污染场景 | 中 |
| P1 | library UI feedback | 让用户和 agent 能发现当前状态 | 中 |
| P1 | focused verifier + gate integration | 防止 resource lifecycle 回归 | 低 |

## 2. 预定实现

1. 新增纯资源生命周期模块，定义 descriptor、attempt、status、failure reason、
   lease 和 terminal transition；
2. 扩展本地模型导入结果，记录 MIME/size/lastModified/extension 和 session-only
   locator；
3. 使用 Three.js `OBJLoader`/`FBXLoader` 做有限的真实本地 materialization；
4. 在 `DirectorViewport` 中以资源状态选择真实 parsed object、loading proxy、
   failed proxy 或 canceled placeholder；
5. 资源完成、失败、取消和删除都检查当前 owner、asset identity 和 attempt；
6. 将 UI feedback 控制在模型库卡片和场景对象的可观察属性，不引入新的全局
   toast 系统；
7. 用 pure Node corpus + fresh BrowserContext 验证本批状态机和实际页面路径。

## 3. 保守决策

| 未决问题 | 本批默认 |
|---|---|
| 文件 bytes 的持久化 | 继续沿用现有 clone local catalog，明确标为 session/local prototype；不进入 portable project |
| parser 支持 | OBJ/FBX，其他类型继续拒绝 |
| 解析失败时场景显示 | 保留 proxy 并显示 failed 状态，不移除用户已加入的对象 |
| 重试语义 | 新 attempt，保留同一 resource ID |
| 取消语义 | 终止当前 attempt，资源回到 `canceled`，不写 project history |
| 删除语义 | 复用既有 resource delete planner；有引用时仍遵守 BLOCK/CASCADE |
| remote/cloud | 不实现 |

## 4. 验证矩阵

| Case | 断言 |
|---|---|
| valid descriptor | accepted + stable resource ID |
| invalid extension | rejected, zero mutation |
| loading | not ready, no success projection |
| success | ready + parsed object |
| parse failure | failed + reason + proxy retained |
| retry | new attempt, stale previous completion ignored |
| cancel | canceled + no scene mutation |
| release | released only after lease/reachability permits |
| delete with instance | BLOCK/CASCADE follows existing contract |
| reload | catalog metadata may restore; runtime parsed object re-materializes |
| diagnostics | zero console/page/request errors |

## 5. 文档同步

- 本目录 `IMPLEMENTATION.md`；
- `docs/research/LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md`；
- `docs/research/LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`；
- `docs/research/LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`；
- `docs/research/LIBTV_FIXTURE_CATALOG.md`；
- `docs/research/VERIFICATION_LEDGER.md`；
- `docs/HARNESS.md`、`docs/AGENT_TASK_MAP.md`、`docs/index.md` 或 research index
  若入口需要更新。
