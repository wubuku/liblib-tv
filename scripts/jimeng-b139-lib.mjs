// 批次 139 共用件：**建节点 → 编组 → 读组态 → 拆干净**。
//
// 🔑 靶子：`organize-group-layout.md:195` 记「工具条**宽度跟随组卡片宽度**，不是固定值：
//   实测 336×40、367×40、296×40、312×40 四种（同样 60%/47% 缩放下卡片宽度不同所致）」。
//   🔴 **这句话有两个从没被验过的地方**：
//     ① 「跟随卡片宽度」—— 批次 18 记过 `1378×40（= 卡片宽 1378）`，但那是 **100% 单档**，
//        而且是**屏上**对**屏上**；从没在**同一张卡**上换过缩放。
//     ② 「同样 60%/47% 缩放下卡片宽度不同所致」—— 这是**归因**，不是读数。
//        组卡片是 React Flow 节点，宽是 canvas 口径的 style.width，
//        **理论上不该随缩放变**；如果真变了，说明卡片宽度另受别的东西影响。
//   📌 批次 135 已经定过多选工具条的公式：`屏上宽 = (包围盒 canvas 宽 + 80) × scale`。
//      组工具条**是不是同一套公式**（尤其那个 `+80`），全册没有任何一处量过。
//
// ⚠️ 组卡片是**共享画布上的产物**：组存在时，它的右键「删除」会连成员一起删
//   （SOURCE_OBSERVATIONS.md:567 记过这个坑）。⇒ 归位走 `jimeng-b139-rescue.mjs`。
import { readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { findEmptyPane } from './jimeng-b136-lib.mjs';

const idsOf = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const selCount = (p) => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const selIds = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')).sort());
const 组数 = (p) => p.evaluate(() => document.querySelectorAll('.react-flow__node-group').length);
const overlays = (p) => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]'))
  .filter((m) => m.getBoundingClientRect().width > 1).length);
const canvasPos = (p) => p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
  return [n.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null];
})));

/** 在一个元素内部找一个真能点到它的点（批次 137 护栏同款：逐格采样 + elementFromPoint 双重把关）。 */
export async function 可点落点(p, sel, inset = 3, step = 3) {
  return p.evaluate(([q, ins, st]) => {
    const e = document.querySelector(q); if (!e) return { __err: 'not-found' };
    const r = e.getBoundingClientRect(); if (r.width < 1) return { __err: 'zero-size' };
    for (let y = Math.ceil(r.y) + ins; y <= r.y + r.height - ins; y += st)
      for (let x = Math.ceil(r.x) + ins; x <= r.x + r.width - ins; x += st) {
        const h = document.elementFromPoint(x, y);
        if (h && (h === e || e.contains(h))) return { x, y, 命中: h.getAttribute('data-testid') || h.tagName };
      }
    return { __err: 'no-point' };
  }, [sel, inset, step]);
}

/**
 * 连建 N 个同类型节点。每一步都现算前置条件并断言（批次 132 立规）。
 * 🔴 护栏：建前 0 选中、每次建后**差集恰好 1**、新节点**恰好 .selected**。
 *   前一条是硬的：上一个新建节点会留下选中态，不清掉的话下一次「建后只有 1 个 selected」不成立。
 * @returns {{ok:boolean, ids:string[], 护栏:Array, 建后canvas:object}}
 */
