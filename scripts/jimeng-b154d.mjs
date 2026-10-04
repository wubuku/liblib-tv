// 批次 154-d —— **只补 Q2**（「从画布选择」全屏拾取模式）
//
// 🔴 154-c 的 Q2 为什么没成（**自身 bug，不是产品的**）：
//    手册 `20-reference.md:710-722` 写明「添加参考 48×48」打开的是
//    `[role="menu"][aria-label="添加参考"]` 240×130，里面的三项是 **`role="menuitem"`**。
//    而我的找点只搜 `button,[role=button]` ⇒ **三个菜单项一个都没进候选**（候选数 = 0）。
//    📌 这与批次 153「把 `data-testid` 当 class」同族：**找错元素类型 ⇒ 读数 0，
//    而读数 0 长得和「功能没了」一模一样。**
//
// 🎯 本轮三问：
//   Q2-a 点「添加参考」→ `[role=menu][aria-label=添加参考]` 的盒、逐字、三个 menuitem 的逐字与盒
//   Q2-b 点 menuitem「从画布选择」→ `canvas-source-picker-canvas-frame` / `-mask` /
//        `generation-source-picker-chip` / `-close` + 那行 1×1 英文辅助文案
//   Q2-c 点「取消选择」→ 四个元素是否全部消失、节点与提示词是否原样
//
// ⛔ 红线：绝不点 submit / 绝不点 aria 含「确认」「插入」「立即」「提交」「生成」的按钮；
//    **打开浮层后绝不调 settle()**；不按字母数字键；积分每步记，收尾必须 805。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { 建N个, selCount, idsOf, canvasPos, 可点落点, 组数 } from './jimeng-b139-lib.mjs';

const rec = { 批次: '154d', 目的: '补 Q2：添加参考菜单 → 从画布选择 → 全屏拾取模式 → 取消' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b154d.json', import.meta.url), JSON.stringify(rec, null, 1));
const 出图 = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const 禁词 = ['提交', '确认', '插入', '立即', '生成', '上传'];

// 🔑 找点：页面内现取现算，只回 {x,y} 标量。**元素类型由 pred.sel 决定** ——
//    上一批就是在这里栽的（只搜 button，漏掉全部 menuitem）。
const 找点 = (pred) => p.evaluate((pd) => {
  const cands = Array.from(document.querySelectorAll(pd.sel)).filter((b) => {
    const a = b.getAttribute('aria-label') || '';
    const t = (b.innerText || '').replace(/\s+/g, ' ').trim();
    if (pd.文字Includes && t.indexOf(pd.文字Includes) < 0) return false;
    if (pd.文字Regex && !new RegExp(pd.文字Regex).test(t)) return false;
    if (pd.ariaIncludes && a.indexOf(pd.ariaIncludes) < 0) return false;
    if (pd.testidIncludes && (b.getAttribute('data-testid') || '').indexOf(pd.testidIncludes) < 0) return false;
    if (/submit/i.test(b.getAttribute('data-testid') || '')) return false;
    if (pd.禁词 && pd.禁词.some((w) => a.indexOf(w) >= 0)) return false;
    return true;
  });
  const out = [];
  for (const b of cands) {
    const r = b.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) continue;
    const cx = Math.round(r.x + r.width / 2); const cy = Math.round(r.y + r.height / 2);
    const h = document.elementFromPoint(cx, cy);
    const btn = h && h.closest(pd.sel);
    out.push({ x: cx, y: cy, 宽: Math.round(r.width), 高: Math.round(r.height), 左: Math.round(r.x), 上: Math.round(r.y),
      aria: b.getAttribute('aria-label'), testid: b.getAttribute('data-testid'),
      逐字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30),
      中心是自己: btn === b, 中心是谁: btn ? ((btn.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30) || btn.tagName.toLowerCase()) : null });
  }
  return { 候选数: cands.length, 点: out };
}, { ...pred, 禁词 });

const 读testid = (ids) => p.evaluate((list) => {
  const 出 = {};
  for (const n of list) {
    const all = Array.from(document.querySelectorAll('[data-testid="' + n + '"]'));
    出[n] = { 命中: all.length, 实例: all.slice(0, 2).map((e) => { const r = e.getBoundingClientRect();
      return { 盒: [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x * 10) / 10, Math.round(r.y * 10) / 10],
        role: e.getAttribute('role'), aria: e.getAttribute('aria-label'),
        逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 90),
        祖先链: (() => { const c = []; let n = e; for (let i = 0; i < 8 && n; i++) { n = n.parentElement; if (!n || n === document.body) break;
          c.push(n.tagName.toLowerCase() + (n.getAttribute('data-testid') ? '{' + n.getAttribute('data-testid') + '}' : '') + (typeof n.className === 'string' && n.className ? '.' + n.className.split(/\s+/)[0] : '')); } return c; })() }; }) };
  }
  return 出;
}, ids);

