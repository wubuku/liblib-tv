// 批次 144 b 轮 —— a 轮的失败原因已定位，两处都改：
//   ① `document.querySelector('.react-flow__node-toolbar')` 抓到的是那个**常驻 0×0 容器**
//      （a 轮实测 `盒: [640,476,0,0]`、按钮 0 个）⇒ 必须**按面积取最大的那个**。
//   ② 节点工具条**只在悬停节点时出现**（§3.14），而 `settle()` 把鼠标移到了 (1276,716)
//      ⇒ 查工具条**之前必须先把鼠标移回节点上**。
//
// ⚠️ 沿用 a 轮的两条安全纪律：**不用 F 键**（打开后按键会变打字）、
//   **关闭用「Close full-screen editor」按钮不用 Esc**。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { 建N个, selCount, idsOf, 可点落点, canvasPos } from './jimeng-b139-lib.mjs';

const rec = { 批次: 144, 轮: 'b', 目的: '按面积取工具条 + 鼠标回节点，验全屏编辑器' };
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

const testid清单 = () => p.evaluate(() => {
  const m = new Set();
  for (const e of document.querySelectorAll('[data-testid]')) m.add(e.getAttribute('data-testid'));
  return [...m];
});

/** 🔑 按面积取**可见的**节点工具条（跳过 0×0 常驻容器）。 */
const 可见工具条 = () => p.evaluate(() => {
  const 全部 = Array.from(document.querySelectorAll('.react-flow__node-toolbar'))
    .map((e) => { const r = e.getBoundingClientRect();
      return { el: e, 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10], 面积: r.width * r.height }; })
    .sort((a, b) => b.面积 - a.面积);
  const 可用 = 全部.filter((q) => q.盒[2] > 1 && q.盒[3] > 1);
  return { 全部: 全部.map((q) => ({ 盒: q.盒, 面积: Math.round(q.面积) })),
    可见数: 可用.length,
    最大: 可用.length ? { 盒: 可用[0].盒,
      祖先链: (() => { const c = []; for (let n = 可用[0].el; n && n !== document.body; n = n.parentElement) c.push(String(n.className || '').split(' ')[0] || n.tagName); return c.slice(0, 5); })(),
      按钮: Array.from(可用[0].el.querySelectorAll('button,[role=button]')).map((e) => { const q = e.getBoundingClientRect();
        return { aria: e.getAttribute('aria-label'), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim(),
          盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
          禁用: e.getAttribute('aria-disabled') || e.getAttribute('data-disabled') }; }) } : null };
});

const 编辑器清单 = () => p.evaluate(() => {
  const 根 = document.querySelector('[data-testid="text-editor-fullscreen-dialog"]') || document.querySelector('[role=dialog]');
  if (!根) return { __err: 'no-dialog' };
  const r = 根.getBoundingClientRect();
  return { 根: { tag: 根.tagName, testid: 根.getAttribute('data-testid'), role: 根.getAttribute('role'),
      aria: 根.getAttribute('aria-label'), cls: String(根.className || '').slice(0, 60),
      盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] },
    内部testid: Array.from(根.querySelectorAll('[data-testid]')).map((e) => { const q = e.getBoundingClientRect();
      return { testid: e.getAttribute('data-testid'), tag: e.tagName,
        盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width * 10) / 10, Math.round(q.height * 10) / 10],
        aria: e.getAttribute('aria-label'), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 36) }; }),
    contenteditable: Array.from(根.querySelectorAll('[contenteditable]')).map((e) => ({ tag: e.tagName, cls: String(e.className || '').slice(0, 50), testid: e.getAttribute('data-testid') })),
    按钮: Array.from(根.querySelectorAll('button,[role=button]')).map((e) => { const q = e.getBoundingClientRect();
      return { aria: e.getAttribute('aria-label'), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim(),
        盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
        禁用: e.getAttribute('aria-disabled') || e.getAttribute('data-disabled') }; }) };
});

