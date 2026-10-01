// 批次 64：关闭「方式 D 本地上传」的上传流程未验证。
//
// `create-first-node.md` 结尾写着：
//   「方式 D 的文件选择与上传完成态在当前轮次未实际执行，
//     正式标注为『入口已验证、上传流程待验证』。」
// 理由没写出来，但**它早已过期**：批次 22 就是用
// `page.waitForEvent('filechooser')` + `/tmp/b22-upload.png` 传成功的
// （批次 61 还用同一张图建出过带 `img` 的图片节点）。
// ⇒ 这是「未验证清单重审」这条纪律的第四个应验目标。
//
// 本轮把整条链路走完并登记：
//   点左栏「上传」→ filechooser 事件 → 选文件 → **密集采样**节点出现/标题/内容/工具条
//   → 完成态 → 积分核对 → 按 id 删净。
//
// 🔑 两处纪律：
//   ① 临时节点**记账**，收尾按 data-id 精确删（共享画布上那 6 个是别人的）；
//   ② 判「上传完成」不能只看节点出现了 —— 节点可能先是空壳再填充，
//      所以**密集采样**内容元素（`img`/`video`/`audio`）的出现时刻。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const SHOTS = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const OUT = new URL('./_tmp-b64-upload.json', import.meta.url);
const FILE = '/tmp/b22-upload.png';
const MINE = [];

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('ABORT: 找不到画布页面'); process.exit(1); }
await pinViewport(p);

const credit = () => p.evaluate(() => { const m = document.body.innerText.match(/(\d[\d,]*)\s*基础会员/); return m ? parseInt(m[1].replace(/,/g, ''), 10) : null; });
const statusLine = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const canvasPos = () => p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
  return [e.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null]; })));
const nodeIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const isEmpty = (x, y) => p.evaluate(([x, y]) => { const el = document.elementFromPoint(x, y); if (!el) return true;
  if (el.closest('.react-flow__node')) return false;
  if (el.closest('button,[role="button"],input,textarea,[role="menu"],[role="listbox"],[data-testid="node-toolbar"],[data-testid="workspace-bottom-dock-frame"],[data-testid="canvas-fixed-toolbar-left-rail"],[data-testid="canvas-top-bar-actions"],[data-testid="canvas-panel-launcher"],[data-testid="canvas-feature-sidecar"]')) return false;
  return true; }, [x, y]);
const findEmpty = async () => { for (let y = 110; y <= 600; y += 20) for (let x = 90; x <= 1240; x += 20) {
  if (x > 1140 && y > 570) continue; if (await isEmpty(x, y)) return { x, y }; } return null; };
const reset = async () => { for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(320); } };
const deselect = async () => { await reset(); const e = await findEmpty(); if (e) { await p.mouse.click(e.x, e.y); await p.waitForTimeout(600); } };
const selectMine = async (id) => { await deselect();
  const pts = await p.evaluate((vid) => { const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!n) return []; const r = n.getBoundingClientRect(); const o = [];
    for (let fy = 0.14; fy <= 0.88; fy += 0.07) for (let fx = 0.14; fx <= 0.88; fx += 0.07) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
      const el = document.elementFromPoint(x, y); if (!el || !el.closest(`.react-flow__node[data-id="${vid}"]`)) continue;
      if (el.closest('button,a,[role="button"],input,textarea,select,[role="menu"]')) continue; o.push({ x, y }); } return o; }, id);
  for (const pt of pts) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(600);
    if (await p.evaluate((v) => !!document.querySelector(`.react-flow__node[data-id="${v}"].selected`), id)) return true; } return false; };
const deleteById = async (id) => { await reset(); await selectMine(id); await p.waitForTimeout(400);
  await p.evaluate((vid) => { const e = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!e) return; const r = e.getBoundingClientRect();
    for (let fy = 0.12; fy <= 0.9; fy += 0.08) for (let fx = 0.12; fx <= 0.9; fx += 0.08) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const t = document.elementFromPoint(x, y); if (!t || !t.closest(`.react-flow__node[data-id="${vid}"]`)) continue;
      if (t.closest('button,a,[role="button"],input,textarea,select')) continue;
      e.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, clientX: x, clientY: y }));
      e.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, clientX: x, clientY: y }));
      e.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x, clientY: y })); return; } }, id);
  await p.waitForTimeout(900);
  if (await p.evaluate((v) => !!document.querySelector(`.react-flow__node[data-id="${v}"].selected`), id)) {
    await p.evaluate(() => { const e = document.querySelector('.react-flow__node.selected'); if (!e) return; const r = e.getBoundingClientRect();
      e.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 14) })); });
    await p.waitForTimeout(800);
    await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
      const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
    await p.waitForTimeout(1400); }
  await reset();
  return (await p.evaluate((v) => !document.querySelector(`.react-flow__node[data-id="${v}"]`), id)) ? 'deleted' : 'STILL-THERE'; };
