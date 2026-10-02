// 批次 109 · f 轮：给 e 轮那个「没有」配一条**同轮、同判据、同会话**的阳性对照。
//
// e 轮读数：`.txt` 上传后活区域条目 **26 → 26（净增 0）**，连采 24 次 / 30.8 秒。
// 那是一条「没有」的结论 —— 按手册纪律，**「没有」必须配一条不共享同一假设的旁证**。
// 旁证不能来自「我另写一段代码再看一遍」，得来自**同一次运行里的正向信号**。
//
// 本轮顺序（顺序很重要：先做预期为负的，再做预期为正的，正的那条才不可能是残留）：
//   ① 传 `.md`（批次 107 已证会变成文本节点）⇒ 预期**净增 0**
//   ② 传**同一个** `/tmp/jimeng-b104-test.wav` ⇒ 预期 wav 条目 **2 → 3**
//   两次之间只改**一个变量**（文件类型），判据、时长、采样频率、会话全不变。
//
// 另：这次把**全部**活区域都采下来（不只是 `role=status`），
// 好回答「md/txt 是不是换了个别的地方播报」。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'f' };
const save = () => writeFileSync(new URL('./_tmp-b109f.json', import.meta.url), JSON.stringify(out, null, 1));

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const status = () => p.evaluate(() => {
  const t = document.body.innerText;
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1],
    credits: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label') };
});
// 判据（与 c/d/e 完全一致）：role=status 里每个子元素的完整文字
const entries = () => p.evaluate(() => {
  const st = document.querySelector('[role=status]');
  if (!st) return [];
  return Array.from(st.children).map((k) => (k.textContent || '').trim());
});
// 旁证通道：全部活区域（与上面那条判据**不共享同一套过滤**）
const allLive = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=status],[aria-live],[role=log],output,.sr-only'))
  .map((e) => { const t = (e.textContent || '').replace(/\s+/g, ' ').trim();
    return { role: e.getAttribute('role'), live: e.getAttribute('aria-live'), testid: e.getAttribute('data-testid'), tag: e.tagName, text: t }; })
  .filter((x) => x.text));

const countOf = (arr, s) => arr.filter((x) => x === s).length;
const uploadOnce = async (file, idsBeforeArr, secs = 26) => {
  const before = await entries();
  const rail = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role=button]'))
    .map((e) => { const r = e.getBoundingClientRect();
      return { aria: e.getAttribute('aria-label'), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; })
    .filter((x) => x.aria === '上传' && x.w > 0 && x.h > 0));
  if (!rail.length) { log('🔴 找不到上传入口'); return { err: 'no-rail' }; }
  const r0 = rail[0];
  let ok = false;
  const onFc = async (fc) => { try { await fc.setFiles(file); ok = true; } catch (e) { log('  setFiles 失败：', e.message); } };
  p.on('filechooser', onFc);
  const t0 = Date.now();
  await p.mouse.move(r0.x + r0.w / 2, r0.y + r0.h / 2); await p.waitForTimeout(600);
  await p.mouse.click(r0.x + r0.w / 2, r0.y + r0.h / 2);
  const samples = [];
  let diff = [], selIds = [];
  for (let k = 1; k <= secs; k++) {
    await p.waitForTimeout(1200);
    const ents = await entries();
    const ids = await allIds();
    diff = ids.filter((id) => !idsBeforeArr.includes(id));
    selIds = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
    const before2 = new Map(); before.forEach((t) => before2.set(t, (before2.get(t) || 0) + 1));
    const now2 = new Map(); ents.forEach((t) => now2.set(t, (now2.get(t) || 0) + 1));
    const delta = Array.from(now2.entries()).map(([t, n]) => ({ t, delta: n - (before2.get(t) || 0) })).filter((x) => x.delta !== 0);
    samples.push({ k, ms: Date.now() - t0, n: ents.length, diff, delta });
    if (delta.length) { log(`   #${String(k).padStart(2)} ${String(Date.now() - t0).padStart(5)}ms 净变 ${JSON.stringify(delta)}`); break; }
  }
  p.off('filechooser', onFc);
  const after = await entries();
  return { file, ok, before: before.length, after: after.length, samples, diff, selIds, entriesAfter: after };
};

