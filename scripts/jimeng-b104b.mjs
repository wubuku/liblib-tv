// 批次 104 · b 轮：带媒体音频节点的播放行为。
//
// a 轮的结构读数已经把「未验证」那一条的一半答掉了：
//   · 内部 **17 个 testid**，其中波形是**分层 SVG**：
//     `audio-playback-waveform` → `-base` / `-progress` / `-playhead`（→ `-line` / `-cap`）
//   · `audio-simple-player`（aria `Play <名>`）、`audio-duration` / `audio-duration-accessible`
//   · **`media(audio|video) = []` ⇒ 节点里根本没有 `<audio>` 元素**（与批次 32 一致）
//   · `canvas` **0 个**（波形不是 canvas 画的）｜`svg` **4 个**
//   · 积分 **805 → 805**（音频上传也免费）
//
// 本轮四问：
//   ① 静止态有什么？点一下播放，`<audio>` 会不会才挂载？（视频侧就是这样的）
//   ② 播放/暂停：时间读数走不走？`aria` 翻不翻？**`audio-waveform-playhead` 动不动**？
//   ③ 进度条：波形能点着跳转吗？（aria `Seek <名>` 摆在那儿）
//   ④ 🔴 **有没有静音钮？** a 轮的 aria 清单里**只有 `Play` 和 `Seek`，没有任何 Mute**
//      ⇒ 视频节点有 `video-node-mute-toggle`，音频节点**似乎没有**
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), selfId: 'node_rezb9hd9kv' };
const SELF = out.selfId;

const scaleNow = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport');
  const m = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; });

// 读数：一次读全，aria 与 DOM 状态一起读
const probe = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { gone: true };
  const sc = (() => { const e = document.querySelector('.react-flow__viewport');
    const m = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; })();
  const nodeRect = n.getBoundingClientRect();
  const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
  const ox = t ? Number(t[1]) : 0, oy = t ? Number(t[2]) : 0;
  const cvOf = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
    return sc ? `${Math.round(r.width / sc * 100) / 100}×${Math.round(r.height / sc * 100) / 100}@${Math.round((r.x - nodeRect.x) / sc + ox)},${Math.round((r.y - nodeRect.y) / sc + oy)}` : null; };
  const g = (sel) => n.querySelector(sel);
  const a = g('[data-testid="audio-simple-player"]');
  const wf = g('[data-testid="audio-playback-waveform"]');
  const ph = g('[data-testid="audio-waveform-playhead"]');
  const phLine = g('[data-testid="audio-waveform-playhead-line"]');
  const phCap = g('[data-testid="audio-waveform-playhead-cap"]');
  const prog = g('[data-testid="audio-waveform-progress"]');
  const dur = g('[data-testid="audio-duration"]');
  const durA11y = g('[data-testid="audio-duration-accessible"]');
  const media = Array.from(n.querySelectorAll('audio,video')).map((e) => ({ tag: e.tagName, paused: e.paused,
    ct: e.currentTime, dur: e.duration, muted: e.muted, vol: e.volume, readyState: e.readyState, loop: e.loop }));
  const R = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
    return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
      cv: cvOf(e), style: (e.getAttribute('style') || '').slice(0, 80), opacity: getComputedStyle(e).opacity,
      visibility: getComputedStyle(e).visibility }; };
  return {
    testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
    arias: Array.from(new Set(Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')))),
    playAria: a ? a.getAttribute('aria-label') : null, playTag: a ? a.tagName : null, play: R(a),
    seekAria: wf ? wf.getAttribute('aria-label') : null, seekRole: wf ? wf.getAttribute('role') : null,
    waveform: R(wf), base: R(g('[data-testid="audio-waveform-base"]')), progress: R(prog),
    playhead: R(ph), playheadLine: R(phLine), playheadCap: R(phCap),
    durText: dur ? (dur.innerText || dur.textContent || '').replace(/\s+/g, ' ').trim() : null, dur: R(dur),
    durA11yText: durA11y ? (durA11y.textContent || '').replace(/\s+/g, ' ').trim() : null,
    media, innerText: n.innerText.replace(/\s+/g, ' ').trim(),
  };
}, SELF);

async function clickIn(sel, label, fx = 0.5, fy = 0.5) {
  const land = await p.evaluate(([i, s, ax, ay]) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const e = n.querySelector(s); if (!e) return { missing: true };
    const r = e.getBoundingClientRect();
    const x = Math.round(r.x + r.width * ax), y = Math.round(r.y + r.height * ay);
    const el = document.elementFromPoint(x, y);
    return { point: [x, y], rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
      hitTag: el ? el.tagName : null, hitAria: el ? el.getAttribute('aria-label') : null,
      insideSelf: !!(el && el.closest(`.react-flow__node[data-id="${i}"]`)),
      insideTarget: !!(el && (el === e || e.contains(el))) };
  }, [SELF, sel, fx, fy]);
  log(`  [${label}] 落点：`, JSON.stringify(land));
  if (land.missing || !land.insideSelf || !land.insideTarget) { log(`  🔴 ${label} 落点判失败 ⇒ 跳过`); return false; }
  await p.mouse.move(land.point[0], land.point[1]); await p.waitForTimeout(400);
  await p.mouse.click(land.point[0], land.point[1]); return true;
}

