// 批次 135 共用件：缩放归位、框选、多选工具条读数。
//
// 🔑 本批要回答的唯一问题：**多选工具条的宽度到底跟谁走** ——
//   跟画布缩放？还是跟选中集？
//
//   手册现状（批次 87 已订正归因，但**实验有两个自变量一起动**）：
//     organize-group-layout.md:70 「工具条宽度不是固定值：同一天两次实测分别为
//       511×40（缩放 74%）与 1298×40（缩放 100%），计数项也从 54×32 变成 256×40」
//     批次 87 自己写「**只改缩放，选中集跟着变**，但分别记下」并列出
//       74% / 选中 7 个 与 60% / 选中 8 个 —— **选中集不是受控量**。
//   ⇒ 「宽度随缩放变」与「宽度由选中集撑开」这两个解释，**至今没被单自变量实验分开过**。
//
// ⚠️ 缩放归位纪律（批次 131/134 两次教训）：
//   ① 缩放菜单**没有 60% 档**（只有 50/100/200 + 三个动作）⇒ 归位只能走**输入框**；
//   ② **任何缩放操作都会关掉小地图**（批次 134 受控实验，三次独立复现）⇒ 收尾必须重开；
//   ③ 缩放后要**连读两次** zoom aria 才算数。
import { keyGuard } from './jimeng-safe-keys.mjs';

export const PORT = 9444;

/** 接上已有的独立 Chrome，只 pin 视口，不导航。 */
export async function openCanvas() {
  const { chromium } = await import('playwright');
  const b = await chromium.connectOverCDP(`http://127.0.0.1:${PORT}`);
  const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
  if (!p) throw new Error('找不到画布页');
  const { pinViewport } = await import('./jimeng-safe-keys.mjs');
  await pinViewport(p);
  return { b, p };
}

export const readers = (p) => ({
  zoom: () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; }),
  status: () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]),
  selCount: () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length),
  // ⚠️ 不把 role=tooltip 算进浮层（批次 133 教训：那是鼠标悬停的瞬时态）
  overlays: () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]'))
    .filter((m) => m.getBoundingClientRect().width > 1).length),
  testids: () => p.evaluate(() => Array.from(new Set(Array.from(document.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid'))))),
  ids: () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort()),
  canvasPos: () => p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
    return [n.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null];
  }))),
  minimap: () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-display-toggle-minimap"]'); return e ? { ariaPressed: e.getAttribute('aria-pressed'), dataState: e.getAttribute('data-state') } : null; }),
  credits: () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label')),
});

/** 关掉所有浮层（不数 tooltip），并把鼠标移出画布 —— 收尾读 testid 种类数的前置条件。 */
export async function settle(p, R) {
  for (let i = 0; i < 4; i++) { if (!(await R.overlays())) break; await p.keyboard.press('Escape'); await p.waitForTimeout(900); }
  await p.mouse.move(1276, 716); await p.waitForTimeout(800);
}

/**
 * 通过缩放按钮的输入框把画布设到任意百分比。
 * 依据：批次 106（输入框契约）+ 批次 131（fill+Enter 归位已验证）。
 * 返回 { 目标, 回读, 菜单出现过 }。
 */
