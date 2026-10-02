// 批次 108 · a 轮：造**两个自己的**节点，准备自建一个组。
//
// 🎯 靶子：`organize-group-layout.md:347`
//   **仍未实测**：0 成员空组（只剩两项时）「背景色」展开的色板是否与有成员时相同。
// 批次 50 已定「有成员的组工具条恒为四项（解除编组/布局/背景色/下载）」、
//   「0 成员空组只有两项（无『布局』无『下载』）」——
//   但**「背景色」那一项点开之后的色板本身**两态从没并排读过。
//
// 🔴 共享画布上的最高风险：**⌘G 会把我框到的所有人都编进组**。
//   本批的纪律：
//   ① **绝不用框选**（`organize-group-layout.md` 自己写着「框选会框进所有人的节点」）；
//      一律「点一个 + Shift 点一个」，且**每个落点先过 `elementFromPoint`**；
//   ② 按 ⌘G **之前**先把当前选中的 `data-id` 全量打出来，**逐字核对只有本轮那两个**；
//   ③ 编组后再核对组的成员**恰好**是那两个。
//   任何一步对不上 ⇒ **中止，不继续**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), mine: [] };
const save = () => writeFileSync(new URL('./_tmp-b108a.json', import.meta.url), JSON.stringify(out, null, 1));

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const selIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
const status = () => p.evaluate(() => { const t = document.body.innerText;
  const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
  const tb = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1],
    edges: (t.match(/(\d+) edges?/) || [])[1], zoom: z ? z.getAttribute('aria-label') : null,
    tool: tb ? tb.getAttribute('aria-label') : null,
    credits: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label') }; });
const safeEval = async (fn, arg, tries = 8) => {
  for (let k = 0; k < tries; k++) { const r = await p.evaluate(fn, arg); if (!r || !r.__err) return r; await p.waitForTimeout(700); }
  return { __err: 'gave-up' }; };

/** 上传一个文件建节点，核验差集恰好一个且同时 selected */
async function upload(file) {
  const before = await allIds();
  let seen = null;
  const h = (fc) => { seen = { isMultiple: fc.isMultiple() };
    fc.setFiles(file).catch((e) => log('  setFiles 失败：', e.message)); };
  p.on('filechooser', h);
  const up = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button,[role=button]'))
    .find((x) => x.getAttribute('aria-label') === '上传'); if (!e) return null;
    const r = e.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  if (!up) { log('🔴 找不到上传入口'); return null; }
  await p.mouse.move(up.x, up.y); await p.waitForTimeout(600);
  await p.mouse.click(up.x, up.y);
  let created = [];
  for (let k = 1; k <= 24; k++) {
    await p.waitForTimeout(1500);
    created = (await allIds()).filter((id) => !before.includes(id));
    if (created.length) break;
  }
  p.off('filechooser', h);
  if (created.length !== 1) { log(`  🔴 ${file}：新增 ${created.length} 个，护栏不通过`); return null; }
  await p.waitForTimeout(1300);
  const newSel = (await selIds()).filter((id) => !before.includes(id));
  const ok = newSel.length === 1 && newSel[0] === created[0];
  log(`  ${file}：新增 ${created[0]}｜新选中 ${JSON.stringify(newSel)} ⇒ ${ok ? '✅' : '🔴'}`);
  return ok ? created[0] : null;
}

// 安全落点（第四道护栏）
const spot = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect();
  const others = Array.from(document.querySelectorAll('.react-flow__node')).filter((e) => e.getAttribute('data-id') !== i)
    .map((e) => { const q = e.getBoundingClientRect(); return { x: q.x, y: q.y, w: q.width, h: q.height }; });
  const c = [];
  for (let fy = 0.2; fy <= 0.6; fy += 0.1) for (let fx = 0.2; fx <= 0.8; fx += 0.1) {
    const x = r.x + r.width * fx, y = r.y + r.height * fy;
    if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
    const el = document.elementFromPoint(x, y);
    if (!el || !(el === n || n.contains(el))) continue;
    if (others.some((o) => x >= o.x && x <= o.x + o.w && y >= o.y && y <= o.y + o.h)) continue;
    c.push({ x: Math.round(x), y: Math.round(y) });
  }
  return { rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`, total: c.length, sample: c.slice(0, 4) };
}, id);

out.start = await status();
out.idsBefore = (await allIds()).length;
log('起点：', JSON.stringify(out.start), '｜id 数', out.idsBefore);

log('\n===== ① 上传甲 =====');
const a = await upload('/tmp/jimeng-b108-g1.md');
out.a = a;
save();
log('\n===== ② 上传乙 =====');
const c = await upload('/tmp/jimeng-b108-g2.md');
out.c = c;
save();
out.mine = [a, c].filter(Boolean);
log('\n本轮自建：', JSON.stringify(out.mine));

if (out.mine.length === 2) {
  for (const id of out.mine) {
    const s = await spot(id);
    const info = await safeEval((i) => {
      const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
      const r = n.getBoundingClientRect();
      return { aria: n.getAttribute('aria-label'), text: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 60),
        rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` };
    }, id);
    out['info_' + id] = { spot: s, info };
    log(`\n${id}：`, JSON.stringify({ spot: s.total, ...info }));
  }
  out.end = await status();
  log('\n终态：', JSON.stringify(out.end), '｜id 数', out.idsBefore, '→', (await allIds()).length);
}
out.clean = out.mine.length === 2;
save();
log('\n已落盘 clean =', out.clean);
await b.close();
