"use client";

import { useEffect, useRef } from "react";

export interface CanvasContextMenuTarget {
  x: number;
  y: number;
  variant: "pane" | "node";
}

interface CanvasContextMenuProps {
  target: CanvasContextMenuTarget;
  canUndo: boolean;
  canRedo: boolean;
  onUpload: () => void;
  onSaveSelectionToAssets: () => void;
  onAddNode: () => void;
  onUndo: () => void;
  onRedo: () => void;
  onPaste: () => void;
  onCopyNode: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
  onCopyToClipboard: () => void;
  onClose: () => void;
}

const itemClass =
  /* Batch 179: 文字对齐源站 token --canvas-controls-text (#fff)。 */
  "flex h-8 w-full shrink-0 items-center justify-between rounded-lg px-2 text-[13px] text-[var(--canvas-controls-text,#fff)] transition-colors duration-100 disabled:cursor-default disabled:opacity-30 enabled:hover:bg-white/[0.07]";

const shortcutClass = "ml-6 whitespace-nowrap text-xs opacity-40";

const dividerClass = "mx-2 h-[0.5px] shrink-0 bg-[#363636]";

/* 源站节点菜单「复制节点/创建副本」标签后的 14px 问号提示图标（2026-09-07 采样）。 */
const infoGlyph = (
  <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="ml-1 opacity-35">
    <circle cx="7" cy="7" r="6" stroke="currentColor" strokeWidth="1.2" />
    <text x="7" y="10.5" textAnchor="middle" fill="currentColor" fontSize="9" fontWeight="500" fontFamily="sans-serif">
      ?
    </text>
  </svg>
);

/**
 * Batch 172/173: 源站画布右键菜单（2026-09-07 CDP 采样）。
 * 结构：全屏透明点击层 + fixed 于点击点的菜单容器
 * `min-width: 196px; padding: 8px; gap: 4px; border-radius: 16px;
 * background: #262626; border: 0.5px solid #363636`。
 * pane 变体六项：上传/保存到我的资产/添加节点/撤销⌘Z/重做⇧⌘Z/粘贴⌘V；
 * node 变体七项：保存到我的资产/创建主体/复制节点⌘C/创建副本⌘D/粘贴⌘V/
 * 删除⌘⌫/复制到剪贴板（两组 0.5px 分隔线）。
 */