const 清零 = async () => {
  for (let k = 0; k < 4 && (await selCount(p)) > 0; k++) {
    const 空 = await p.evaluate(() => { const 坏 = (x, y) => { const h = document.elementFromPoint(x, y); if (!h) return 1;
      if (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button],[role=menuitem]')) return 1;
      if (h.closest('.react-flow__node') || h.closest('[data-testid="node-toolbar"]') || h.closest('[role=dialog],[role=menu],[role=listbox]')) return 1;
      return !(h.classList && h.classList.contains('react-flow__pane')); };
      for (let y = 90; y < innerHeight - 90; y += 8) for (let x = 360; x < innerWidth - 350; x += 8) if (!坏(x, y)) return { x, y };
      return { __err: 'no-free-pane' }; });
    if (空.__err) break; await p.mouse.click(空.x, 空.y); await p.waitForTimeout(1000);
  }
  return selCount(p);
};

const 关一个 = async (id) => {
  await 清零();
  const 前 = await idsOf(p);
  const 落 = await 可点落点(p, `.react-flow__node[data-id="${id}"]`, 4, 4);
  if (落.__err) return { id, __err: 'no-point' };
  const 归属 = await p.evaluate(([x, y, i]) => { const h = document.elementFromPoint(x, y);
    const n = h && h.closest('.react-flow__node'); return { 对: !!(n && n.getAttribute('data-id') === i) }; }, [落.x, 落.y, id]);
  if (!归属.对) return { id, __err: 'wrong-target' };
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
  if (del.__err) return { id, __err: del.__err };
  await p.mouse.click(del.x, del.y); await p.waitForTimeout(2500); await settle(p, R);
  const 后 = await idsOf(p);
  return { id, 消失: 前.filter((x) => !后.includes(x)), 删除项逐字: del.逐字 };
};

const 七项 = ['generation-form', 'generation-source-picker-chip', 'generation-source-picker-close',
  'canvas-source-picker-canvas-frame', 'canvas-source-picker-canvas-mask', 'generation-mention-panel', 'node-toolbar'];

