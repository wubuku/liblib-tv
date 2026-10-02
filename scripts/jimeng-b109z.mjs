// 批次 109 · z 轮：删掉本轮自建的 8 个节点，归位。
//
// 本轮自建（每一条都对应一轮里「差集恰好一个且同时 .selected」✅ 的那次上传）：
//   c 轮 node_n62gwfa97f  wav
//   e 轮 node_5g8wzx4f2k  txt
//   f 轮 node_2zjg6dzhqw  md
//   f 轮 node_3ht5tnv5m9  wav
//   g 轮 node_90381kf6an  wav
//   g 轮 node_kg0tbhxrg7  md
//   g 轮 node_nkseq2ymcz  txt
//   h 轮 node_0c1s36n62s  png
// 起点 76 → 现在 84，**净增 8**，与上表逐条吻合。
//
// 第四道护栏（批次 108 定稿，本轮照它执行）：
//   ① `elementFromPoint` 命中目标**内部**（`el === t || t.contains(el)`）——**不叠矩形条件**
//   ② 落点**按动作时刻现算**（前一步会改变层叠）
//   ③ 点完必须读到预期状态才继续，读不到就**中止，不猜不硬删**
// 另外：点选与右键**彻底分开**并留足重渲染时间（批次 107 教训）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'z' };
const save = () => writeFileSync(new URL('./_tmp-b109z.json', import.meta.url), JSON.stringify(out, null, 1));

const MINE = ['node_n62gwfa97f', 'node_5g8wzx4f2k', 'node_2zjg6dzhqw', 'node_3ht5tnv5m9',
  'node_90381kf6an', 'node_kg0tbhxrg7', 'node_nkseq2ymcz', 'node_0c1s36n62s'];