export async function setZoom(p, pct) {
  const cur = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e && e.getAttribute('aria-label'); });
  // 先点开菜单让输入框出现（批次 106：菜单打开时 input 出现，值就是当前百分比）
  const pt = await p.evaluate(() => {
    const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2)
      for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
        const h = document.elementFromPoint(x, y);
        if (h && (h === e || e.contains(h))) return { x, y };
      }
    return null;
  });
  if (!pt) throw new Error('缩放按钮找不到落点');
  await p.mouse.click(pt.x, pt.y);
  await p.waitForTimeout(1200);
  const seenInput = await p.evaluate(() => !!document.querySelector('[data-testid="canvas-zoom-percent-input"]'));
  if (!seenInput) throw new Error('缩放输入框没出现');
  await p.fill('[data-testid="canvas-zoom-percent-input"]', String(pct));
  await p.waitForTimeout(300);
  await p.keyboard.press('Enter');
  await p.waitForTimeout(2000);
  const back = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });

  // 🔴 批次 137 a 轮实测到的**探针时序缺陷**：改完缩放后，**aria 文字立刻变成目标值，
  //   但 `.react-flow__viewport` 的 transform 还没跟上** —— 同一轮里同一个元素
  //   「`node-toolbar` 占位」在标称 60% 的那一档读出的是 40% 档的数值（`227.6` 而不是 `341.4`）。
  //   ⇒ **aria 文字不是就绪信号**。改成**轮询实测 `scale()`，追平目标才算设成功**。
  const 实测 = async () => p.evaluate(() => { const vp = document.querySelector('.react-flow__viewport');
    const m = vp ? /scale\(([-\d.]+)\)/.exec(vp.style.transform || '') : null; return m ? Math.round(parseFloat(m[1]) * 1000) / 1000 : null; });
  const t0 = Date.now();
  let got = await 实测();
  const want = Math.round(pct / 100 * 1000) / 1000;
  while (got !== null && Math.abs(got - want) > 0.002 && Date.now() - t0 < 6000) {
    await p.waitForTimeout(200);
    got = await 实测();
  }
  return { 前: cur, 目标: pct, 回读: back, 输入框出现过: seenInput,
    实测scale: got, 期望scale: want, scale已追平: got !== null && Math.abs(got - want) <= 0.002, 等待ms: Date.now() - t0 };
}

/**
 * 规划一块安全的框选矩形：四角必须**既命中 .react-flow__pane 又不在任何节点内**。
 * （批次 131 立的判据：mousedown 落在 pane = 框选模式，后续路径穿节点完全安全。）
 * @param {number} 至少罩住多少个节点
 * @param {number} 目标缩放百分比（只影响「完整在视口内」的判断）
 */
export async function planBox(p, 最少罩住 = 2) {
  return p.evaluate((minN) => {
    const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
      const r = n.getBoundingClientRect();
      return { id: n.getAttribute('data-id'), x: r.x, y: r.y, right: r.right, bottom: r.bottom, w: r.width, h: r.height };
    });
    const vis = nodes.filter((n) => n.right > 4 && n.x < innerWidth - 4 && n.bottom > 62 && n.y < innerHeight - 62);
    const isPane = (x, y) => { const h = document.elementFromPoint(x, y); return !!(h && h.classList && h.classList.contains('react-flow__pane')); };
    const isFree = (x, y) => !nodes.some((n) => x >= n.x && x <= n.right && y >= n.y && y <= n.bottom);
    for (let pad = 20; pad <= 220; pad += 10) {
      const L = Math.min(...vis.map((n) => n.x)) - pad, R = Math.max(...vis.map((n) => n.right)) + pad;
      const T = Math.max(Math.min(...vis.map((n) => n.y)), 64), B = Math.min(Math.max(...vis.map((n) => n.bottom)), innerHeight - 70);
      if (!(L > 6 && R < innerWidth - 320 && T > 62 && B < innerHeight - 62)) continue;
      if (![[L, T], [R, T], [L, B], [R, B]].every(([x, y]) => isPane(x, y) && isFree(x, y))) continue;
      const 罩住 = nodes.filter((n) => n.right > L && n.x < R && n.bottom > T && n.y < B).map((n) => n.id);
      if (罩住.length >= minN) return { ok: true, 矩形: [L, T, R, B].map(Math.round), 罩住数: 罩住.length, 罩住 };
    }
    return { ok: false, 可见节点数: vis.length, 可见: vis.map((n) => ({ id: n.id, x: Math.round(n.x), y: Math.round(n.y), right: Math.round(n.right), bottom: Math.round(n.bottom) })) };
  }, 最少罩住);
}

