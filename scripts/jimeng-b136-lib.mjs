// 批次 136 共用件：**拖拽建线**的半程取证仪表。
//
// 🔑 靶子：`10-tasks/connect-nodes.md:104` 记着上一次拖拽的结局 ——
//   「拖完源节点变成选中态（`1 selected`），但**节点自身没有被拖走**（canvas 位移 `[0,0]`），
//   **也没有建出连线**」。拖拽建线在这个会话里**一次都没成功过**，而它是整页文档的核心动作。
//
// 🔑 为什么这一轮**不做完整建线**：共享画布。建边会留下一个**撤不干净就永久污染别人画布**的产物。
//   ⇒ 本轮只做**半程**：按下 → 拖动 → 读预览层与候选高亮 → **松在空白处取消**。
//   零副作用，且恰好能回答「到底有没有起拖」这个真正的问题。
//
// 📌 手册已定的两条前提（批次 91）：
//   ① **要拖手柄就别先选中** —— 选中时手柄左右中点被两个 ⊕ 接管，从那里起手是「点 ⊕」；
//   ② **手柄元素本体的 `pointer-events` 永远是 `none`**，真正 `auto` 的是它的 `::before`（`40×80`）。
//      ⇒ **读元素本体的 pe 读不到想要的东西**，必须读 `getComputedStyle(el,'::before')`。

/** 读连线相关的一切：手柄、伪元素、预览层、候选高亮、边数。 */
export async function readConnect(p) {
  return p.evaluate(() => {
    const cs = (e, pseudo) => { try { return getComputedStyle(e, pseudo || null); } catch { return null; } };
    const box = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
      return { w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10, x: Math.round(r.x), y: Math.round(r.y) }; };
    // 手柄：本体 pe + ::before / ::after 的 pe 与尺寸
    const handle = (e) => { if (!e) return null; const s = cs(e), b = cs(e, '::before'), a = cs(e, '::after');
      return { testid: e.getAttribute('data-testid'), className: e.className, rect: box(e),
        本体pe: s.pointerEvents, 本体opacity: s.opacity, 本体visibility: s.visibility,
        before: b ? { pe: b.pointerEvents, w: b.width, h: b.height, content: b.content, opacity: b.opacity } : null,
        after: a ? { pe: a.pointerEvents, w: a.width, h: a.height, content: a.content } : null }; };
    const all = (sel) => Array.from(document.querySelectorAll(sel));
    // 连线预览层：React Flow 用 .react-flow__connectionline / .react-flow__connection
    const 线 = all('.react-flow__connectionline, .react-flow__connection, [class*="connection-line"], [class*="connectionline"]')
      .map((e) => ({ cls: e.className, tag: e.tagName, rect: box(e), testid: e.getAttribute('data-testid') }));
    const svg = all('.react-flow__edgelabel-renderer, .react-flow__edge, .react-flow__edges > *').length;
    // 候选高亮：选中节点上可能出现的 class 标记
    const 标记 = {};
    for (const n of all('.react-flow__node')) {
      for (const c of n.classList) if (/valid|target|connect|drop|hover/.test(c)) 标记[c] = (标记[c] || 0) + 1;
    }
    return {
      testid: Array.from(new Set(all('[data-testid]').map((e) => e.getAttribute('data-testid')))),
      边数: all('.react-flow__edge').length,
      边svg子元素: svg,
      线预览层: 线,
      节点class标记: 标记,
      选中: all('.react-flow__node.selected').map((n) => n.getAttribute('data-id')),
      // 第一个带 source 手柄的节点（优先取视口内、非时间线）
      source手柄: handle(document.querySelector('[data-testid="flow-node-source-handle"]')),
      target手柄: handle(document.querySelector('[data-testid="flow-node-target-handle"]')),
      source手柄总数: all('[data-testid="flow-node-source-handle"]').length,
      target手柄总数: all('[data-testid="flow-node-target-handle"]').length,
      加号按钮数: all('[data-testid$="connection-menu-button"]').length,
      鼠标是否按下: (() => { const e = all('.react-flow__handle'); return e.filter((x) => cs(x, '::before') && cs(x, '::before').pointerEvents !== 'none').length; })(),
    };
  });
}

