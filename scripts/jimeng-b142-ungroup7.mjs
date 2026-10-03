// 批次 142 归位 i 轮（**已验证的完整归位流程**）：删掉最后 1 条边 + 1 个孤儿节点。
//
// ✅ 本轮确认了「点组卡片本体（不是中心、不是标题）」这条路是可靠的：
//   逐格扫组卡片矩形，命中组真身或其后代的点有 **972 / 3800** 个
//   （全在卡片**边缘带**上 —— 中心区域被自己的 `DIV.absolute` 内层占着，
//    而那层是 `pointer-events: none`，点它等于点空白）。
//   命中后一点，组真身立刻 `selected`、组工具条出现、点「解除编组」生效。
//   ⇒ **归位三步**：① 滚轮把组带进视口 ② 逐格扫出命中组本体的点并点击
//      ③ 点工具条「解除编组」。两步之后组成员回到顶层、可点、可删。
//
// 本轮只做收尾：删边（批次 136 已验成的路径）+ 删孤儿节点。
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { 组数, idsOf, canvasPos, 可点落点 } from './jimeng-b139-lib.mjs';
import fs from 'node:fs';

const 基线 = fs.readFileSync('/tmp/b120-baseline-ids.txt', 'utf8').split('\n').map((s) => s.trim()).filter(Boolean);
const rec = {};
const { b, p } = await openCanvas();
const R = readers(p);

