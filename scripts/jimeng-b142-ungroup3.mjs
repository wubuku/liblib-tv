// 批次 142 归位 e 轮：删掉意外产生的边，并把两个 0 成员空组清掉。
//
// 🔴 当前画布状态（被前几轮弄脏）：`79 nodes, 1 edge, 2 组（均 0 成员）, 缩放 20%`。
//   `⌘Z` 撤不掉那条边（实测）。
//
// 本轮两件事：
//   ① 删边：走批次 136 已验成的路径 —— 点边中点选中 → 点 `Delete connection` ×。
//      ⚠️ 批次 136 的纪律：边可能已是 selected（先读 `data-state`），点中点会**取消**选中；
//      点 × 之前要**复查按钮还在 + 边仍 selected**（点别处会取消选中、按钮消失）。
//   ② 删组：先试「点组卡片**中心**」（选中态下卡片 `pointer-events: auto` 可点）——
//      组是 0 成员空组，中心没有成员节点遮挡。
//      删组走**右键 →「删除」**（手册记：编组卡片的右键「删除」会连成员一起删；
//      这里是 0 成员组，**删它没有副作用** —— 这正是必须**先解组**的原因在本轮不成立）。
//      ⚠️ 删完必须核对**组数减少 1 且成员数不变**。
import { openCanvas, readers, settle, keyGuard, setZoom } from './jimeng-b135-lib.mjs';
import { 组数, idsOf, selCount, 可点落点, 组数 as 真身组数 } from './jimeng-b139-lib.mjs';
import fs from 'node:fs';

const 基线 = fs.readFileSync('/tmp/b120-baseline-ids.txt', 'utf8').split('\n').map((s) => s.trim()).filter(Boolean);
const rec = {};
const { b, p } = await openCanvas();
const R = readers(p);

