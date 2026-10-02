// 批次 104 · d 轮：决定性播放测试。
//
// c 轮把元素定位钉死了：
//   · `audio-playback-waveform` = **`role="slider"` + `aria-label="Seek <名>"`**、`272×82` canvas、
//     `cursor: ew-resize` ⇒ **波形本身就是那条进度条**
//   · 真正的播放钮是**另一个元素**：`BUTTON`，aria `Play <名>`，`36×36` canvas，
//     **没有 testid**，父元素也没有 testid
//   · `audio-simple-player` 是**铺满整卡的 DIV、没有 aria** —— b 轮我按 testid 去读它，
//     读出空串，还以为「没有播放钮」
//   · 🔴 **`替换媒体` 在同一个节点里出现了两次**：一个 `BUTTON 36×36`，一个 `INPUT 0×0`
//     （`cursor: default`）—— 后者就是那个隐藏的文件选择框（批次 102 说的「挂在节点自己 DOM 里」那个）
//   · `<audio preload="none">` ⇒ `readyState 0` 是**正常的**（不播就不加载），
//     `src` 指向 `…/video/tos/…`（音频素材也走 `video` 路径段）
//
// 本轮：真播放 / 暂停 / 波形跳转 / 时间格式。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), selfId: 'node_rezb9hd9kv' };
const SELF = out.selfId;
const safeEval = async (fn, arg, tries = 6) => {
  for (let k = 0; k < tries; k++) { const r = await p.evaluate(fn, arg); if (!r || !r.__err) return r; await p.waitForTimeout(700); }
  return { __err: 'gave-up' }; };

const probe = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { gone: true };
  const v = n.querySelector('audio');
  const wf = n.querySelector('[data-testid="audio-playback-waveform"]');
  const ph = n.querySelector('[data-testid="audio-waveform-playhead"]');
  const dur = n.querySelector('[data-testid="audio-duration"]');
  const a11y = n.querySelector('[data-testid="audio-duration-accessible"]');
  const btn = Array.from(n.querySelectorAll('button')).find((e) => /^Play |^Pause /.test(e.getAttribute('aria-label') || ''));
  const R = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
    return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; };
  return {
    btnAria: btn ? btn.getAttribute('aria-label') : null, btn: R(btn),
    durVisible: dur ? Array.from(dur.querySelectorAll('span')).map((s) => (s.textContent || '').trim()).join('') : null,
    durA11y: a11y ? (a11y.textContent || '').trim() : null,
    playheadLeft: ph ? /left:\s*([^;]+)/.exec(ph.getAttribute('style') || '') : null,
    playheadLeftPct: ph ? (/left:\s*([\d.]+)%/.exec(ph.getAttribute('style') || '') || [])[1] : null,
    playheadX: ph ? R(ph).x : null,
    waveform: R(wf),
    media: v ? { paused: v.paused, ct: v.currentTime, dur: v.duration, muted: v.muted, vol: v.volume,
      readyState: v.readyState, err: v.error ? v.error.code : null } : null,
  };
}, SELF);

async function clickBtnBy(label, tag) {
  const land = await p.evaluate(([i, lb, tg]) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const list = Array.from(n.querySelectorAll(tg)).filter((e) => (e.getAttribute('aria-label') || '') === lb);
    const e = list[0]; if (!e) return { missing: true, seen: Array.from(n.querySelectorAll(tg)).map((x) => x.getAttribute('aria-label')) };
    const r = e.getBoundingClientRect();
    const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2);
    const el = document.elementFromPoint(x, y);
    return { point: [x, y], rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
      hitTag: el ? el.tagName : null, hitAria: el ? el.getAttribute('aria-label') : null,
      insideSelf: !!(el && el.closest(`.react-flow__node[data-id="${i}"]`)),
      insideTarget: !!(el && (el === e || e.contains(el))) };
  }, [SELF, label, tag]);
  log(`  [${label}] 落点：`, JSON.stringify(land));
  if (land.missing || !land.insideSelf || !land.insideTarget) { log(`  🔴 ${label} 落点判失败`); return false; }
  await p.mouse.move(land.point[0], land.point[1]); await p.waitForTimeout(400);
  await p.mouse.click(land.point[0], land.point[1]); return true;
}

log('=== 起点 ===');
out.s0 = await probe();
log(JSON.stringify(out.s0, null, 1));

// ================= ① 真播放 =================
log('\n=== ① 点真正的 Play 按钮 ===');
if (await clickBtnBy('Play jimeng-b104-test', 'button')) {
  await p.waitForTimeout(1000);
  out.s1 = await probe();
  log('  +1s：', JSON.stringify(out.s1));
  out.playStarted = out.s1.media && out.s1.media.paused === false;
  out.ariaToPause = /^Pause /.test(out.s1.btnAria || '');
  log('  ⇒ 真的开始播了？', out.playStarted, '｜aria 翻成 Pause？', out.ariaToPause);
}

