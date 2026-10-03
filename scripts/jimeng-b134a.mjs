// 批次 134 · a 轮：**按护栏建一个图片节点 → 取证 → 删掉**，攻 `image-node-empty`。
//
// 🔑 靶子：批次 129 的 18 个「全灭 testid」里，`image-node-empty` 是**唯一还能安全推进**的
//   —— 画布上唯一的图片节点 `node_gref4sw056` **有内容**（有 `image-node-result` /
//   `image-primary-preview-viewport`），所以空态一直验不到；
//   而**新建的图片节点刚创建时必然是空的**。
//
// 🔴 共享画布纪律：左栏「文本/图片/视频/音频」**都会建节点**（批次 129 已逐个确认 4 个 40×40 按钮）。
//   本轮是**有意的建-删循环**，护栏写死在脚本里，任一条不满足就中止：
//   ① 建前存全画布 id 集合；
//   ② 建后差集**恰好 1 个**，且该节点**恰好 `.selected`**（批次 128 实测：点建节点会顺手选中它）；
//   ③ 删除走**右键 → 上下文菜单 →「删除」**（前缀匹配，菜单项逐字是 `删除 ⌫`），
//      **不走键盘**（节点有子控件时中心落点会把焦点交给子控件）；
//   ④ 删除后「本轮消失的 id 集合」**恰好只有 SELF**。
//
// ⚠️ 绝不点：任何生成/扣费按钮、图片生成面板里的任何项。生成面板**只读 DOM**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a', 护栏: [] };
const save = () => writeFileSync(new URL('./_tmp-b134a.json', import.meta.url), JSON.stringify(out, null, 1));
const 断言 = (名, 条件, 详情) => { const ok = !!条件; out.护栏.push({ 名, 通过: ok, 详情 });
  log(`  ${ok ? '✅' : '⛔'} 护栏·${名}：${JSON.stringify(详情)}`); save(); return ok; };

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const selCount = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);
const collect = () => p.evaluate(() => { const s = new Set(); for (const e of document.querySelectorAll('[data-testid]')) s.add(e.getAttribute('data-testid')); return Array.from(s); });
const idsNow = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const escAll = async () => { for (let i = 0; i < 4; i++) { if (!(await overlays())) break; await p.keyboard.press('Escape'); await p.waitForTimeout(900); } };
const 点 = async (s, label) => {
  const pt = await p.evaluate((q) => { const e = document.querySelector(q); if (!e) return { __err: 'not-found' };
    const r = e.getBoundingClientRect(); if (r.width < 1) return { __err: 'zero-size' };
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) { const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y, 命中: h.tagName }; }
    return { __err: 'no-point' }; }, s);
  if (pt.__err) { log(`  【${label}】⛔ ${pt.__err}`); return pt; }
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1800);
  return pt;
};

