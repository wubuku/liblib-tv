# 组件规格：LibTV Keyboard Shortcuts Closure

## Goal

快捷键面板必须只展示当前 LibTV 克隆真实处理的命令。原站抽取到的暂未实现的成组、连线和生成快捷键先不展示，避免“文案承诺”大于行为。

## Implemented Commands

| 命令 | Mac | Windows/Linux | 实际行为 |
|---|---|---|---|
| 复制节点和连线 | `⌘D` | `Ctrl+D` | 复制当前选中节点及关联边 |
| 新建节点 | `Tab` | `Tab` | 打开添加节点面板 |
| 撤销 | `⌘Z` | `Ctrl+Z` | 当前画布撤销 |
| 重做 | `⌘⇧Z` / `⌘Y` | `Ctrl+Shift+Z` / `Ctrl+Y` | 当前画布重做 |
| 删除 | `Delete` / `Backspace` | `Delete` / `Backspace` | 删除当前选中节点 |
| 放大 | `⌘+` | `Ctrl+Plus` | 画布放大 |
| 缩小 | `⌘-` | `Ctrl+Minus` | 画布缩小 |
| 适应画布 | `⌘0` | `Ctrl+0` | 调用 `fitView` |
| 移动工具 | `V` | `V` | 切换选择工具 |
| 抓手工具 | `H` | `H` | 切换抓手工具 |
| 整理画布 | `⌥⇧F` | `Alt+Shift+F` | 执行一次画布整理 |

## Input Guard

焦点在 `input`、`textarea` 或 `[contenteditable=true]` 时，除 `Escape` 外不触发全局快捷键。右键菜单打开时，`Escape` 优先关闭菜单，再由页面级 Escape 处理其他面板。

## Non-goals

- 不把 `Option+拖动` 在本批实现为复制拖动；
- 不展示尚未实现的成组、合并分镜组、解组、连线和生成快捷键；
- 不为浏览器默认的 `Cmd/Ctrl+C/X/V` 伪造剪贴板功能。

