// 批次 155-c —— 追「点导出时间线之后弹出来的那个浮层」是什么
//
// 🔑 155-b 追到的事实：点节点内的「导出时间线」**没有触发 download 事件**，
//    但**浮层数从 0 变成 1** ⇒ 它不是「一点就下载」，而是**先弹一层**。
//    手册 `timeline-node.md:166` 写的是一句式「点击 导出时间线 导出整条时间线」—— 🔴 **漏了中间这一层**。
//
// 🎯 本轮只回答：那一层是什么、有哪些 testid / 按钮 / 文案、能不能在里面真的导出。
// ⛔ 若那一层里有真正的「确认导出」按钮，**点它会产出对外文件** —— 本轮**只读不点**，
//    记录 DOM 契约后如实标注「未执行最终导出」；只有当它是纯展示层时才继续。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { 建N个, selCount, idsOf, canvasPos, 可点落点, 组数 } from './jimeng-b139-lib.mjs';

const rec = { 批次: '155c', 目的: '查「导出时间线」点开后弹出的是哪一层' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b155c.json', import.meta.url), JSON.stringify(rec, null, 1));
const 出图 = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const 串 = (x, n) => { const s = JSON.stringify(x, null, 1); return s === undefined ? 'undefined' : s.slice(0, n || 2000); };

const 找点 = (pred) => p.evaluate((pd) => {
  const cands = Array.from(document.querySelectorAll(pd.sel)).filter((b) => {
    const a = b.getAttribute('aria-label') || '';
    if (pd.字面等于 && a !== pd.字面等于) return false;
    if (pd.文字Includes && (b.innerText || '').replace(/\s+/g, ' ').trim().indexOf(pd.文字Includes) < 0) return false;
    if (pd.testidIncludes && (b.getAttribute('data-testid') || '').indexOf(pd.testidIncludes) < 0) return false;
    if (pd.在节点内 === true && !b.closest('.react-flow__node')) return false;
    return true;
  });
  const 全候选 = [];
  for (const b of cands) {
    const r = b.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) continue;
    const cx = Math.round(r.x + r.width / 2); const cy = Math.round(r.y + r.height / 2);
    const h = document.elementFromPoint(cx, cy);
    const btn = h && h.closest(pd.sel);
    全候选.push({ x: cx, y: cy, 宽: Math.round(r.width), 高: Math.round(r.height), 左: Math.round(r.x), 上: Math.round(r.y),
      aria: b.getAttribute('aria-label'), testid: b.getAttribute('data-testid'),
      逐字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24),
      在视口内: cx >= 0 && cy >= 0 && cx <= innerWidth && cy <= innerHeight, 中心是自己: btn === b });
  }
  const 可用 = 全候选.filter((z) => z.在视口内 && z.中心是自己);
  return { 候选数: cands.length, 全候选, 可用, 可用数: 可用.length };
}, pred);