// ================= ② 连采 8 次看时间与播放头 =================
log('\n=== ② 连采 8 次 ===');
out.series = [];
for (let k = 0; k < 8; k++) {
  await p.waitForTimeout(500);
  const s = await probe();
  out.series.push({ t: (k + 1) * 500, ct: s.media && s.media.ct, paused: s.media && s.media.paused,
    a11y: s.durA11y, vis: s.durVisible, ph: s.playheadLeftPct, aria: s.btnAria });
  log(`  t=${(k + 1) * 500}  ct=${s.media && s.media.ct}  paused=${s.media && s.media.paused}  可访问读数=${s.durA11y}  可见读数=${s.durVisible}  播放头left=${s.playheadLeftPct}%  aria=${s.btnAria}`);
}
const cts = out.series.map((r) => r.ct).filter((x) => typeof x === 'number');
out.ctMoved = cts.length >= 2 && Math.abs(cts[cts.length - 1] - cts[0]) > 0.3;
out.ariaFlipped = out.series.some((r) => /^Pause /.test(r.aria || ''));
log('  ⇒ currentTime 在走？', out.ctMoved, '（', JSON.stringify(cts), '）｜aria 翻成过 Pause？', out.ariaFlipped);

// ================= ③ 暂停 =================
log('\n=== ③ 暂停 ===');
if (await clickBtnBy('Pause jimeng-b104-test', 'button')) {
  await p.waitForTimeout(700); out.q1 = await probe();
  await p.waitForTimeout(1100); out.q2 = await probe();
  log('  t1：', JSON.stringify({ aria: out.q1.btnAria, media: out.q1.media, a11y: out.q1.durA11y }));
  log('  t2：', JSON.stringify({ aria: out.q2.btnAria, media: out.q2.media, a11y: out.q2.durA11y }));
  out.pausedFlag = out.q1.media && out.q1.media.paused;
  out.frozen = out.q1.media && out.q2.media && typeof out.q1.media.ct === 'number' && typeof out.q2.media.ct === 'number'
    && Math.abs(out.q1.media.ct - out.q2.media.ct) < 0.02;
  out.ariaBackToPlay = /^Play /.test(out.q2.btnAria || '');
  log('  ⇒ paused？', out.pausedFlag, '｜时间冻结？', out.frozen, '｜aria 翻回 Play？', out.ariaBackToPlay);
}

// ================= ④ 点波形跳转 =================
log('\n=== ④ 点波形跳转 ===');
out.seeks = [];
for (const frac of [0.25, 0.75]) {
  const wf = (await probe()).waveform;
  if (!wf) { log('  找不到波形'); break; }
  const x = Math.round(wf.x + wf.w * frac), y = Math.round(wf.y + wf.h / 2);
  const land = await p.evaluate(([px, py, i]) => { const el = document.elementFromPoint(px, py);
    return { hitTag: el ? el.tagName : null, role: el ? el.getAttribute('role') : null,
      aria: el ? el.getAttribute('aria-label') : null, tid: el ? el.getAttribute('data-testid') : null,
      insideSelf: !!(el && el.closest(`.react-flow__node[data-id="${i}"]`)) }; }, [x, y, SELF]);
  log(`  点 ${Math.round(frac * 100)}% @${x},${y}：`, JSON.stringify(land));
  if (!land.insideSelf || land.tid !== 'audio-playback-waveform') { log('    🔴 落点不对 ⇒ 跳过'); continue; }
  const before = await probe();
  await p.mouse.move(x, y); await p.waitForTimeout(350);
  await p.mouse.click(x, y); await p.waitForTimeout(700);
  const after = await probe();
  const row = { frac, beforeCt: before.media && before.media.ct, afterCt: after.media && after.media.ct,
    beforeA11y: before.durA11y, afterA11y: after.durA11y, beforePh: before.playheadLeftPct, afterPh: after.playheadLeftPct };
  row.landed = typeof row.afterCt === 'number' && typeof row.beforeCt === 'number' && Math.abs(row.afterCt - row.beforeCt) > 0.3;
  row.expect = 4 * frac;   // 素材 4 秒
  row.accurate = row.landed && Math.abs(row.afterCt - row.expect) < 0.5;
  out.seeks.push(row);
  log(`  ⇒ ct ${row.beforeCt} → ${row.afterCt}（期望≈${row.expect}）｜a11y ${row.beforeA11y} → ${row.afterA11y}｜播放头 ${row.beforePh}% → ${row.afterPh}%｜落点=${row.landed} 准=${row.accurate}`);
}

// ================= ⑤ 时间格式判据 =================
log('\n=== ⑤ 时间格式 ===');
out.fmt = { samples: out.seeks.map((s) => ({ frac: s.frac, ct: s.afterCt, a11y: s.afterA11y })) };
for (const s of out.fmt.samples) {
  const a = s.a11y || '';
  const m = /^(\d+):(\d+):(\d+)$/.exec(a);
  out.fmt.parsed = out.fmt.parsed || [];
  if (m) out.fmt.parsed.push({ raw: a, h: m[1], m: m[2], s: m[3],
    asSeconds: Number(m[1]) * 3600 + Number(m[2]) * 60 + Number(m[3]), actualCt: s.ct });
}
log('  读数 → currentTime 对照：', JSON.stringify(out.fmt.parsed, null, 1));
if (out.fmt.parsed.length) {
  const ok = out.fmt.parsed.every((r) => Math.abs(r.asSeconds - (r.actualCt || 0)) < 1.0);
  log('  ⇒ 读数按 HH:MM:SS 解析能对上 currentTime？', ok ? '✅' : '🔴');
  out.fmtRule = ok ? 'HH:MM:SS' : '未定';
}

writeFileSync(new URL('./_tmp-b104d.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