export function CanvasContextMenu({
  target,
  canUndo,
  canRedo,
  onUpload,
  onSaveSelectionToAssets,
  onAddNode,
  onUndo,
  onRedo,
  onPaste,
  onCopyNode,
  onDuplicate,
  onDelete,
  onCopyToClipboard,
  onClose,
}: CanvasContextMenuProps) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.stopPropagation();
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown, true);
    return () => window.removeEventListener("keydown", handleKeyDown, true);
  }, [onClose]);

  return (
    <>
      {/* Batch 365: 菜单开着时, 在菜单外右键**关不掉菜单**。
          现象: backdrop 的 onContextMenu 确实调了 onClose(实测时序是「先关后开」),
          但**同一事件继续被 React Flow 接住**, onPaneContextMenu/onNodeContextMenu
          在新位置把菜单又打开了 —— 实测菜单从 (1123,738) variant=pane 变成
          (300,250), 用户右键想取消, 菜单反而跟着鼠标跑。

          根因不是「忘了 stopPropagation」: React 17+ 把所有事件委托到 root,
          `elementFromPoint` 明明返回 backdrop(z-62, 高于 pane 的 z-1), 事件却仍
          命中 `.react-flow__pane` —— 说明 React Flow 的 handler 在**祖先的委托
          阶段**就已经跑完了, 子元素上的 `event.stopPropagation()` 拦不住。
          实测在 pane/main/body 上都挂了原生监听, 第二次右键三个全中, backdrop
          **一个都没中**。

          修法: 用**捕获阶段**的原生监听拦在 React 之前。React 17+ 的委托在
          bubble 阶段, capture 先跑, 所以这里能真正截断。
          注意用 useEffect + addEventListener 而不是 JSX 的 onContextMenu ——
          JSX 版本走的是 React 自己的委托, 拦不住。 */}
      <Backdrop onClose={onClose} />
      <div
        data-canvas-context-menu
        data-canvas-context-variant={target.variant}
        className="fixed z-[63] flex min-w-[196px] flex-col gap-1 rounded-2xl border-[0.5px] border-[#363636] bg-[#262626] p-2 shadow-[var(--canvas-shadow-menu)]"
        style={{ left: target.x, top: target.y }}
      >
        {target.variant === "pane" ? (
          <>
            <button type="button" data-canvas-context-item="上传" className={itemClass} onClick={onUpload}>
              <span>上传</span>
            </button>
            <button
              type="button"
              data-canvas-context-item="保存到我的资产"
              className={itemClass}
              disabled
              onClick={onSaveSelectionToAssets}
            >
              <span>保存到我的资产</span>
            </button>
            <button type="button" data-canvas-context-item="添加节点" className={itemClass} onClick={onAddNode}>
              <span>添加节点</span>
            </button>
            <div className={dividerClass} />
            <button
              type="button"
              data-canvas-context-item="撤销"
              className={itemClass}
              disabled={!canUndo}
              onClick={onUndo}
            >
              <span>撤销</span>
              <span className={shortcutClass}>⌘Z</span>
            </button>
            <button
              type="button"
              data-canvas-context-item="重做"
              className={itemClass}
              disabled={!canRedo}
              onClick={onRedo}
            >
              <span>重做</span>
              <span className={shortcutClass}>⇧⌘Z</span>
            </button>
            <div className={dividerClass} />
            <button type="button" data-canvas-context-item="粘贴" className={itemClass} onClick={onPaste}>
              <span>粘贴</span>
              <span className={shortcutClass}>⌘V</span>
            </button>
          </>
        ) : (
          <>
            <button
              type="button"
              data-canvas-context-item="保存到我的资产"
              className={itemClass}
              disabled
              onClick={onSaveSelectionToAssets}
            >
              <span>保存到我的资产</span>
            </button>
            <button
              type="button"
              data-canvas-context-item="创建主体"
              className={itemClass}
              disabled
              onClick={onSaveSelectionToAssets}
            >
              <span>创建主体</span>
            </button>
            <div className={dividerClass} />
            <button type="button" data-canvas-context-item="复制节点" className={itemClass} onClick={onCopyNode}>
              <span className="flex items-center">
                复制节点
                {infoGlyph}
              </span>
              <span className={shortcutClass}>⌘C</span>
            </button>
            <button type="button" data-canvas-context-item="创建副本" className={itemClass} onClick={onDuplicate}>
              <span className="flex items-center">
                创建副本
                {infoGlyph}
              </span>
              <span className={shortcutClass}>⌘D</span>
            </button>
            <button type="button" data-canvas-context-item="粘贴" className={itemClass} onClick={onPaste}>
              <span>粘贴</span>
              <span className={shortcutClass}>⌘V</span>
            </button>
            <button type="button" data-canvas-context-item="删除" className={itemClass} onClick={onDelete}>
              <span>删除</span>
              <span className={shortcutClass}>⌘⌫</span>
            </button>
            <div className={dividerClass} />
            <button
              type="button"
              data-canvas-context-item="复制到剪贴板"
              className={itemClass}
              onClick={onCopyToClipboard}
            >
              <span>复制到剪贴板</span>
            </button>
          </>
        )}
      </div>
    </>
  );
}

/** Batch 365: backdrop 用**捕获阶段**的原生监听, 而不是 JSX 的 onContextMenu。
 *
 *  为什么不能直接写 JSX: React 17+ 把事件委托到 root 的 bubble 阶段,
 *  而 React Flow 的 pane handler 也在同一棵委托树上跑 —— 子元素上的
 *  `event.stopPropagation()` 拦不住它。实测(菜单开着时):
 *  `document.elementFromPoint(300,250)` 返回 backdrop(z-62, 高于 pane 的 z-1),
 *  但在 `.react-flow__pane` / `main` / `body` 上挂的原生监听**全都收到**了
 *  contextmenu, backdrop 自己反而没收到。
 *
 *  捕获阶段先于 React 的冒泡委托跑, 所以在这里 `stopPropagation` 才真正有效。
 */