// 全页面快照：找「刚多出来的那一层」是什么
const 全页快照 = () => p.evaluate(() => {
  const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; };
  return {
    对话框: Array.from(document.querySelectorAll('[role=dialog]')).map((e) => ({ testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'), 盒: 盒(e), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160) })),
    菜单: Array.from(document.querySelectorAll('[role=menu]')).map((e) => ({ testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'), 盒: 盒(e), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160) })),
    浮层: Array.from(document.querySelectorAll('[data-state=open]')).map((e) => ({ testid: e.getAttribute('data-testid'), 标签: e.tagName.toLowerCase(), aria: e.getAttribute('aria-label'), 盒: 盒(e) })),
    列表框: Array.from(document.querySelectorAll('[role=listbox],[role=alertdialog],[role=sheet]')).map((e) => ({ testid: e.getAttribute('data-testid'), 盒: 盒(e), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160) })),
  };
});

const { b, p } = await openCanvas();
const R = readers(p);
let 基线canvas = null;
try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(), 积分: await R.credits(), 选中: await selCount(p) };
  基线canvas = await canvasPos(p);
  rec.点前快照 = await 全页快照();
  rec.点前浮层数 = await R.overlays();

  const 建 = await 建N个(p, '时间线', 1, null, (await idsOf(p)).length);
  rec.建 = { ids: 建.ids, 护栏全过: (建.护栏 || []).every((h) => h.通过) };
  落盘();
  断言('⓪ 护栏建出 1 个时间线节点', (建.ids || []).length === 1, { 护栏: 建.护栏 });

  if (建.ids && 建.ids.length) {
    const 找 = await 找点({ sel: 'button,[role=button]', 字面等于: '导出时间线', 在节点内: true });
    rec.找点 = 找;
    const E = (找.可用 || [])[0];
    rec.用的点 = E || null;
    if (E) {
      const dl = p.waitForEvent('download', { timeout: 6000 }).catch(() => null);
      await p.mouse.click(E.x, E.y);
      const d = await dl;
      rec.有无下载事件 = !!d;
      if (d) { rec.建议文件名 = d.suggestedFilename(); await d.cancel().catch(() => {}); }
      await p.waitForTimeout(2000);
      rec.点后快照 = await 全页快照();
      rec.点后浮层数 = await R.overlays();
      rec.积分 = await R.credits();
      // 新出现的层 = 点后有、点前没有的
      const 前testid = new Set(rec.点前快照.浮层.map((x) => x.testid));
      rec.新出现的浮层 = rec.点后快照.浮层.filter((x) => !前testid.has(x.testid));
      rec.新出现的对话框 = rec.点后快照.对话框.filter((x) => !(rec.点前快照.对话框 || []).some((y) => y.testid === x.testid && y.盒.join() === x.盒.join()));
      落盘();
      console.log('\n点前浮层数', rec.点前浮层数, '→ 点后', rec.点后浮层数, '| download 事件 =', rec.有无下载事件);
      console.log('点前 浮层', 串(rec.点前快照.浮层, 800));
      console.log('\n点后 浮层', 串(rec.点后快照.浮层, 1400));
      console.log('\n🆕 新出现的浮层', 串(rec.新出现的浮层, 1400));
      console.log('\n点后 对话框', 串(rec.点后快照.对话框, 1200));
      console.log('\n🆕 新出现的对话框', 串(rec.新出现的对话框, 1400));
      console.log('\n点后 菜单', 串(rec.点后快照.菜单, 900));
      console.log('\n点后 列表框', 串(rec.点后快照.列表框, 900));
      断言('① 点「导出时间线」**多弹出一层**（浮层数 0 → 1）且**没有 download 事件**',
        rec.点后浮层数 > rec.点前浮层数 && rec.有无下载事件 === false,
        { 前: rec.点前浮层数, 后: rec.点后浮层数, 下载: rec.有无下载事件 });
      if ((rec.新出现的浮层 || []).length || (rec.新出现的对话框 || []).length) {
        await p.screenshot({ path: new URL('./59-timeline-export-overlay.png', 出图).pathname });
        rec.截图 = 'screenshots/59-timeline-export-overlay.png';
      }
      // 记录这一层里的全部按钮（**只读，一个都不点**）
      rec.层内按钮 = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role=button]'))
        .map((e) => { const r = e.getBoundingClientRect();
          return { aria: e.getAttribute('aria-label'), testid: e.getAttribute('data-testid'),
            逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18),
            盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
            disabled: e.getAttribute('aria-disabled'), 在节点内: !!e.closest('.react-flow__node') }; })
        .filter((z) => z.盒[0] > 0 && z.盒[1] > 0));
      落盘();
      console.log('\n导出层在场时页面全部可见按钮', 串(rec.层内按钮, 2600));
      await p.keyboard.press('Escape'); await p.waitForTimeout(1600);
      rec.Esc一次后浮层数 = await R.overlays();
      await p.keyboard.press('Escape'); await p.waitForTimeout(1600);
      rec.Esc两次后浮层数 = await R.overlays();
      console.log('\nEsc 一次后浮层', rec.Esc一次后浮层数, '| 两次后', rec.Esc两次后浮层数);
    }
  }

  // 收尾删除
  for (let k = 0; k < 4 && (await selCount(p)) > 0; k++) {
    const 空 = await p.evaluate(() => { const 坏 = (x, y) => { const h = document.elementFromPoint(x, y); if (!h) return 1;
      if (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button],[role=menuitem]')) return 1;
      if (h.closest('.react-flow__node') || h.closest('[data-testid="node-toolbar"]') || h.closest('[role=dialog],[role=menu],[role=listbox]')) return 1;
      return !(h.classList && h.classList.contains('react-flow__pane')); };
      for (let y = 90; y < innerHeight - 90; y += 8) for (let x = 360; x < innerWidth - 350; x += 8) if (!坏(x, y)) return { x, y };
      return { __err: 'no-free-pane' }; });
    if (空.__err) break; await p.mouse.click(空.x, 空.y); await p.waitForTimeout(1000);
  }
  rec.删除 = [];
  for (const x of (建.ids || [])) {
    const 前 = await idsOf(p);
    const 落 = await 可点落点(p, `.react-flow__node[data-id="${x}"]`, 4, 4);
    if (落.__err) { rec.删除.push({ id: x, __err: 'no-point' }); continue; }
    const 归属 = await p.evaluate(([x2, y, i]) => { const h = document.elementFromPoint(x2, y);
      const n = h && h.closest('.react-flow__node'); return { 对: !!(n && n.getAttribute('data-id') === i) }; }, [落.x, 落.y, x]);
    if (!归属.对) { rec.删除.push({ id: x, __err: 'wrong-target' }); continue; }
    await p.mouse.click(落.x, 落.y, { button: 'right' }); await p.waitForTimeout(1800);
    const del = await p.evaluate(() => {
      const els = Array.from(document.querySelectorAll('[role=menuitem],[role=menu] button,li,button'))
        .filter((e) => /^删除/.test((e.innerText || '').replace(/\s+/g, '').trim()));
      if (!els.length) return { __err: 'no-delete-item' };
      const e = els[0]; const r = e.getBoundingClientRect();
      for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2)
        for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) {
          const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y, 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim() }; }
      return { __err: 'no-point' };
    });
    if (del.__err) { rec.删除.push({ id: x, __err: del.__err }); continue; }
    await p.mouse.click(del.x, del.y); await p.waitForTimeout(2500); await settle(p, R);
    const 后 = await idsOf(p);
    rec.删除.push({ id: x, 消失: 前.filter((y) => !后.includes(y)) });
  }
  await setZoom(p, 60); await p.waitForTimeout(1400);
  const 末 = await idsOf(p); const 末c = await canvasPos(p);
  rec.收尾检查 = { 节点数: 末.length, 位移节点: 基线canvas ? Object.keys(基线canvas).filter((k) => 末c[k] && (末c[k][0] !== 基线canvas[k][0] || 末c[k][1] !== 基线canvas[k][1])) : null };
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

