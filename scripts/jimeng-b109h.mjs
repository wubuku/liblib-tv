// 批次 109 · h 轮：给「文本类不产生播报条目」再补一个**图片**对照，把规则的边界钉死。
//
// g 轮已得（同一会话、同一个判据、顺序 wav→md→txt）：
//   wav  27 → 28（wav 条目 3 → 4）  ✅ 正例，且证明判据本轮能抓到新增
//   md   28 → 28（26 次采样 / 32.9s，节点确实建出来了）
//   txt  28 → 28（26 次采样 / 32.4s，节点确实建出来了）
//
// 🔴 仍存的一个反驳空间：**「文本类不产生」可能只是「图片/音频/视频产生」**，
//    也可能只是「文本上传得太快、条目来得晚还没出现」。
//    本轮直接传一张 PNG（`/tmp/jimeng-b102-tiny.png`，批次 102 已用它建过节点）：
//    若 png 条目 22 → 23 ⇒ **三类媒体都产生、只有文本不产生**，
//    规则就不是「媒体 vs 非媒体」，而是**按文件类型**分的。
//    顺带：这一轮也能再次验证「条目来得很快」（第几次采样就出现）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'h' };
const save = () => writeFileSync(new URL('./_tmp-b109h.json', import.meta.url), JSON.stringify(out, null, 1));

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const status = () => p.evaluate(() => {
  const t = document.body.innerText;
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1],
    credits: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label') };
});
const regions = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=status]')).map((e, i) => ({
  idx: i, inNode: !!e.closest('.react-flow__node'),
  ownerNode: (e.closest('.react-flow__node') || { getAttribute: () => null }).getAttribute('data-id'),
  testid: e.getAttribute('data-testid'),
  own: (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 60),
  entries: Array.from(e.children).map((k) => (k.textContent || '').trim()),
})));
const globalEntries = async () => { const R = await regions(); const g = R.filter((r) => !r.inNode && r.entries.length > 0); return g.length === 1 ? g[0].entries : []; };
const counts = (arr) => { const m = new Map(); arr.forEach((e) => m.set(e, (m.get(e) || 0) + 1)); return Array.from(m.entries()); };

const PNG = '/tmp/jimeng-b102-tiny.png';
out.start = await status();
const before = await globalEntries();
out.countsBefore = counts(before);
log('起点：', JSON.stringify(out.start), '｜全局条目', before.length);
log('起点去重计数：', JSON.stringify(out.countsBefore));
save();

const g = await keyGuard(p);
log('\n焦点守卫：', g.safe ? '✅' : '⛔', g.where || '', g.reason || '');
if (!g.safe) { log('⛔ 中止'); await b.close(); process.exit(2); }

const rail = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role=button]'))
  .map((e) => { const r = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; })
  .filter((x) => x.aria === '上传' && x.w > 0 && x.h > 0));
const r0 = rail[0];
const onFc = async (fc) => { try { await fc.setFiles(PNG); log('  setFiles ok'); } catch (e) { log('  setFiles 失败：', e.message); } };
p.on('filechooser', onFc);
const idsBefore = await allIds();
const t0 = Date.now();
await p.mouse.move(r0.x + r0.w / 2, r0.y + r0.h / 2); await p.waitForTimeout(600);
await p.mouse.click(r0.x + r0.w / 2, r0.y + r0.h / 2);

out.samples = [];
for (let k = 1; k <= 26; k++) {
  await p.waitForTimeout(1200);
  const ents = await globalEntries();
  const ids = await allIds();
  const diff = ids.filter((id) => !idsBefore.includes(id));
  const m = new Map(); ents.forEach((e) => m.set(e, (m.get(e) || 0) + 1));
  const b2 = new Map(); before.forEach((e) => b2.set(e, (b2.get(e) || 0) + 1));
  const delta = Array.from(m.entries()).map(([t, n]) => ({ t, d: n - (b2.get(t) || 0) })).filter((x) => x.d !== 0);
  const R = await regions();
  const st = await status();
  out.samples.push({ k, ms: Date.now() - t0, n: ents.length, delta, diff,
    nodeRegions: R.filter((r) => r.inNode).map((r) => ({ testid: r.testid, own: r.own })), st });
  log(`  #${String(k).padStart(2)} ${String(Date.now() - t0).padStart(5)}ms 全局条目=${ents.length} 净变=${JSON.stringify(delta)} 节点内=${JSON.stringify(out.samples.at(-1).nodeRegions)}`);
  save();
  if (delta.length) { out.hitAtMs = Date.now() - t0; out.hitAtSample = k; break; }
}
p.off('filechooser', onFc);

const after = await globalEntries();
out.countsAfter = counts(after);
out.countsBefore = counts(before);
log('\nPNG 传完：全局条目', before.length, '→', after.length);
log('最终去重计数：', JSON.stringify(out.countsAfter));
const pngN0 = (out.countsBefore.find(([t]) => /b22-upload\.png/.test(t)) || [, 0])[1];
const pngN1 = (out.countsAfter.find(([t]) => /b22-upload\.png/.test(t)) || [, 0])[1];
const mine = (out.countsAfter.find(([t]) => /b102-tiny\.png/.test(t)) || [, 0])[1];
out.pngOk = mine >= 1;
log(`  本轮新条目 "jimeng-b102-tiny.png: Upload complete" ×${mine}｜旧的 b22-upload.png 条目 ${pngN0} → ${pngN1}`);
log('  ⇒', out.pngOk ? `✅ 图片也产生（第 ${out.hitAtSample} 次采样 / ${out.hitAtMs}ms 出现）` : '🔴 没抓到');
save();

out.selfIds = [...new Set(out.samples.flatMap((s) => s.diff))];
log('\n本轮自建节点：', JSON.stringify(out.selfIds));
out.end = await status();
log('终点：', JSON.stringify(out.end));
save();

out.table = [
  { type: '图片 png', entries: true, how: `b22-upload.png ×22（本轮 +1 "jimeng-b102-tiny.png" ×${mine}）` },
  { type: '视频 mp4', entries: true, how: 'jimeng-b101-test-avc1.mp4 ×2（批次 101、105 各一次）' },
  { type: '音频 wav', entries: true, how: 'jimeng-b104-test.wav ×4（批次 104、109c、109f、109g 各一次）' },
  { type: '文档 md', entries: false, how: '全局条目 28 → 28，26 次采样 / 32.9s' },
  { type: '文档 txt', entries: false, how: '全局条目 28 → 28，26 次采样 / 32.4s' },
];
log('\n=== 文件类型 × 是否产生播报条目 ===');
out.table.forEach((r) => log(`  ${r.entries ? '✅' : '❌'}  ${r.type.padEnd(12)} ${r.how}`));
save();
log('\nDONE h');
process.exit(0);