const restoreZoom = async () => { for (let t = 0; t < 3; t++) { const z = await zoomOf();
    if (z && z.includes('60%')) { console.log('  缩放归位 ok:', z); return true; }
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
    const s = 'input[data-testid=canvas-zoom-percent-input]';
    if (await p.$(s)) { await p.fill(s, '60'); await p.keyboard.press('Enter'); await p.waitForTimeout(1100); }
    else { await p.keyboard.press('Escape'); await p.waitForTimeout(400); } }
  console.log('  缩放归位 FAILED:', await zoomOf()); return false; };

// 节点内容读数：标题行 / 卡片类名 / 内部媒体元素 / 工具条
const nodeRead = (id) => p.evaluate((vid) => {
  const e = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!e) return null;
  const r = e.getBoundingClientRect();
  const vis = (x) => { const q = x.getBoundingClientRect(); return q.width > 1 && q.height > 1; };
  return {
    cls: Array.from(e.classList).filter((c) => c.startsWith('react-flow__node-')).join(' '),
    aria: e.getAttribute('aria-label'),
    title: (() => { const t = Array.from(e.querySelectorAll('*')).find((x) => vis(x) && /Rename |Edit /.test(x.getAttribute('aria-label') || ''));
      return t ? (t.getAttribute('aria-label') || '').replace(/^Rename /, '') : null; })(),
    box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    media: Array.from(e.querySelectorAll('img,video,audio,canvas,svg')).filter(vis).map((x) => `${x.tagName.toLowerCase()}${x.tagName === 'IMG' ? ` src=${(x.getAttribute('src') || '').slice(0, 24)}…` : ''}`),
    imgs: Array.from(e.querySelectorAll('img')).filter(vis).map((x) => { const q = x.getBoundingClientRect();
      return { src: (x.getAttribute('src') || '').slice(0, 40), natural: `${x.naturalWidth}x${x.naturalHeight}`, box: `${Math.round(q.width)}x${Math.round(q.height)}` }; }),
    text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120),
    selected: e.classList.contains('selected'),
    toolbar: !!e.parentElement && !!document.querySelector('[data-testid="node-toolbar"]'),
  };
}, id);

const out = { startedAt: new Date().toISOString() };
const c0 = await credit();
console.log('=== 批次 64：方式 D 本地上传的完整链路 ===\n起点:', await statusLine(), '| 积分', c0, '| 缩放', await zoomOf());
out.start = { status: await statusLine(), credit: c0, zoom: await zoomOf() };
await restoreZoom();

