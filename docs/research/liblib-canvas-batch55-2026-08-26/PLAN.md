# Batch 55 计划：源站新鲜度复核受阻

> 对应 backlog：`LIBTV-PAR-005`
> 对应 evidence queue：`OC-EQ-001`

## 1. 研究问题

在不污染共享 LibTV 项目的前提下，补充以下当前源站证据：

1. page shell、顶部导航、底栏、drawer 和主入口是否漂移；
2. selection transition、空白点击、节点切换和 fit view 的 overlay 生命周期；
3. safe zoom 与 mobile 下的 node/toolbar/panel 几何；
4. 当前登录态是否仍能作为只读 fixture 使用。

## 2. 计划动作

| 阶段 | 动作 | 安全等级 |
|---|---|---|
| 连接 | 接管现有有头浏览器 tab，读取 URL/title/login state | 只读 |
| 页面壳 | 读取 DOM、可访问名称、computed rect 和 viewport | 只读 |
| 画布基线 | 只读取既有 selected node、toolbar、panel 和 zoom | 只读 |
| 生命周期 | 仅在已有安全状态下读取空白/selection/fit/zoom 的结果 | 低副作用，需登录态 |
| 停止 | 需要输入、生成、上传、保存、下载、连线或创建测试图时立即停止 | 强制 |

## 3. 实际阻塞

- 目标画布 URL 没有保持登录态，接管后落到 LibTV 首页；
- 当前浏览器自动化运行时存在插件版本路径不一致；
- 没有 disposable source project，因此不能通过重新登录或新建项目恢复研究；
- 用户未授权在共享项目上进行写入或不可逆操作。

## 4. 结果判定

本批不产生新的 source behavior claim：

```text
OC-EQ-001 = PARTIAL_RECORDED
LIBTV-PAR-005 = RESEARCH_FIRST
source freshness refresh = BLOCKED_BY_SOURCE_SESSION
```

已有 standard image evidence 继续有效，但只覆盖其自身 viewport、zoom
和既有选中态。

## 5. 下一步决策

1. 浏览器恢复登录态后，补未覆盖的只读 freshness slice；
2. 登录态持续不可用时，推进有本地 fixture 和 focused verifier 的
   clone-owned 高价值批次；
3. 任何需要 source mutation 的图片动作（旋转、图层分离、标注 dirty/save、
   元素编辑非空 record）继续等待 disposable source fixture。

本批不修改代码，不新增 verifier，不更新 source screenshot。