out.start = await status();
const idsStart = await allIds();
out.idsStart = idsStart.length;
log('起点：', JSON.stringify(out.start), '｜id 数', out.idsStart);
out.liveStart = await allLive();
log('\n起点活区域（全部，去重前 ' + out.liveStart.length + ' 条）：');
out.liveStart.forEach((x) => log(`   · role=${x.role} live=${x.live} ${x.tag}#${x.testid} "${x.text.slice(0, 70)}"`));
save();

const g = await keyGuard(p);
log('\n焦点守卫：', g.safe ? '✅' : '⛔', g.where || '', g.reason || '');
if (!g.safe) { log('⛔ 中止'); await b.close(); process.exit(2); }

// ---- ① `.md`：预期净增 0 ----
log('\n=== ① 传 .md（预期：没有 Upload complete 条目）===');
out.md = await uploadOnce('/tmp/jimeng-b107-h3.md', idsStart);
log(`  传完：条目 ${out.md.before} → ${out.md.after}｜diff=${JSON.stringify(out.md.diff)}｜selected=${JSON.stringify(out.md.selIds)}`);
log(`  采样 ${out.md.samples.length} 次，全程净变 =`, JSON.stringify(out.md.samples.map((s) => s.delta)));
out.mdNoEntry = out.md.after === out.md.before;
log('  ⇒', out.mdNoEntry ? '✅ 没有新增条目' : '🔴 有新增');
save();

out.liveAfterMd = await allLive();
out.liveNewAfterMd = out.liveAfterMd.filter((x) => !out.liveStart.some((y) => y.text === x.text && y.testid === x.testid));
log('  md 之后新出现的活区域文本：', JSON.stringify(out.liveNewAfterMd.map((x) => x.text.slice(0, 70))));
save();

// ---- ② 同一个 wav：预期 +1（阳性对照，与 ① 只差文件类型） ----
log('\n=== ② 传同一个 .wav（阳性对照：预期 +1 条） ===');
const idsBeforeWav = await allIds();
out.wav = await uploadOnce('/tmp/jimeng-b104-test.wav', idsBeforeWav);
const w0 = countOf(out.wav.entriesAfter, 'jimeng-b104-test.wav: Upload complete');
log(`  传完：条目 ${out.wav.before} → ${out.wav.after}｜diff=${JSON.stringify(out.wav.diff)}｜selected=${JSON.stringify(out.wav.selIds)}`);
log(`  wav 条目现在 ×${w0}`);
log(`  采样净变 =`, JSON.stringify(out.wav.samples.map((s) => s.delta)));
out.wavGotEntry = w0 >= 3;
log('  ⇒', out.wavGotEntry ? '✅ 追加了一条（判据在本次运行里确实能抓到新增）' : '🔴 没抓到 ⇒ 判据本轮失灵，① 的结论不成立');
save();

out.liveEnd = await allLive();
log('\n终点活区域：');
out.liveEnd.forEach((x) => log(`   · role=${x.role} live=${x.live} ${x.tag}#${x.testid} "${x.text.slice(0, 70)}"`));
out.liveNewEnd = out.liveEnd.filter((x) => !out.liveStart.some((y) => y.text === x.text && y.testid === x.testid));
log('本轮新出现的活区域文本：', JSON.stringify(out.liveNewEnd.map((x) => x.text.slice(0, 70))));

out.verdict = {
  md_added_entry: !out.mdNoEntry,
  wav_added_entry: out.wavGotEntry,
  text_types_produce_status_string: !out.mdNoEntry,
  control_valid: out.wavGotEntry,
};
log('\n=== 判定 ===', JSON.stringify(out.verdict, null, 1));
out.end = await status();
log('终点状态：', JSON.stringify(out.end));
save();
log('\nDONE f');
process.exit(0);
