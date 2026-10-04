// 批次 155 —— 🔴 结清 `timeline-node.md:206` 那条悬案：「左栏那个「时间线」按钮本轮仍未走通」
//                                    （批次 107 记过「点 24 轮无新节点」）
//
// 🎯 五问：
//   Q1 🔑 左栏「时间线」键**到底能不能建节点** —— 手册明写「批次 107 点 24 轮无新节点」。
//      本轮带**建-删护栏**（建前节点数 == 预期基线 76、建前 0 选中、建前无组；
//      建后差集恰好 1 且 .selected）重做一次。**先只读左栏九键的逐字 aria 与盒，
//      确认第几个键是「时间线」**，不靠记忆。
//   Q2 建成功后读**自建时间线节点的完整 testid / aria / 按钮尺寸**，
//      与批次 111 的「20 个 testid / 9 个 aria / 6 个按钮尺寸」**逐条 diff**。
//   Q3 点「静音」→ aria 翻转 → 再点回来（**可逆**），两次都记。
//   Q4 点「全屏编辑」→ 读 `timeline-fullscreen-editor` 全谱 + **截图** → Esc。
//   Q5 「导出时间线」：**只验证「点它会触发下载」并读建议文件名，不落盘、不核验成片内容**
//      —— 诚���标注为「验了触发、未验成片」。
//
// ⛔ 红线（写进代码）：不点任何生成/发送/扣费按钮；**打开浮层后绝不调 `settle()`**；
//    不按任何字母/数字键（`F` 开全屏那条已被批次 144 证明会变打字）；只用 Esc 关自己开的东西。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { 建N个, selCount, idsOf, canvasPos, 可点落点, 组数 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 155, 目的: '结清「左栏时间线键走不通」+ 静音 aria 翻转 + 全屏编辑 + 导出触发' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b155.json', import.meta.url), JSON.stringify(rec, null, 1));
const 出图 = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);

// 🔑 找点：页面内现取现算，只回 {x,y} 标量 + 归属证据
const 找点 = (pred) => p.evaluate((pd) => {
  const cands = Array.from(document.querySelectorAll(pd.sel)).filter((b) => {
    const a = b.getAttribute('aria-label') || '';
    const t = (b.innerText || '').replace(/\s+/g, ' ').trim();
    const inNode = !!b.closest('.react-flow__node');
    if (pd.ariaIncludes && a.indexOf(pd.ariaIncludes) < 0) return false;
    if (pd.ariaRegex && !new RegExp(pd.ariaRegex).test(a)) return false;
    if (pd.字面等于 && a !== pd.字面等于) return false;
    if (pd.testidIncludes && (b.getAttribute('data-testid') || '').indexOf(pd.testidIncludes) < 0) return false;
    if (pd.在节点内 === true && !inNode) return false;
    if (pd.在节点内 === false && inNode) return false;
    if (/submit/i.test(b.getAttribute('data-testid') || '')) return false;
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
      逐字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 26),
      中心是自己: btn === b, 中心是谁: btn ? (btn.getAttribute('aria-label') || btn.getAttribute('data-testid') || btn.tagName.toLowerCase()) : null });
  }
  return { 候选数: cands.length, 点: out };
}, pred);

const 读testid = (ids) => p.evaluate((list) => {
  const 出 = {};
  for (const n of list) {
    const all = Array.from(document.querySelectorAll('[data-testid="' + n + '"]'));
    出[n] = { 命中: all.length, 实例: all.slice(0, 2).map((e) => { const r = e.getBoundingClientRect();
      return { 盒: [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x * 10) / 10, Math.round(r.y * 10) / 10],
        role: e.getAttribute('role'), aria: e.getAttribute('aria-label'),
        逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 90),
        祖先链: (() => { const c = []; let n = e; for (let i = 0; i < 6 && n; i++) { n = n.parentElement; if (!n || n === document.body) break;
        c.push(n.tagName.toLowerCase() + (n.getAttribute('data-testid') ? '{' + n.getAttribute('data-testid') + '}' : '') + (typeof n.className === 'string' && n.className ? '.' + n.className.split(/\s+/)[0] : '')); } return c; })() }; }) };
  }
  return 出;
}, ids);

// 手册批次 111 记的「20 个 testid」，用来做逐条 diff
const 手册111 = ['timeline-flow-node', 'flow-node-media-stroke', 'flow-node-target-handle',
  'flow-node-target-connection-menu-button', 'flow-node-title', 'flow-node-selected-tag',
  'timeline-flow-node-main-track', 'timeline-toolbar', 'timeline-playback-clock',
  'timeline-visual-track', 'timeline-track-gutter', 'timeline-mute-button',
  'timeline-node-track-divider', 'timeline-track-scroll', 'timeline-track-canvas',
  'timeline-ruler', 'timeline-ruler-interaction-extension', 'timeline-clip-track',
  'timeline-source-picker-slot', 'timeline-empty-track-label', 'timeline-node-resize-handle'];
