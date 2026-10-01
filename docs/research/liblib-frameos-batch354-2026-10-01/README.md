# Batch 354 — 门禁的「贫瘠环境」假设，以及同一颗哑弹的 8 处漏网

日期：2026-10-01
范围：`scripts/verify-frameos-batch352.py`、8 个自带监听器的验证器
性质：**CLONE_DECISION**（验证基础设施；不改任何产品行为）

---

## 问题一：我的门禁依赖「我 shell 里恰好有 node」

Batch 353 收尾时的全量回归里，`batch352` 挂了：

```
FileNotFoundError: [Errno 2] No such file or directory: 'node'
```

单独手跑能过，**进门禁就挂** —— 因为 `run-frameos-verifiers.sh` 的运行环境
只用 pyenv 的 python，**不导出 nvm 的 node 路径**。我的验证器 `subprocess` 调
`node` 时直接崩。

> **门禁必须在最贫瘠的环境里也能跑。** 把门禁的可靠性绑在调用者的 `PATH` 上，
> 等于给它留了一个「在我这儿好好的」型故障。

修：`find_node()` 按 `LIBLIB_NODE` → `PATH` → `~/.nvm/versions/node/*/bin/node`
→ homebrew → `/usr/local/bin` 逐级探测，找不到才报错退出。
验证方式刻意做了「**贫瘠环境演练**」：
`env PATH="/usr/bin:/bin:...:$HOME/.pyenv/versions/3.10.6/bin"`（不含 node）实跑通过。

## 问题二：同一颗哑弹还有 8 处漏网

Batch 351 修的是「错误收集把浏览器中止的请求当成应用错误」，当时只改了
**两处**：共享的 `frameos_verify_common.attach_errors` + `batch333` 自己内联的
那份。

但全量回归里 **batch327 又以 `diagnostics:zero` 失败** —— 查下去发现
**frameos 套件里有 10 个验证器各自带一份内联 `requestfailed` 监听器**
（133 / 134 / 327 / 328 / 329 / 330 / 331 / 332 / 333 / 351），
其中 **8 个**（除已修的 333/351）仍在把 `net::ERR_ABORTED` 当应用错误。

> Batch 351 的教训在这次被放大：**修了「一处漏网」不等于修了「这类问题」。**
> 判据应该放在**单一出处**并让所有副本都引用它，而不是逐个打补丁。

全部 8 个已接入 `is_dev_server_noise`（单一出处），并逐个实跑确认：

| 验证器 | 结果 |
|---|---|
| 133 / 134 | 10 / 7 checks PASS |
| 327 | 14 checks PASS |
| 328 / 329 / 330 / 331 / 332 | 17 / 23 / 22 / 19 / 17 checks PASS |

## 过程中的一个自伤

批量注入时，我加的 `sys.path.insert(...)` 用了**没导入的 `sys`**。
`py_compile` **抓不到**这种运行时 `NameError` —— 编译通过、实跑才炸
（`batch328: NameError: name 'sys' is not defined`）。

7 个文件都缺 `import sys`，全部补齐后**逐个实跑**（不再只靠编译检查）。

> **`py_compile` 只保证语法，不保证名字存在。** 批量改动后必须**实跑**，
> 尤其是给别人的文件注入代码时 —— 我这两轮都栽在「以为编译过了就等于能跑」。

## 验证

- `verify-frameos-batch352.py`：贫瘠环境下 **7 checks PASS**
- 8 个改动的验证器：全部实跑 PASS
- 全量回归见 checkpoint

## 遗留

- 同样的内联监听器在 **liblib / jimeng / director** 套件里可能也存在，
  本批只清了 frameos 一条线。判据已是单一出处，推广是机械工作。
- 门禁的**运行环境约定**（`LIBLIB_BASE_URL`、python 解释器、node 位置）
  目前靠各验证器自己兜底。更彻底的做法是让套件 runner 统一注入一份环境，
  否则每个新验证器都要各自重造一遍「怎么找到工具链」。
