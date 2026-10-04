// 批次 155-b —— 只补 Q3（静音）/ Q4（全屏编辑）/ Q5（导出），不重建节点
//
// 🔴 155 主脚本为什么这三问没跑（**自身 bug，且是一个值得记住的门类**）：
//    `找点` 的候选过滤只判了 `width > 0 && height > 0`，**没判落点是否在视口内**。
//    画布上还有**两个别人建的时间线节点**，它们整块在视口外 ——
//    `getBoundingClientRect()` 对它们照样返回非零矩形（实测 `静音` 按钮盒在
//    `x=-2429,y=-1413`、另一个在 `x=-1683,y=-1036`）。
//    我写的 `const S = (点 || [])[0]` 于是取到了**第一个候选 = 视口外那个**，
//    `中心是自己` 为 false ⇒ 整块 if 不进 ⇒ Q3/Q4/Q5 静默跳过，
//    最后 `JSON.stringify(undefined).slice` 又崩在收尾日志上。
//
// 📌 **立规 11：找点必须同时满足三条 —— ① 有面积 ② 算出来的落点在视口内
//    （0 ≤ cx ≤ innerWidth 且 0 ≤ cy ≤ innerHeight）③ `elementFromPoint` 命中自己。**
//    批次 111 那条「节点选中时屏上 266×46」也正是这类越界/错对象读数的产物（见本批 §4.78.4）。
//
// ✅ 本轮固定：过滤条件加「落点在视口内」，并**优先取 `中心是自己` 的候选**。
// ⛔ 红线不变：不点生成/发送/扣费；不按任何字母数字键；打开浮层后绝不调 settle()。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { 建N个, selCount, idsOf, canvasPos, 可点落点, 组数 } from './jimeng-b139-lib.mjs';

const rec = { 批次: '155b', 目的: '补 Q3 静音 aria 翻转 / Q4 全屏编辑 / Q5 导出触发（修「落点未判视口内」）' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b155b.json', import.meta.url), JSON.stringify(rec, null, 1));
const 出图 = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const 串 = (x, n) => { const s = JSON.stringify(x, null, 1); return s === undefined ? 'undefined' : s.slice(0, n || 2000); };

// 🔑 立规 11：三条同时成立才算候选
const 找点 = (pred) => p.evaluate((pd) => {
  const cands = Array.from(document.querySelectorAll(pd.sel)).filter((b) => {
    const a = b.getAttribute('aria-label') || '';
    const inNode = !!b.closest('.react-flow__node');
    if (pd.字面等于 && a !== pd.字面等于) return false;
    if (pd.ariaRegex && !new RegExp(pd.ariaRegex).test(a)) return false;
    if (pd.testidIncludes && (b.getAttribute('data-testid') || '').indexOf(pd.testidIncludes) < 0) return false;
    if (pd.在节点内 === true && !inNode) return false;
    if (pd.在节点内 === false && inNode) return false;
    if (/submit/i.test(b.getAttribute('data-testid') || '')) return false;
    return true;
  });
  const 全候选 = [];
  for (const b of cands) {
    const r = b.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) continue;
    const cx = Math.round(r.x + r.width / 2); const cy = Math.round(r.y + r.height / 2);
    const h = document.elementFromPoint(cx, cy);
    const btn = h && h.closest(pd.sel);
    const 在视口内 = cx >= 0 && cy >= 0 && cx <= innerWidth && cy <= innerHeight;
    全候选.push({ x: cx, y: cy, 宽: Math.round(r.width), 高: Math.round(r.height), 左: Math.round(r.x), 上: Math.round(r.y),
      aria: b.getAttribute('aria-label'), testid: b.getAttribute('data-testid'),
      在视口内, 中心是自己: btn === b,
      中心是谁: btn ? (btn.getAttribute('aria-label') || btn.getAttribute('data-testid') || btn.tagName.toLowerCase()) : null });
  }
  // ✅ 三条同时成立才算可用
  const 可用 = 全候选.filter((z) => z.在视口内 && z.中心是自己);
  return { 候选数: cands.length, 全候选, 可用, 可用数: 可用.length };
}, pred);