/** 执行框选：mousedown 落在 pane 上，随后 12 步拖到终点，松开。 */
export async function doBox(p, 矩形) {
  const [L, T, R, B] = 矩形;
  await p.mouse.move(L, T);
  const hit = await p.evaluate(([x, y]) => { const h = document.elementFromPoint(x, y); return h ? h.tagName + '.' + String(h.className || '').split(' ')[0] : null; }, [L, T]);
  if (!hit || !hit.includes('react-flow__pane')) throw new Error(`按下点没有命中 pane，而是 ${hit} —— 拒绝拖（那会移动节点）`);
  await p.mouse.down();
  for (let i = 1; i <= 12; i++) {
    await p.mouse.move(Math.round(L + ((R - L) * i) / 12), Math.round(T + ((B - T) * i) / 12));
    await p.waitForTimeout(30);
  }
  await p.mouse.up();
  await p.waitForTimeout(1500);
  return hit;
}

/**
 * 找一个**恰好罩住 K 个**节点的安全矩形（第二臂「剂量-反应」用）。
 * 同样的安全判据：四角必须既命中 `.react-flow__pane` 又不在任何节点内。
 */
export async function planBoxExact(p, K) {
  return p.evaluate((k) => {
    const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
      const r = n.getBoundingClientRect();
      return { id: n.getAttribute('data-id'), x: r.x, y: r.y, right: r.right, bottom: r.bottom };
    });
    const vis = nodes.filter((n) => n.right > 4 && n.x < innerWidth - 320 && n.bottom > 62 && n.y < innerHeight - 62);
    const isPane = (x, y) => { const h = document.elementFromPoint(x, y); return !!(h && h.classList && h.classList.contains('react-flow__pane')); };
    const isFree = (x, y) => !nodes.some((n) => x >= n.x && x <= n.right && y >= n.y && y <= n.bottom);
    // 以每个可见节点为左下角逐个试矩形，右上角向四周扩张，取第一个恰好 k 个的
    for (const a of vis) {
      for (let pad = 4; pad <= 260; pad += 6) {
        for (const cand of [[a.x - pad, a.y - pad], [a.x - pad, a.bottom + pad], [a.right + pad, a.y - pad], [a.right + pad, a.bottom + pad]]) {
          const L = Math.min(a.x, cand[0]), T = Math.min(a.y, cand[1]);
          const R = Math.max(a.right, cand[0]), B = Math.max(a.bottom, cand[1]);
          if (!(L > 6 && R < innerWidth - 320 && T > 62 && B < innerHeight - 62)) continue;
          if (![[L, T], [R, T], [L, B], [R, B]].every(([x, y]) => isPane(x, y) && isFree(x, y))) continue;
          const 罩住 = nodes.filter((n) => n.right > L && n.x < R && n.bottom > T && n.y < B).map((n) => n.id);
          if (罩住.length === k) return { ok: true, 矩形: [L, T, R, B].map(Math.round), 罩住数: 罩住.length, 罩住 };
        }
      }
    }
    return { ok: false, 可见节点数: vis.length, 可见: vis.map((n) => ({ id: n.id, x: Math.round(n.x), y: Math.round(n.y), right: Math.round(n.right), bottom: Math.round(n.bottom) })) };
  }, K);
}

/**
 * 网格扫描：**枚举出所有可达的「恰好罩住 K 个节点」的安全矩形**，返回 `K -> 矩形`。
 *
 * 🔴 批次 135 c 轮第一版 `planBoxExact(K)` 用「以节点为锚 + 4 个角点候选」搜索，
 *   搜索空间太窄（角点只有 `x-pad` / `right+pad` 两种取值）⇒ K=2/3/4/6 **全部找不到**。
 *   节点在 60% 下互相重叠严重，安全的矩形角点又必须在 pane 上，两者只能靠扫出来。
 *   ⇒ 立规：**当「构造性搜索」找不到东西时，先确认搜索空间够不够大**，
 *     不要直接判定「页面不给我这个状态」。
 */