function Backdrop({ onClose }: { onClose: () => void }) {
  // Batch 365: `onClose` 是 page.tsx 里内联箭头函数, **每次渲染都是新引用**。
  // 直接把它放进 useEffect 依赖, 每次父组件重渲染都会 cleanup + 重新注册 ——
  // 在「刚打开菜单 -> onClose 改变 -> 卸载重挂」的那个窗口里, 监听可能短暂缺席,
  // 右键就会漏过去。用 ref 固定回调, 让监听只挂一次。
  const closeRef = useRef(onClose);
  // ⚠️ 不能在 render 期写 `closeRef.current` —— react-hooks/refs 判它为
  // 「render 期间访问 ref」，因为 React 无法保证组件在该变化后重渲染。
  // 挪进 effect 是安全的：这个 ref 只被下面的 document 级事件监听器读取，
  // 而那些回调必然在 commit **之后**才可能触发，不会早于这次 effect。
  // （本条是解除 `npm run check` 门禁的最小修复，不改任何行为。）
  useEffect(() => {
    closeRef.current = onClose;
  });

  useEffect(() => {
    // 菜单本体在 backdrop 之上(z-63), 点菜单项时 target 在菜单里而不是 backdrop
    // 上。**必须放行** —— 早先版本在 document 上无条件 preventDefault +
    // stopPropagation, 把菜单项自己的 onClick 也吃掉了, 结果 batch172
    // 「点添加节点 -> 菜单关 + 打开添加节点面板」、batch173「复制」两条直接回归。
    const insideMenu = (event: MouseEvent): boolean => {
      const menu = document.querySelector("[data-canvas-context-menu]");
      return !!menu && menu.contains(event.target as Node);
    };

    const onContextMenu = (event: MouseEvent) => {
      if (insideMenu(event)) return;
      event.preventDefault();
      // 阻止事件继续冒泡到 React Flow 的 onPaneContextMenu —— 它挂在 document
      // 捕获阶段且注册更早(React Flow 在 `main` 下, 属于另一个 React 根),
      // 由它把菜单在新位置重开。
      //
      // **不要**加 `stopImmediatePropagation`: 它只停掉「同一节点上其他监听器」,
      // 而 React 的委托监听在子节点上, 照样收得到。实测对照:
      //   stopPropagation             -> pane 收到 0 次, 菜单关闭 ✅
      //   stopPropagation + immediate  -> pane 收到 1 次, 菜单重开 ❌
      event.stopPropagation();
      closeRef.current();
    };
    // 左键点外面 -> 立刻关(用户预期)。
    // 右键点外面 -> **不在 mousedown 关**: 浏览器右键会接着派发 contextmenu,
    // 而 mousedown 就关的话 backdrop 先卸载, 随后的 contextmenu 落到已消失的
    // backdrop 之后, 直接命中 .react-flow__pane 被 React Flow 在新位置重开
    // (实测菜单从 1123,738 跳到 300,250)。右键的关闭只交给 contextmenu。
    const onMouseDown = (event: MouseEvent) => {
      if (insideMenu(event)) return;
      event.preventDefault();
      event.stopPropagation();
      if (event.button !== 2) closeRef.current();
    };
    // 挂在 document 的捕获阶段: backdrop 自己虽然在最上层, 但 React Flow 的
    // pane 在另一个 React 根里, 从 document 捕获最稳。
    document.addEventListener("contextmenu", onContextMenu, true);
    document.addEventListener("mousedown", onMouseDown, true);
    return () => {
      document.removeEventListener("contextmenu", onContextMenu, true);
      document.removeEventListener("mousedown", onMouseDown, true);
    };
  }, []);

  return <div data-canvas-context-backdrop className="fixed inset-0 z-[62]" />;
}
