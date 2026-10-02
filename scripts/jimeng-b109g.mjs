// 批次 109 · g 轮：修掉 f 轮**自己**判出来的负例，再把两条结论重做一遍。
//
// f 轮的阳性对照失败了（`control_valid: false`）⇒ 按设计，① 的结论**当时不成立**。
// 失败原因不是产品，是**判据说错了宿主**：
//   · f 轮用 `document.querySelector('[role=status]')` —— 取的是**文档顺序第一个**
//   · 音频节点上传期间，节点内部会冒出一个 `role="status"` 且
//     `data-testid="audio-node-uploading"`、文字 `正在上传音频 0%`（批次 104 记过 `video-node-uploading`）
//   · 它排在全局那条**前面** ⇒ `querySelector` 取到了它，`children` 只有 1 个
//     ⇒ 「条目 26 → 1」是我读错了宿主，不是产品没追加
//   ⇒ 📌 **同一个 `role` 在这张画布上有多个宿主；按文档顺序取第一个会取错。**
//      这是「testid 相同不等于同一个东西」的**第三次同款**（批次 105、107 各一次，这次是 role 版）
//
// 本轮判据（换成**带归属**的）：
//   `[role=status]` 逐个读，**并标明它在不在某个 `.react-flow__node` 里**
//   只认「不在任何节点里」的那一条全局播报区。
//
// 顺序：先 wav（预期 +1，正）→ 再 md（预期 +0，负）。
// 正的先做，负的就不能用「区域已经满了 / 之前有残留」来解释。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'g' };
const save = () => writeFileSync(new URL('./_tmp-b109g.json', import.meta.url), JSON.stringify(out, null, 1));

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const status = () => p.evaluate(() => {
  const t = document.body.innerText;
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1],
    credits: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label') };
});
// ✅ 新判据：**逐个** [role=status]，标注归属；条目只取「不在任何节点里、且自己有条目」的那一条。
// 📌 画布上共有 **两个** `[role=status]` 都不在节点里：一个是这条上传播报日志，
//    另一个是底部 dock 里那个空的 `P`（`123,699 1×1`，0 个子元素）——
//    所以「不在节点里」还不够，得再加「自己有条目」。
const regions = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=status]')).map((e, i) => ({
  idx: i,
  inNode: !!e.closest('.react-flow__node'),
  ownerNode: (e.closest('.react-flow__node') || { getAttribute: () => null }).getAttribute('data-id'),
  testid: e.getAttribute('data-testid'),
  own: (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 60),
  entries: Array.from(e.children).map((k) => (k.textContent || '').trim()),
})));
// 📌 画布上共有 **两个** `[role=status]` 都不在节点里：一个是这条上传播报日志，
//    另一个是底部 dock 里那个空的 `P`（`123,699 1×1`，0 个子元素）——
//    所以「不在节点里」还不够，得再加「自己有条目」。
const globalEntries = async () => {
  const R = await regions();
  const g = R.filter((r) => !r.inNode && r.entries.length > 0);
  if (g.length === 1) return g[0].entries;
  if (g.length === 0) return [];
  return { __ambiguous: g.length, g: g.map((r) => ({ idx: r.idx, n: r.entries.length, own: r.own })) };
};

// ---- ① 先把「[role=status] 到底有几个宿主」读清楚 ----
out.regionsAtStart = await regions();
log('=== ① 起点 [role=status] 宿主清单 ===');
out.regionsAtStart.forEach((r) => log(`  [${r.idx}] inNode=${r.inNode} owner=${r.ownerNode} testid=${r.testid} 条目数=${r.entries.length} 文字="${r.own}"`));
out.start = await status();
out.entries0 = await globalEntries();
log('\n起点全局条目数：', Array.isArray(out.entries0) ? out.entries0.length : JSON.stringify(out.entries0));
if (Array.isArray(out.entries0)) { const m = new Map(); out.entries0.forEach((e) => m.set(e, (m.get(e) || 0) + 1));
  for (const [t, n] of m) log(`   ×${n} "${t}"`); }
save();

const g = await keyGuard(p);
log('\n焦点守卫：', g.safe ? '✅' : '⛔', g.where || '', g.reason || '');
if (!g.safe) { log('⛔ 中止'); await b.close(); process.exit(2); }