export async function scanBox(p) {
  return p.evaluate(() => {
    const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
      const r = n.getBoundingClientRect();
      return { id: n.getAttribute('data-id'), x: r.x, y: r.y, right: r.right, bottom: r.bottom };
    });
    const isPane = (x, y) => { const h = document.elementFromPoint(x, y); return !!(h && h.classList && h.classList.contains('react-flow__pane')); };
    const isFree = (x, y) => !nodes.some((n) => x >= n.x && x <= n.right && y >= n.y && y <= n.bottom);
    const found = {};
    const Rs = [180, 240, 300, 360, 420, 480, 540, 600, 660, 720, 780, 840, 900];
    const Ts = [64, 78, 92, 106, 120, 134, 148, 162, 190, 220];
    const Bs = [129, 143, 157, 171, 185, 199, 213, 240, 280, 320];
    for (const L of [8, 20, 38]) {
      for (const R of Rs) {
        if (!(L > 6 && R < innerWidth - 320)) continue;
        for (const T of Ts) {
          for (const B of Bs) {
            if (!(T > 62 && B < innerHeight - 62 && B > T + 20)) continue;
            if (![[L, T], [R, T], [L, B], [R, B]].every(([x, y]) => isPane(x, y) && isFree(x, y))) continue;
            const 罩住 = nodes.filter((n) => n.right > L && n.x < R && n.bottom > T && n.y < B);
            if (罩住.length >= 2 && !found[罩住.length]) found[罩住.length] = [L, T, R, B].map(Math.round);
          }
        }
      }
    }
    return { 可达K: Object.keys(found).map(Number).sort((a, b) => a - b), 矩形表: found };
  });
}

/** 读画布上所有**每节点**连接手柄的屏上尺寸（用来和「多选手柄」对照）。 */
export async function readNodeHandles(p) {
  return p.evaluate(() => {
    const 读 = (tid) => {
      const a = Array.from(document.querySelectorAll(`[data-testid="${tid}"]`));
      const sizes = {};
      for (const e of a) { const r = e.getBoundingClientRect(); const k = `${Math.round(r.width * 10) / 10}×${Math.round(r.height * 10) / 10}`; sizes[k] = (sizes[k] || 0) + 1; }
      return { 实例数: a.length, 尺寸分布: sizes };
    };
    return { target: 读('flow-node-target-handle'), source: 读('flow-node-source-handle'),
      多选source: 读('flow-node-multi-selection-source-handle') };
  });
}

/**
 * 读多选工具条全层。**按面积排序后取**，因为 `node-toolbar` 有三种语义
 * （生成面板 / 文本节点浮动条 / 多选条），手册 §3.82 已记过这个陷阱。
 *
 * 🔑 额外读「选中集包围盒」的 **canvas 与屏上两套**，用来判外层宽度到底跟谁走。
 */
