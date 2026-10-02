// 批次 112 · a 轮：把 `20-reference.md` 里那行「`2 resources: 1 ready, 0 processing, 1 failed.` ← 抄写，未实测」
// 变成实测 —— 目标是**造出一个 `failed` 资源**。
//
// 此前两次尝试都没造出来：
//   批次 105：合法 `ftyp` 头 + 1MB 伪随机字节的 mp4、`jimeng-b105-truncated.mp4`
//     ⇒ 都停在 `processing`，**11 分钟内账本逐位不动**，**不会自己翻成 `failed`**
//   批次 110：拦播放取流 ⇒ 卡片变红，但**资源账纹丝不动**（仍是 `1 ready`）
//     ⇒ 证明「播放期失败」根本不走资源账
//
// 本轮换素材类型与损坏程度（全部**自造**，免费，上传不扣分）：
//   ① `/tmp/jimeng-b112-empty.png`      **0 字节**（扩展名在白名单里）
//   ② `/tmp/jimeng-b112-truncated.png`  合法 PNG 签名 + 完整 IHDR（33 字节，缺 IDAT/IEND）
//   ③ `/tmp/jimeng-b112-badidat.png`    结构/CRC 全合法，但 IDAT 是 64 字节垃圾（解压必失败）
//   ④ `/tmp/jimeng-b112-text.png`       纯文本改 `.png` 扩展名
//   `file` 命令的读数：②③ 都被认成「PNG image data, 2 x 2, 8-bit/color RGB」
//
// 🔴 判据：**资源账**（`X resource(s): Y ready, Z processing, W failed.`）
//   —— 这是「素材走到哪一步」最省事的判据（批次 105 立的）。
//   🔴 停止条件**不能**写成 `/failed|失败|error/i`（批次 105 的坑：会被账本里的 `0 failed` 命中），
//   本轮**先取数字再比大小**。
// 🔴 护栏三道：建前存全画布 id 集合；建后差集**恰好一个**且**同时 `.selected`**；
//    z 轮删除时落点**按动作时刻现算**、`elementFromPoint` 命中目标内部、不叠矩形条件。
// 📌 本轮**逐个上传、逐个观察完再传下一个**（串行），避免多个自建节点同时在场。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a' };
const save = () => writeFileSync(new URL('./_tmp-b112a.json', import.meta.url), JSON.stringify(out, null, 1));

const FILES = [
  { key: 'empty', path: '/tmp/jimeng-b112-empty.png', note: '0 字节' },
  { key: 'truncated', path: '/tmp/jimeng-b112-truncated.png', note: '合法签名+IHDR，缺 IDAT/IEND（33 字节）' },
  { key: 'badidat', path: '/tmp/jimeng-b112-badidat.png', note: '结构/CRC 合法，IDAT 是 64 字节垃圾（解压必失败）' },
  { key: 'text', path: '/tmp/jimeng-b112-text.png', note: '纯文本改 .png 扩展名' },
];
out.files = FILES;

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);

// 🔑 资源账解析：**先取数字再比大小**，绝不用字面量去 match（批次 105 的坑）
const ledger = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const t = (n.innerText || '').replace(/\s+/g, ' ').trim();
  const m = t.match(/(\d+) resources?: (\d+) ready, (\d+) processing, (\d+) failed/);
  return {
    innerText: t.slice(0, 180),
    aria: n.getAttribute('aria-label'),
    cls: n.className,
    n: m ? m[1] : null, ready: m ? Number(m[2]) : null, processing: m ? Number(m[3]) : null, failed: m ? Number(m[4]) : null,
    hasFailed: m ? Number(m[4]) > 0 : false,
    hasProcessing: m ? Number(m[3]) > 0 : false,
    uploading: /正在上传/.test(t),
    playbackError: !!n.querySelector('[data-testid$="-playback-error"]'),
    testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
    arias: Array.from(new Set(Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')))),
    imgs: n.querySelectorAll('img').length,
  };
}, id);