const 手册111aria = ['分割', '删除', '导出时间线', '全屏编辑', '静音', '添加素材到时间线', 'Resize timeline'];

const { b, p } = await openCanvas();
const R = readers(p);
let 基线canvas = null;
try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(),
    实测scale: await p.evaluate(() => { const e = document.querySelector('.react-flow__viewport'); return e ? e.style.transform : null; }),
    积分: await R.credits(), 组数: await 组数(p), 选中: await selCount(p) };
  基线canvas = await canvasPos(p);

  // ---------- Q0：只读左栏九键（不靠记忆，先确认第几个键是「时间线」） ----------
  rec.左栏 = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role=button]'))
    .map((b) => { const r = b.getBoundingClientRect();
      return { aria: b.getAttribute('aria-label'), testid: b.getAttribute('data-testid'),
        盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
        有面积: r.width > 0 && r.height > 0, 在左栏: r.x < 60 && r.y > 100 && r.y < 700 }; })
    .filter((x) => x.有面积 && x.在左栏));
  rec.左栏建键 = (rec.左栏 || []).filter((x) => x.盒[0] === 40 && x.盒[1] === 40);
  落盘();
  const 时间线键 = (rec.左栏建键 || []).find((x) => x.aria === '时间线');
  rec.时间线键 = 时间线键 || null;
  console.log('左栏 40×40 建键逐个：', JSON.stringify((rec.左栏建键 || []).map((x) => [x.aria, x.盒[2], x.盒[3]])));
  断言('⓪ 左栏 7 个 40×40 建节点键在场，其中一个是 `aria="时间线"`', !!时间线键, { 建键: (rec.左栏建键 || []).map((x) => x.aria) });

  // ---------- Q1：带护栏建一个时间线节点 ----------
  const 建 = 时间线键 ? await 建N个(p, '时间线', 1, null, (await idsOf(p)).length) : { ids: [], 护栏: [], 护栏全过: false };
  rec.建 = { ids: 建.ids, 护栏: 建.护栏, 护栏全过: 建.护栏 ? 建.护栏.every((h) => h.通过) : false };
  落盘();
  断言('① 🔑 左栏「时间线」键**能建出节点**（建后差集恰好 1 且 .selected）—— 结清批次 107 的「24 轮无新节点」',
    rec.建.护栏全过 === true && (建.ids || []).length === 1, { 护栏: rec.建.护栏, ids: 建.ids });

  if (建.ids && 建.ids.length) {
    const SELF = 建.ids[0];
    // ---------- Q2：自建时间线节点全谱 + 与批次 111 逐条 diff ----------
    rec.自建 = await p.evaluate((i) => {
      const n = document.querySelector('.react-flow__node[data-id="' + i + '"]');
      const r = n.getBoundingClientRect();
      const 盒 = (e) => { const q = e.getBoundingClientRect(); return [Math.round(q.width * 10) / 10, Math.round(q.height * 10) / 10, Math.round(q.x * 10) / 10, Math.round(q.y * 10) / 10]; };
      return {
        class逐字: n.className, 屏上盒: 盒(n), canvas: n.style.transform,
        逐字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300),
        testid: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))).sort(),
        aria: Array.from(new Set(Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')))).filter(Boolean).sort(),
        按钮: Array.from(n.querySelectorAll('button,[role=button]')).map((e) => { const q = e.getBoundingClientRect();
          return { aria: e.getAttribute('aria-label'), testid: e.getAttribute('data-testid'),
            逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18),
            盒: [Math.round(q.width * 10) / 10, Math.round(q.height * 10) / 10], 有面积: q.width > 0 }; }),
      };
    }, SELF);
    const 实有 = new Set(rec.自建.testid);
    rec.diff = { 手册有实测无: 手册111.filter((x) => !实有.has(x)), 实测有手册无: rec.自建.testid.filter((x) => 手册111.indexOf(x) < 0) };
    rec.ariaDiff = { 手册有实测无: 手册111aria.filter((x) => rec.自建.aria.indexOf(x) < 0), 实测有手册无: rec.自建.aria.filter((x) => 手册111aria.indexOf(x) < 0) };
    落盘();
    console.log('\n自建时间线节点 testid 数量 =', rec.自建.testid.length, '| 手册 111 记 20');
    console.log('  手册有实测无 =', JSON.stringify(rec.diff.手册有实测无));
    console.log('  实测有手册无 =', JSON.stringify(rec.diff.实测有手册无));
    console.log('  aria 手册有实测无 =', JSON.stringify(rec.ariaDiff.手册有实测无));
    console.log('  aria 实测有手册无 =', JSON.stringify(rec.ariaDiff.实测有手册无));
    断言('② 手册批次 111 的 20 个 testid 在自建节点上**一个不缺**', rec.diff.手册有实测无.length === 0, rec.diff);
    断言('③ 手册批次 111 的 7 个专有 aria 一个不缺', rec.ariaDiff.手册有实测无.length === 0, rec.ariaDiff);
    rec.拍前断言1 = { 积分: await R.credits(), 节点数: (await idsOf(p)).length };
    await p.screenshot({ path: new URL('./57-timeline-node-created-from-rail.png', 出图).pathname });
    rec.截图1 = 'screenshots/57-timeline-node-created-from-rail.png';

    // ---------- Q3：静音 aria 翻转（可逆，点两次） ----------
    const 静 = await 找点({ sel: 'button,[role=button]', 字面等于: '静音', 在节点内: true });
    rec.Q3_静音钮 = 静;
    const S = (静.点 || [])[0];
    if (S && S.中心是自己) {
      rec.Q3_前 = await p.evaluate((i) => { const n = document.querySelector('.react-flow__node[data-id="' + i + '"]');
        const e = n.querySelector('[data-testid="timeline-mute-button"]');
        const q = e.getBoundingClientRect();
        return { aria: e.getAttribute('aria-label'), 盒: [Math.round(q.width * 10) / 10, Math.round(q.height * 10) / 10], ariaDisabled: e.getAttribute('aria-disabled') }; }, SELF);
      await p.mouse.click(S.x, S.y); await p.waitForTimeout(1500);
      rec.Q3_点一次后 = await p.evaluate((i) => { const n = document.querySelector('.react-flow__node[data-id="' + i + '"]');
        const e = n.querySelector('[data-testid="timeline-mute-button"]');
        return { aria: e.getAttribute('aria-label') }; }, SELF);
      const S2 = (await 找点({ sel: 'button,[role=button]', 在节点内: true, ariaRegex: '^(取消静音|静音|Unmute|Mute)$' })).点 || [];
      rec.Q3_再点候选 = S2;
      const S2b = S2.find((z) => z.aria !== rec.Q3_前.aria) || S2[0];
      if (S2b && S2b.中心是自己) { await p.mouse.click(S2b.x, S2b.y); await p.waitForTimeout(1500); rec.Q3_点了两次 = true; }
      rec.Q3_终态 = await p.evaluate((i) => { const n = document.querySelector('.react-flow__node[data-id="' + i + '"]');
        const e = n.querySelector('[data-testid="timeline-mute-button"]');
        return { aria: e.getAttribute('aria-label') }; }, SELF);
      落盘();
      断言('④ 🔑 点「静音」aria **确实翻转**且再点一次**能翻回来**（可逆）',
        rec.Q3_前.aria !== rec.Q3_点一次后.aria && rec.Q3_终态.aria === rec.Q3_前.aria,
        { 前: rec.Q3_前.aria, 点一次后: rec.Q3_点一次后.aria, 终态: rec.Q3_终态.aria, 点了两次: rec.Q3_点了两次 });
    }

    // ---------- Q4：全屏编辑 ----------
    const 全 = await 找点({ sel: 'button,[role=button]', 字面等于: '全屏编辑', 在节点内: true });
    rec.Q4_全屏钮 = 全;
    const F = (全.点 || [])[0];
    if (F && F.中心是自己) {
      await p.mouse.click(F.x, F.y); await p.waitForTimeout(2400);
      rec.Q4 = await p.evaluate(() => {
        const e = document.querySelector('[data-testid="timeline-fullscreen-editor"]') ||
          Array.from(document.querySelectorAll('[role=dialog]')).find((d) => d.getBoundingClientRect().width > 1200);
        if (!e) return { 命中: false };
        const r = e.getBoundingClientRect();
        const 盒 = (x) => { const q = x.getBoundingClientRect(); return [Math.round(q.width), Math.round(q.height), Math.round(q.x), Math.round(q.y)]; };
        return { 命中: true, testid: e.getAttribute('data-testid'), role: e.getAttribute('role'), 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
          逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 220),
          testid清单: Array.from(new Set(Array.from(e.querySelectorAll('[data-testid]')).map((x) => x.getAttribute('data-testid')))).sort(),
          按钮: Array.from(e.querySelectorAll('button,[role=button]')).map((x) => ({ aria: x.getAttribute('aria-label'), 逐字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14), 盒: 盒(x) })).filter((z) => z.盒[0] > 0) };
      });
      rec.拍前断言2 = { 命中: rec.Q4.命中, 盒: rec.Q4.盒, 关闭钮: (rec.Q4.按钮 || []).filter((z) => /Close|关闭|✕/.test(z.aria || '')), 积分: await R.credits() };
      断言('⑤ 点「全屏编辑」打开 `timeline-fullscreen-editor` 且铺满视口', rec.Q4.命中 === true && rec.Q4.盒 && rec.Q4.盒[0] >= 1270, rec.拍前断言2);
      if (rec.Q4.命中) {
        await p.screenshot({ path: new URL('./58-timeline-fullscreen-from-node.png', 出图).pathname });
        rec.截图2 = 'screenshots/58-timeline-fullscreen-from-node.png';
      }
      await p.keyboard.press('Escape'); await p.waitForTimeout(1600);
      rec.Q4_Esc后 = await p.evaluate(() => document.querySelectorAll('[data-testid="timeline-fullscreen-editor"]').length);
      落盘();
    }

    // ---------- Q5：导出时间线 —— 只验「触发下载」+ 建议文件名，不落盘不核验成片 ----------
    const 导 = await 找点({ sel: 'button,[role=button]', 字面等于: '导出时间线', 在节点内: true });
    rec.Q5_导出钮 = 导;
    const E = (导.点 || [])[0];
    rec.Q5 = { 点了: false };
    if (E && E.中心是自己) {
      const dl = p.waitForEvent('download', { timeout: 8000 }).catch(() => null);
      await p.mouse.click(E.x, E.y);
      const d = await dl;
      rec.Q5.点了 = true;
      rec.Q5.触发下载 = !!d;
      if (d) { rec.Q5.建议文件名 = d.suggestedFilename(); await d.cancel().catch(() => {}); rec.Q5.已丢弃 = true; }
      await p.waitForTimeout(1500);
      rec.Q5_点后浮层 = await R.overlays();
      rec.Q5_积分 = await R.credits();
      落盘();
    }
    断言('⑥ 点「导出时间线」**确实触发了下载**（只验触发与建议文件名，不落盘、不核验成片）',
      rec.Q5.触发下载 === true, rec.Q5);
    断言('⑦ 导出**不扣积分**（仍 805）', String(rec.Q5_积分).indexOf('805') >= 0, { 积分: rec.Q5_积分 });
  }

  // ---------- 收尾：右键 → 上下文菜单 → 删除 ⌫ ----------
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

