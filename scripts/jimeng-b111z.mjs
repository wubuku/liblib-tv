// 批次 111 · z 轮：删掉本轮自建的时间线节点，并把画布视图与缩放归位。
//
// 本轮自建：`node_egh7n0acaw`（a 轮「空白右键 → 新建节点 → 时间线」，
// 差集**恰好 1 个**且**同时 `.selected`** ✅）
// 起点 76 → 现在 77，净增 1，与之吻合。
//
// 🔴 本轮留下一个**额外问题**：d 轮做 `⌘ scroll` 时**视图被推走了**
//   （三个时间线节点跑到 `-1328,-910` / `-582,-533` / `148,-515`，全在视口外）
//   ⇒ 我的自建节点**当前点不到**，必须先把它找回来再删。
//   **绝不因为「点不到」就跳过删除、把自建节点留在共享画布上。**
//
// 归位顺序：先删自建节点 → 再归位缩放（回读 + 连读两次）→ 再归位工具态 → 确认 sel=0
// 第四道护栏（批次 108 定稿）：落点**按动作时刻现算**、`elementFromPoint` 命中目标内部、
//   **不叠矩形条件**、点完读到 `selected === true` 才继续，读不到就**中止不硬删**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'z', self: 'node_egh7n0acaw' };
const SELF = out.self;
const save = () => writeFileSync(new URL('./_tmp-b111z.json', import.meta.url), JSON.stringify(out, null, 1));

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const status = () => p.evaluate(() => {
  const t = document.body.innerText;
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1],
    edges: (t.match(/(\d+) edges?/) || [])[1],
    zoom: (document.querySelector('[data-testid="canvas-zoom-percent"]') || { getAttribute: () => null }).getAttribute('aria-label'),
    tool: (document.querySelector('[data-testid="canvas-pointer-tool-toggle"]') || { getAttribute: () => null }).getAttribute('aria-label'),
    credits: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label') };
});
const selfBox = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect();
  return { box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
    onScreen: r.x + r.width > 0 && r.y + r.height > 0 && r.x < innerWidth && r.y < innerHeight,
    transform: n.style.transform };
}, SELF);
const setZoom = async (v) => {
  const bt = await p.evaluate(() => { const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
    if (!z) return null; const r = z.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  if (!bt) return false;
  await p.mouse.click(bt.x, bt.y); await p.waitForTimeout(900);
  const inp = await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-zoom-percent-input"]');
    if (!i) return null; i.focus(); const r = i.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  if (!inp) { await p.keyboard.press('Escape'); return false; }
  await p.mouse.click(inp.x, inp.y); await p.waitForTimeout(350);
  await p.keyboard.press('ControlOrMeta+a'); await p.waitForTimeout(180);
  await p.keyboard.type(String(v), { delay: 110 }); await p.waitForTimeout(400);
  await p.keyboard.press('Enter'); await p.waitForTimeout(1500);
  return true;
};
// 落点扫描：**只问「命中元素是否落在目标内部」**，不叠矩形条件
const spotNow = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect(); const c = [];
  for (let y = Math.ceil(r.y) + 3; y < r.y + r.height - 3; y += 4)
    for (let x = Math.ceil(r.x) + 3; x < r.x + r.width - 3; x += 4) {
      if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
      const el = document.elementFromPoint(x, y);
      if (el && (el === n || n.contains(el))) c.push({ x, y });
    }
  return { total: c.length, box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`, sample: c.slice(0, 3) };
}, id);
const selOf = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); return n ? n.classList.contains('selected') : null; }, id);
const isMenu = () => p.evaluate(() => {
  for (const m of document.querySelectorAll('[role=menu]')) {
    const t = (m.innerText || '').replace(/\s+/g, ' ').trim();
    if (t.startsWith('复制 ⌘ C') && (t.match(/⌫/g) || []).length === 1) {
      const r = m.getBoundingClientRect();
      return { ok: true, box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`, text: t.slice(0, 130) }; } }
  return { ok: false }; });