export async function 建N个(p, 左栏aria, N, 断言, 预期建前节点数) {
  const R = readers(p);
  const 护栏 = [];
  const rec = { 护栏, 左栏aria, N };
  const 记 = async (名, 条件, 详情) => { const ok = !!!!条件; 护栏.push({ 名, 通过: ok, 详情 });
    if (断言) 断言(名, ok, 详情); return ok; };

  await keyGuard(p);
  await settle(p, R);
  const 基线ids = await idsOf(p);
  rec.建前 = { 节点数: 基线ids.length, 状态行: await R.status() };
  // 🔴 批次 139 a 轮第一版崩在框选那一步，**留下 3 个孤儿文本节点（79 个）**。
  //   直接重跑会**再建 3 个**（82 个）⇒ 加一条「建前节点数 == 预期基线」硬护栏。
  if (预期建前节点数 !== undefined) {
    await 记('①a 建前节点数 == 预期基线（挡上轮残留）', 基线ids.length === 预期建前节点数,
      { 实际: 基线ids.length, 预期: 预期建前节点数, 提示: '不等就先跑 jimeng-b139-rescue.mjs 归位' });
    if (基线ids.length !== 预期建前节点数) { rec.ok = false; return rec; }
  }
  await 记('①建前 0 选中（不能有上次留下的选中态）', (await selCount(p)) === 0, { 选中数: await selCount(p) });
  await 记('①b 建前无组卡片（本批专属：组会干扰框选与差集）', (await 组数(p)) === 0, { 组数: await 组数(p) });

  const 自建 = [];
  for (let i = 0; i < N; i++) {
    // 🔴 每次建之前先清选中：上一个新建节点默认就是选中态。
    if (await selCount(p) > 0) {
      const 空 = await findEmptyPane(p);
      if (空) { await p.mouse.click(空.x, 空.y); await p.waitForTimeout(900); }
      // 复查：点空白必须先校验落点不是控件（批次 132 立的「点空白 vs 点控件」相反用法）
      const 落是控件 = 空 ? await p.evaluate(([x, y]) => {
        const h = document.elementFromPoint(x, y);
        return h ? (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button]') ? 1 : 0) : -1;
      }, [空.x, 空.y]) : -1;
      await 记(`第${i + 1}个建前清选中：落点不是控件`, 落是控件 === 0, { 落点: 空, 命中判定: 落是控件 });
      await 记(`第${i + 1}个建前清选中：选中数归 0`, (await selCount(p)) === 0, { 选中数: await selCount(p) });
    }
    const 前 = await idsOf(p);
    const pt = await 可点落点(p, `[aria-label="${左栏aria}"]`, 3, 3);
    if (pt.__err) { await 记(`第${i + 1}个建节点失败（${pt.__err}）`, false, pt); rec.ok = false; return rec; }
    await p.mouse.click(pt.x, pt.y);
    await p.waitForTimeout(2500);
    await settle(p, R);
    const 后 = await idsOf(p);
    const 新增 = 后.filter((x) => !前.includes(x));
    await 记(`②第${i + 1}个建后差集恰好 1 个`, 新增.length === 1, { 新增, 前数: 前.length, 后数: 后.length });
    if (新增.length !== 1) { rec.ok = false; return rec; }
    const SELF = 新增[0]; 自建.push(SELF);
    const 是选中 = await p.evaluate((i2) => { const n = document.querySelector(`.react-flow__node[data-id="${i2}"]`);
      return !!(n && n.classList.contains('selected')); }, SELF);
    await 记(`②b 第${i + 1}个新节点恰好 .selected`, 是选中, { SELF, 选中数: await selCount(p) });
  }
  rec.ids = 自建;
  rec.建后canvas = await canvasPos(p);
  rec.ok = 护栏.every((h) => h.通过);
  return rec;
}

/**
 * 找一个**恰好罩住给定 id 集合**的安全框选矩形。
 * 安全判据（批次 131/135 立的）：四角必须既命中 `.react-flow__pane`、又不在**任何**节点内。
 */
export async function planBoxFor(p, want) {
  return p.evaluate((W) => {
    const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
      const r = n.getBoundingClientRect();
      return { id: n.getAttribute('data-id'), x: r.x, y: r.y, right: r.right, bottom: r.bottom };
    });
    const mine = nodes.filter((n) => W.includes(n.id));
    if (mine.length !== W.length) return { ok: false, 理由: '有目标节点不在 DOM 里', 目标: W.length, 实到: mine.length };
    const isPane = (x, y) => { const h = document.elementFromPoint(x, y); return !!(h && h.classList && h.classList.contains('react-flow__pane')); };
    const isFree = (x, y) => !nodes.some((n) => x >= n.x && x <= n.right && y >= n.y && y <= n.bottom);
    const L0 = Math.min(...mine.map((n) => n.x)), R0 = Math.max(...mine.map((n) => n.right));
    const T0 = Math.min(...mine.map((n) => n.y)), B0 = Math.max(...mine.map((n) => n.bottom));
    for (let p2 = 6; p2 <= 260; p2 += 6) {
      // 🔴 批次 139 a 轮踩过：这里原来把候选矩形解构成 `const [L, T, R, B]`，
      //   循环体里又写 `const L = Math.round(L)` —— **同一作用域重名 ⇒ TDZ 报错**
      //   （`Cannot access 'L' before initialization`）。候选解构成 `c0..c3`。
      for (const c of [[L0 - p2, T0 - p2, R0 + p2, B0 + p2],
                        [L0 - p2, T0 - p2, R0 + p2, B0 + p2 * 2],
                        [L0 - p2, T0 - p2 * 2, R0 + p2, B0 + p2]]) {
        const L = Math.round(c[0]), T = Math.round(c[1]), R = Math.round(c[2]), B = Math.round(c[3]);
        if (!(L > 6 && R < innerWidth - 330 && T > 64 && B < innerHeight - 70 && B > T + 20)) continue;
        if (![[L, T], [R, T], [L, B], [R, B]].every(([x, y]) => isPane(x, y) && isFree(x, y))) continue;
        const 罩 = nodes.filter((n) => n.right > L && n.x < R && n.bottom > T && n.y < B).map((n) => n.id).sort();
        if (罩.length === W.length && W.every((x) => 罩.includes(x))) return { ok: true, 矩形: [L, T, R, B], 罩 };
      }
    }
    return { ok: false, 理由: '找不到四角安全且恰好罩住目标集合的矩形', 目标包围盒: { L0, T0, R0, B0 },
      mine: mine.map((n) => ({ id: n.id, x: Math.round(n.x), y: Math.round(n.y), right: Math.round(n.right), bottom: Math.round(n.bottom) })) };
  }, want);
}

