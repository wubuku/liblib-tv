# Batch 351 — 门禁分不清「应用抛错」与「浏览器中止的请求」

日期：2026-10-01
范围：`scripts/frameos_verify_common.py`（共享）、`scripts/verify-frameos-batch333.py`
性质：**CLONE_DECISION**（验证基础设施修正；不涉及产品行为）

---

## 问题

`verify-frameos-batch333.py` 的 `diagnostics:zero` **连续三轮**在全量套件里失败、
重试也失败；但同一份代码在**隔离跑 5+ 次、6 路并发 3 次、重编译扰动 3 次全部通过**。

三轮套件分别挂了不同的批次（首轮 171/172/221/327/333，次轮 208/209/333，
第三轮 216/220/221/327/333），但 **batch333 三次都在**，且失败点始终是
`diagnostics:zero`——一条「控制台零错误」的断言。

### 抓证据的过程（两次都失败，值得记）

1. **第一次**在失败前 `print` 诊断 → 被
   `run-frameos-verifiers.sh` 的 `echo "$out" | tail -5` **截掉了**。
2. **第二次**改成写文件 → 拿到原文。

> 门禁失败时，能看到的信息恰恰是最少的。**诊断必须写到不会被截断的地方**
> （文件），不要 print 到会被 `tail` 截掉的 stdout。

### 原文

```
requestfailed:GET:.../_next/static/chunks/%5Bturbopack%5D_browser_dev_hmr-client_....js:net::ERR_ABORTED
requestfailed:GET:.../_next/static/chunks/Documents_wubuku_liblib-tv_src_....js:net::ERR_ABORTED
requestfailed:GET:http://localhost:4317/images/frameos/node-vid-cover-2.jpg:net::ERR_ABORTED
requestfailed:GET:http://localhost:4317/images/frameos/node-image-1.png:net::ERR_ABORTED
```

**全部是 `net::ERR_ABORTED`** —— 浏览器**主动取消**的请求，不是服务器或应用失败。
两个来源：

1. **Turbopack HMR chunk**：别的 session 改源文件触发重编译，旧 hash 的 chunk
   失效，飞行中的请求被中止；
2. **`/images/frameos/*.jpg|png`**：batch333 专门测**跨刷新持久化**，
   密集 `page.reload()`，飞行中的图片请求随导航被取消。

### 一个必须先查清的细节

抓到的条目**没有 `console:error:` 前缀**——说明它们**不来自**共享的
`attach_errors`（那个会给 console 事件加前缀），而是 batch333 **自己内联**的
`requestfailed` 监听器（第 99–102 行）。所以要收口**两处**，只改共享函数是不够的。

## 修法

`is_dev_server_noise()` 判定「这条错误是不是开发服务器基础设施噪音」，
放在 `frameos_verify_common.py` 作为**单一出处**，两处监听器都用它。

判据刻意用「**中止**」而不是路径白名单：

> 被中止的请求**不携带任何关于服务端或应用健康状况的信息**——应用自己用
> `AbortController` 取消的请求同理，那是应用主动要求的取消。
> 而 404 / 500 / 连接失败**不是** ERR_ABORTED，它们照旧计入。

## 验证：这是一个**反向测试**

只测「噪音被过滤」的修复，很可能顺手把真错误也滤掉。所以
`scripts/verify-frameos-batch351.py` 的重点是**证明门禁没被削弱**：

| 断言 | 作用 |
|---|---|
| `pure:*`（8 条） | 分类器逐例判定：3 类中止=噪音；连接失败/域名解析失败/404/`pageerror`/`console.error`=真错误 |
| `catch:console-error` | 真实 `console.error` **必须**被抓到 |
| `catch:pageerror` | 真实未捕获异常 **必须**被抓到 |
| `catch:http-404` | 真实 404 **必须**被抓到 |
| `filter:err-aborted` | 真实 `ERR_ABORTED` **必须被过滤** |
| `anti-false-green:abort-really-happened` | 另挂**不经过滤的原始监听器**做对照，确认事件真的发生了 |
| `anti-false-green:clean-start` | 干净起点下错误列表就是空的 |

**15 项检查，0 诊断。**

### 双向变异测试（门禁改动必须两个方向都测）

| 变异 | 结果 |
|---|---|
| A: 撤销过滤（`return False`，= 修复前） | 红：`pure:hmr_chunk_aborted is_noise=False want=True` |
| B: **过滤过头**（`return True`，真错误也被吞） | 红：`pure:not_found is_noise=True want=False` |

> 只做变异 A 是不够的：那只能证明「测试抓得住没修」，
> 抓不住「修过头把门禁掏空」。**门禁类改动必须双向变异。**

### 防假绿自检踩的坑

`anti-false-green:abort-really-happened` 第一次失败了（saw=0）。原因是我用
**页内 `console.error` 猴补丁**去抓原始事件做对照——但 `requestfailed` 是
**浏览器**发出的，**不经过页面的 `console.error`**，所以对照恒为空，
「被过滤」这条就成了空断言。

改成另挂一个**不经过滤的原始 `requestfailed` 监听器**（同一个事件、两个收集器）
之后才有真正的对照。

> 防假绿自检本身也会写错。**自检失败时要先怀疑自检**，而不是相信「那大概是个 bug」。

## 影响面

`attach_errors` 被 86 个 frameos 验证器共用。收窄的是「**浏览器中止的请求**」
这一类，其余（`console.error` / `pageerror` / 404 / 连接失败）全部照旧计入，
由上面的反向测试逐条兜住。

## 保真度差距

无。本批只改验证基础设施，不动任何产品行为。