log('=== 静止基线 ===');
out.base = await probe();
log('playAria=', out.base.playAria, '| playTag=', out.base.playTag, '| play=', JSON.stringify(out.base.play));
log('waveform=', JSON.stringify(out.base.waveform));
log('durText=', JSON.stringify(out.base.durText), '｜durA11y=', JSON.stringify(out.base.durA11yText));
log('playhead=', JSON.stringify(out.base.playhead));
log('progress=', JSON.stringify(out.base.progress));
log('media=', JSON.stringify(out.base.media));
log('arias=', JSON.stringify(out.base.arias));
out.hasMute = out.base.arias.some((x) => /mute|静音/i.test(x || ''));
log('  ⇒ 静止态有没有静音相关 aria？', out.hasMute ? '✅ 有' : '❌ 没有');

// ================= ① 点播放 =================
log('\n=== ① 点播放 ===');
if (await clickIn('[data-testid="audio-simple-player"]', 'Play')) {
  await p.waitForTimeout(900);
  out.p1 = await probe();
  log('  播放中：playAria=', out.p1.playAria, '| media=', JSON.stringify(out.p1.media));
  log('    durText=', JSON.stringify(out.p1.durText), '｜durA11y=', JSON.stringify(out.p1.durA11yText));
  log('    playhead=', JSON.stringify(out.p1.playhead));
  log('    progress=', JSON.stringify(out.p1.progress));
  log('    arias=', JSON.stringify(out.p1.arias));
  out.mountedAudio = out.p1.media.length > 0;
  out.ariaFlips = out.p1.playAria !== out.base.playAria;
  log('  ⇒ 播放时挂载了 <audio>？', out.mountedAudio, '｜aria 翻转？', out.ariaFlips);
}

// ================= ② 时间与播放头是否真的在走 =================
log('\n=== ② 连采 6 次：时间 / 播放头位置 ===');
out.series = [];
for (let k = 0; k < 6; k++) {
  await p.waitForTimeout(500);
  const s = await probe();
  out.series.push({ t: (k + 1) * 500, durText: s.durText, a11y: s.durA11yText,
    media: s.media, phStyle: s.playhead && s.playhead.style, phX: s.playhead && s.playhead.x,
    progStyle: s.progress && s.progress.style, playAria: s.playAria });
  log(`  t=${(k + 1) * 500}  时长文本=${JSON.stringify(s.durText)}  a11y=${JSON.stringify(s.durA11yText)}  media=${JSON.stringify(s.media)}  播放头x=${s.playhead && s.playhead.x}  style=${JSON.stringify(s.playhead && s.playhead.style)}`);
}
const cts = out.series.map((r) => r.media[0] && r.media[0].ct).filter((x) => x !== null && x !== undefined);
out.ctMoved = cts.length >= 2 && Math.abs(cts[cts.length - 1] - cts[0]) > 0.3;
log('  ⇒ `currentTime` 在走？', out.ctMoved, '（' + JSON.stringify(cts) + '）');

// ================= ③ 暂停 =================
log('\n=== ③ 暂停 ===');
{
  const s = await probe();
  const tog = s.arias.includes('Pause jimeng-b104-test') ? '[aria-label^="Pause"]' : '[data-testid="audio-simple-player"]';
  if (await clickIn(tog, 'Pause', 0.5, 0.5)) {
    await p.waitForTimeout(700); out.q1 = await probe();
    await p.waitForTimeout(1100); out.q2 = await probe();
    log('  暂停后 t1：', JSON.stringify({ aria: out.q1.playAria, media: out.q1.media, durText: out.q1.durText }));
    log('  暂停后 t2：', JSON.stringify({ aria: out.q2.playAria, media: out.q2.media, durText: out.q2.durText }));
    const a = out.q1.media[0] && out.q1.media[0].ct, c = out.q2.media[0] && out.q2.media[0].ct;
    out.paused = out.q1.media[0] ? out.q1.media[0].paused : null;
    out.frozen = a !== null && c !== null && a !== undefined && c !== undefined && Math.abs(a - c) < 0.02;
    out.ariaBackToPlay = /^Play /.test(out.q2.playAria || '');
    log('  ⇒ 冻结？', out.frozen, '｜aria 翻回 Play？', out.ariaBackToPlay, '（读作', out.q2.playAria, '）');
  }
}

writeFileSync(new URL('./_tmp-b104b.json', import.meta.url), JSON.stringify(out, null, 1));
log('\nscale（记录用）：', await scaleNow());
await b.close();