/** 执行框选：mousedown 必须落在 `.react-flow__pane` 上（落在节点上会变成拖动节点）。 */
export async function doBox(p, 矩形) {
  const [L, T, R, B] = 矩形;
  const hit = await p.evaluate(([x, y]) => { const h = document.elementFromPoint(x, y);
    return h ? h.tagName + '.' + String(h.className || '').split(' ')[0] : null; }, [L, T]);
  if (!hit || !hit.includes('react-flow__pane')) throw new Error(`按下点没有命中 pane，而是 ${hit} —— 拒绝拖（那会移动节点）`);
  await p.mouse.move(L, T);
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
 * 点多选工具条上的「编组」（`data-toolbar-value="batch-group"`，**无 aria-label，只有 innerText** ——
 * 20-reference.md:440 逐字记着这一点，所以定位只能靠 data-toolbar-value）。
 */
export async function 点编组(p) {
  const 计划 = await p.evaluate(() => {
    const b = document.querySelector('[data-toolbar-value="batch-group"]');
    if (!b) return { __err: 'not-found' };
    const r = b.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2)
      for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
        const h = document.elementFromPoint(x, y);
        if (h && (h === b || b.contains(h))) return { x, y, 逐字: (b.innerText || '').replace(/\s+/g, ' ').trim(),
          aria: b.getAttribute('aria-label'), 祖先链: (() => { const c = []; for (let n = b; n && n !== document.body; n = n.parentElement) c.push(String(n.className || '').split(' ')[0] || n.tagName); return c; })() };
      }
    return { __err: 'no-point' };
  });
  if (计划.__err) return { ok: false, 计划 };
  // 每次点击前重新断言：按钮还在 + 没有浮层挡路
  const 前置 = await p.evaluate(() => ({
    还在: !!document.querySelector('[data-toolbar-value="batch-group"]'),
    浮层: Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length,
    选中数: document.querySelectorAll('.react-flow__node.selected').length,
  }));
  if (!前置.还在 || 前置.浮层 > 0 || 前置.选中数 < 2) return { ok: false, 计划, 前置, 理由: '前置不满足' };
  await p.mouse.click(计划.x, 计划.y);
  await p.waitForTimeout(2500);
  await settle(p, readers(p));
  return { ok: (await 组数(p)) === 1, 计划, 前置, 之后组数: await 组数(p) };
}

/** 点组工具条上的「解除编组」（`data-toolbar-value="ungroup"`）。 */
export async function 点解除编组(p) {
  const 计划 = await 可点落点(p, '[data-toolbar-value="ungroup"]', 3, 3);
  if (计划.__err) return { ok: false, 计划 };
  // 🔴 批次 139 d 轮踩过：前置写成「`.react-flow__node-group.selected` 计数 == 1」是**错的** ——
  //   一个组在 DOM 里**匹配 2 个** `.react-flow__node-group`（真身 + `__group-resize-chrome__`
  //   影子，两者都带 `selected`），所以真选中时读数是 **2**，守卫把「该点」判成了「不点」。
  //   ⇒ 改成「至少 1 个真身组处于选中」。真身 = data-id 不以 `__group-resize-chrome__` 开头。
  const 前置 = await p.evaluate(() => {
    const 真身 = Array.from(document.querySelectorAll('.react-flow__node-group'))
      .filter((g) => !/^__group-resize-chrome__/.test(g.getAttribute('data-id') || ''));
    return { 真身组数: 真身.length, 真身选中: 真身.filter((g) => g.classList.contains('selected')).length };
  });
  if (前置.真身选中 < 1) return { ok: false, 计划, 前置, 理由: '组真身没处于选中态，不点' };
  await p.mouse.click(计划.x, 计划.y);
  await p.waitForTimeout(2500);
  await settle(p, readers(p));
  return { ok: (await 组数(p)) === 0, 计划, 前置, 之后组数: await 组数(p) };
}