const railPt = () => p.evaluate(() => Array.from(document.querySelectorAll('button,[role=button]'))
  .map((e) => { const r = e.getBoundingClientRect(); return { aria: e.getAttribute('aria-label'), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; })
  .filter((x) => x.aria === '上传' && x.w > 0 && x.h > 0)[0] || null);

out.start = { nodes: await nodeN(), credits: await credits() };
log('起点：', JSON.stringify(out.start));
save();

const g = await keyGuard(p);
log('焦点守卫：', g.safe ? '✅' : '⛔', g.where || '');
if (!g.safe) { log('⛔ 中止'); await b.close(); process.exit(2); }

out.runs = [];
for (const F of FILES) {
  const idsBefore = await allIds();
  const rail = await railPt();
  if (!rail) { log('\n🔴 找不到上传入口 ⇒ 中止'); break; }
  const onFc = async (fc) => { try { await fc.setFiles(F.path); } catch (e) { log('  setFiles 失败：', e.message); } };
  p.on('filechooser', onFc);
  await p.mouse.move(rail.x + rail.w / 2, rail.y + rail.h / 2); await p.waitForTimeout(500);
  await p.mouse.click(rail.x + rail.w / 2, rail.y + rail.h / 2);

  let SELF = null;
  for (let k = 1; k <= 14; k++) {
    await p.waitForTimeout(1200);
    const ids = await allIds();
    const diff = ids.filter((id) => !idsBefore.includes(id));
    if (diff.length) { SELF = diff[0]; break; }
  }
  p.off('filechooser', onFc);
  log(`\n=== ${F.key}（${F.note}）===`);
  if (!SELF) { log('  🔴 没有建出新节点'); out.runs.push({ ...F, self: null, note: 'no node created' }); save(); continue; }
  const selIds = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
  const g2 = { diffN: 1, ok: selIds.includes(SELF) };
  log('  节点：', SELF, '｜护栏② 差集恰好一个且同时 selected =', g2.ok);
  if (!g2.ok) { log('  ⛔ 护栏不过 ⇒ 不再观察，记为中止'); out.runs.push({ ...F, self: SELF, guardrail2: g2, aborted: true }); save(); continue; }

  // 连采 14 次 / ~17 秒，看账本会不会翻到 failed
  const samples = [];
  const t0 = Date.now();
  let stopped = null;
  for (let k = 1; k <= 14; k++) {
    await p.waitForTimeout(1200);
    const s = await ledger(SELF);
    samples.push({ k, ms: Date.now() - t0, innerText: s.innerText, ready: s.ready, processing: s.processing, failed: s.failed, uploading: s.uploading, imgs: s.imgs, hasPlaybackError: s.playbackError });
    log(`   #${String(k).padStart(2)} ${String(Date.now() - t0).padStart(5)}ms  ready=${s.ready} processing=${s.processing} failed=${s.failed} 上传中=${s.uploading} imgs=${s.imgs} 播失败=${s.playbackError}`);
    save();
    if (s.hasFailed) { stopped = 'failed'; log('   ⇒ ✅ 出现 failed！'); break; }
    if (!s.hasProcessing && !s.uploading && s.ready !== null) { stopped = k === 1 ? 'settled-immediately' : 'settled'; log('   ⇒ 已落定（不再 processing）'); break; }
  }
  const fin = await ledger(SELF);
  log('  最终账：', JSON.stringify({ ready: fin.ready, processing: fin.processing, failed: fin.failed, imgs: fin.imgs, playbackError: fin.playbackError }));
  log('  innerText：', fin.innerText);
  log('  testids：', JSON.stringify(fin.testids));
  log('  arias：', JSON.stringify(fin.arias));
  out.runs.push({ ...F, self: SELF, guardrail2: g2, samples, stopped, final: fin });
  save();

  // 这一格观察完，**立刻删掉**，避免多个自建节点同时在场
  const idsA = await allIds();
  const spot = await p.evaluate((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!n) return { __err: 'gone' };
    const r = n.getBoundingClientRect(); const c = [];
    for (let y = Math.ceil(r.y) + 3; y < r.y + r.height - 3; y += 4)
      for (let x = Math.ceil(r.x) + 3; x < r.x + r.width - 3; x += 4) {
        if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
        const el = document.elementFromPoint(x, y);
        if (el && (el === n || n.contains(el))) c.push({ x, y }); }
    return { total: c.length, sample: c.slice(0, 2) };
  }, SELF);
  if (spot.__err || !spot.total) { log('  ⚠️ 落点不可用，本轮这个节点先留着，z 轮统一清'); out.runs.at(-1).cleanup = 'deferred'; save(); continue; }
  const pt = spot.sample[0];
  await p.mouse.move(pt.x, pt.y); await p.waitForTimeout(300);
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1300);
  const selOk = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); return n ? n.classList.contains('selected') : null; }, SELF);
  if (selOk !== true) { log('  ⚠️ 没读到 selected ⇒ 留到 z 轮'); out.runs.at(-1).cleanup = 'deferred'; save(); continue; }
  const spot2 = await p.evaluate((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const r = n.getBoundingClientRect(); const c = [];
    for (let y = Math.ceil(r.y) + 3; y < r.y + r.height - 3; y += 4)
      for (let x = Math.ceil(r.x) + 3; x < r.x + r.width - 3; x += 4) {
        if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
        const el = document.elementFromPoint(x, y);
        if (el && (el === n || n.contains(el))) c.push({ x, y }); }
    return { total: c.length, sample: c.slice(-2) };
  }, SELF);
  const rp = spot2.sample[spot2.sample.length - 1];
  await p.mouse.move(rp.x, rp.y); await p.waitForTimeout(350);
  await p.mouse.down({ button: 'right' }); await p.waitForTimeout(300); await p.mouse.up({ button: 'right' });
  await p.waitForTimeout(1200);
  const menu = await p.evaluate(() => { for (const m of document.querySelectorAll('[role=menu]')) {
    const t = (m.innerText || '').replace(/\s+/g, ' ').trim();
    if (t.startsWith('复制 ⌘ C') && (t.match(/⌫/g) || []).length === 1) return { ok: true, text: t.slice(0, 140) }; } return { ok: false }; });
  log('  右键菜单：', JSON.stringify(menu).slice(0, 200));
  const dp = await p.evaluate(() => { for (const m of document.querySelectorAll('[role=menu]')) {
    const t = (m.innerText || '').replace(/\s+/g, ' ').trim();
    if (!t.startsWith('复制 ⌘ C') || (t.match(/⌫/g) || []).length !== 1) continue;
    for (const e of m.querySelectorAll('*')) { if (e.children.length) continue;
      if ((e.textContent || '').trim().startsWith('删除')) { const r = e.getBoundingClientRect();
        return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; } } } return null; });
  if (!dp) { log('  ⚠️ 菜单里没有删除项 ⇒ 留到 z 轮'); await p.keyboard.press('Escape'); out.runs.at(-1).cleanup = 'deferred'; save(); continue; }
  await p.mouse.move(dp.x, dp.y); await p.waitForTimeout(250);
  await p.mouse.click(dp.x, dp.y); await p.waitForTimeout(1700);
  const idsB = await allIds();
  const gone = idsA.filter((x) => !idsB.includes(x));
  const onlySelf = gone.length === 1 && gone[0] === SELF;
  log('  删除：消失的 id', JSON.stringify(gone), '｜恰好只有 SELF =', onlySelf);
  out.runs.at(-1).deleted = { gone, onlySelf };
  save();
  await p.mouse.click(8, 300); await p.waitForTimeout(900);   // 取消选中
}

out.end = { nodes: await nodeN(), credits: await credits() };
log('\n终点：', JSON.stringify(out.end));
out.summary = out.runs.map((r) => ({ key: r.key, self: r.self, stopped: r.stopped,
  final: r.final ? { ready: r.final.ready, processing: r.final.processing, failed: r.final.failed, imgs: r.final.imgs } : null,
  deleted: r.deleted ? r.deleted.onlySelf : (r.cleanup || null) }));
log('\n=== 汇总 ===');
log(JSON.stringify(out.summary, null, 1));
const anyFailed = out.runs.some((r) => r.final && r.final.failed > 0);
log('\n有没有造出 failed 资源 =', anyFailed);
save();
log('\nDONE a');
process.exit(0);