const 全页找testid = (ns) => p.evaluate((a) => a.map((n) => {
  const els = document.querySelectorAll('[data-testid="' + n + '"]');
  return { testid: n, 命中数: els.length,
    盒: els.length ? (() => { const r = els[0].getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() : null,
    逐字: els.length ? (els[0].innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40) : null };
}), ns);

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
  rec.打开前testid = await testid清单();

  const 建 = await 建N个(p, '文本', 1, 断言, 76);
  rec.建 = 建;
  const SELF = 建.ids && 建.ids[0];
  if (!SELF) { rec.中止 = '建节点未成'; }
  else {
    // ---- 🔑 查工具条**之前**先把鼠标移回节点（工具条是悬停触发的）
    const 落 = await 独占像素(SELF);
    rec.落点 = 落;
    await p.mouse.move(落.落点[0], 落.落点[1]);
    await p.waitForTimeout(1400);
    rec.悬停时工具条 = await 可见工具条();
    断言('① 悬停后有可见工具条（宽高都 > 1）', (rec.悬停时工具条.可见数 || 0) >= 1, rec.悬停时工具条.全部);

    const 钮 = ((rec.悬停时工具条.最大 || {}).按钮) || [];
    rec.按钮 = 钮;
    const 全屏钮 = 钮.find((q) => q.aria === '全屏' || q.逐字 === '全屏');
    rec.全屏钮 = 全屏钮;
    if (!全屏钮) { rec.中止 = '可见工具条上没有「全屏」按钮'; }
    else {
      const 前置 = await p.evaluate(([x, y, id]) => { const h = document.elementFromPoint(x, y);
        const btn = h ? h.closest('button,[role=button]') : null;
        return { 命中aria: btn ? btn.getAttribute('aria-label') : null, 命中逐字: btn ? (btn.innerText || '').replace(/\s+/g, ' ').trim() : null,
          浮层: Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length,
          目标仍选中: !!document.querySelector(`.react-flow__node[data-id="${id}"].selected`),
          编辑器已开: !!document.querySelector('[data-testid="text-editor-fullscreen-dialog"]') }; },
        [全屏钮.盒[0] + Math.round(全屏钮.盒[2] / 2), 全屏钮.盒[1] + Math.round(全屏钮.盒[3] / 2), SELF]);
      rec.点全屏前 = 前置;
      if (前置.命中aria === '全屏' && 前置.浮层 === 0 && 前置.目标仍选中 && !前置.编辑器已开) {
        await p.mouse.click(全屏钮.盒[0] + Math.round(全屏钮.盒[2] / 2), 全屏钮.盒[1] + Math.round(全屏钮.盒[3] / 2));
        await p.waitForTimeout(2600);
      }
      rec.点后 = { 状态行: await R.status(), 浮层: await R.overlays() };
      rec.编辑器 = await 编辑器清单();
      rec.打开后testid = await testid清单();
      rec.差分 = { 新增: rec.打开后testid.filter((t) => !rec.打开前testid.includes(t)),
        消失: rec.打开前testid.filter((t) => !rec.打开后testid.includes(t)) };
      rec.五项核验 = await 全页找testid(['text-editor-fullscreen-dialog', 'text-editor-fullscreen-placeholder',
        'text-editor-fullscreen-scroll-region', 'text-editor-toolbar', 'text-editor-toolbar-separator',
        'text-editor-scroll-region', 'text-editor-placeholder']);
      断言('① 5 个待验 testid 至少有一个真身（不是全灭）', rec.五项核验.some((q) => q.命中数 > 0), rec.五项核验);
      断言('② 编辑器真的开了', !!(rec.编辑器 && rec.编辑器.根), rec.点后);

      if (await p.evaluate(() => !!document.querySelector('[data-testid="text-editor-fullscreen-dialog"]'))) {
        const 关 = await 可点落点(p, '[aria-label="Close full-screen editor"]', 3, 3);
        rec.关闭钮 = 关;
        if (!关.__err) {
          const 前置2 = await p.evaluate(([x, y]) => { const h = document.elementFromPoint(x, y); const b = h ? h.closest('button,[role=button]') : null;
            return { aria: b ? b.getAttribute('aria-label') : null, 对: !!(b && b.getAttribute('aria-label') === 'Close full-screen editor') }; }, [关.x, 关.y]);
          rec.点关闭前 = 前置2;
          if (前置2.对) { await p.mouse.click(关.x, 关.y); await p.waitForTimeout(2400); await settle(p, R); }
        }
      }
      rec.关后 = { 状态行: await R.status(), 浮层: await R.overlays() };
      rec.关后testid = await testid清单();
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
  zoom: await R.zoom(), 积分: await R.credits(), 剩余自建: 末.filter((x) => ((rec.建 && rec.建.ids) || []).includes(x)) };
rec.断言全过 = 断言过;
fs.writeFileSync(new URL('./_tmp-b144b.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify({ 中止: rec.中止, 异常: rec.异常, 落点: rec.落点 && rec.落点.总数, 悬停工具条: rec.悬停时工具条,
  按钮: rec.按钮, 全屏钮: rec.全屏钮, 点全屏前: rec.点全屏前, 点后: rec.点后, 编辑器: rec.编辑器,
  差分: rec.差分, 五项核验: rec.五项核验, 关闭钮: rec.关闭钮, 点关闭前: rec.点关闭前, 关后: rec.关后,
  归零差分: rec.归零差分, 删除: rec.删除, 收尾: rec.收尾 }, null, 1));
await b.close();
