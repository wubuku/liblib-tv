// 批次 111 · a 轮：用「空白右键 → 新建节点 → 时间线」造一个**自建时间线节点**。
//
// 本批靶子：`help-and-shortcuts.md:329`
//   | 时间线 | 缩放时间线 | `⌘ scroll` | ❓ **未单独实测** | 只验证过**画布侧**的同一按键 |
// 附带：`按 F 键` 表里「时间线 → ✅ `timeline-fullscreen-editor` 1280×720」这条此前是**在别人节点上**读的，
//   可以在自建节点上独立复核一次。
//
// 🔴 批次 107 记过一条：**左栏「时间线」那一行点下去 24 轮没建出新节点**。
//   本轮改走批次 102 已验证的入口：**空白右键 → 新建节点 → 时间线**
//   （该子菜单逐字 9 项 `文本｜图片｜视频｜音频｜时间线｜主体｜导演台｜从资产库添加｜本地上传`）。
//
// 🔴 护栏三道：① 建前存全画布 id 集合 ② 建后差集**恰好一个**且**同时 `.selected`**
//    ③ z 轮删除时落点**按动作时刻现算**、`elementFromPoint` 命中目标内部、不叠矩形条件
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a' };
const save = () => writeFileSync(new URL('./_tmp-b111a.json', import.meta.url), JSON.stringify(out, null, 1));

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const status = () => p.evaluate(() => {
  const t = document.body.innerText;
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1],
    edges: (t.match(/(\d+) edges?/) || [])[1],
    zoom: (document.querySelector('[data-testid="canvas-zoom-percent"]') || { getAttribute: () => null }).getAttribute('aria-label'),
    tool: (document.querySelector('[data-testid="canvas-pointer-tool-toggle"]') || { getAttribute: () => null }).getAttribute('aria-label'),
    credits: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label') };
});

out.start = await status();
const idsBefore = await allIds();
out.idsBefore = idsBefore.length;
log('起点：', JSON.stringify(out.start), '｜id 数', out.idsBefore);
save();

const g = await keyGuard(p);
log('焦点守卫：', g.safe ? '✅' : '⛔', g.where || '');
if (!g.safe) { log('⛔ 中止'); await b.close(); process.exit(2); }

// ---- 找一块空白处 ----
out.blank = await p.evaluate(() => {
  const bad = (x, y) => { const el = document.elementFromPoint(x, y);
    if (!el || el.closest('.react-flow__node')) return true;
    if (x < 200 || y < 60 || y > 630 || x > 1120) return true;
    if (el.closest('button,[role=button],input,a')) return true; return false; };
  const all = [];
  for (let y = 280; y < 630; y += 12) for (let x = 260; x < 1100; x += 12) if (!bad(x, y)) all.push([x, y]);
  return { n: all.length, first: all[0] || null };
});
log('可用空白点数：', out.blank.n, '｜第一块：', JSON.stringify(out.blank.first));
if (!out.blank.first) { log('🔴 找不到空白 ⇒ 中止'); save(); await b.close(); process.exit(3); }
const [bx, by] = out.blank.first;

await p.mouse.move(bx, by); await p.waitForTimeout(400);
await p.mouse.down({ button: 'right' }); await p.waitForTimeout(300); await p.mouse.up({ button: 'right' });
await p.waitForTimeout(1200);

out.menus = await p.evaluate(() => Array.from(document.querySelectorAll('[role=menu]')).map((m) => {
  const r = m.getBoundingClientRect(); const cs = getComputedStyle(m);
  return { aria: m.getAttribute('aria-label'), rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
    vis: cs.visibility, items: Array.from(m.querySelectorAll('[role=menuitem]')).map((i) => (i.innerText || '').trim()).slice(0, 12) }; }));
log('\n=== 右键后 [role=menu] ===');
out.menus.forEach((m, i) => log(`  [${i}] aria=${m.aria} ${m.rect} vis=${m.vis} 项=${JSON.stringify(m.items)}`));
save();

// ---- 悬停「新建节点」把子菜单拉出来 ----
out.nj = await p.evaluate(() => {
  for (const m of document.querySelectorAll('[role=menu]')) for (const it of m.querySelectorAll('[role=menuitem]')) {
    if ((it.innerText || '').trim().startsWith('新建节点')) { const r = it.getBoundingClientRect();
      return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2),
        rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
        expanded: it.getAttribute('aria-expanded') }; } }
  return null; });
log('「新建节点」项：', JSON.stringify(out.nj));
if (!out.nj) { log('🔴 找不到「新建节点」⇒ 中止'); await p.keyboard.press('Escape'); await b.close(); process.exit(3); }
await p.mouse.move(out.nj.x, out.nj.y); await p.waitForTimeout(500);
await p.mouse.move(out.nj.x + 3, out.nj.y); await p.waitForTimeout(1400);
out.njAfter = await p.evaluate(() => {
  for (const m of document.querySelectorAll('[role=menu]')) for (const it of m.querySelectorAll('[role=menuitem]')) {
    if ((it.innerText || '').trim().startsWith('新建节点')) return it.getAttribute('aria-expanded'); }
  return null; });
