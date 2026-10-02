// 批次 109 · c 轮：传一个 `.wav`（音频），全程盯活区域 —— 看它到底会不会产生
// `<文件名>: Upload complete` 那条状态串，以及旧的那条会怎么变。
//
// 已知（a/b 轮）：
//   · 判据可用：全量取 `[role=status],[aria-live],[role=log],output,.sr-only` 的 textContent，**不按子元素过滤**
//   · `b22-upload.png: Upload complete` 命中 ✅，承载者是 `role=status` 里的 **25 个 SPAN**（每个 256 宽、步长 256）
//   · 那 25 个 SPAN 的父容器是 `1×1` + `clip: rect(0px,0px,0px,0px)` + `overflow:hidden`
//     且 1.2 秒连采两次 x **不动** ⇒ **它不是可见跑马灯，是给读屏软件用的活区域**
//   · 顶部 40px 截图里**没有任何这条文案**，只有顶栏「已保存」⇒ **屏幕上根本看不到它**
//   · 页面上一共 **8 个活区域**（清单见 _tmp-b109b.json 的 q3）
//   · 批次 101 传过的 `jimeng-b101-test-avc1.mp4: Upload complete` **已经不在页面上了**
//
// 🔴 本轮会**建一个节点**（音频节点，批次 104 已证免费：805→805），z 轮按护栏删掉。
// 📌 自建节点护栏三道：① 建前存全画布 id 集合 ② 建后差集**恰好一个**且**同时 `.selected`**
//    ③ z 轮删除前现算落点（`elementFromPoint` 命中目标内部即可，**不叠矩形条件** —— 批次 108 订正）
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'c', file: '/tmp/jimeng-b104-test.wav' };
const save = () => writeFileSync(new URL('./_tmp-b109c.json', import.meta.url), JSON.stringify(out, null, 1));

const WAV = out.file;
const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const status = () => p.evaluate(() => {
  const t = document.body.innerText;
  return {
    nodes: (t.match(/(\d+) nodes?/) || [])[1],
    sel: (t.match(/(\d+) selected/) || [])[1],
    credits: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'),
  };
});

// ---- 活区域快照：唯一一个判据，三轮都用它，保证可比 ----
const liveSnap = () => p.evaluate(() => {
  const nodes = Array.from(document.querySelectorAll('[role=status],[aria-live],[role=log],output,.sr-only'));
  const texts = [];
  for (const e of nodes) {
    const t = (e.textContent || '').replace(/\s+/g, ' ').trim();
    if (!t) continue;
    // 跑马灯式重复：把相邻重复折叠掉，只留一份
    const m = t.match(/^(.*?)\1+$/);
    texts.push(m ? m[1] : t);
  }
  return Array.from(new Set(texts));
});

out.start = await status();
out.liveBefore = await liveSnap();
const idsBeforeArr = await allIds();
out.idsBefore = idsBeforeArr.length;
log('起点：', JSON.stringify(out.start), '｜id 数', out.idsBefore);
log('活区域去重后（传之前）：');
out.liveBefore.forEach((t) => log('   ·', t));
save();

const g = await keyGuard(p);
log('\n焦点守卫：', g.safe ? '✅' : '⛔', g.where || '', g.reason || '');
if (!g.safe) { log('⛔ 焦点不安全 ⇒ 中止'); await b.close(); process.exit(2); }

// ---- 触发上传（左栏「上传」+ 全局 filechooser）----
const rail = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role=button]'))
  .map((e) => { const r = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; })
  .filter((x) => x.aria === '上传' && x.w > 0 && x.h > 0));
log('上传入口：', JSON.stringify(rail));
if (!rail.length) { log('🔴 找不到上传入口'); save(); await b.close(); process.exit(1); }

let seen = null;
p.on('filechooser', async (fc) => {
  seen = { isMultiple: fc.isMultiple() };
  log('  filechooser：', JSON.stringify(seen));
  try { await fc.setFiles(WAV); log('  setFiles ok:', WAV); }
  catch (e) { log('  setFiles 失败：', e.message); out.setFilesErr = e.message; }
});

const r0 = rail[0];
const t0 = Date.now();
await p.mouse.move(r0.x + r0.w / 2, r0.y + r0.h / 2); await p.waitForTimeout(600);
await p.mouse.click(r0.x + r0.w / 2, r0.y + r0.h / 2);

// ---- 边传边采：每 1.2s 采一次活区域 + 一次 id 差集，**每采一次就落盘** ----
out.samples = [];
for (let k = 1; k <= 30; k++) {
  await p.waitForTimeout(1200);
  const live = await liveSnap();
  const ids = await allIds();
  const st = await status();
  const selAll = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
  const selNew = selAll.filter((id) => !idsBeforeArr.includes(id));
  const s = { k, ms: Date.now() - t0, live, st,
    diff: ids.filter((id) => !idsBeforeArr.includes(id)),
    selNew };
  out.samples.push(s);
  const has = live.filter((t) => /Upload complete/i.test(t));
  log(`  #${String(k).padStart(2)} ${String(s.ms).padStart(5)}ms  nodes=${st.nodes} sel=${st.sel}  diff=${JSON.stringify(s.diff)}  Upload complete 条数=${has.length}${has.length ? ' → ' + JSON.stringify(has) : ''}`);
  save();
  if (has.some((t) => /jimeng-b104-test\.wav/i.test(t))) { log('  ⇒ ✅ 命中本轮这条'); out.hitAtMs = s.ms; break; }
}

// ---- 收：护栏三道之 ② 差集恰好一个且同时 selected ----
const idsAfter = await allIds();
out.idsAfter = idsAfter.length;
out.diff = idsAfter.filter((id) => !idsBeforeArr.includes(id));
log('\n上传后 id 差集：', JSON.stringify(out.diff));
save();

const selIds = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
out.selIds = selIds;
log('当前 .selected：', JSON.stringify(selIds));
out.guardrail2 = { diffN: out.diff.length, diffIsSelected: out.diff.length === 1 && selIds.includes(out.diff[0]) };
log('护栏② 差集恰好一个且同时 selected =', out.guardrail2.diffN === 1 && out.guardrail2.diffIsSelected);
save();

// 本轮自建节点 = 「带 selected 且我这一轮没见过」的；此处用**上传后新出现**的判定：
// 直接读所有节点，找出 innerText 含本轮文件名的
out.selfCandidates = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node'))
  .filter((n) => /jimeng-b104-test/i.test((n.innerText || '') + ' ' + (n.getAttribute('aria-label') || '')))
  .map((n) => { const r = n.getBoundingClientRect();
    return { id: n.getAttribute('data-id'), cls: n.className, aria: n.getAttribute('aria-label'),
      box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
      selected: n.classList.contains('selected'),
      innerText: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120) }; }));
log('\n本轮文件相关的节点：', JSON.stringify(out.selfCandidates, null, 1));
out.selfId = out.selfCandidates.length === 1 ? out.selfCandidates[0].id : null;
log('SELF =', out.selfId, out.selfId ? '✅' : '🔴 不是恰好一个 ⇒ 不删不猜');
save();

out.liveAfter = await liveSnap();
log('\n活区域去重后（传之后）：');
out.liveAfter.forEach((t) => log('   ·', t));
out.liveNew = out.liveAfter.filter((t) => !out.liveBefore.includes(t));
out.liveGone = out.liveBefore.filter((t) => !out.liveAfter.includes(t));
log('新增：', JSON.stringify(out.liveNew));
log('消失：', JSON.stringify(out.liveGone));
out.end = await status();
log('\n终点：', JSON.stringify(out.end));
save();
log('\nDONE c');
process.exit(0);