const { b, p } = await openCanvas();
const R = readers(p);
let 基线canvas = null;
try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(),
    实测scale: await p.evaluate(() => { const e = document.querySelector('.react-flow__viewport'); return e ? e.style.transform : null; }),
    积分: await R.credits(), 组数: await 组数(p), 选中: await selCount(p) };
  基线canvas = await canvasPos(p);

  const 建 = await 建N个(p, '图片', 1, null, (await idsOf(p)).length);
  rec.建 = { ids: 建.ids, 护栏: 建.护栏, 护栏全过: 建.护栏.every((h) => h.通过) };
  落盘();
  if (建.ids && 建.ids.length) {
    const id = 建.ids[0];
    const 节点盒 = await p.evaluate((i) => { const n = document.querySelector('.react-flow__node[data-id="' + i + '"]'); const r = n.getBoundingClientRect();
      return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }, id);
    await p.mouse.move(节点盒.cx, 节点盒.cy); await p.waitForTimeout(1400);
    rec.默认态 = await 读testid(七项);
    rec.开点前的菜单数 = await p.evaluate(() => document.querySelectorAll('[role=menu]').length);

    // ---------- Q2-a：点「添加参考」 ----------
    const 添 = await 找点({ sel: 'button,[role=button]', ariaIncludes: '添加参考' });
    rec.Q2a_添加参考钮 = 添;
    const A = (添.点 || [])[0];
    if (A && A.中心是自己) {
      await p.mouse.click(A.x, A.y); await p.waitForTimeout(2000);
      rec.Q2a_菜单 = await p.evaluate(() => Array.from(document.querySelectorAll('[role=menu]')).map((m) => {
        const r = m.getBoundingClientRect();
        return { aria: m.getAttribute('aria-label'), 盒: [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x), Math.round(r.y)],
          逐字: (m.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80),
          项: Array.from(m.querySelectorAll('[role=menuitem]')).map((it) => { const q = it.getBoundingClientRect();
            const cx = Math.round(q.x + q.width / 2); const cy = Math.round(q.y + q.height / 2);
            const h = document.elementFromPoint(cx, cy);
            return { 逐字: (it.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20), 盒: [Math.round(q.width * 10) / 10, Math.round(q.height * 10) / 10, Math.round(q.x), Math.round(q.y)],
              svg数: it.querySelectorAll('svg').length, x: cx, y: cy, 中心命中: h ? (h.closest('[role=menuitem]') === it) : false }; }) };
      }));
      落盘();
      const 菜单 = (rec.Q2a_菜单 || []).find((m) => m.aria === '添加参考') || (rec.Q2a_菜单 || [])[0];
      const 从项 = 菜单 && (菜单.项 || []).find((z) => z.逐字 === '从画布选择');
      rec.Q2a_从画布项 = 从项 || null;
      断言('① `[role=menu][aria-label="添加参考"]` 命中 1，且三个 `role=menuitem` 齐', !!菜单 && 菜单.项.length === 3, { 菜单: rec.Q2a_菜单 });

      // ---------- Q2-b：点 menuitem「从画布选择」 ----------
      if (从项 && 从项.中心命中) {
        await p.mouse.click(从项.x, 从项.y); await p.waitForTimeout(2400);
        rec.Q2b = await 读testid(七项);
        rec.Q2b_英文辅助 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('*'))
          .find((x) => (x.textContent || '').trim() === 'Select a supported ready media item on the canvas. Press Escape to cancel.');
          if (!e) return { 命中: false };
          const r = e.getBoundingClientRect();
          return { 命中: true, 标签: e.tagName.toLowerCase(), 盒: [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x), Math.round(r.y)],
            样式: (() => { const s = getComputedStyle(e); return { position: s.position, overflow: s.overflow, clip: s.clip, clipPath: s.clipPath, w: s.width, h: s.height }; })() }; });
        rec.积分_模式内 = await R.credits();
        const f = rec.Q2b['canvas-source-picker-canvas-frame'];
        const m = rec.Q2b['canvas-source-picker-canvas-mask'];
        const c = rec.Q2b['generation-source-picker-chip'];
        const x = rec.Q2b['generation-source-picker-close'];
        const 拍前 = { frame: f.命中, frame盒: (f.实例[0] || {}).盒, mask: m.命中, mask盒: (m.实例[0] || {}).盒,
          chip: c.命中, chip盒: (c.实例[0] || {}).盒, chip逐字: (c.实例[0] || {}).逐字,
          close: x.命中, close盒: (x.实例[0] || {}).盒, closearia: (x.实例[0] || {}).aria,
          formaria: (rec.Q2b['generation-form'].实例[0] || {}).aria, 积分: rec.积分_模式内 };
        rec.拍前断言2 = 拍前;
        断言('② 🔑 `canvas-source-picker-canvas-frame` 与 `-mask` 各命中 ≥ 1', 拍前.frame >= 1 && 拍前.mask >= 1, 拍前);
        断言('③ 🔑 `generation-source-picker-chip` 命中且有面积、`generation-source-picker-close` 命中',
          拍前.chip >= 1 && !!拍前.chip盒 && 拍前.chip盒[0] > 0 && 拍前.close >= 1, 拍前);
        断言('④ 进入拾取模式**不扣积分**（仍 805）', String(拍前.积分).indexOf('805') >= 0, { 积分: 拍前.积分 });
        if (拍前.frame >= 1) {
          await p.screenshot({ path: new URL('./55-source-picker-canvas-mode.png', 出图).pathname });
          rec.截图 = 'screenshots/55-source-picker-canvas-mode.png';
        }

        // ---------- Q2-c：点「取消选择」 ----------
        const 取 = await 找点({ sel: '[data-testid="generation-source-picker-close"]' });
        rec.Q2c_取消钮 = 取;
        const X = (取.点 || [])[0];
        rec.Q2c_点了 = false;
        if (X && X.中心是自己) {
          await p.mouse.click(X.x, X.y); await p.waitForTimeout(1800);
          rec.Q2c_点了 = true;
        }
        rec.Q2c_取消后 = await 读testid(七项);
        rec.积分_取消后 = await R.credits();
        const 后 = { frame: rec.Q2c_取消后['canvas-source-picker-canvas-frame'].命中,
          mask: rec.Q2c_取消后['canvas-source-picker-canvas-mask'].命中,
          chip: rec.Q2c_取消后['generation-source-picker-chip'].命中,
          close: rec.Q2c_取消后['generation-source-picker-close'].命中,
          form: rec.Q2c_取消后['generation-form'].命中, 节点仍在: (await idsOf(p)).includes(id), 积分: rec.积分_取消后 };
        rec.Q2c_摘要 = 后;
        断言('⑤ 点「取消选择」后 frame/mask/chip/close **四项全部归 0**，节点与表单原样保留',
          后.frame === 0 && 后.mask === 0 && 后.chip === 0 && 后.close === 0 && 后.节点仍在 && 后.form >= 1, 后);
        断言('⑥ 取消后积分**仍是 805**', String(后.积分).indexOf('805') >= 0, { 积分: 后.积分 });
        落盘();
      }
    }
    for (let k = 0; k < 5; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(900); }
    rec.删除 = []; for (const xx of 建.ids) rec.删除.push(await 关一个(xx));
    落盘();
  }
  await setZoom(p, 60); await p.waitForTimeout(1400);
  const 末 = await idsOf(p); const 末c = await canvasPos(p);
  rec.收尾检查 = { 节点数: 末.length,
    位移节点: 基线canvas ? Object.keys(基线canvas).filter((k) => 末c[k] && (末c[k][0] !== 基线canvas[k][0] || 末c[k][1] !== 基线canvas[k][1])) : null };
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

