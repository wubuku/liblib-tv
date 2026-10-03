// 批次 144 a 轮 —— 验 5 个「全灭 testid」：文本节点的全屏编辑器。
//
// 📌 靶子（SOURCE_OBSERVATIONS.md §4.49 存活率普查的分诊表第 1 行）：
//   `text-editor-fullscreen-dialog` / `-placeholder` / `-scroll-region`
//   / `text-editor-toolbar` / `-toolbar-separator`（5 个）
//   当年没验的理由：**「3 个文本节点全在视口外；平移会改共享画布视图，不做」**。
//
// 🔑 批次 143 之后这条路通了：**护栏建一个文本节点，它就落在视口中央** ——
//   完全不用平移、不用碰共享画布的视图。
//
// ⚠️ **两条安全纪律（都是本项目交过学费的）**：
//   ① **不用 F 键**。§3.56.1 教训 #2 记着「F 开了全屏编辑器 → V/G/V 变成打字」，
//      「在共享画布上后果最重：它让我改动了别人的数据」。⇒ 改走**工具条上的「全屏」按钮**。
//   ② **关闭用「Close full-screen editor」按钮，不用 Esc** —— 全屏编辑器里有
//      `contenteditable`，任何按键都有变打字的风险。**全程不按任何字母/数字键。**
//
// 本轮读三样：① 打开前后的**全页 testid 差分**；② 编辑器内每个 `[data-testid]`
//   的 testid + 盒 + 逐字；③ 关闭后是否**完全归零**。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { 建N个, selCount, idsOf, 可点落点, canvasPos } from './jimeng-b139-lib.mjs';

const rec = { 批次: 144, 轮: 'a', 目的: '验全屏文本编辑器的 5 个全灭 testid' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };

const 独占像素 = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'not-found' };
  const r = n.getBoundingClientRect(); const 好 = [];
  for (let y = Math.ceil(r.y) + 4; y <= r.y + r.height - 4; y += 2)
    for (let x = Math.ceil(r.x) + 4; x <= r.x + r.width - 4; x += 2) {
      const h = document.elementFromPoint(x, y); if (!h) continue;
      const nn = h.closest('.react-flow__node');
      if (!nn || nn.getAttribute('data-id') !== i) continue;
      if (h.tagName !== 'DIV' || h.closest('.octo-text-node-resize-controls') || h.closest('[contenteditable]')) continue;
      if (/text-octo-ui-copy/.test(String(h.className || ''))) continue;
      好.push([x, y]);
    }
  if (!好.length) return { __err: 'no-exclusive-point' };
  const cx = 好.reduce((a, q) => a + q[0], 0) / 好.length, cy = 好.reduce((a, q) => a + q[1], 0) / 好.length;
  好.sort((u, v) => Math.hypot(u[0] - cx, u[1] - cy) - Math.hypot(v[0] - cx, v[1] - cy));
  return { 总数: 好.length, 落点: 好[0] };
}, id);

const 找真空白 = () => p.evaluate(() => {
  const 坏 = (x, y) => { const h = document.elementFromPoint(x, y);
    if (!h) return 1;
    if (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button]')) return 1;
    if (h.closest('.react-flow__node') || h.closest('[data-testid="text-editor-node-overlay"]') || h.closest('.react-flow__node-toolbar')) return 1;
    return !(h.classList && h.classList.contains('react-flow__pane')); };
  for (let y = 90; y < innerHeight - 90; y += 8) for (let x = 360; x < innerWidth - 350; x += 8) if (!坏(x, y)) return { x, y };
  return { __err: 'no-free-pane' };
});

/** 全页 testid 清单（含盒与逐字），用于差分。 */
const testid清单 = () => p.evaluate(() => {
  const m = new Map();
  for (const e of document.querySelectorAll('[data-testid]')) {
    const t = e.getAttribute('data-testid');
    if (m.has(t)) continue;
    const r = e.getBoundingClientRect();
    m.set(t, { testid: t, tag: e.tagName, 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10],
      aria: e.getAttribute('aria-label'), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40),
      cls: String(e.className || '').slice(0, 60) });
  }
  return [...m.values()];
});

