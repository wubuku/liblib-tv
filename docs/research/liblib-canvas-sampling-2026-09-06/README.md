# LibTV 丢弃式项目采样 — 2026-09-06

> 状态:`SAMPLING_COMPLETE`(用户授权的丢弃式测试项目内完成全部操作,采样后测试项目已删除)。
>
> 环境:外部有头 Chromium for Testing 147(CDP 9222,持久 profile `~/.libtv-playwright-profile`),登录态,viewport 1920x820。
> 测试项目:spaceId=7619024(独立 workspace,与共享项目隔离),采样后已删除。

## 1. 多画布下拉(完整 CRUD)

`SOURCE_FACT`:

- 触发:顶栏当前画布名按钮(Mantine Popover,`aria-haspopup=dialog`);面板向上/下方展开,`214x117` 起步。
- 结构:`画布` 头部 + `新建画布` 按钮(aria-label=新建画布)+ 画布行列表(新画布在前)。
- 行结构:`切换到画布 {名称}`(点击切换,**URL projectId 跟随变化**)+ `更多操作`(hover 门控,`opacity-0 group-hover:pointer-events-auto`)。
- 行级菜单:**在新窗口打开 / 重命名画布 / 复制画布 / 删除画布**。
- 新建:`+` 创建 `画布 {N+1}`,新画布插入列表最前。
- 重命名:行内 input(选中全部),Enter 提交(画布 2→测试A 已验证)。
- 复制:命名 `{名称}副本{序号}`(测试A→测试A副本1),**自动切换到副本**。
- 删除:确认框 `删除画布 / 确定要删除画布「X」吗？此操作不可恢复。/ 取消 / 确认`;删除活动画布后自动切到剩余画布,URL projectId 跟随。

`CLONE_GAP`:clone CanvasTabDropdown 为旧结构(编辑草稿+行级更多),无 切换/更多操作 双按钮行、无 在新窗口打开、无确认框文案、无活动画布删除 fallback 与 URL 跟随。

## 2. 双击画布生成流

`SOURCE_FACT`:空画布上双击任意位置 → **打开添加节点面板**(与 + 按钮同一面板;并非独立自由生成输入框)。提示文案「双击画布 自由生成节点」的"自由生成"即通过该面板实现。

`CLONE_GAP`:clone 无画布双击行为。

## 3. 脚本 NEW 节点 = 脚本生成器

`SOURCE_FACT`(节点已创建并选中,350x350 卡片):

- 节点标题:**脚本生成器**。
- `尝试:` 三种模式:**剧本生成分镜脚本 / 角色生成分镜脚本 / 自己编写分镜脚本**。
- `参考图` 入口。
- Prompt placeholder:`描述剧情片段、故事，为你生成分镜脚本`。
- 模型:**GVLM 3.1**(面板内可见,数字 6 为积分/次数标记)。

`INFERENCE`:与脚本生成相关的新一代节点,面向分镜脚本产出;旧脚本节点保留为 Beta。
`CLONE_GAP`:clone 无此节点类型(BLOCKED 由本采样解锁)。

## 4. 导演台空项目入口

`SOURCE_FACT`:

- 添加面板 → `导演台(NEW)` **先在画布创建「导演台 N」节点**(350x350 卡片,描述「在3D空间中搭建场景并进行多视角截图」+ `打开导演台` 按钮),不直接进入 R3F。
- `打开导演台` → 全屏 R3F 工作区(`div[data-prevent-global-shortcut]` fixed inset-0):tabs `导演视角 / 机位视角`;左树 `场景 + 搜索场景对象 + 机位1 + 角色A + 重置视角`;右侧 Inspector `角色/属性/姿势` tabs(名称/位置 XYZ/旋转 XYZ/缩放 XYZ/统一缩放/颜色);顶部 `关闭`、`截图` 按钮。
- 默认场景:**机位1 + 角色A**(与 clone 默认一致)。
- 退出:顶部 `关闭` 按钮(aria-label=关闭)。

`CLONE_GAP`:clone 从添加面板直接进入 R3F 工作区(无画布节点卡),入口行为不同;工作区内部结构一致度高。

## 5. 交互环境备注

- 站点有**单画布单编辑者保护**:同 project 在第二处打开时出现 `data-practice-ui` 遮罩「会话已过期…请刷新页面以继续编辑」。
- 项目菜单的 删除项目 确认框与 画布删除 确认框同构(`此操作不可恢复`)。
- 自动化点击对 Mantine hover 门控按钮(更多操作)无效,需先 hover 行或用 `el.click()` 绕过 pointer-events。

## 截图索引

| 文件 | 内容 |
|---|---|
| `s1-dropdown-1canvas.png` | 单画布下拉 |
| `s1-dropdown-2canvas.png` | 新建画布后下拉 |
| `s1-dropdown-row2-hover.png` | 行 hover |
| `s1-row-more-menu.png` | 更多操作菜单 |
| `s1-after-rename-duplicate.png` | 重命名/复制过程 |
| `s1-delete-confirm.png` | 删除画布确认框 |
| `s1-after-delete.png` | 删除后状态 |
| `s2-after-dblclick.png` / `s2-dblclick-locator.png` | 双击前后 |
| `s3-script-new-node.png` / `s3-node-selected.png` | 脚本生成器节点 |
| `s4-director-entry.png` / `s4-director-workspace.png` | 导演台入口与工作区 |
| `s5-after-cleanup.png` | 测试项目删除后 |
