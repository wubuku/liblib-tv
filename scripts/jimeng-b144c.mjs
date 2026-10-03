// 批次 144 c 轮 —— 钉死两处与旧记录的差异，并拍**手册至今没有过**的文本全屏编辑器图。
//
// b 轮已把 4 个「全灭 testid」验成真身，但还剩两处需要读死：
//   ① §3.14 记节点工具条「**185×40** 三项」，b 轮实测是 **192×40**（差 7px）。
//   ② §3.56.2 记「打开全屏编辑器后，消失的正是画布上的 `node-toolbar` /
//      `selection-context-toolbar` / `node-feature-chrome-host` —— 被全屏编辑器顶掉了」。
//      b 轮的 testid 差分**没有这三项**，只少了 1 个 `default-feature-overlay-interaction-boundary`。
//      已知：`.react-flow__node-toolbar` 在画布上**本来就有 2 个常驻 0×0 容器**
//      （b 轮实测三个实例：192×40 + 两个 0×0）⇒ 「消失」可能指的是**可见那个**。
//      本轮读编辑器打开时它们各自的实例数与盒，把这件事读死。
//
// 📌 截图价值：时间线全屏编辑器拍过（`47-timeline-fullscreen-editor.png`），
//   **文本全屏编辑器全册从未拍过**（`13-edit-text-node-editing.png` 是行内编辑，不是全屏）。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { 建N个, selCount, idsOf, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 144, 轮: 'c', 目的: '钉死工具条宽度 + 编辑器打开时的工具条归属；拍全屏编辑器图' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 出图 = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);

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