try {
  await keyGuard(p);
  await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p) };
  rec.边起点 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__edge')).map((e) => {
    const r = e.getBoundingClientRect();
    const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
    return { testid: e.getAttribute('data-testid'), dataState: e.getAttribute('data-state'),
      屏上: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }, 中点: [cx, cy],
      在视口内: r.top >= 66 && r.bottom <= 690 && r.left >= 0 && r.right <= 1270 };
  }));

  // ---- 删边：先确保边在视口内（滚轮带进来），再走批次 136 的四步
  const e0 = rec.边起点[0];
  if (e0) {
    if (!e0.在视口内) {
      await p.mouse.move(640, 400);
      for (let i = 0; i < 60; i++) {
        const 在 = await p.evaluate(() => {
          const e = document.querySelector('.react-flow__edge');
          if (!e) return true;
          const r = e.getBoundingClientRect();
          return r.top >= 66 && r.bottom <= 690 && r.left >= 0 && r.right <= 1270;
        });
        if (在) break;
        await p.mouse.wheel(0, 240);
        await p.waitForTimeout(260);
      }
    }
    const 边 = await p.evaluate(() => {
      const e = document.querySelector('.react-flow__edge'); if (!e) return null;
      const r = e.getBoundingClientRect();
      return { 中点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], state: e.getAttribute('data-state'),
        命中: (() => { const h = document.elementFromPoint(Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2));
          return h ? (h.tagName + '.' + String(h.className || '').split(' ')[0]).slice(0, 40) : null; })() };
    });
    rec.边现况 = 边;
    if (边) {
      // ① 不先选中：点中点（若已 selected 则不点，否则点一下反而取消）
      if (边.state !== 'selected') { await p.mouse.click(边.中点[0], 边.中点[1]); await p.waitForTimeout(1300); }
      const 选中后 = await p.evaluate(() => ({
        state: (document.querySelector('.react-flow__edge') || { getAttribute: () => null }).getAttribute('data-state'),
        钮: !!document.querySelector('[data-testid$="-control"]') }));
      rec.边选中后 = 选中后;
      if (选中后.state === 'selected' && 选中后.钮) {
        const 落 = await 可点落点(p, '[data-testid$="-control"]', 3, 3);
        rec.删钮落点 = 落;
        const 前置 = await p.evaluate(() => ({
          边还selected: (document.querySelector('.react-flow__edge') || { getAttribute: () => null }).getAttribute('data-state') === 'selected',
          钮还在: !!document.querySelector('[data-testid$="-control"]') }));
        rec['点X前复查'] = 前置;
        if (前置.边还selected && 前置.钮还在 && !落.__err) {
          await p.mouse.click(落.x, 落.y);
          await p.waitForTimeout(2500);
          await settle(p, R);
        }
      }
    }
    rec.删边后 = { 状态行: await R.status(), 边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length) };
  }

  // ---- 删孤儿节点
  const 当前 = await idsOf(p);
  rec.多余 = 当前.filter((x) => !基线.includes(x) && !/^__group-resize-chrome__/.test(x));
  rec.删除 = [];
  for (const id of rec.多余) {
    // 先把它带进视口
    for (let i = 0; i < 60; i++) {
      const 在 = await p.evaluate((k) => {
        const n = document.querySelector(`.react-flow__node[data-id="${k}"]`); if (!n) return true;
        const r = n.getBoundingClientRect();
        return r.top >= 66 && r.bottom <= 690 && r.left >= 0 && r.right <= 1270;
      }, id);
      if (在) break;
      await p.mouse.move(640, 400);
      await p.mouse.wheel(0, 240);
      await p.waitForTimeout(240);
    }
    // 清选中 → 单选 → 右键 → 删除
    const 空 = await p.evaluate(() => {
      const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
      for (let y = 660; y >= 90; y -= 6) for (let x = 360; x <= innerWidth - 360; x += 8) {
        const h = document.elementFromPoint(x, y);
        if (h && h.classList && h.classList.contains('react-flow__pane')
          && !nodes.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return { x, y };
      } return null;
    });
    if (空) { await p.mouse.click(空.x, 空.y); await p.waitForTimeout(900); }
    const 落 = await 可点落点(p, `.react-flow__node[data-id="${id}"]`, 4, 4);
    if (落.__err) { rec.删除.push({ id, 失败: '单选落点', 落 }); continue; }
    await p.mouse.click(落.x, 落.y);
    await p.waitForTimeout(1000);
    const 选中 = await p.evaluate((k) => {
      const s = Array.from(document.querySelectorAll('.react-flow__node.selected'))
        .filter((n) => !/^__group-resize-chrome__/.test(n.getAttribute('data-id') || ''))
        .map((n) => n.getAttribute('data-id'));
      return { 数: s.length, 选中: s }; }, id);
    rec.删除.push({ id, 单选后: 选中 });
    if (选中.数 !== 1 || 选中.选中[0] !== id) continue;
    await p.mouse.click(落.x, 落.y, { button: 'right' });
    await p.waitForTimeout(1600);
    const del = await p.evaluate(() => {
      const els = Array.from(document.querySelectorAll('[role=menuitem],[role=menu] button,li,button'))
        .filter((e) => /^删除/.test((e.innerText || '').replace(/\s+/g, '').trim()));
      if (!els.length) return { __err: 'no-delete-item' };
      const e = els[0]; const r = e.getBoundingClientRect();
      for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2)
        for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) {
          const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y, 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim() };
        }
      return { __err: 'no-point' };
    });
    rec.删除[rec.删除.length - 1].删除项 = del;
    if (!del.__err) { await p.mouse.click(del.x, del.y); await p.waitForTimeout(2300); await settle(p, R); }
    rec.删除[rec.删除.length - 1].已消失 = !(await idsOf(p)).includes(id);
  }

  // ---- 收尾：缩放归 60% + 重开小地图
  const { setZoom } = await import('./jimeng-b135-lib.mjs');
  const z = await setZoom(p, 60);
  rec.归位 = { zoom: await R.zoom(), 追平: z.scale已追平 };
  if ((await R.minimap()) && (await R.minimap()).ariaPressed !== 'true') {
    const mm = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3);
    if (!mm.__err) { await p.mouse.click(mm.x, mm.y); await p.waitForTimeout(1200); }
  }
  const 终 = await idsOf(p);
  rec.末尾 = { 状态行: await R.status(), 节点数: 终.length, 组数: await 组数(p),
    边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length),
    浮层: await R.overlays(), 选中: await R.selCount(), zoom: await R.zoom(), minimap: await R.minimap() };
  rec.与基线差集 = { 多: 终.filter((x) => !基线.includes(x) && !/^__group-resize-chrome__/.test(x)), 少: 基线.filter((x) => !终.includes(x)) };
  rec.是否干净 = (await 组数(p)) === 0 && rec.与基线差集.多.length === 0 && rec.与基线差集.少.length === 0
    && rec.末尾.边数 === 0;
} catch (e) { rec.异常 = String(e && e.stack || e).slice(0, 600); }
fs.writeFileSync(new URL('./_tmp-b142-ungroup7.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log('起点', JSON.stringify(rec.起点));
console.log('边', JSON.stringify(rec.边起点), '| 删边后', JSON.stringify(rec.删边后));
console.log('删除', JSON.stringify(rec.删除, null, 1));
console.log('末尾', JSON.stringify(rec.末尾, null, 1));
console.log('差集', JSON.stringify(rec.与基线差集), '| 是否干净', rec.是否干净);
await b.close();