log('悬停后 aria-expanded =', out.njAfter);
save();

// ---- 找子菜单里的「时间线」并逐字确认选中范围 ----
out.tl = await p.evaluate(() => {
  const cands = [];
  for (const m of document.querySelectorAll('[role=menu]')) {
    const r = m.getBoundingClientRect(); const cs = getComputedStyle(m);
    for (const it of m.querySelectorAll('[role=menuitem]')) {
      const t = (it.innerText || '').replace(/\s+/g, ' ').trim();
      const ir = it.getBoundingClientRect();
      if (ir.width === 0) continue;
      cands.push({ t, vis: cs.visibility, rect: `${Math.round(ir.x)},${Math.round(ir.y)} ${Math.round(ir.width)}×${Math.round(ir.height)}`,
        x: Math.round(ir.x + ir.width / 2), y: Math.round(ir.y + ir.height / 2), menuRect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` }); } }
  return cands; });
log('\n=== 可见的菜单项 ===');
out.tl.forEach((c) => log(`  "${c.t}"  ${c.rect} vis=${c.vis} 所属menu=${c.menuRect}`));
const target = out.tl.find((c) => c.t === '时间线' && c.vis !== 'hidden');
log('\n目标项「时间线」：', JSON.stringify(target));
if (!target) { log('🔴 找不到可见的「时间线」项 ⇒ 中止'); await p.keyboard.press('Escape'); save(); await b.close(); process.exit(3); }
save();

// ---- 点它 ----
await p.mouse.move(target.x, target.y); await p.waitForTimeout(500);
out.hitCheck = await p.evaluate((t) => {
  const el = document.elementFromPoint(t.x, t.y);
  return { ok: !!el, text: el ? (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 30) : null,
    inMenu: el ? !!el.closest('[role=menu]') : false };
}, target);
log('点前落点校验：', JSON.stringify(out.hitCheck));
if (!out.hitCheck.ok || !out.hitCheck.inMenu) { log('🔴 落点校验不过 ⇒ 中止'); await p.keyboard.press('Escape'); save(); await b.close(); process.exit(3); }
await p.mouse.click(target.x, target.y);
log('已点「时间线」');
save();

// ---- 护栏②：差集恰好一个且同时 selected ----
let SELF = null;
for (let k = 1; k <= 16; k++) {
  await p.waitForTimeout(1200);
  const ids = await allIds();
  const diff = ids.filter((id) => !idsBefore.includes(id));
  if (diff.length) { out.diff = diff; SELF = diff[0]; log(`  #${k} 差集 = ${JSON.stringify(diff)}`); }
  if (SELF) { const selIds = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
    out.selIds = selIds; out.guardrail2 = { diffN: (out.diff || []).length, ok: (out.diff || []).length === 1 && selIds.includes(SELF) };
    if (out.guardrail2.ok) { log(`  ⇒ 护栏② 通过（selected=${JSON.stringify(selIds)}）`); break; } }
  save();
}
out.selfId = SELF;
log('SELF =', SELF, SELF ? '✅' : '🔴');
save();

// ---- 结构清点 ----
out.selfInfo = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect();
  const leaves = Array.from(n.querySelectorAll('*')).filter((e) => e.children.length === 0 && (e.textContent || '').trim())
    .map((e) => { const b = e.getBoundingClientRect();
      return { tag: e.tagName, text: (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 50),
        box: `${Math.round(b.x)},${Math.round(b.y)} ${Math.round(b.width)}×${Math.round(b.height)}` }; }).slice(0, 20);
  return { id: i, cls: n.className, aria: n.getAttribute('aria-label'),
    innerText: (n.innerText || '').replace(/\s+/g, ' ').trim(),
    screen: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
    transform: n.style.transform,
    testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
    arias: Array.from(new Set(Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')))),
    buttons: Array.from(n.querySelectorAll('button')).map((x) => { const br = x.getBoundingClientRect();
      return { aria: x.getAttribute('aria-label'), testid: x.getAttribute('data-testid'),
        box: `${Math.round(br.x)},${Math.round(br.y)} ${Math.round(br.width)}×${Math.round(br.height)}` }; }),
    roles: Array.from(new Set(Array.from(n.querySelectorAll('[role]')).map((e) => e.getAttribute('role')))),
    leaves };
}, SELF);
log('\n=== 自建时间线节点结构 ===');
log(JSON.stringify(out.selfInfo, null, 1));
save();

out.end = await status();
log('\n终点：', JSON.stringify(out.end));
save();
log('\nDONE a');
process.exit(0);