/** 编辑器内全部元素（不只 testid），用于查那两个**推测拼法**的 testid。 */
const 全页找testid = (名字列表) => p.evaluate((ns) => ns.map((n) => {
  const els = document.querySelectorAll('[data-testid="' + n + '"]');
  return { testid: n, 命中数: els.length,
    盒: els.length ? (() => { const r = els[0].getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() : null,
    逐字: els.length ? (els[0].innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40) : null };
}), 名字列表);

/** 编辑器内所有 testid 及其盒（编辑器开着时用）。 */
const 编辑器清单 = () => p.evaluate(() => {
  const 根 = document.querySelector('[data-testid="text-editor-fullscreen-dialog"]')
    || document.querySelector('[role=dialog]');
  if (!根) return { __err: 'no-dialog' };
  const r = 根.getBoundingClientRect();
  const 内 = Array.from(根.querySelectorAll('[data-testid]')).map((e) => {
    const q = e.getBoundingClientRect();
    return { testid: e.getAttribute('data-testid'), tag: e.tagName,
      盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width * 10) / 10, Math.round(q.height * 10) / 10],
      aria: e.getAttribute('aria-label'), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 36),
      cls: String(e.className || '').slice(0, 56) };
  });
  return { 根: { tag: 根.tagName, testid: 根.getAttribute('data-testid'), role: 根.getAttribute('role'),
      盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] },
    内部testid数: 内.length, 内部: 内,
    contenteditable: Array.from(根.querySelectorAll('[contenteditable]')).map((e) => ({ tag: e.tagName,
      cls: String(e.className || '').slice(0, 50), testid: e.getAttribute('data-testid') })),
    按钮: Array.from(根.querySelectorAll('button,[role=button]')).map((e) => { const q = e.getBoundingClientRect();
      return { aria: e.getAttribute('aria-label'), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim(),
        盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
        禁用: e.getAttribute('aria-disabled') || e.getAttribute('data-disabled') }; }) };
});