/** 找一个「命中 .react-flow__pane 且不在任何节点内」的空落点（用来安全地松手取消）。 */
export async function findEmptyPane(p) {
  return p.evaluate(() => {
    const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
    for (let y = 660; y >= 90; y -= 6) {
      for (let x = 8; x <= innerWidth - 8; x += 6) {
        const h = document.elementFromPoint(x, y);
        if (h && h.classList && h.classList.contains('react-flow__pane')
          && !nodes.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return { x, y };
      }
    }
    return null;
  });
}

/** node 级 canvas 坐标（位置核对必须用它，屏上坐标随平移变）。 */
export async function canvasPos(p) {
  return p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
    return [n.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null];
  })));
}

/**
 * 建一条边（批次 136 b/c/d/e/h/s 轮逐字相同的序列，抽到这里以便批次 138 复用）。
 *
 * 📌 **两个批次的取证代码必须一模一样**，否则「对照」就不是对照
 *   （批次 137 §4.58.3 立的规）。
 *
 * 序列只有四步、**零中间点击**（批次 136 h 轮立的规）：
 *   ① 不先选中，从 source 热区 `mousedown` → 12 步拖到目标节点**可见部分**中心 → `mouseup`
 *   ② 单击边中点（前置：先读 `data-state`，已经是 `selected` 就不点，否则点一下反而会取消选中）
 *   ③ ……（本函数只做 ①，不做 ②）
 *
 * @returns {Promise<{ok:boolean, 边数:number, 计划:any, 理由?:string}>}
 */
export async function 建一条边(p) {
  const plan = await p.evaluate(() => {
    const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
      const r = n.getBoundingClientRect();
      const h = n.querySelector('[data-testid="flow-node-source-handle"]');
      const hr = h ? h.getBoundingClientRect() : null;
      return { id: n.getAttribute('data-id'), x: r.x, y: r.y, right: r.right, bottom: r.bottom,
        手柄中心: hr ? [Math.round(hr.x + hr.width / 2), Math.round(hr.y + hr.height / 2)] : null };
    });
    // 源：手柄中心**逐字**在视口内
    const 源 = nodes.find((n) => n.手柄中心 && n.手柄中心[0] > 4 && n.手柄中心[0] < innerWidth - 4 && n.手柄中心[1] > 4 && n.手柄中心[1] < innerHeight - 4);
    if (!源) return null;
    // 落点：**先判正性再算面积**（批次 137 a 轮踩过「负宽 × 负高 = 正」）
    const 落 = nodes.filter((n) => n.id !== 源.id).map((n) => {
      const L = Math.max(n.x, 4), R2 = Math.min(n.right, innerWidth - 4), T = Math.max(n.y, 66), B2 = Math.min(n.bottom, innerHeight - 66);
      const 宽 = R2 - L, 高 = B2 - T; if (!(宽 > 20 && 高 > 20)) return null;
      return { id: n.id, 面积: 宽 * 高, 落点: [Math.round((L + R2) / 2), Math.round((T + B2) / 2)] };
    }).filter(Boolean).sort((a, b) => b.面积 - a.面积);
    return { 源: { id: 源.id, 手柄中心: 源.手柄中心 }, 落: 落[0] || null };
  });
  if (!plan || !plan.落) return { ok: false, 边数: 0, 计划: plan, 理由: '找不到「手柄中心在视口内」的源，或没有合格落点' };
  await p.mouse.move(plan.源.手柄中心[0], plan.源.手柄中心[1]); await p.waitForTimeout(300);
  await p.mouse.down(); await p.waitForTimeout(250);
  for (let i = 1; i <= 12; i++) {
    await p.mouse.move(Math.round(plan.源.手柄中心[0] + ((plan.落.落点[0] - plan.源.手柄中心[0]) * i) / 12),
                       Math.round(plan.源.手柄中心[1] + ((plan.落.落点[1] - plan.源.手柄中心[1]) * i) / 12));
    await p.waitForTimeout(55);
  }
  await p.waitForTimeout(500);
  await p.mouse.up(); await p.waitForTimeout(2500);
  const 边数 = (await readConnect(p)).边数;
  return { ok: 边数 === 1, 边数, 计划: plan };
}