console.log('\n起点', JSON.stringify(rec.起点));
console.log('时间线键', JSON.stringify(rec.时间线键));
console.log('建', JSON.stringify(rec.建));
console.log('自建 屏上盒', JSON.stringify(rec.自建 && rec.自建.屏上盒), '| canvas', JSON.stringify(rec.自建 && rec.自建.canvas));
console.log('自建 逐字', JSON.stringify(rec.自建 && rec.自建.逐字));
console.log('自建 按钮', JSON.stringify(rec.自建 && rec.自建.按钮));
console.log('\nQ3 静音', JSON.stringify({ 前: rec.Q3_前, 点一次后: rec.Q3_点一次后, 终态: rec.Q3_终态, 再点候选: rec.Q3_再点候选 }));
console.log('\nQ4 全屏', JSON.stringify(rec.Q4, null, 1).slice(0, 2400));
console.log('Q4 Esc后 fullscreen-editor 命中 =', rec.Q4_Esc后);
console.log('\nQ5 导出', JSON.stringify(rec.Q5), '| 点后浮层', rec.Q5_点后浮层, '| 积分', rec.Q5_积分);
console.log('\n删除', JSON.stringify((rec.删除 || []).map((d) => d.消失 || d.__err)));
console.log('收尾检查', JSON.stringify(rec.收尾检查));
console.log('收尾', JSON.stringify(rec.收尾), '| 小地图', JSON.stringify(rec.小地图), '| 异常', rec.异常 || '无');
console.log('截图', JSON.stringify([rec.截图1, rec.截图2]));

断言('⑧ 建-删护栏全过 + 消失集合恰好 {SELF}', (rec.删除 || []).length > 0 && (rec.删除 || []).every((d) => d.消失 && d.消失.length === 1), { 删除: (rec.删除 || []).map((d) => d.消失 || d.__err) });
断言('⑨ 🔑 收尾积分**仍是 805**', String((rec.收尾 || {}).积分).indexOf('805') >= 0, { 积分: (rec.收尾 || {}).积分 });
if (rec.收尾检查 && rec.收尾检查.位移节点) 断言('⑩ 其余节点零位移', rec.收尾检查.位移节点.length === 0, rec.收尾检查);
rec.断言全过 = 断言过; 落盘();
await b.close();