const delItemPos = () => p.evaluate(() => {
  for (const m of document.querySelectorAll('[role=menu]')) {
    const t = (m.innerText || '').replace(/\s+/g, ' ').trim();
    if (!t.startsWith('复制 ⌘ C') || (t.match(/⌫/g) || []).length !== 1) continue;
    for (const e of m.querySelectorAll('*')) {
      if (e.children.length) continue;
      if ((e.textContent || '').trim().startsWith('删除')) { const r = e.getBoundingClientRect();
        return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; } } }
  return null; });

out.start = await status();
out.selfBefore = await selfBox();
log('起点：', JSON.stringify(out.start));
log('自建节点位置：', JSON.stringify(out.selfBefore));
save();

if (out.selfBefore.__err) { log('节点已不在，跳过删除'); out.alreadyGone = true; }
else if (!out.selfBefore.onScreen) {
  // 视图被推走了 ⇒ 先缩小画布把它带回来（输入框能填任意值，菜单只有 50/100/200）
  log('\n🔴 自建节点不在视口内 ⇒ 先缩到 20% 把它带回来');
  out.zoomForFind = true;
  await setZoom(20); await p.waitForTimeout(1200);
  out.at20 = await selfBox();
  log('  20% 下：', JSON.stringify(out.at20));
  save();
  if (!out.at20.onScreen) { log('  ⛔ 20% 下仍不可见 ⇒ 中止（不硬来）'); await b.close(); process.exit(3); }
} else {
  out.zoomForFind = false;
}

const g0 = await keyGuard(p);
log('焦点守卫：', g0.safe ? '✅' : '⛔', g0.where || '');
if (!g0.safe) { log('⛔ 中止'); await b.close(); process.exit(2); }

const idsA = await allIds();
const sp = await spotNow(SELF);
log('\n落点扫描：', JSON.stringify(sp));
if (!sp.total) { log('🔴 可用落点 0 个 ⇒ 中止（不猜不硬删）'); save(); await b.close(); process.exit(3); }
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
log('右键菜单：', JSON.stringify(m).slice(0, 240));
if (!m.ok) { log('🔴 菜单没弹出 ⇒ 中止'); await p.keyboard.press('Escape'); await b.close(); process.exit(3); }
out.menuText = m.text;

const dp = await delItemPos();
if (!dp) { log('🔴 菜单里没有删除项 ⇒ 中止'); await p.keyboard.press('Escape'); await b.close(); process.exit(3); }
await p.mouse.move(dp.x, dp.y); await p.waitForTimeout(300);
await p.mouse.click(dp.x, dp.y); await p.waitForTimeout(1900);

const idsB = await allIds();
const gone = idsA.filter((x) => !idsB.includes(x));
const onlySelf = gone.length === 1 && gone[0] === SELF;
log('删除后消失的 id：', JSON.stringify(gone), '｜恰好只有 SELF =', onlySelf);
out.deleted = { gone, onlySelf };
save();

// ---- 归位：缩放回 60%、取消选中、工具态、视图 ----
log('\n=== 归位 ===');
if (out.zoomForFind) { await setZoom(60); await p.waitForTimeout(1000); }
const z1 = await status();
log('缩放：', z1.zoom);
if (z1.zoom !== 'Zoom options, 60%') { await setZoom(60); await p.waitForTimeout(1100); }
await p.mouse.click(8, 300); await p.waitForTimeout(1200);   // 取消选中
out.end = await status();
await p.waitForTimeout(900);
out.read2 = await status();
log('终点：', JSON.stringify(out.end));
log('连读：', JSON.stringify(out.read2));
const idsEnd = await allIds();
out.idsEnd = idsEnd.length;
out.leftover = idsEnd.includes(SELF) ? [SELF] : [];
out.clean = out.leftover.length === 0;
out.zoomStable = out.end.zoom === out.read2.zoom;
log('本轮遗留：', JSON.stringify(out.leftover), '｜缩放连读一致 =', out.zoomStable, '｜自建节点 =', out.selfBefore.transform);
save();
log('\nDONE z');
process.exit(0);