out.mine = MINE;

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const status = () => p.evaluate(() => {
  const t = document.body.innerText;
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1],
    edges: (t.match(/(\d+) edges?/) || [])[1],
    zoom: (document.querySelector('[data-testid="canvas-zoom-percent"]') || { getAttribute: () => null }).getAttribute('aria-label'),
    tool: (document.querySelector('[data-testid="canvas-pointer-tool-toggle"]') || { getAttribute: () => null }).getAttribute('aria-label'),
    credits: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label') };
});
// 落点扫描：**只问「命中元素是否落在目标内部」**，不叠任何矩形条件（批次 108 订正）
const spotNow = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect(); const c = [];
  for (let y = Math.ceil(r.y) + 3; y < r.y + r.height - 3; y += 4)
    for (let x = Math.ceil(r.x) + 3; x < r.x + r.width - 3; x += 4) {
      if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
      const el = document.elementFromPoint(x, y);
      if (el && (el === n || n.contains(el))) c.push({ x, y });
    }
  return { total: c.length, box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`, sample: c.slice(0, 3) };
}, id);
const selOf = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); return n ? n.classList.contains('selected') : null; }, id);
const isMenu = () => p.evaluate(() => {
  // 右键菜单按**内容**定位（不按面积）：文本以「复制 ⌘ C」开头且「⌫」只出现一次
  const menus = Array.from(document.querySelectorAll('[role=menu]'));
  for (const m of menus) {
    const t = (m.innerText || '').replace(/\s+/g, ' ').trim();
    if (t.startsWith('复制 ⌘ C') && (t.match(/⌫/g) || []).length === 1) {
      const r = m.getBoundingClientRect();
      return { ok: true, box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`, text: t.slice(0, 120) };
    }
  }
  return { ok: false, nMenus: menus.length, texts: menus.map((m) => (m.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40)) };
});
const delItemPos = () => p.evaluate(() => {
  for (const m of document.querySelectorAll('[role=menu]')) {
    const t = (m.innerText || '').replace(/\s+/g, ' ').trim();
    if (!t.startsWith('复制 ⌘ C') || (t.match(/⌫/g) || []).length !== 1) continue;
    for (const e of m.querySelectorAll('*')) {
      if (e.children.length) continue;
      if ((e.textContent || '').trim().startsWith('删除')) { const r = e.getBoundingClientRect();
        return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` }; }
    }
  }
  return null;
});

out.start = await status();
const idsNow0 = await allIds();
out.idsStart = idsNow0.length;
out.presentBefore = MINE.filter((id) => idsNow0.includes(id));
log('起点：', JSON.stringify(out.start), '｜id 数', out.idsStart);
log('本轮自建且仍在：', JSON.stringify(out.presentBefore));
save();

const g0 = await keyGuard(p);
log('焦点守卫：', g0.safe ? '✅' : '⛔', g0.where || '');

out.deleted = [];
out.aborted = [];
for (const id of MINE) {
  const idsA = await allIds();
  const sp = await spotNow(id);
  if (sp.__err) { log(`\n${id}：已经不在了，跳过`); out.deleted.push({ id, note: 'already-gone' }); continue; }
  if (!sp.total) { log(`\n${id}：可用落点 0 个 ⇒ 中止（不猜不硬删）`); out.aborted.push({ id, why: 'no-landing-point', sp }); save(); continue; }
  const pt = sp.sample[0];

  // ① 点选（点完必须读到 selected=true）
  await p.mouse.move(pt.x, pt.y); await p.waitForTimeout(350);
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1400);
  const sel1 = await selOf(id);
  log(`\n${id}：落点 ${JSON.stringify(pt)}（可用 ${sp.total} 个）｜点选后 selected =`, sel1);
  if (sel1 !== true) { log('  🔴 没读到 selected ⇒ 中止'); out.aborted.push({ id, why: 'not-selected', sel1 }); save(); continue; }

  // ② 右键（**重新现算**落点 —— 选中会浮出工具条，层叠已变）
  const sp2 = await spotNow(id);
  if (!sp2.total) { log('  🔴 右键前落点归零 ⇒ 中止'); out.aborted.push({ id, why: 'no-landing-point-before-rmb' }); save(); continue; }
  const rp = sp2.sample[sp2.sample.length - 1];   // 换一个点，避开刚点过的那个
  await p.mouse.move(rp.x, rp.y); await p.waitForTimeout(400);
  await p.mouse.down({ button: 'right' }); await p.waitForTimeout(300); await p.mouse.up({ button: 'right' });
  await p.waitForTimeout(1200);
  const m = await isMenu();
  log('  右键菜单：', JSON.stringify(m).slice(0, 220));
  if (!m.ok) { log('  🔴 菜单没弹出来 ⇒ 中止'); await p.keyboard.press('Escape'); await p.waitForTimeout(600); out.aborted.push({ id, why: 'menu-not-open', m }); save(); continue; }

  // ③ 点「删除」
  const dp = await delItemPos();
  if (!dp) { log('  🔴 菜单里没有删除项 ⇒ 中止'); await p.keyboard.press('Escape'); await p.waitForTimeout(600); out.aborted.push({ id, why: 'no-delete-item' }); save(); continue; }
  await p.mouse.move(dp.x, dp.y); await p.waitForTimeout(300);
  await p.mouse.click(dp.x, dp.y); await p.waitForTimeout(1800);

  // ④ 核对：本轮消失的 id **恰好只有 SELF**
  const idsB = await allIds();
  const gone = idsA.filter((x) => !idsB.includes(x));
  const onlySelf = gone.length === 1 && gone[0] === id;
  log(`  删除后消失的 id：${JSON.stringify(gone)}｜恰好只有 SELF =`, onlySelf);
  out.deleted.push({ id, gone, onlySelf });
  save();
  if (!onlySelf) log('  🔴 消失集合不符合预期 —— 停下人工看');
}

out.end = await status();
const idsEndArr = await allIds();
out.idsEnd = idsEndArr.length;
out.leftover = MINE.filter((id) => idsEndArr.includes(id));
log('\n终点：', JSON.stringify(out.end), '｜id 数', out.idsEnd);
log('本轮遗留：', JSON.stringify(out.leftover));
out.clean = out.leftover.length === 0;
log('清理干净 =', out.clean);
save();
log('\nDONE z');
process.exit(0);