await settle(p, R);
const mm = await R.minimap();
if (!mm || mm.ariaPressed !== 'true') { const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3); if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400); } }
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(),
  zoom: await R.zoom(), 积分: await R.credits(), 组数: await 组数(p),
  边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length),
  残留自建: (await idsOf(p)).filter((x) => ((rec.建 || {}).ids || []).includes(x)) };
落盘();

console.log('\n收尾检查', JSON.stringify(rec.收尾检查));
console.log('收尾', JSON.stringify(rec.收尾), '| 小地图', JSON.stringify(rec.小地图 || await R.minimap()), '| 异常', rec.异常 || '无');
console.log('截图', rec.截图 || '无');
断言('② 建-删护栏全过 + 消失集合恰好 {SELF}', (rec.删除 || []).length > 0 && (rec.删除 || []).every((d) => d.消失 && d.消失.length === 1), { 删除: (rec.删除 || []).map((d) => d.消失 || d.__err) });
断言('③ 🔑 收尾积分**仍是 805**', String((rec.收尾 || {}).积分).indexOf('805') >= 0, { 积分: (rec.收尾 || {}).积分 });
if (rec.收尾检查 && rec.收尾检查.位移节点) 断言('④ 其余节点零位移', rec.收尾检查.位移节点.length === 0, rec.收尾检查);
rec.断言全过 = 断言过; 落盘();
await b.close();