out.start = { 状态行: await status(), 选中: await selCount(), zoom: await zoom(), credits: await credits(), 浮层: await overlays() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
await escAll();
await p.mouse.move(1276, 716); await p.waitForTimeout(700);

// ---- 护栏 ①：建前存全画布 id 集合 ----
const 基线ids = await idsNow();
const 基线testid = await collect();
out.基线 = { 节点数: 基线ids.length, testid种类: 基线testid.length };
断言('①建前已存全画布 id 集合', 基线ids.length === 76, { 节点数: 基线ids.length, testid种类: 基线testid.length });

// ---- 建节点 ----
log('\n=== 点左栏「图片」建一个图片节点（有意为之，护栏已就位）===');
const 建 = await 点('[aria-label="图片"]', '左栏图片');
out.建落点 = 建;
if (建.__err) { log('  ⛔ 未能建节点，中止'); process.exit(0); }
log('  落点：', JSON.stringify(建));
await p.waitForTimeout(600);

const 建后ids = await idsNow();
const 新增 = 建后ids.filter((x) => !基线ids.includes(x));
const 消失 = 基线ids.filter((x) => !建后ids.includes(x));
out.建后 = { 节点数: 建后ids.length, 新增, 消失, 选中数: await selCount(), 状态行: await status() };
log('  建后节点数', out.建后.节点数, '｜新增', JSON.stringify(新增), '｜消失', JSON.stringify(消失), '｜选中数', out.建后.选中数);

// ---- 护栏 ②：差集恰好 1 个，且恰好选中 ----
if (!断言('②建后差集恰好 1 个且无消失', 新增.length === 1 && 消失.length === 0, { 新增, 消失, 节点数: out.建后.节点数 })) {
  log('  ⛔ 差集不合法 —— 不再继续，先归位'); process.exit(1);
}
const SELF = 新增[0];
const 选中的是我 = await p.evaluate((id) => { const n = document.querySelector('.react-flow__node[data-id="' + id + '"]');
  return !!(n && n.classList.contains('selected')); }, SELF);
if (!断言('②b 新节点恰好处于选中态', 选中的是我 && (await selCount()) === 1, { 选中的是我, 选中数: await selCount() })) {
  log('  ⛔ 选中态异常 —— 中止'); process.exit(1);
}
out.SELF = SELF;
log('  🔑 SELF =', SELF);
save();

// ---- 取证：空态 testid ----
log('\n=== 取证：新节点内部的 testid 与空态 ===');
out.新节点 = await p.evaluate((id) => {
  const n = document.querySelector('.react-flow__node[data-id="' + id + '"]');
  if (!n) return { __err: 'nf' };
  const r = n.getBoundingClientRect(); const cs = getComputedStyle(n);
  const 层 = Array.from(n.querySelectorAll('[data-testid]')).map((e) => { const q = e.getBoundingClientRect(); const c = getComputedStyle(e);
    return { tid: e.getAttribute('data-testid'), tag: e.tagName, role: e.getAttribute('role'), aria: e.getAttribute('aria-label'),
      矩形: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)], 有面积: q.width >= 1 && q.height >= 1,
      op: c.opacity, 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40) }; });
  return { 矩形: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    cls: Array.from(n.classList), opacity: cs.opacity, pointerEvents: cs.pointerEvents,
    逐字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120),
    层, 层数: 层.length, img数: n.querySelectorAll('img').length, 空态testid: 层.filter((x) => x.逐字 === '' ).map((x) => x.tid) };
}, SELF);
if (out.新节点.__err) log('  ⛔', out.新节点.__err);
else {
  log('  矩形', JSON.stringify(out.新节点.矩形), '｜class', JSON.stringify(out.新节点.cls));
  log('  逐字：«' + out.新节点.逐字 + '»');
  log('  内部 testid', out.新节点.层数, '个｜img 数', out.新节点.img数);
  out.新节点.层.forEach((e) => log(`      · ${e.tid} <${e.tag}>${e.role ? ' role=' + e.role : ''} ${e.矩形.join(',')} 有面积=${e.有面积} «${e.逐字}»`));
  const 空 = out.新节点.层.find((e) => e.tid === 'image-node-empty');
  out.imageNodeEmpty = !!空;
  log('  🔑 `image-node-empty`：**' + (空 ? '✅ 在' : '❌ 不在') + '**' + (空 ? ' ' + JSON.stringify(空) : ''));
  const 建后testid = await collect();
  out.建后testid = { 种类: 建后testid.length, 增量: 建后testid.filter((x) => !基线testid.includes(x)), 减量: 基线testid.filter((x) => !建后testid.includes(x)) };
  log('  testid', 建后testid.length, '种｜**增量**', JSON.stringify(out.建后testid.增量), '**减量**', JSON.stringify(out.建后testid.减量));
  save();
}

// ---- 观察是否有生成面板弹出来（只读，绝不点） ----
log('\n=== 观察：新建后是否弹出图片生成面板（只读）===');
out.浮层快照 = await p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).map((e) => {
  const r = e.getBoundingClientRect();
  return { tag: e.tagName, role: e.getAttribute('role'), tid: e.getAttribute('data-testid'),
    矩形: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120),
    按钮: Array.from(e.querySelectorAll('button,[role=button]')).map((x) => (x.innerText || x.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim().slice(0, 14)) }; }));
log('  浮层数', await overlays(), '｜清单：', JSON.stringify(out.浮层快照, null, 1).slice(0, 1200));
out.工具条 = await p.evaluate(() => ['node-toolbar', 'node-feature-chrome-host', 'node-toolbar-feature-host', 'image-generation-form', 'generation-form', 'video-generation-form']
  .map((t) => { const e = document.querySelector('[data-testid="' + t + '"]'); if (!e) return { t, 存在: false };
    const r = e.getBoundingClientRect();
    return { t, 存在: true, 矩形: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80),
      按钮: Array.from(e.querySelectorAll('button,[role=button]')).map((x) => ((x.innerText || '').replace(/\s+/g, ' ').trim() || x.getAttribute('aria-label') || '').slice(0, 16)) }; }));
out.工具条.forEach((e) => { if (e.存在) log(`  · ${e.t} ${JSON.stringify(e.矩形)} «${e.逐字}» 按钮 ${JSON.stringify(e.按钮)}`); else log(`  · ${e.t} —— 不存在`); });
save();