try {
  await keyGuard(p);
  await settle(p, R);
  // ⚠️ 先把缩放拉回 60%，让元素回到可点的正常尺寸（20% 下什么都点不中）
  const z = await setZoom(p, 60);
  rec.归位缩放 = { zoom: await R.zoom(), 追平: z.scale已追平 };
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p) };

  // ---- ① 删边
  const 边信息 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__edge')).map((e) => {
    const r = e.getBoundingClientRect();
    const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
    return { testid: e.getAttribute('data-testid'), dataState: e.getAttribute('data-state'),
      屏上: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
      中点: [cx, cy], 中点命中: (() => { const h = document.elementFromPoint(cx, cy);
        return h ? (h.tagName + '.' + String(h.className || '').split(' ')[0]).slice(0, 40) : null; })() };
  }));
  rec.边 = 边信息;
  if (边信息.length) {
    const e0 = 边信息[0];
    // 前置：若已 selected 就不点中点（点了反而取消）
    if (e0.dataState !== 'selected') {
      await p.mouse.click(e0.中点[0], e0.中点[1]);
      await p.waitForTimeout(1200);
    }
    const 选中态 = await p.evaluate(() => {
      const e = document.querySelector('.react-flow__edge');
      const btn = document.querySelector('[data-testid$="-control"]');
      return { 边state: e ? e.getAttribute('data-state') : null,
        删除钮: btn ? { tag: btn.tagName, aria: btn.getAttribute('aria-label'),
          矩形: (() => { const r = btn.getBoundingClientRect();
            return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; })() } : null };
    });
    rec.边选中后 = 选中态;
    if (选中态.边state === 'selected' && 选中态.删除钮) {
      const 落 = await 可点落点(p, '[data-testid$="-control"]', 3, 3);
      rec.删除钮落点 = 落;
      // 🔴 点 × 之前**复查**（批次 136 立的纪律）：点别处会取消选中、按钮消失
      const 前置 = await p.evaluate(() => ({
        边还selected: (document.querySelector('.react-flow__edge') || { getAttribute: () => null }).getAttribute('data-state') === 'selected',
        钮还在: !!document.querySelector('[data-testid$="-control"]') }));
      rec["点X前复查"] = 前置;
      if (前置.边还selected && 前置.钮还在 && !落.__err) {
        await p.mouse.click(落.x, 落.y);
        await p.waitForTimeout(2500);
        await settle(p, R);
      }
    }
    rec.删边后 = await R.status();
  }

  // ---- ② 删组：点组卡片中心（0 成员 ⇒ 中心无成员遮挡）
  rec.删组 = [];
  for (let k = 0; k < 4 && (await 组数(p)) > 0; k++) {
    const 中心 = await p.evaluate(() => {
      const gs = Array.from(document.querySelectorAll('.react-flow__node-group'))
        .filter((g) => !/^__group-resize-chrome__/.test(g.getAttribute('data-id') || ''));
      if (!gs.length) return null;
      return gs.map((g) => { const r = g.getBoundingClientRect();
        return { id: g.getAttribute('data-id'),
          中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
          成员数: g.querySelectorAll('.react-flow__node').length,
          中心命中: (() => { const h = document.elementFromPoint(Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2));
            return h ? (h.tagName + '.' + String(h.className || '').split(' ')[0]).slice(0, 40) : null; })() }; });
    });
    rec.删组.push({ 第k轮: k, 中心 });
    if (!中心 || !中心.length) break;
    const g0 = 中心[0];
    // 点中心选中组
    await p.mouse.click(g0.中心[0], g0.中心[1]);
    await p.waitForTimeout(1300);
    const 选中组 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node-group'))
      .filter((g) => !/^__group-resize-chrome__/.test(g.getAttribute('data-id') || ''))
      .filter((g) => g.classList.contains('selected')).length);
    rec.删组[rec.删组.length - 1].点后选中组 = 选中组;
    if (选中组 > 0) {
      // 优先走「解除编组」按钮
      const 解 = await 可点落点(p, '[data-toolbar-value="ungroup"]', 3, 3);
      rec.删组[rec.删组.length - 1].解除编组落点 = 解;
      if (!解.__err) {
        await p.mouse.click(解.x, 解.y);
        await p.waitForTimeout(2500);
        await settle(p, R);
        rec.删组[rec.删组.length - 1].解后组数 = await 组数(p);
        if ((await 组数(p)) === 0) break;
        continue;
      }
    }
    // 兜底：右键组中心 → 上下文菜单「删除」
    const 右 = 中心[0];
    await p.mouse.click(右.中心[0], 右.中心[1], { button: 'right' });
    await p.waitForTimeout(1600);
    const 菜单 = await p.evaluate(() => Array.from(document.querySelectorAll('[role=menuitem]'))
      .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()));
    rec.删组[rec.删组.length - 1].右键菜单 = 菜单;
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
    rec.删组[rec.删组.length - 1].删除项 = del;
    if (!del.__err) {
      await p.mouse.click(del.x, del.y);
      await p.waitForTimeout(2500);
      await settle(p, R);
      rec.删组[rec.删组.length - 1].删后组数 = await 组数(p);
    }
  }

  const 终 = await idsOf(p);
  rec.末尾 = { 状态行: await R.status(), 节点数: 终.length, 组数: await 组数(p), 边: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length) };
  rec.多余 = 终.filter((x) => !基线.includes(x) && !/^__group-resize-chrome__/.test(x));
  rec.与基线差集 = { 多: 终.filter((x) => !基线.includes(x) && !/^__group-resize-chrome__/.test(x)), 少: 基线.filter((x) => !终.includes(x)) };
} catch (e) { rec.异常 = String(e && e.stack || e).slice(0, 600); }
fs.writeFileSync(new URL('./_tmp-b142-ungroup3.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log('起点', JSON.stringify(rec.起点));
console.log('边', JSON.stringify(rec.边), '| 边选中后', JSON.stringify(rec.边选中后));
console.log('删边后', rec.删边后);
console.log('删组', JSON.stringify(rec.删组, null, 1));
console.log('末尾', JSON.stringify(rec.末尾), '| 差集', JSON.stringify(rec.与基线差集));
await b.close();