/**
 * 🔑 读组态全层 —— 本批的判据核心。
 *
 * 一次性把**四个量**都读出来，才能判「工具条宽度跟谁走」：
 *   ① 组卡片**屏上**矩形（`.react-flow__node-group` 的 getBoundingClientRect）
 *   ② 组卡片**canvas** 宽（`offsetWidth/offsetHeight` + inline `style.width`）
 *   ③ 组工具条**屏上**宽（最大面积的 `node-toolbar`）
 *   ④ 组工具条**canvas** 口径（`offsetWidth`；它不在 viewport 里，offsetWidth 已是真实值）
 * 另外读内层 `selection-context-toolbar` 与祖先链 —— 祖先链决定「谁乘 scale」。
 */
export async function 读组态(p) {
  return p.evaluate(() => {
    const box = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
      return { w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10, x: Math.round(r.x), y: Math.round(r.y) }; };
    const chain = (e) => { const c = []; for (let n = e; n && n !== document.body; n = n.parentElement) c.push(String(n.className || '').split(' ')[0] || n.tagName); return c; };
    const vp = document.querySelector('.react-flow__viewport');
    const ms = vp ? /scale\(([-\d.]+)\)/.exec(vp.style.transform || '') : null;
    const scale = ms ? Math.round(parseFloat(ms[1]) * 1000) / 1000 : null;

    const g = document.querySelector('.react-flow__node-group');
    const 组 = g ? {
      id: g.getAttribute('data-id'), 屏上: box(g),
      canvas宽: g.offsetWidth, canvas高: g.offsetHeight,
      styleWidth: g.style.width, styleHeight: g.style.height,
      transform: g.style.transform,
      选中: g.classList.contains('selected'),
      aria: g.getAttribute('aria-label'),
      逐字: (g.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40),
      匹配groupResizeChrome: document.querySelectorAll('.react-flow__node-group__group-resize-chrome__' + g.getAttribute('data-id')).length,
      resizeChrome总数: document.querySelectorAll('[class*="group-resize-chrome"]').length,
      groupBackground: (() => { const e = document.querySelector('[data-testid="group-background"]'); return e ? { 屏上: box(e), pe: getComputedStyle(e).pointerEvents } : null; })(),
      groupBodyFrame: (() => { const e = document.querySelector('[data-testid="group-body-frame"]'); return e ? { 屏上: box(e), pe: getComputedStyle(e).pointerEvents } : null; })(),
      四角把手: Array.from(document.querySelectorAll('[aria-label^="Resize group from"]')).map((e) => e.getAttribute('aria-label')).sort(),
    } : null;

    // 🔴 `node-toolbar` 有三种语义（生成面板 / 节点浮动条 / 多选条），批次 137 已栽过一次：
    //   **必须按面积排序后取**，不能 querySelector 取第一个。
    const tbAll = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'));
    const 排 = tbAll.map((e) => ({ e, 屏上: box(e) })).sort((a, b) => (b.屏上.w * b.屏上.h) - (a.屏上.w * a.屏上.h));
    const 最大 = 排[0] || null;
    const inner = document.querySelector('[data-testid="selection-context-toolbar"]');
    const surface = document.querySelector('[data-testid="selection-context-toolbar-surface"]');
    return {
      scale, 组, 组数: document.querySelectorAll('.react-flow__node-group').length,
      tb实例数: tbAll.length,
      tb全部: 排.map((x) => x.屏上),
      外层: 最大 ? { ...最大.屏上, offsetWidth: 最大.e.offsetWidth, 祖先链: chain(最大.e), 在viewport内: !!最大.e.closest('.react-flow__viewport') } : null,
      inner: inner ? { ...box(inner), offsetWidth: inner.offsetWidth, 祖先链: chain(inner) } : null,
      surface: surface ? box(surface) : null,
      逐字: inner ? (inner.innerText || '').replace(/\s+/g, ' ').trim() : null,
      按钮: inner ? Array.from(inner.querySelectorAll('button,[role=button]')).map((b) => {
        const r = b.getBoundingClientRect();
        return { 逐字: (b.innerText || '').replace(/\s+/g, ' ').trim() || null, aria: b.getAttribute('aria-label'),
          value: b.getAttribute('data-toolbar-value'), 屏上: `${Math.round(r.width * 10) / 10}×${Math.round(r.height * 10) / 10}` };
      }) : null,
    };
  });
}

