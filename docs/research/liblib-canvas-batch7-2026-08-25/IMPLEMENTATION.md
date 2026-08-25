# LibTV 画布 Batch 7 实施记录

> 状态：已完成
> 最后更新：2026-08-25

## 1. 规划与证据

- 对比原站与 Batch3 clone 的整理预览截图；
- 复核当前 10 个节点的身份、尺寸和原始位置；
- 分离截图直接事实、反推坐标和 clone fallback 决策；
- 建立 Batch7 计划、整理画布规格和确认卡规格。

规划已提交并推送：

```text
263955b docs: plan LibTV organize fidelity batch
```

## 2. 源码实施

### 整理模块

新增 `src/lib/liblibOrganize.ts`：

- 当前项目 10 个已知节点使用截图反推的语义拓扑；
- 女性、咖啡馆、男性、咖啡形成左列；
- 剧本执行和 `分镜 #2` 形成中列；
- 图片组、视频组和失败视频形成右列；
- 剧本位于更右上方；
- 未知顶层节点从已知拓扑下方按稳定三列 fallback 排列；
- 有 `parentId` 的 child 保留相对 parent 坐标；
- 节点尺寸兼容 React Flow 的 `width/height` 和 `style.width/style.height`；
- viewport 根据整理后的实际横向边界计算，并限制在 `10%` 到 `52.6%`。

### 页面事务

`src/app/page.tsx`：

- 整理前保存 nodes 与当前 viewport；
- 整理时清除选择，避免节点工具条污染预览；
- 节点变更作为一个 graph history 命令入栈；
- 直接同步整理 viewport 和底部缩放百分比，不再调用旧 `fitView()`；
- “还原”恢复节点与 viewport；
- “保留”只关闭预览卡，保留后可 undo/redo。

### 确认卡

- 从底部居中横条改为桌面 `left:49px; bottom:53px`；
- 宽 `168px`、最小高 `88px`；
- 问题文案独占第一行；
- “还原”“保留”在第二行右对齐；
- 移动端使用 `left:12px; bottom:106px`，该值是没有原站移动证据时的 clone 防重叠决策；
- 增加 `data-organize-confirmation` 自动化钩子。

实现与专项验证已提交并推送：

```text
33c5f9b feat: align LibTV organize preview
```

## 3. 专项验证

```bash
python3 scripts/verify-liblib-batch7.py
```

验证通过：

- `929x874` 为 `28%`；
- 10 个关键节点 x/y 进入 `3px` 容差；
- 确认卡 x/y/宽/高进入 `1px` 容差；
- 节点数保持 `10`，边数保持 `11`；
- “还原”恢复整理前 node transform 与 viewport；
- “保留”关闭卡片并保留整理位置；
- 保留后 undo/redo 在整理前后位置间切换；
- `1440x900` 为约 `46%`；
- `390x844` 受最小缩放约束为 `10%`；
- 三个视口均无页面横向溢出；
- 控制台 error 为 0。

截图：

- `docs/design-references/liblib-clone-batch7-organize-929-2026-08-25.png`
- `docs/design-references/liblib-clone-batch7-organize-desktop-2026-08-25.png`
- `docs/design-references/liblib-clone-batch7-organize-mobile-390-2026-08-25.png`

## 4. 跨批与工程验证

以下全部通过：

```bash
python3 scripts/verify-liblib-batch4.py
python3 scripts/verify-liblib-batch5.py
python3 scripts/verify-liblib-batch6.py
python3 scripts/verify-liblib-batch7.py
npm run check
```

- lint：0 error，保留仓库既有 9 个 warning；
- TypeScript：通过；
- Next.js production build：通过；
- `/`、`/_not-found`、`/frameos`、`/frameos/canvas/[id]` 构建成功。

## 5. 接力边界

- 当前项目专属位置映射是截图复刻，不是通用自动布局算法；
- wider desktop 的按宽度放大和 mobile 的 `10%` 下限是 clone 响应式决策；
- 原站移动端确认卡位置、整理动画和动态节点算法仍没有直接证据；
- 不应据此增加整理模式菜单；FrameOS 的整理菜单不能作为 LibTV 事实；
- 后续若重新获得已登录原站浏览器控制，应优先抽取整理前后 DOM transform 和动画过程，再决定是否替换本批反推值。