try {
  // ── 0. 左栏「上传」入口
  const rail = await p.evaluate(() => Array.from(document.querySelectorAll('aside[data-testid="canvas-fixed-toolbar-left-rail"] button,[data-testid="canvas-fixed-toolbar-left-rail"] button'))
    .map((e) => { const r = e.getBoundingClientRect();
      return { aria: e.getAttribute('aria-label'), box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, vis: r.width > 1 }; }));
  console.log('\n左栏入口:', JSON.stringify(rail, null, 1));
  out.rail = rail;
  const up = rail.find((x) => x.vis && /上传/.test(x.aria || ''));
  if (!up) throw new Error('左栏找不到「上传」入口');
  console.log('\n上传入口:', JSON.stringify(up));

  await deselect();
  const pre = await nodeIds();
  console.log('上传前节点数:', pre.length, '| 状态', await statusLine());

  // ── 1. 点「上传」→ 接 filechooser
  console.log('\n点「上传」并接 filechooser…');
  const mm = up.box.match(/(\d+)x(\d+)@(-?\d+),(-?\d+)/);
  const bw = Number(mm[1]), bh = Number(mm[2]), ox = Number(mm[3]), oy = Number(mm[4]);
  const pt = { x: Math.round(ox + bw / 2), y: Math.round(oy + bh / 2) };
  const land = await p.evaluate(([x, y]) => { const t = document.elementFromPoint(x, y); const o = t && t.closest('button');
    return { tag: t && t.tagName, aria: o && o.getAttribute('aria-label'), ok: !!o }; }, [pt.x, pt.y]);
  console.log('  落点:', JSON.stringify(land));
  if (!land.ok) throw new Error('上传入口落点不是按钮');

  const chooserP = p.waitForEvent('filechooser', { timeout: 8000 });
  await p.mouse.click(pt.x, pt.y);
  const chooser = await chooserP;
  console.log('  ✅ filechooser 事件触发 | multiple =', chooser.isMultiple());
  out.chooser = { multiple: chooser.isMultiple() };
  const t0 = Date.now();
  await chooser.setFiles([FILE]);
  console.log('  已 setFiles:', FILE);

  // ── 2. 密集采样：节点何时出现 / 何时有内容
  console.log('\n=== 密集采样（t=0…8000ms）===');
  const ser = [];
  for (const t of [0, 300, 700, 1200, 1800, 2500, 3500, 5000, 6500, 8000]) {
    const w = t0 + t - Date.now(); if (w > 0) await p.waitForTimeout(w);
    const ids = (await nodeIds()).filter((x) => !pre.includes(x));
    const st = await statusLine(); const cr = await credit();
    let rd = null;
    if (ids.length === 1) rd = await nodeRead(ids[0]);
    ser.push({ t, newNodes: ids.length, id: ids[0] || null, status: st, credit: cr,
      cls: rd && rd.cls, title: rd && rd.title, imgs: rd && rd.imgs, media: rd && rd.media, text: rd && rd.text });
    console.log(`  t=${String(t).padStart(4)}ms 新节点=${ids.length} ${st} 积分${cr}` +
      (rd ? ` | ${rd.cls} | 标题=${JSON.stringify(rd.title)} | img=${JSON.stringify(rd.imgs)}` : ''));
    if (ids.length === 1) { MINE.push(ids[0]); }
  }
  out.series = ser;
  const finalIds = (await nodeIds()).filter((x) => !pre.includes(x));
  console.log('\n最终新增节点:', JSON.stringify(finalIds), '| 状态', await statusLine());
  if (finalIds.length === 1) {
    if (!MINE.includes(finalIds[0])) MINE.push(finalIds[0]);
    const rd = await nodeRead(finalIds[0]);
    console.log('\n=== 完成态读数 ===');
    console.log(JSON.stringify(rd, null, 1));
    out.final = rd;
    // 选中它看工具条
    if (await selectMine(finalIds[0])) { await p.waitForTimeout(1600);
      const tb = await p.evaluate(() => { const t = document.querySelector('[data-testid="node-toolbar"]'); if (!t) return null;
        const r = t.getBoundingClientRect();
        return { box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
          buttons: Array.from(t.querySelectorAll('button,[role="button"]')).filter((x) => x.getBoundingClientRect().width > 1)
            .map((x) => { const q = x.getBoundingClientRect(); return { aria: x.getAttribute('aria-label'), text: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20), box: `${Math.round(q.width)}x${Math.round(q.height)}` }; }) }; });
      console.log('\n选中后工具条:', JSON.stringify(tb, null, 1));
      out.toolbar = tb;
      await p.screenshot({ path: new URL('64-upload-node-selected.png', SHOTS).pathname, clip: { x: 260, y: 420, width: 720, height: 240 } });
      console.log('📷 64-upload-node-selected.png');
    }
    await reset(); await p.waitForTimeout(600);
    const rd2 = await nodeRead(finalIds[0]);
    await p.screenshot({ path: new URL('64-upload-node-idle.png', SHOTS).pathname, clip: { x: 260, y: 420, width: 720, height: 240 } });
    console.log('\n📷 64-upload-node-idle.png（未选中）');
    console.log('未选中读数:', JSON.stringify({ cls: rd2.cls, aria: rd2.aria, imgs: rd2.imgs, text: rd2.text }));
  }
  const cE = await credit();
  console.log('\n=== 积分全程 ===', c0, '->', cE, 'Δ=', cE - c0);
  out.creditEnd = cE;
} catch (e) { console.error('ABORT:', e.message); out.error = e.message; }
finally {
  console.log('\n=== 收尾 ===');
  const now = await nodeIds();
  for (const id of MINE) if (now.includes(id)) console.log('删', id, '->', await deleteById(id));
  for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(300); }
  await restoreZoom();
  for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(300); }
  const fin = await canvasPos();
  let dev = 0;
  for (const [id, b2] of Object.entries(BASE.nodes)) { const cur = fin[id];
    const d = cur && b2.canvas ? [Math.round((cur[0] - b2.canvas[0]) * 100) / 100, Math.round((cur[1] - b2.canvas[1]) * 100) / 100] : 'MISSING';
    if (d === 'MISSING' || (Array.isArray(d) && (Math.abs(d[0]) > 0.01 || Math.abs(d[1]) > 0.01))) dev++; }
  console.log('终态:', await statusLine(), '| 缩放', await zoomOf(), '| 积分', await credit(), '| 节点', Object.keys(fin).length, '| 偏离', dev);
  console.log('剩余待删:', JSON.stringify(MINE.filter((id) => fin[id])));
  out.end = { status: await statusLine(), zoom: await zoomOf(), credit: await credit(), dev, mineLeft: MINE.filter((id) => fin[id]) };
  writeFileSync(OUT, JSON.stringify(out, null, 1));
  console.log('写入', OUT.pathname);
  await b.close();
}
