// 批次 109 · e 轮：传一个 `.txt`，看文本文件到底会不会也追加一条 `<文件名>: Upload complete`。
//
// 这是 `assets-and-upload.md:208` 那条挂了很久的「仍未验证」——
// 批次 102 的判据把祖先节点排掉了，连页面上**早就在**的那条都没取到 ⇒ 记成了「未定」。
//
// d 轮已把机制读清，本轮只做一件事，并**用同一个判据**（三轮可比）：
//   `[role=status]` 区域里**每一个子元素的完整文字**（不截断、不按子元素过滤）
//
// 🔴 本轮会建一个文本节点（批次 102 已证免费）。z 轮按护栏删掉本轮两个自建节点。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'e', file: '/tmp/jimeng-b102-doc.txt' };
const save = () => writeFileSync(new URL('./_tmp-b109e.json', import.meta.url), JSON.stringify(out, null, 1));

const TXT = out.file;
const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const status = () => p.evaluate(() => {
  const t = document.body.innerText;
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1],
    credits: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label') };
});
// 同一个判据：role=status 区域的每一条，**完整文字**
const entries = () => p.evaluate(() => {
  const st = document.querySelector('[role=status]');
  if (!st) return [];
  return Array.from(st.children).map((k) => (k.textContent || '').trim());
});

out.start = await status();
out.entriesBefore = await entries();
const idsBeforeArr = await allIds();
out.idsBefore = idsBeforeArr.length;
log('起点：', JSON.stringify(out.start), '｜id 数', out.idsBefore);
const beforeCounts = new Map();
out.entriesBefore.forEach((e) => beforeCounts.set(e, (beforeCounts.get(e) || 0) + 1));
log('活区域条目（去重计数）：');
for (const [t, n] of beforeCounts) log(`   ×${n}  "${t}"`);
out.nEntriesBefore = out.entriesBefore.length;
save();

const g = await keyGuard(p);
log('\n焦点守卫：', g.safe ? '✅' : '⛔', g.where || '', g.reason || '');
if (!g.safe) { log('⛔ 中止'); await b.close(); process.exit(2); }

const rail = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role=button]'))
  .map((e) => { const r = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; })
  .filter((x) => x.aria === '上传' && x.w > 0 && x.h > 0));
log('上传入口：', JSON.stringify(rail));

p.on('filechooser', async (fc) => {
  log('  filechooser isMultiple =', fc.isMultiple());
  try { await fc.setFiles(TXT); log('  setFiles ok:', TXT); } catch (e) { log('  setFiles 失败：', e.message); }
});

const r0 = rail[0];
const t0 = Date.now();
await p.mouse.move(r0.x + r0.w / 2, r0.y + r0.h / 2); await p.waitForTimeout(600);
await p.mouse.click(r0.x + r0.w / 2, r0.y + r0.h / 2);

out.samples = [];
for (let k = 1; k <= 24; k++) {
  await p.waitForTimeout(1200);
  const ents = await entries();
  const ids = await allIds();
  const st = await status();
  const diff = ids.filter((id) => !idsBeforeArr.includes(id));
  const cnt = new Map();
  ents.forEach((e) => cnt.set(e, (cnt.get(e) || 0) + 1));
  const newOnes = Array.from(cnt.entries()).filter(([t, n]) => (beforeCounts.get(t) || 0) < n);
  out.samples.push({ k, ms: Date.now() - t0, n: ents.length, diff, st, newOnes: newOnes.map(([t, n]) => ({ t, n, was: beforeCounts.get(t) || 0 })) });
  log(`  #${String(k).padStart(2)} ${String(Date.now() - t0).padStart(5)}ms  条目数=${ents.length}  nodes=${st.nodes} sel=${st.sel} diff=${JSON.stringify(diff)}  新增条目=${JSON.stringify(out.samples.at(-1).newOnes)}`);
  save();
  if (newOnes.some((x) => /jimeng-b102-doc\.txt/i.test(x.t))) { log('  ⇒ ✅ 命中本轮这条 txt'); out.hitAtMs = Date.now() - t0; break; }
}

const idsAfter = await allIds();
out.diff = idsAfter.filter((id) => !idsBeforeArr.includes(id));
const selIds = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
out.selIds = selIds;
out.guardrail2 = { diffN: out.diff.length, diffIsSelected: out.diff.length === 1 && selIds.includes(out.diff[0]) };
log('\n差集：', JSON.stringify(out.diff), '｜selected：', JSON.stringify(selIds), '｜护栏② =', out.guardrail2.diffN === 1 && out.guardrail2.diffIsSelected);
save();

out.selfCandidates = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node'))
  .filter((n) => /jimeng-b102-doc/i.test((n.innerText || '') + ' ' + (n.getAttribute('aria-label') || '')))
  .map((n) => { const r = n.getBoundingClientRect();
    return { id: n.getAttribute('data-id'), cls: n.className, aria: n.getAttribute('aria-label'),
      box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
      selected: n.classList.contains('selected'),
      innerText: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160) }; }));
log('\n与本轮文件相关的节点：', JSON.stringify(out.selfCandidates, null, 1));
out.selfId = out.selfCandidates.length === 1 ? out.selfCandidates[0].id : null;
log('SELF =', out.selfId, out.selfId ? '✅' : '🔴');
save();

out.entriesAfter = await entries();
out.nEntriesAfter = out.entriesAfter.length;
const afterCounts = new Map();
out.entriesAfter.forEach((e) => afterCounts.set(e, (afterCounts.get(e) || 0) + 1));
log('\n活区域条目（传之后，去重计数）：');
for (const [t, n] of afterCounts) log(`   ×${n}（传前 ×${beforeCounts.get(t) || 0}）  "${t}"`);
out.appended = out.entriesAfter.length - out.entriesBefore.length;
log('\n条目总数：', out.nEntriesBefore, '→', out.nEntriesAfter, '（净增', out.appended, '）⇒',
  out.appended > 0 ? '✅ 追加式日志' : '🔴 没增加');
out.end = await status();
log('终点：', JSON.stringify(out.end));
save();
log('\nDONE e');
process.exit(0);