/** 读组态全层（把 evaluate 里读不到的东西补上：选中集、状态行）。 */
export async function 读组态全(p) {
  const r = await 读组态(p);
  r.选中 = await selIds(p);
  r.选中数 = await selCount(p);
  r.状态行 = await p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
  return r;
}

/**
 * 用「点选 + Shift 加选」选中一组节点 —— **框选的备选路径**。
 *
 * 🔑 批次 139 a 轮为什么需要它：左栏连建的文本节点是**阶梯状叠放**的
 *   （实测 60% 下三个分别在 `(544,264)`/`(568,288)`/`(592,312)`，各 `192×192`，
 *   canvas 都是 `320×320`）⇒ 它们的并集包围盒 `240×240` 四周全是别人的节点，
 *   `planBoxFor` 扫遍 pad 6..260 **一个四角安全且恰好罩住这 3 个的矩形都找不到**。
 *   ⇒ 立规：**框选找不到就换点选，不要一直加大搜索空间**（批次 135 c 轮同一个教训的另一半）。
 *
 * 📌 落点判据（批次 133/136 立的「我打算点的 ≠ 我点到的」）：
 *   逐格采样，要求 `elementFromPoint` 命中元素**所属的 `.react-flow__node` 的 data-id
 *   必须正好是目标 id** —— 阶梯叠放时，三个节点互相压住对方的大部分面积，
 *   不校验归属就会点到压在上面那个。
 */
export async function 点选一组(p, ids) {
  const rec = { 落点: {}, 序列: [] };
  // 先清选中
  if (await selCount(p) > 0) {
    const 空 = await findEmptyPane(p);
    if (空) { await p.mouse.click(空.x, 空.y); await p.waitForTimeout(900); }
    rec.清选中后 = { 选中数: await selCount(p) };
    if (await selCount(p) !== 0) return { ok: false, ...rec, 理由: '清不掉选中' };
  }
  for (let i = 0; i < ids.length; i++) {
    const pt = await p.evaluate((id) => {
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      if (!n) return { __err: 'node-not-found' };
      const r = n.getBoundingClientRect();
      for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2)
        for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) {
          const h = document.elementFromPoint(x, y);
          if (!h) continue;
          const owner = h.closest('.react-flow__node');
          // 🔑 归属判据：命中的节点必须**正好是目标**，且命中点不能是控件
          if (owner && owner.getAttribute('data-id') === id
            && !h.closest('button,[role=button],[contenteditable],input,textarea')) {
            return { x, y, 命中节点: id, 命中tag: h.tagName, 命中testid: h.getAttribute('data-testid') };
          }
        }
      return { __err: 'no-point' };
    }, ids[i]);
    rec.落点[ids[i]] = pt;
    if (pt.__err) return { ok: false, ...rec, 理由: `第${i + 1}个找不到归属正确的落点` };
    // 每次点击前现算前置：目标节点此刻仍在 DOM 里
    const 前置 = await p.evaluate((id) => {
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      const h = n ? document.elementFromPoint(
        Math.round(n.getBoundingClientRect().x + n.getBoundingClientRect().width / 2),
        Math.round(n.getBoundingClientRect().y + n.getBoundingClientRect().height / 2)) : null;
      return { 在DOM: !!n, 浮层: Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]'))
        .filter((m) => m.getBoundingClientRect().width > 1).length };
    }, ids[i]);
    if (!前置.在DOM || 前置.浮层 > 0) return { ok: false, ...rec, 理由: '前置不满足', 前置 };
    if (i === 0) { await p.mouse.click(pt.x, pt.y); }
    else { await p.keyboard.down('Shift'); await p.mouse.click(pt.x, pt.y); await p.keyboard.up('Shift'); }
    await p.waitForTimeout(1000);
    rec.序列.push({ id: ids[i], 落点: [pt.x, pt.y], 点后选中: await selIds(p) });
  }
  rec.最终选中 = await selIds(p);
  rec.ok = JSON.stringify(rec.最终选中) === JSON.stringify([...ids].sort());
  return rec;
}

export { idsOf, selCount, selIds, 组数, overlays, canvasPos };