// ---- 护栏 ③④：删除 ----
log('\n=== 护栏 ③：右键 → 上下文菜单 →「删除」===');
{
  // 先确认 SELF 仍处于选中态
  const 仍选中 = await p.evaluate((id) => { const n = document.querySelector('.react-flow__node[data-id="' + id + '"]'); return !!(n && n.classList.contains('selected')); }, SELF);
  断言('③a 删除前 SELF 仍选中', 仍选中, { 仍选中, 选中数: await selCount() });
  const 落 = await p.evaluate((id) => { const n = document.querySelector('.react-flow__node[data-id="' + id + '"]'); if (!n) return { __err: 'nf' };
    const r = n.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 4; y <= r.y + r.height - 4; y += 4) for (let x = Math.ceil(r.x) + 4; x <= r.x + r.width - 4; x += 4) {
      const h = document.elementFromPoint(x, y); if (h && (h === n || n.contains(h))) return { x, y, 命中: h.getAttribute('data-testid') || h.tagName };
    }
    return { __err: 'no-point' }; }, SELF);
  out.删除落点 = 落;
  if (落.__err) { log('  ⛔', 落.__err); }
  else {
    log('  右键落点', JSON.stringify(落));
    await p.mouse.click(落.x, 落.y, { button: 'right' }); await p.waitForTimeout(1600);
    const 菜单 = await p.evaluate(() => Array.from(document.querySelectorAll('[role=menuitem],[role=menu] button,li,button')).filter((e) => { const r = e.getBoundingClientRect(); return r.width > 1; })
      .map((e) => ({ 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24), 矩形: (r => [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)])(e.getBoundingClientRect()) })));
    out.菜单 = 菜单;
    log('  菜单项：', JSON.stringify(菜单.map((m) => m.逐字)));
    const del = await p.evaluate(() => {
      const els = Array.from(document.querySelectorAll('[role=menuitem],[role=menu] button,li,button'))
        .filter((e) => /^删除/.test((e.innerText || '').replace(/\s+/g, '').trim()));
      if (!els.length) return { __err: 'no-delete-item' };
      const e = els[0]; const r = e.getBoundingClientRect();
      for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2) for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) { const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y, 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim() }; }
      return { __err: 'no-point' }; });
    out.删除项 = del;
    if (del.__err) log('  ⛔', del.__err);
    else {
      log('  删除项逐字 «' + del.逐字 + '» @', del.x + ',' + del.y);
      await p.mouse.click(del.x, del.y); await p.waitForTimeout(1800);
      const 删后 = await idsNow();
      out.删后 = { 节点数: 删后.length, 消失: 基线ids.filter((x) => !删后.includes(x)), 新增: 删后.filter((x) => !基线ids.includes(x)) };
      log('  删后节点数', out.删后.节点数, '｜消失', JSON.stringify(out.删后.消失), '｜新增', JSON.stringify(out.删后.新增));
      断言('④ 删除后消失的 id 恰好只有 SELF', out.删后.消失.length === 1 && out.删后.消失[0] === SELF && out.删后.新增.length === 0, out.删后);
    }
  }
  await escAll();
  save();
}

// ---- 收尾 ----
log('\n=== 收尾归位 ===');
{
  const pp = await p.evaluate(() => { for (let y = 300; y < 640; y += 7) for (let x = 300; x < 760; x += 7) { const h = document.elementFromPoint(x, y); if (h && h.classList && h.classList.contains('react-flow__pane')) return { x, y }; } return null; });
  if (pp) { await p.mouse.click(pp.x, pp.y); await p.waitForTimeout(1200); }
  await p.mouse.move(1276, 716); await p.waitForTimeout(700);
  const endIds = await idsNow(); const endT = await collect();
  out.收尾 = { 选中: await selCount(), 状态行: await status(), 浮层: await overlays(), zoom: await zoom(), credits: await credits(),
    节点数: endIds.length, 基线节点数: 基线ids.length, testid种类: endT.length, 基线testid: 基线testid.length };
  out.收尾.节点差集 = { 多: endIds.filter((x) => !基线ids.includes(x)), 少: 基线ids.filter((x) => !endIds.includes(x)) };
  out.收尾.testid差集 = { 多: endT.filter((x) => !基线testid.includes(x)), 少: 基线testid.filter((x) => !endT.includes(x)) };
  log('收尾：', JSON.stringify(out.收尾));
  log('  节点差集：多', JSON.stringify(out.收尾.节点差集.多), '少', JSON.stringify(out.收尾.节点差集.少));
  log('  testid 差集：多', JSON.stringify(out.收尾.testid差集.多), '少', JSON.stringify(out.收尾.testid差集.少));
  断言('收尾 节点 id 与基线逐个一致', out.收尾.节点差集.多.length === 0 && out.收尾.节点差集.少.length === 0, out.收尾.节点差集);
  断言('收尾 testid 与基线逐个一致', out.收尾.testid差集.多.length === 0 && out.收尾.testid差集.少.length === 0, out.收尾.testid差集);
  save();
}
log('\n护栏小结：', out.护栏.map((h) => (h.通过 ? '✅' : '⛔') + h.名).join(' | '));
log('\nDONE a');
process.exit(0);