/** 画布上各类 chrome 容器的实例数与盒 —— 用来判「谁被顶掉了」。 */
const chrome盘点 = () => p.evaluate(() => {
  const 读 = (sel) => Array.from(document.querySelectorAll(sel)).map((e) => { const r = e.getBoundingClientRect();
    return { 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10],
      testid: e.getAttribute('data-testid'), 可见: r.width > 1 && r.height > 1 }; });
  return {
    nodeToolbar: 读('.react-flow__node-toolbar'),
    nodeToolbarTestid: 读('[data-testid="node-toolbar"]'),
    featureChromeHost: 读('[data-testid="node-feature-chrome-host"]'),
    selectionContextToolbar: 读('[data-testid="selection-context-toolbar"]'),
    popupHost: 读('[data-testid="selection-context-toolbar-popup-host"]'),
    默认边界: 读('[data-testid="default-feature-overlay-interaction-boundary"]'),
    编辑器: 读('[data-testid="text-editor-fullscreen-dialog"]'),
  };
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
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom() };
  rec.建前chrome = await chrome盘点();

  const 建 = await 建N个(p, '文本', 1, 断言, 76);
  rec.建 = 建;
  const SELF = 建.ids && 建.ids[0];
  if (!SELF) { rec.中止 = '建节点未成'; }
  else {
    const 落 = await 独占像素(SELF);
    await p.mouse.move(落.落点[0], 落.落点[1]);
    await p.waitForTimeout(1500);
    rec.悬停chrome = await chrome盘点();
    const 可见工具条 = rec.悬停chrome.nodeToolbar.filter((q) => q.可见).sort((a, b) => b.盒[2] * b.盒[3] - a.盒[2] * a.盒[3])[0];
    rec.可见工具条 = 可见工具条;
    断言('① 节点工具条实测宽度（§3.14 记 185）', 可见工具条 !== undefined, { 可见工具条 });
    rec.工具条按钮 = await p.evaluate(() => {
      const tb = Array.from(document.querySelectorAll('.react-flow__node-toolbar'))
        .map((e) => ({ e, r: e.getBoundingClientRect() })).sort((a, b) => b.r.width * b.r.height - a.r.width * a.r.height)[0];
      return tb && tb.r.width > 1 ? Array.from(tb.e.querySelectorAll('button,[role=button]')).map((e) => { const q = e.getBoundingClientRect();
        return { aria: e.getAttribute('aria-label'), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim(),
          盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width * 10) / 10, Math.round(q.height * 10) / 10] }; }) : [];
    });
    const 全屏钮 = rec.工具条按钮.find((q) => q.aria === '全屏');
    if (!全屏钮) { rec.中止 = '没有「全屏」按钮'; }
    else {
      const 前置 = await p.evaluate(([x, y, id]) => { const h = document.elementFromPoint(x, y); const b = h ? h.closest('button,[role=button]') : null;
        return { aria: b ? b.getAttribute('aria-label') : null, 对: !!(b && b.getAttribute('aria-label') === '全屏'),
          浮层: Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length,
          目标仍选中: !!document.querySelector(`.react-flow__node[data-id="${id}"].selected`) }; },
        [全屏钮.盒[0] + 16, 全屏钮.盒[1] + 16, SELF]);
      rec.点全屏前 = 前置;
      if (前置.对 && 前置.浮层 === 0 && 前置.目标仍选中) {
        await p.mouse.click(全屏钮.盒[0] + 16, 全屏钮.盒[1] + 16);
        await p.waitForTimeout(2600);
      }
      rec.编辑器chrome = await chrome盘点();
      rec.编辑器断言 = await p.evaluate(() => {
        const d = document.querySelector('[data-testid="text-editor-fullscreen-dialog"]');
        const ph = document.querySelectorAll('[data-testid="text-editor-fullscreen-placeholder"]').length;
        const wrong = document.querySelectorAll('[data-testid="text-editor-fullscreen-scroll-region"]').length;
        const sr = document.querySelectorAll('[data-testid="text-editor-scroll-region"]').length;
        const tb = document.querySelector('[data-testid="text-editor-toolbar"]');
        const box = (e) => { if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10]; };
        return { 对话框: d ? box(d) : null, placeholder命中: ph, 错拼命中: wrong,
          scrollRegion命中: sr, scrollRegion: box(document.querySelector('[data-testid="text-editor-scroll-region"]')),
          工具条aria: tb ? tb.getAttribute('aria-label') : null, 工具条: box(tb),
          标题片: (() => { const t = Array.from(d.querySelectorAll('span,div')).map((e) => (e.innerText || '').trim())
            .filter((s) => /\.md$/.test(s) && s.length < 30); return t.slice(0, 3); })() };
      });
      rec.编辑器断言读数 = rec.编辑器断言;
      断言('② text-editor-fullscreen-placeholder 命中恰好 1', rec.编辑器断言.placeholder命中 === 1, rec.编辑器断言);
      断言('③ text-editor-fullscreen-scroll-region（错拼）命中 0', rec.编辑器断言.错拼命中 === 0, rec.编辑器断言);
      断言('④ text-editor-scroll-region 命中 1', rec.编辑器断言.scrollRegion命中 === 1, rec.编辑器断言);
      断言('⑤ 工具条 aria 逐字 Text formatting', rec.编辑器断言.工具条aria === 'Text formatting', rec.编辑器断言);

      // 拍前复查：浮层仍在、鼠标移开不关浮层
      await p.mouse.move(640, 690); await p.waitForTimeout(700);
      rec.拍前 = { 对话框还在: await p.evaluate(() => !!document.querySelector('[data-testid="text-editor-fullscreen-dialog"]')),
        浮层数: await R.overlays(), 状态行: await R.status() };
      断言('⑥ 鼠标移开后编辑器仍在（不是悬停浮层）', rec.拍前.对话框还在, rec.拍前);
      const f = new URL('./53-text-fullscreen-editor.png', 出图);
      await p.screenshot({ path: f.pathname });
      rec.截图 = 'screenshots/53-text-fullscreen-editor.png';

      const 关 = await 可点落点(p, '[aria-label="Close full-screen editor"]', 3, 3);
      rec.关闭钮 = 关;
      if (!关.__err) {
        const 前置2 = await p.evaluate(([x, y]) => { const h = document.elementFromPoint(x, y); const b = h ? h.closest('button,[role=button]') : null;
          return { 对: !!(b && b.getAttribute('aria-label') === 'Close full-screen editor') }; }, [关.x, 关.y]);
        if (前置2.对) { await p.mouse.click(关.x, 关.y); await p.waitForTimeout(2400); await settle(p, R); }
        rec.关后chrome = await chrome盘点();
        rec.关后 = { 对话框还在: await p.evaluate(() => !!document.querySelector('[data-testid="text-editor-fullscreen-dialog"]')), 浮层: await R.overlays() };
      }
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
fs.writeFileSync(new URL('./_tmp-b144c.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify({ 中止: rec.中止, 异常: rec.异常, 可见工具条: rec.可见工具条, 工具条按钮: rec.工具条按钮,
  建前chrome: rec.建前chrome, 悬停chrome: rec.悬停chrome, 编辑器chrome: rec.编辑器chrome, 关后chrome: rec.关后chrome,
  编辑器断言: rec.编辑器断言, 拍前: rec.拍前, 截图: rec.截图, 关闭钮: rec.关闭钮, 关后: rec.关后,
  删除: rec.删除, 收尾: rec.收尾 }, null, 1));
await b.close();
