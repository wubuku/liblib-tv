// 批次 142 归位 d 轮：**平移视图**把组从别人的节点/手柄底下挪出来，再解组。
//
// 🔴 前五版全部失败，卡点始终同一个：**组标题 SPAN 的落点被别人的
//   `DIV.react-flow__handle`（连接手柄）占据**。组卡片 `z-index: -2`、
//   未选中态整卡 `pointer-events: none`，所以：
//   「点标题选中组」被手柄挡住 → 选不中 → 「⌘⇧G」无从谈起 → 死锁。
//   `Tab` 也已证伪（40 次全落在 UI chrome 的按钮上，**根本不进画布节点**）。
//
// ✅ 本轮换招：**先按手册记载的「适配画布」快捷键（`⇧1`）把全部节点收进视野** ——
//   它会重排视口，让原本堆在一起的节点**散开**，组标题就有机会露出来。
//   ⚠️ 平移/缩放**只改视图、不改数据**（节点 canvas 坐标不动），共享画布可接受。
//   ⚠️ 按键前过 `keyGuard`；`⇧1` 是 Shift+1，不是字母键但同样先归位焦点。
//
// 顺带：本轮也会记录「适配画布」本身的行为（手册 §4.15 记过：缩放从 100% 变 62%）。
import { openCanvas, readers, settle, keyGuard, setZoom } from './jimeng-b135-lib.mjs';
import { 组数, idsOf, canvasPos } from './jimeng-b139-lib.mjs';
import fs from 'node:fs';

const 基线 = fs.readFileSync('/tmp/b120-baseline-ids.txt', 'utf8').split('\n').map((s) => s.trim()).filter(Boolean);
const rec = { 尝试: [] };
const { b, p } = await openCanvas();
const R = readers(p);

const 组信息 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node-group'))
  .filter((g) => !/^__group-resize-chrome__/.test(g.getAttribute('data-id') || ''))
  .map((g) => {
    const r = g.getBoundingClientRect();
    const 叶子 = Array.from(g.querySelectorAll('span,div')).filter((e) => {
      if (!(e.textContent || '').trim()) return false;
      if (e.querySelector('span,div')) return false;
      const er = e.getBoundingClientRect();
      return er.width > 1 && er.height > 1 && er.width < 200 && er.height < 60;
    })[0];
    const lr = 叶子 ? 叶子.getBoundingClientRect() : null;
    const lx = lr ? Math.round(lr.x + lr.width / 2) : null;
    const ly = lr ? Math.round(lr.y + lr.height / 2) : null;
    return { id: g.getAttribute('data-id'), 选中: g.classList.contains('selected'),
      卡片: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
      标题点: lx !== null ? [lx, ly] : null,
      标题命中: lx !== null ? (() => { const h = document.elementFromPoint(lx, ly);
        return h ? (h.tagName + '.' + String(h.className || '').split(' ')[0]).slice(0, 44) : null; })() : null };
  }));

try {
  await keyGuard(p);
  await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p), zoom: await R.zoom() };
  rec.适配前 = { 组: await 组信息(), canvas前: Object.keys(await canvasPos(p)).length };

  // ---- 适配画布：把焦点先交回画布，再按 ⇧1
  await p.mouse.click(8, 660); await p.waitForTimeout(700);
  const g = await keyGuard(p);
  rec.keyGuard = { safe: g.safe, where: g.where };
  if (g.safe) {
    await p.keyboard.press('Shift+Digit1');
    await p.waitForTimeout(2500);
    await settle(p, R);
  }
  rec.适配后 = { 状态行: await R.status(), zoom: await R.zoom(), 组: await 组信息() };
  // 关键：节点 canvas 坐标必须**一个都没变**（适配画布只改视图）
  const 后canvas = await canvasPos(p);
  rec.canvas位移 = Object.keys(后canvas).filter((k) => JSON.stringify(后canvas[k]) !== JSON.stringify(rec.适配前.canvas前[k])).length;

  // ---- 逐个组尝试：现在标题点应该没被压住了
  for (const ginfo of rec.适配后.组 || []) {
    if (!ginfo.标题点) { rec.尝试.push({ id: ginfo.id, 跳过: '无标题点' }); continue; }
    const [x, y] = ginfo.标题点;
    rec.尝试.push({ id: ginfo.id, 标题命中: ginfo.标题命中, 点: [x, y] });
    await p.mouse.click(x, y);
    await p.waitForTimeout(1400);
    const 选中了 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node-group'))
      .filter((q) => !/^__group-resize-chrome__/.test(q.getAttribute('data-id') || ''))
      .filter((q) => q.classList.contains('selected')).length);
    rec.尝试[rec.尝试.length - 1].点后选中真身组 = 选中了;
    if (选中了 > 0) {
      const { 可点落点 } = await import('./jimeng-b139-lib.mjs');
      const 解 = await 可点落点(p, '[data-toolbar-value="ungroup"]', 3, 3);
      rec.尝试[rec.尝试.length - 1].解除编组落点 = 解;
      if (!解.__err) {
        await p.mouse.click(解.x, 解.y);
        await p.waitForTimeout(2500);
        await settle(p, R);
      }
      rec.尝试[rec.尝试.length - 1].解后组数 = await 组数(p);
    }
  }
  rec.末尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p), zoom: await R.zoom() };
  rec.多余 = (await idsOf(p)).filter((x) => !基线.includes(x) && !/^__group-resize-chrome__/.test(x));
} catch (e) { rec.异常 = String(e && e.stack || e).slice(0, 500); }
fs.writeFileSync(new URL('./_tmp-b142-ungroup2.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log('适配前 zoom', rec.起点.zoom, '→ 适配后 zoom', rec.适配后 && rec.适配后.zoom);
console.log('适配后组', JSON.stringify(rec.适配后 && rec.适配后.组, null, 1));
console.log('尝试', JSON.stringify(rec.尝试, null, 1));
console.log('末尾', JSON.stringify(rec.末尾), '| 多余', JSON.stringify(rec.多余));
await b.close();