export async function readMultiToolbar(p) {
  return p.evaluate(() => {
    const box = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
      return { w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10, x: Math.round(r.x), y: Math.round(r.y), transform: e.style.transform || getComputedStyle(e).transform }; };
    const all = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).map((e) => ({ ...box(e), testid: 'node-toolbar' }));
    const pick = (tid) => { const a = all.filter((x) => x.testid === tid).sort((x, y) => y.w * y.h - x.w * x.h); return a[0] || null; };
    const q = (tid) => document.querySelector(`[data-testid="${tid}"]`);
    // 画布缩放：viewport 的 transform 是 `translate(x, y) scale(s)` 形态（**不是** `matrix(...)`，
    // 🔴 批次 135 b 轮只写了 matrix 正则 ⇒ scale 读成 null ⇒ 换算表整列变成 0，
    //    还「算出」一个假的四档恒定。教训：**读数异常先怀疑自己的读数**。）
    const vp = document.querySelector('.react-flow__viewport');
    const ms = vp ? /scale\(([-\d.]+)\)/.exec(vp.style.transform || '') : null;
    const scale = ms ? parseFloat(ms[1]) : null;
    // 选中集的屏上包围盒 与 canvas 包围盒
    const sel = Array.from(document.querySelectorAll('.react-flow__node.selected'));
    let scr = null, cvs = null;
    if (sel.length && scale) {
      const rs = sel.map((n) => n.getBoundingClientRect());
      scr = { x: Math.min(...rs.map((r) => r.x)), y: Math.min(...rs.map((r) => r.y)),
        w: Math.round((Math.max(...rs.map((r) => r.right)) - Math.min(...rs.map((r) => r.x))) * 10) / 10,
        h: Math.round((Math.max(...rs.map((r) => r.bottom)) - Math.min(...rs.map((r) => r.y))) * 10) / 10 };
      // canvas 坐标 = 节点 inline transform 的平移量（与视口平移无关）
      const cs = sel.map((n) => { const t = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || ''); const r = n.getBoundingClientRect();
        return { x: t ? parseFloat(t[1]) : null, y: t ? parseFloat(t[2]) : null, w: r.width / scale, h: r.height / scale }; });
      if (cs.every((c) => c.x !== null)) {
        const x0 = Math.min(...cs.map((c) => c.x)), x1 = Math.max(...cs.map((c) => c.x + c.w));
        const y0 = Math.min(...cs.map((c) => c.y)), y1 = Math.max(...cs.map((c) => c.y + c.h));
        cvs = { x: Math.round(x0 * 100) / 100, y: Math.round(y0 * 100) / 100, w: Math.round((x1 - x0) * 100) / 100, h: Math.round((y1 - y0) * 100) / 100 };
      }
    }
    const surface = q('selection-context-toolbar-surface');
    const inner = q('selection-context-toolbar');
    const cnt = q('selection-context-toolbar-count');
    // 🔑 祖先链：判断「这个元素在不在画布坐标系里」的结构性证据。
    //   `.react-flow__renderer` 是 `.react-flow__viewport` 的**父级** ——
    //   所以「父级是 renderer」= 不在画布坐标系（生成面板，手册 §3.82 记的就是它），
    //   「祖先里有 viewport」= 在画布坐标系里（会被 scale 乘上）。
    const chain = (e) => { const c = []; for (let n = e; n && n !== document.body; n = n.parentElement) c.push(String(n.className || '').split(' ')[0] || n.tagName); return c; };
    const maxTb = pick('node-toolbar');
    const maxTbEl = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'))
      .sort((x, y) => (y.getBoundingClientRect().width * y.getBoundingClientRect().height) - (x.getBoundingClientRect().width * x.getBoundingClientRect().height))[0];
    return {
      scale,
      选区框: box(document.querySelector('.react-flow__selection')),
      包围盒屏上: scr, 包围盒canvas: cvs,
      nodeToolbar全部实例: all,
      nodeToolbar最大: maxTb,
      nodeToolbar祖先链: maxTbEl ? chain(maxTbEl) : null,
      nodeToolbar在viewport内: maxTbEl ? !!maxTbEl.closest('.react-flow__viewport') : null,
      nodeToolbaroffsetWidth: maxTbEl ? maxTbEl.offsetWidth : null,
      surface: box(surface),
      inner: box(inner),
      count: box(cnt),
      多选手柄: box(q('flow-node-multi-selection-source-handle')),
      多选sourceToolbar: box(q('flow-node-multi-selection-source-toolbar')),
      多选连接菜单按钮: box(q('flow-node-multi-selection-source-connection-menu-button')),
      选中集: sel.map((n) => n.getAttribute('data-id')).sort(),
      选中节点屏上: sel.slice(0, 3).map((n) => { const r = n.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; }),
      选中节点数: sel.length,
      按钮数: (inner ? inner.querySelectorAll('button,[role=button]').length : 0),
      逐字: (inner ? (inner.innerText || '').replace(/\s+/g, ' ').trim() : null),
    };
  });
}

/** 收尾前置：把鼠标移出画布再读 testid 种类数（批次 129 立规）。 */
export async function endState(p, R, 基线) {
  await settle(p, R);
  const ids = await R.ids(); const t = await R.testids();
  const 多 = ids.filter((x) => !基线.ids.includes(x)), 少 = 基线.ids.filter((x) => !ids.includes(x));
  const t多 = t.filter((x) => !基线.testids.includes(x)), t少 = 基线.testids.filter((x) => !t.includes(x));
  return {
    状态行: await R.status(), 选中: await R.selCount(), 浮层: await R.overlays(),
    zoom: await R.zoom(), credits: await R.credits(), minimap: await R.minimap(),
    testid种类: t.length, 节点数: ids.length,
    节点差集: { 多, 少 }, testid差集: { 多: t多, 少: t少 },
  };
}

export { keyGuard };
