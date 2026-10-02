// 批次 112 · z 轮：删掉本轮自建的那个截断 png 节点，归位。
//
// 本轮自建：`node_67havtjgd8`（b 轮上传 33 字节截断 png，
// 差集**恰好 1 个**且**同时 `.selected`** ✅，积分 805 → 805 ✅）
// a 轮建的两个（truncated / badidat）**当场就删了**，消失的 id 都恰好只有 SELF ✅
// 起点 76 → 现在 77，净增 1，与之吻合。
//
// 第四道护栏（批次 108 定稿）：落点**按动作时刻现算**、`elementFromPoint` 命中目标内部、
//   **不叠矩形条件**、点完读到 `selected === true` 才继续，读不到就**中止不硬删**。
const SELF = 'node_67havtjgd8';
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'z', self: SELF };
const save = () => writeFileSync(new URL('./_tmp-b112z.json', import.meta.url), JSON.stringify(out, null, 1));

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const status = () => p.evaluate(() => { const t = document.body.innerText;
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1],
    edges: (t.match(/(\d+) edges?/) || [])[1],
    zoom: (document.querySelector('[data-testid="canvas-zoom-percent"]') || { getAttribute: () => null }).getAttribute('aria-label'),
    tool: (document.querySelector('[data-testid="canvas-pointer-tool-toggle"]') || { getAttribute: () => null }).getAttribute('aria-label'),
    credits: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label') }; });
const spotNow = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect(); const c = [];
  for (let y = Math.ceil(r.y) + 3; y < r.y + r.height - 3; y += 4)
    for (let x = Math.ceil(r.x) + 3; x < r.x + r.width - 3; x += 4) {
      if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
      const el = document.elementFromPoint(x, y);
      if (el && (el === n || n.contains(el))) c.push({ x, y }); }
  return { total: c.length, box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`, sample: c.slice(0, 3) };
}, id);
const selOf = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); return n ? n.classList.contains('selected') : null; }, id);
const isMenu = () => p.evaluate(() => { for (const m of document.querySelectorAll('[role=menu]')) {
  const t = (m.innerText || '').replace(/\s+/g, ' ').trim();
  if (t.startsWith('复制 ⌘ C') && (t.match(/⌫/g) || []).length === 1) {
    const r = m.getBoundingClientRect();
    return { ok: true, box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`, text: t.slice(0, 200) }; } } return { ok: false }; });
const delItemPos = () => p.evaluate(() => { for (const m of document.querySelectorAll('[role=menu]')) {
  const t = (m.innerText || '').replace(/\s+/g, ' ').trim();
  if (!t.startsWith('复制 ⌘ C') || (t.match(/⌫/g) || []).length !== 1) continue;
  for (const e of m.querySelectorAll('*')) { if (e.children.length) continue;
    if ((e.textContent || '').trim().startsWith('删除')) { const r = e.getBoundingClientRect();
      return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; } } } return null; });

out.start = await status();
log('起点：', JSON.stringify(out.start));
const sp = await spotNow(SELF);
log('落点扫描：', JSON.stringify(sp));
save();
if (sp.__err) { log('节点已不在，跳过'); }
else if (!sp.total) { log('🔴 可用落点 0 个 ⇒ 中止（不猜不硬删）'); save(); await b.close(); process.exit(3); }
else {
  const g0 = await keyGuard(p);
  log('焦点守卫：', g0.safe ? '✅' : '⛔', g0.where || '');
  if (!g0.safe) { log('⛔ 中止'); await b.close(); process.exit(2); }
  const pt = sp.sample[0];
  await p.mouse.move(pt.x, pt.y); await p.waitForTimeout(350);
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1400);
  const sel1 = await selOf(SELF);
  log('点选后 selected =', sel1);
  if (sel1 !== true) { log('🔴 没读到 selected ⇒ 中止'); save(); await b.close(); process.exit(3); }
  const sp2 = await spotNow(SELF);
  const rp = sp2.sample[sp2.sample.length - 1];
  log('右键落点（现算）：', JSON.stringify(rp), '｜可用', sp2.total);
  await p.mouse.move(rp.x, rp.y); await p.waitForTimeout(400);
  await p.mouse.down({ button: 'right' }); await p.waitForTimeout(300); await p.mouse.up({ button: 'right' });
  await p.waitForTimeout(1300);
  const m = await isMenu();
  log('右键菜单：', JSON.stringify(m).slice(0, 260));
  out.menuText = m.text;
  if (!m.ok) { log('🔴 菜单没弹出 ⇒ 中止'); await p.keyboard.press('Escape'); await b.close(); process.exit(3); }
  const dp = await delItemPos();
  if (!dp) { log('🔴 菜单里没有删除项 ⇒ 中止'); await p.keyboard.press('Escape'); await b.close(); process.exit(3); }
  const idsA = await allIds();
  await p.mouse.move(dp.x, dp.y); await p.waitForTimeout(300);
  await p.mouse.click(dp.x, dp.y); await p.waitForTimeout(1900);
  const idsB = await allIds();
  const gone = idsA.filter((x) => !idsB.includes(x));
  const onlySelf = gone.length === 1 && gone[0] === SELF;
  log('删除后消失的 id：', JSON.stringify(gone), '｜恰好只有 SELF =', onlySelf);
  out.deleted = { gone, onlySelf };
  save();
}
await p.mouse.click(8, 300); await p.waitForTimeout(1100);
out.end = await status();
await p.waitForTimeout(900);
out.read2 = await status();
const idsEnd = await allIds();
out.idsEnd = idsEnd.length;
out.leftover = idsEnd.includes(SELF) ? [SELF] : [];
out.clean = out.leftover.length === 0;
log('\n终点：', JSON.stringify(out.end));
log('连读：', JSON.stringify(out.read2));
log('本轮遗留：', JSON.stringify(out.leftover), '｜干净 =', out.clean);
save();
log('\nDONE z');
process.exit(0);