const { b, p } = await openCanvas();
const R = readers(p);
let 基线canvas = null;
try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(), 积分: await R.credits(), 组数: await 组数(p), 选中: await selCount(p) };
  基线canvas = await canvasPos(p);

  const 建 = await 建N个(p, '时间线', 1, null, (await idsOf(p)).length);
  rec.建 = { ids: 建.ids, 护栏全过: (建.护栏 || []).every((h) => h.通过) };
  落盘();
  断言('⓪ 护栏建出 1 个时间线节点', (建.ids || []).length === 1, { 护栏: 建.护栏 });

  if (建.ids && 建.ids.length) {
    const SELF = 建.ids[0];
    // ---------- Q3：静音 aria 翻转 ----------
    const 读静音 = () => p.evaluate((i) => { const n = document.querySelector('.react-flow__node[data-id="' + i + '"]');
      const e = n && n.querySelector('[data-testid="timeline-mute-button"]');
      if (!e) return null; const q = e.getBoundingClientRect();
      return { aria: e.getAttribute('aria-label'), 盒: [Math.round(q.width * 10) / 10, Math.round(q.height * 10) / 10], ariaPressed: e.getAttribute('aria-pressed'), ariaDisabled: e.getAttribute('aria-disabled') }; }, SELF);
    rec.Q3_前置 = await 读静音();
    rec.Q3_找点 = await 找点({ sel: '[data-testid="timeline-mute-button"]', 在节点内: true });
    const S = (rec.Q3_找点.可用 || [])[0];
    rec.Q3_用的点 = S || null;
    if (S) {
      await p.mouse.click(S.x, S.y); await p.waitForTimeout(1600);
      rec.Q3_点一次后 = await 读静音();
      const 翻回 = (await 找点({ sel: '[data-testid="timeline-mute-button"]', 在节点内: true })).可用 || [];
      const S2 = 翻回[0];
      rec.Q3_翻回点 = S2 || null;
      if (S2) { await p.mouse.click(S2.x, S2.y); await p.waitForTimeout(1600); }
      rec.Q3_终态 = await 读静音();
      落盘();
      断言('① 🔑 点「静音」aria **确实翻转**、再点一次**翻回原值**（可逆）',
        rec.Q3_前置 && rec.Q3_点一次后 && rec.Q3_终态 && rec.Q3_前置.aria !== rec.Q3_点一次后.aria && rec.Q3_终态.aria === rec.Q3_前置.aria,
        { 前: rec.Q3_前置, 点一次后: rec.Q3_点一次后, 终态: rec.Q3_终态 });
    }

    // ---------- Q4：全屏编辑 ----------
    rec.Q4_找点 = await 找点({ sel: 'button,[role=button]', 字面等于: '全屏编辑', 在节点内: true });
    const F = (rec.Q4_找点.可用 || [])[0];
    rec.Q4_用的点 = F || null;
    if (F) {
      await p.mouse.click(F.x, F.y); await p.waitForTimeout(2600);
      rec.Q4 = await p.evaluate(() => {
        const e = document.querySelector('[data-testid="timeline-fullscreen-editor"]') ||
          Array.from(document.querySelectorAll('[role=dialog]')).find((d) => d.getBoundingClientRect().width > 1200);
        if (!e) return { 命中: false, 现有dialog: Array.from(document.querySelectorAll('[role=dialog]')).map((d) => { const r = d.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y), d.getAttribute('data-testid')]; }) };
        const r = e.getBoundingClientRect();
        const 盒 = (x) => { const q = x.getBoundingClientRect(); return [Math.round(q.width), Math.round(q.height), Math.round(q.x), Math.round(q.y)]; };
        return { 命中: true, testid: e.getAttribute('data-testid'), role: e.getAttribute('role'),
          盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
          逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 260),
          testid数: Array.from(new Set(Array.from(e.querySelectorAll('[data-testid]')).map((x) => x.getAttribute('data-testid')))).length,
          testid清单: Array.from(new Set(Array.from(e.querySelectorAll('[data-testid]')).map((x) => x.getAttribute('data-testid')))).sort(),
          按钮: Array.from(e.querySelectorAll('button,[role=button]')).map((x) => ({ aria: x.getAttribute('aria-label'), 逐字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12), 盒: 盒(x) })).filter((z) => z.盒[0] > 0) };
      });
      rec.拍前断言2 = { 命中: rec.Q4.命中, 盒: rec.Q4.盒, 关闭钮: (rec.Q4.按钮 || []).filter((z) => /Close|关闭/.test(z.aria || '')), 积分: await R.credits() };
      断言('② 点「全屏编辑」打开铺满视口的 `timeline-fullscreen-editor`', rec.Q4.命中 === true && rec.Q4.盒 && rec.Q4.盒[0] >= 1270, rec.拍前断言2);
      if (rec.Q4.命中) {
        await p.screenshot({ path: new URL('./58-timeline-fullscreen-from-node.png', 出图).pathname });
        rec.截图 = 'screenshots/58-timeline-fullscreen-from-node.png';
      }
      await p.keyboard.press('Escape'); await p.waitForTimeout(1800);
      rec.Q4_Esc后命中 = await p.evaluate(() => document.querySelectorAll('[data-testid="timeline-fullscreen-editor"]').length);
      落盘();
    }

    // ---------- Q5：导出时间线（只验触发 + 建议文件名，不落盘、不核验成片） ----------
    rec.Q5_找点 = await 找点({ sel: 'button,[role=button]', 字面等于: '导出时间线', 在节点内: true });
    const E = (rec.Q5_找点.可用 || [])[0];
    rec.Q5_用的点 = E || null;
    rec.Q5 = { 点了: !!E, 触发下载: false };
    if (E) {
      const dl = p.waitForEvent('download', { timeout: 9000 }).catch(() => null);
      await p.mouse.click(E.x, E.y);
      const d = await dl;
      rec.Q5.触发下载 = !!d;
      if (d) { rec.Q5.建议文件名 = d.suggestedFilename(); await d.cancel().catch(() => {}); rec.Q5.已丢弃 = true; }
      await p.waitForTimeout(1600);
      rec.Q5_点后浮层 = await R.overlays();
      rec.Q5_积分 = await R.credits();
      落盘();
    }
    断言('③ 点「导出时间线」**触发了下载**（只验触发与建议文件名，不落盘、不核验成片）', rec.Q5.触发下载 === true, rec.Q5);
    断言('④ 导出**不扣积分**（仍 805）', String(rec.Q5_积分).indexOf('805') >= 0, { 积分: rec.Q5_积分 });
  }

  // ---------- 收尾删除 ----------
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
  await 清零();
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
    rec.删除.push({ id: x, 消失: 前.filter((y) => !后.includes(y)), 删除项逐字: del.逐字 });
  }
  await setZoom(p, 60); await p.waitForTimeout(1400);
  const 末 = await idsOf(p); const 末c = await canvasPos(p);
  rec.收尾检查 = { 节点数: 末.length, 位移节点: 基线canvas ? Object.keys(基线canvas).filter((k) => 末c[k] && (末c[k][0] !== 基线canvas[k][0] || 末c[k][1] !== 基线canvas[k][1])) : null };
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
console.log('建', JSON.stringify(rec.建));
console.log('\nQ3 找点 全候选', 串(rec.Q3_找点 && rec.Q3_找点.全候选, 1200));
console.log('Q3 可用数', rec.Q3_找点 && rec.Q3_找点.可用数);
console.log('Q3 静音', JSON.stringify({ 前: rec.Q3_前置, 点一次后: rec.Q3_点一次后, 终态: rec.Q3_终态 }));
console.log('\nQ4 找点 可用数', rec.Q4_找点 && rec.Q4_找点.可用数, '| 用的点', JSON.stringify(rec.Q4_用的点));
console.log('Q4 全屏', 串(rec.Q4, 2600));
console.log('Q4 Esc后 fullscreen-editor 命中 =', rec.Q4_Esc后命中);
console.log('\nQ5 找点 可用数', rec.Q5_找点 && rec.Q5_找点.可用数);
console.log('Q5 导出', JSON.stringify(rec.Q5), '| 点后浮层', rec.Q5_点后浮层, '| 积分', rec.Q5_积分);
console.log('\n删除', JSON.stringify((rec.删除 || []).map((d) => d.消失 || d.__err)));
console.log('收尾检查', JSON.stringify(rec.收尾检查));
console.log('收尾', JSON.stringify(rec.收尾), '| 小地图', JSON.stringify(rec.小地图), '| 异常', rec.异常 || '无');
console.log('截图', rec.截图 || '无');

断言('⑤ 建-删护栏全过 + 消失集合恰好 {SELF}', (rec.删除 || []).length > 0 && (rec.删除 || []).every((d) => d.消失 && d.消失.length === 1), { 删除: (rec.删除 || []).map((d) => d.消失 || d.__err) });
断言('⑥ 🔑 收尾积分**仍是 805**', String((rec.收尾 || {}).积分).indexOf('805') >= 0, { 积分: (rec.收尾 || {}).积分 });
if (rec.收尾检查 && rec.收尾检查.位移节点) 断言('⑦ 其余节点零位移', rec.收尾检查.位移节点.length === 0, rec.收尾检查);
rec.断言全过 = 断言过; 落盘();
await b.close();