const doUpload = async (file, idsBeforeArr, label, wantDelta) => {
  const before = await globalEntries();
  if (!Array.isArray(before)) { log('  🔴 全局区域不唯一 ⇒ 不测'); return { err: 'ambiguous', before }; }
  const rail = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role=button]'))
    .map((e) => { const r = e.getBoundingClientRect();
      return { aria: e.getAttribute('aria-label'), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; })
    .filter((x) => x.aria === '上传' && x.w > 0 && x.h > 0));
  const r0 = rail[0];
  const onFc = async (fc) => { try { await fc.setFiles(file); } catch (e) { log('  setFiles 失败：', e.message); } };
  p.on('filechooser', onFc);
  const t0 = Date.now();
  await p.mouse.move(r0.x + r0.w / 2, r0.y + r0.h / 2); await p.waitForTimeout(600);
  await p.mouse.click(r0.x + r0.w / 2, r0.y + r0.h / 2);
  const samples = [];
  let lastN = before.length, diff = [], selIds = [];
  for (let k = 1; k <= 26; k++) {
    await p.waitForTimeout(1200);
    const R = await regions();
    const gReg = R.filter((r) => !r.inNode && r.entries.length > 0);
    const ents = gReg.length === 1 ? gReg[0].entries : (gReg.length === 0 ? [] : null);
    const ids = await allIds();
    diff = ids.filter((id) => !idsBeforeArr.includes(id));
    selIds = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
    const st = await status();
    const nodeRegions = R.filter((r) => r.inNode).map((r) => ({ testid: r.testid, own: r.own }));
    if (ents) {
      const m = new Map(); ents.forEach((e) => m.set(e, (m.get(e) || 0) + 1));
      const b2 = new Map(); before.forEach((e) => b2.set(e, (b2.get(e) || 0) + 1));
      const delta = Array.from(m.entries()).map(([t, n]) => ({ t, d: n - (b2.get(t) || 0) })).filter((x) => x.d !== 0);
      samples.push({ k, ms: Date.now() - t0, n: ents.length, delta, nodeRegions, diff, selIds, st });
      log(`   #${String(k).padStart(2)} ${String(Date.now() - t0).padStart(5)}ms 全局条目=${ents.length} 净变=${JSON.stringify(delta)} 节点内 role=status=${JSON.stringify(nodeRegions)}`);
      if (delta.length) { lastN = ents.length; break; }
      lastN = ents.length;
    } else {
      samples.push({ k, ms: Date.now() - t0, ambiguous: R.length, R: R.map((r) => ({ inNode: r.inNode, testid: r.testid })) });
      log(`   #${String(k).padStart(2)} 全局区域数=${R.length} ⇒ 判据不唯一，放弃这一格`);
      break;
    }
  }
  p.off('filechooser', onFc);
  const after = await globalEntries();
  const m = new Map(); (Array.isArray(after) ? after : []).forEach((e) => m.set(e, (m.get(e) || 0) + 1));
  log(`  ${label} 传完：全局条目 ${before.length} → ${Array.isArray(after) ? after.length : '?'}｜diff=${JSON.stringify(diff)}｜selected=${JSON.stringify(selIds)}`);
  log(`  ${label} 最终去重计数：`, JSON.stringify(Array.from(m.entries())));
  return { file, before: before.length, after: Array.isArray(after) ? after.length : null, samples, diff, selIds, counts: Array.from(m.entries()), wantDelta };
};

// ---- ② wav（正） ----
log('\n=== ② 传 .wav（阳性对照，预期全局条目 +1）===');
const idsA = await allIds();
out.wav = await doUpload('/tmp/jimeng-b104-test.wav', idsA, 'wav', 1);
const wavN = (out.wav.counts || []).find(([t]) => t === 'jimeng-b104-test.wav: Upload complete');
log('  wav 条目数 =', wavN ? wavN[1] : 0, '（本轮传之前是 3）');
out.wavOk = !!wavN && wavN[1] === 4;
log('  ⇒', out.wavOk ? '✅ 判据在本轮能抓到新增（3 → 4）' : '🔴 仍未抓到');
save();

// ---- ③ md（负） ----
log('\n=== ③ 传 .md（预期全局条目 +0）===');
const idsB = await allIds();
out.md = await doUpload('/tmp/jimeng-b107-h3.md', idsB, 'md', 0);
log('  md 采样全程净变 =', JSON.stringify((out.md.samples || []).map((s) => s.delta)));
out.mdNoEntry = out.md.after === out.md.after - 0 && (out.md.samples || []).every((s) => !s.delta || s.delta.length === 0);
log('  ⇒', out.mdNoEntry ? '✅ 没有任何新增条目' : '🔴 有新增');
save();

// ---- ④ txt 再来一次（第二个负例，两个独立样本） ----
log('\n=== ④ 传 .txt（第二个负例样本）===');
const idsC = await allIds();
out.txt = await doUpload('/tmp/jimeng-b102-doc.txt', idsC, 'txt', 0);
log('  txt 采样全程净变 =', JSON.stringify((out.txt.samples || []).map((s) => s.delta)));
save();

out.regionsAtEnd = await regions();
log('\n终点 [role=status] 宿主清单：');
out.regionsAtEnd.forEach((r) => log(`  [${r.idx}] inNode=${r.inNode} owner=${r.ownerNode} testid=${r.testid} 条目数=${r.entries.length} 文字="${r.own}"`));
out.selfIds = [...new Set([...(out.wav.diff || []), ...(out.md.diff || []), ...(out.txt.diff || [])])];
log('\n本轮自建节点：', JSON.stringify(out.selfIds));
out.verdict = { wav_entry_2_to_3: out.wavOk, md_no_entry: out.mdNoEntry, txt_no_entry: (out.txt.samples || []).every((s) => !s.delta || s.delta.length === 0) };
log('\n=== 判定 ===', JSON.stringify(out.verdict, null, 1));
out.end = await status();
log('终点状态：', JSON.stringify(out.end));
save();
log('\nDONE g');
process.exit(0);