const 删一个 = async (id) => {
  for (let k = 0; k < 3 && (await selCount(p)) > 0; k++) { const 空 = await 找真空白(); if (空.__err) break;
    await p.mouse.click(空.x, 空.y); await p.waitForTimeout(1100); }
  const 落 = await 独占像素(id); if (落.__err) return { id, __err: '独占 ' + 落.__err };
  await p.mouse.click(落.落点[0], 落.落点[1]); await p.waitForTimeout(1200);
  const 前 = await idsOf(p);
  const 落2 = await 独占像素(id); if (落2.__err) return { id, __err: '右键前 ' + 落2.__err };
  await p.mouse.click(落2.落点[0], 落2.落点[1], { button: 'right' });
  await p.waitForTimeout(1800);
  const del = await p.evaluate(() => {
    const els = Array.from(document.querySelectorAll('[role=menuitem],[role=menu] button,li,button')).filter((e) => /^删除/.test((e.innerText || '').replace(/\s+/g, '').trim()));
    if (!els.length) return { __err: 'no-delete-item' };
    const e = els[0]; const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2) for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) {
      const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y }; }
    return { __err: 'no-point' };
  });
  if (del.__err) return { id, __err: del.__err };
  await p.mouse.click(del.x, del.y); await p.waitForTimeout(2500); await settle(p, R);
  const 后 = await idsOf(p);
  return { id, 消失: 前.filter((x) => !后.includes(x)) };
};

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p);
  await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(), 积分: await R.credits() };
  rec.打开前testid = (await testid清单()).map((q) => q.testid);
  rec.打开前testid数 = rec.打开前testid.length;

  const 建 = await 建N个(p, '文本', 1, 断言, 76);
  rec.建 = 建;
  const SELF = 建.ids && 建.ids[0];
  if (!SELF) { rec.中止 = '建节点未成'; }
  else {
    rec.建后 = { 状态行: await R.status(), 选中: await selCount(p) };
    rec.建后canvas = await canvasPos(p);

    // ---- 找工具条上的「全屏」按钮（不用 F 键）
    rec.工具条 = await p.evaluate(() => {
      const tb = document.querySelector('.react-flow__node-toolbar');
      if (!tb) return { __err: 'no-node-toolbar' };
      const r = tb.getBoundingClientRect();
      return { 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        按钮: Array.from(tb.querySelectorAll('button,[role=button]')).map((e) => { const q = e.getBoundingClientRect();
          return { aria: e.getAttribute('aria-label'), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim(),
            盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] }; }) };
    });
    const 全屏钮 = (rec.工具条.按钮 || []).find((q) => q.aria === '全屏' || q.逐字 === '全屏');
    rec.全屏钮 = 全屏钮;
    if (!全屏钮) { rec.中止 = '工具条上没有「全屏」按钮'; }
    else {
      // 每次点击前重新断言前置：按钮还在、无浮层、落点归属正确、且**不是生成类按钮**
      const 前置 = await p.evaluate(([x, y, SELFID]) => {
        const h = document.elementFromPoint(x, y);
        const btn = h ? h.closest('button,[role=button]') : null;
        return { 命中按钮aria: btn ? btn.getAttribute('aria-label') : null,
          命中按钮逐字: btn ? (btn.innerText || '').replace(/\s+/g, ' ').trim() : null,
          是全屏: !!(btn && (btn.getAttribute('aria-label') === '全屏')),
          浮层: Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length,
          目标仍选中: !!document.querySelector(`.react-flow__node[data-id="${SELFID}"].selected`),
          编辑器已开: !!document.querySelector('[data-testid="text-editor-fullscreen-dialog"]') };
      }, [全屏钮.盒[0] + 8, 全屏钮.盒[1] + 8, SELF]);
      rec.点全屏前 = 前置;
      if (前置.是全屏 && 前置.浮层 === 0 && 前置.目标仍选中 && !前置.编辑器已开) {
        await p.mouse.click(全屏钮.盒[0] + 8, 全屏钮.盒[1] + 8);
        await p.waitForTimeout(2500);
      }
      rec.点后 = { 状态行: await R.status(), 浮层: await R.overlays(), testid数: (await testid清单()).length };
      rec.编辑器 = await 编辑器清单();
      rec.打开后testid = (await testid清单()).map((q) => q.testid);
      rec.差分 = { 新增: rec.打开后testid.filter((t) => !rec.打开前testid.includes(t)),
        消失: rec.打开前testid.filter((t) => !rec.打开后testid.includes(t)) };
      // 🔴 逐个核 5 个「全灭」testid，特别是那两个**推测拼法**
      rec.五项核验 = await 全页找testid(['text-editor-fullscreen-dialog', 'text-editor-fullscreen-placeholder',
        'text-editor-fullscreen-scroll-region', 'text-editor-toolbar', 'text-editor-toolbar-separator',
        'text-editor-scroll-region', 'text-editor-placeholder']);
      断言('① 5 个待验 testid 至少有一个真身（不是全灭）', rec.五项核验.some((q) => q.命中数 > 0), rec.五项核验);

      // ---- 关闭：**用按钮**，不用 Esc
      if (!前置.编辑器已开 && (await p.evaluate(() => !!document.querySelector('[data-testid="text-editor-fullscreen-dialog"]')))) {
        const 关 = await 可点落点(p, '[aria-label="Close full-screen editor"]', 3, 3);
        rec.关闭钮落点 = 关;
        if (!关.__err) {
          const 前置2 = await p.evaluate(([x, y]) => { const h = document.elementFromPoint(x, y);
            const b = h ? h.closest('button,[role=button]') : null;
            return { aria: b ? b.getAttribute('aria-label') : null, 对: !!(b && b.getAttribute('aria-label') === 'Close full-screen editor') }; },
            [关.x, 关.y]);
          rec.点关闭前 = 前置2;
          if (前置2.对) { await p.mouse.click(关.x, 关.y); await p.waitForTimeout(2200); await settle(p, R); }
        }
      }
      rec.关后 = { 状态行: await R.status(), 浮层: await R.overlays(), testid数: (await testid清单()).length };
      rec.关后testid = (await testid清单()).map((q) => q.testid);
      rec.归零差分 = { 相对打开前新增: rec.关后testid.filter((t) => !rec.打开前testid.includes(t)),
        相对打开前消失: rec.打开前testid.filter((t) => !rec.关后testid.includes(t)) };
    }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); }

try { rec.删除 = []; for (const id of ((rec.建 && rec.建.ids) || [])) rec.删除.push(await 删一个(id));
} catch (e) { rec.删除异常 = String(e).slice(0, 300); }

await settle(p, R);
const 末 = await idsOf(p);
rec.收尾 = { 状态行: await R.status(), 节点数: 末.length, 选中: await selCount(p), 浮层: await R.overlays(),
  zoom: await R.zoom(), minimap: await R.minimap(), 积分: await R.credits(),
  剩余自建: 末.filter((x) => ((rec.建 && rec.建.ids) || []).includes(x)) };
rec.断言全过 = 断言过;
fs.writeFileSync(new URL('./_tmp-b144a.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify({ 中止: rec.中止, 异常: rec.异常, 工具条: rec.工具条, 全屏钮: rec.全屏钮, 点全屏前: rec.点全屏前,
  点后: rec.点后, 编辑器根: rec.编辑器 && rec.编辑器.根, 编辑器内部: rec.编辑器 && rec.编辑器.内部,
  编辑器按钮: rec.编辑器 && rec.编辑器.按钮, 差分: rec.差分, 五项核验: rec.五项核验,
  关后: rec.关后, 归零差分: rec.归零差分, 删除: rec.删除, 收尾: rec.收尾 }, null, 1));
await b.close();