await settle(p, R);
const mm = await R.minimap();
if (!mm || mm.ariaPressed !== 'true') { const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3); if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400); } }
rec.小地图 = await R.minimap();
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(),
  zoom: await R.zoom(), 积分: await R.credits(), 组数: await 组数(p),
  边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length),
  残留自建: (await idsOf(p)).filter((x) => ((rec.建 || {}).ids || []).includes(x)) };
落盘();

console.log('起点', JSON.stringify(rec.起点));
console.log('开点前 role=menu 数', rec.开点前的菜单数, '| 默认态', JSON.stringify(Object.fromEntries(Object.entries(rec.默认态 || {}).map(([k, v]) => [k, v.命中]))));
console.log('\nQ2a 添加参考钮', JSON.stringify(rec.Q2a_添加参考钮));
console.log('Q2a 菜单', JSON.stringify(rec.Q2a_菜单, null, 1));
console.log('\nQ2b frame', JSON.stringify((rec.Q2b || {})['canvas-source-picker-canvas-frame'], null, 1));
console.log('Q2b mask', JSON.stringify((rec.Q2b || {})['canvas-source-picker-canvas-mask']));
console.log('Q2b chip', JSON.stringify((rec.Q2b || {})['generation-source-picker-chip'], null, 1));
console.log('Q2b close', JSON.stringify((rec.Q2b || {})['generation-source-picker-close']));
console.log('Q2b 英文辅助', JSON.stringify(rec.Q2b_英文辅助, null, 1));
console.log('\nQ2c 取消钮', JSON.stringify(rec.Q2c_取消钮), '| 点了', rec.Q2c_点了);
console.log('Q2c 摘要', JSON.stringify(rec.Q2c_摘要));
console.log('\n删除', JSON.stringify((rec.删除 || []).map((d) => d.消失 || d.__err)));
console.log('收尾检查', JSON.stringify(rec.收尾检查));
console.log('收尾', JSON.stringify(rec.收尾), '| 小地图', JSON.stringify(rec.小地图), '| 异常', rec.异常 || '无');
console.log('截图', rec.截图 || '无');

断言('⑦ 建-删护栏全过 + 消失集合恰好 {SELF}', rec.建 && rec.建.护栏全过 === true && (rec.删除 || []).length > 0 && (rec.删除 || []).every((d) => d.消失 && d.消失.length === 1), { 护栏: rec.建 && rec.建.护栏全过, 删除: (rec.删除 || []).map((d) => d.消失 || d.__err) });
断言('⑧ 🔑 收尾积分**仍是 805**', String((rec.收尾 || {}).积分).indexOf('805') >= 0, { 积分: (rec.收尾 || {}).积分 });
if (rec.收尾检查 && rec.收尾检查.位移节点) 断言('⑨ 其余节点零位移', rec.收尾检查.位移节点.length === 0, rec.收尾检查);
rec.断言全过 = 断言过; 落盘();
await b.close();
