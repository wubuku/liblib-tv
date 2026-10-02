// 批次 104 · e 轮：把 d 轮的三处判据/顺序错误修掉，补完暂停与波形跳转。
//
// d 轮已确认的（不重测）：
//   ✅ 真能播：`paused:false`、`ct` 2.89→3.40→3.90→4、`readyState:4`、`dur:4`
//   ✅ aria 翻转：`Play <名>` ⇄ `Pause <名>`
//   ✅ 播放头 `left` 跟着走：72.2% → 84.7% → 97.1% → 100%
//   ✅ 播完**自动停**在 `ct=4`、`paused:true`、aria 回到 `Play`
//   ✅ 时间读数是 **`HH:MM:SS` 且向下取整**：`ct 2.89→00:00:02`、`3.40→00:00:03`、`4→00:00:04`
//      （可见读数由三个 SPAN 拼成 `00` + `:00` + `:03`，另有一份 `sr-only` 同值；
//        可见读数与可访问读数**逐字相同**，但可见那三个 SPAN 都在卡片内、`sr-only` 是 `1×1`）
//   ✅ **没有静音控件**：整个节点带 aria 的元素只有 7 个，**没有任何 Mute/静音**
//
// d 轮三处翻车（**全是我的判据/顺序问题，不是页面问题**）：
//   ① ③ 暂停时音频**已经播完自动停了**，aria 早就是 `Play` ⇒ 按 `Pause` 找落点自然找不到。
//      ⇒ **顺序错了**：要测暂停就得在**播放途中**点，不是等到播完再点。
//      （与批次 101 的 c13「选中即播已经发生了，不该再点一次」同族。）
//   ② ④ 波形落点判据要求 `elementFromPoint` 的 testid **就是** `audio-playback-waveform`，
//      实际命中的是它的**子元素** `SPAN#audio-waveform-progress`。
//      ⇒ **这已经是「落点判据」这类错误的第三次**（前两次：按钮内的 `<path>`、菜单项内的 `<span>`）。
//   ⑤ `fmt.parsed` 因为 ④ 全被跳过而从未创建 ⇒ 读 `.length` 抛异常。**空数组要显式初始化。**
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
  const a11y = n.querySelector('[data-testid="audio-duration-accessible"]');
  const btn = Array.from(n.querySelectorAll('button')).find((e) => /^Play |^Pause /.test(e.getAttribute('aria-label') || ''));
  const R = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
    return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; };
  return { btnAria: btn ? btn.getAttribute('aria-label') : null, btn: R(btn),
    durA11y: a11y ? (a11y.textContent || '').trim() : null,
    phPct: ph ? (/left:\s*([\d.]+)%/.exec(ph.getAttribute('style') || '') || [])[1] : null,
    wf: R(wf),
    media: v ? { paused: v.paused, ct: v.currentTime, dur: v.duration, muted: v.muted, vol: v.volume } : null };
}, SELF);

/** ✅ 修正后的落点判据：命中元素落在目标**内部**即可（不再要求「就是」目标） */
async function clickPlayPause(want) {
  const land = await p.evaluate(([i, w]) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const btns = Array.from(n.querySelectorAll('button')).filter((e) => /^Play |^Pause /.test(e.getAttribute('aria-label') || ''));
    const e = btns.find((x) => x.getAttribute('aria-label') === w);
    if (!e) return { missing: true, seen: btns.map((x) => x.getAttribute('aria-label')) };
    const r = e.getBoundingClientRect();
    const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2);
    const el = document.elementFromPoint(x, y);
    return { point: [x, y], hitTag: el ? el.tagName : null, hitAria: el ? el.getAttribute('aria-label') : null,
      insideSelf: !!(el && el.closest(`.react-flow__node[data-id="${i}"]`)),
      insideTarget: !!(el && (el === e || e.contains(el))) };
  }, [SELF, want]);
  log(`  [点 ${want}] 落点：`, JSON.stringify(land));
  if (land.missing || !land.insideSelf || !land.insideTarget) { log('  🔴 落点判失败'); return false; }
  await p.mouse.move(land.point[0], land.point[1]); await p.waitForTimeout(380);
  await p.mouse.click(land.point[0], land.point[1]); return true;
}

async function clickWaveform(frac) {
  const land = await p.evaluate(([i, f]) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const wf = n.querySelector('[data-testid="audio-playback-waveform"]'); if (!wf) return { missing: true };
    const r = wf.getBoundingClientRect();
    const x = Math.round(r.x + r.width * f), y = Math.round(r.y + r.height / 2);
    const el = document.elementFromPoint(x, y);
    return { point: [x, y], hitTag: el ? el.tagName : null, hitTid: el ? el.getAttribute('data-testid') : null,
      hitRole: el ? el.getAttribute('role') : null,
      insideSelf: !!(el && el.closest(`.react-flow__node[data-id="${i}"]`)),
      // ✅ 正路：命中元素在波形**内部**（波形本体或其任何后代）
      insideTarget: !!(el && (el === wf || wf.contains(el))) };
  }, [SELF, frac]);
  log(`  [波形 ${Math.round(frac * 100)}%] 落点：`, JSON.stringify(land));
  if (land.missing || !land.insideSelf || !land.insideTarget) { log('  🔴 落点判失败 ⇒ 跳过'); return false; }
  const before = await probe();
  await p.mouse.move(land.point[0], land.point[1]); await p.waitForTimeout(350);
  await p.mouse.click(land.point[0], land.point[1]); await p.waitForTimeout(700);
  const after = await probe();
  const row = { frac, beforeCt: before.media && before.media.ct, afterCt: after.media && after.media.ct,
    beforeA11y: before.durA11y, afterA11y: after.durA11y, beforePh: before.phPct, afterPh: after.phPct };
  row.landed = typeof row.afterCt === 'number' && typeof row.beforeCt === 'number' && Math.abs(row.afterCt - row.beforeCt) > 0.25;
  row.expect = 4 * frac;
  row.accurate = row.landed && Math.abs(row.afterCt - row.expect) < 0.5;
  log(`  ⇒ ct ${row.beforeCt} → ${row.afterCt}（期望≈${row.expect}）｜读数 ${row.beforeA11y} → ${row.afterA11y}｜播放头 ${row.beforePh}% → ${row.afterPh}%｜落点=${row.landed} 准=${row.accurate}`);
  return row;
}

// ================= ① 播放途中暂停 =================
log('=== ① 播放途中暂停 ===');
out.fmt = { samples: [] };
{
  // 先确保在末尾，Seek 到 0 开始播
  if (await clickWaveform(0.05)) { /* ok */ }
  await p.waitForTimeout(400);
  let s = await probe();
  if (s.media && s.media.paused) {
    if (!/^Play /.test(s.btnAria || '')) { log('  状态异常，aria=', s.btnAria); }
    await clickPlayPause('Play jimeng-b104-test');
    await p.waitForTimeout(1100);          // 播 1.1 秒，**在途中**
    s = await probe();
    log('  播了 1.1s 后：', JSON.stringify({ aria: s.btnAria, ct: s.media && s.media.ct, paused: s.media && s.media.paused }));
    if (/^Pause /.test(s.btnAria || '')) {
      if (await clickPlayPause('Pause jimeng-b104-test')) {
        await p.waitForTimeout(600); out.q1 = await probe();
        await p.waitForTimeout(1100); out.q2 = await probe();
        log('  暂停后 t1：', JSON.stringify({ aria: out.q1.btnAria, ct: out.q1.media && out.q1.media.ct, paused: out.q1.media && out.q1.media.paused }));
        log('  暂停后 t2：', JSON.stringify({ aria: out.q2.btnAria, ct: out.q2.media && out.q2.media.ct, paused: out.q2.media && out.q2.media.paused }));
        out.pausedFlag = out.q1.media && out.q1.media.paused;
        out.frozen = out.q1.media && out.q2.media && typeof out.q1.media.ct === 'number' && typeof out.q2.media.ct === 'number'
          && Math.abs(out.q1.media.ct - out.q2.media.ct) < 0.02;
        out.ariaBackToPlay = /^Play /.test(out.q2.btnAria || '');
        out.fmt.samples.push({ label: '暂停时', ct: out.q2.media && out.q2.media.ct, a11y: out.q2.durA11y });
        log('  ⇒ paused？', out.pausedFlag, '｜时间冻结？', out.frozen, '｜aria 翻回 Play？', out.ariaBackToPlay);
      }
    } else log('  🔴 1.1 秒后 aria 已是', s.btnAria, '（播得太快，素材只有 4 秒）');
  } else log('  🔴 没在暂停态，media=', JSON.stringify(s.media));
}

// ================= ② 波形跳转 =================
log('\n=== ② 波形跳转 ===');
out.seeks = [];
for (const frac of [0.25, 0.75, 0.5]) {
  const row = await clickWaveform(frac);
  if (row) { out.seeks.push(row); out.fmt.samples.push({ label: `seek ${frac}`, ct: row.afterCt, a11y: row.afterA11y }); }
}

// ================= ③ 时间格式交叉验证 =================
log('\n=== ③ 时间格式交叉验证（读数 vs currentTime）===');
out.fmt.parsed = [];
for (const s of out.fmt.samples) {
  const a = s.a11y || ''; const m = /^(\d+):(\d+):(\d+)$/.exec(a);
  if (!m) { out.fmt.parsed.push({ raw: a, ct: s.ct, parsed: null }); continue; }
  const asSeconds = Number(m[1]) * 3600 + Number(m[2]) * 60 + Number(m[3]);
  out.fmt.parsed.push({ raw: a, ct: s.ct, asSeconds, floor: Math.floor(s.ct), diff: Number((asSeconds - Math.floor(s.ct)).toFixed(3)) });
}
log('  ', JSON.stringify(out.fmt.parsed, null, 1));
out.fmt.matchesFloor = out.fmt.parsed.length > 0 && out.fmt.parsed.every((r) => r.parsed === null || Math.abs(r.diff) < 0.001);
log('  ⇒ 读数 == floor(currentTime)？', out.fmt.matchesFloor ? '✅' : '🔴/样本不足');
out.fmt.rule = out.fmt.matchesFloor ? 'HH:MM:SS，按秒向下取整' : '未定';

// ================= ④ 静音复检 =================
log('\n=== ④ 静音复检 ===');
out.mute = await safeEval((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const all = Array.from(n.querySelectorAll('button,[role=button],[aria-label],[role=slider]'))
    .map((e) => ({ tag: e.tagName, role: e.getAttribute('role'), aria: e.getAttribute('aria-label') }));
  return { total: all.length, items: all,
    muteish: all.filter((x) => /mute|静音|音量|volume/i.test((x.aria || '') + ' ' + (x.role || ''))).length,
    ranges: n.querySelectorAll('input[type=range]').length,
    sliders: n.querySelectorAll('[role=slider]').length }; }, SELF);
log('  带语义元素共', out.mute.total, '｜与静音/音量相关的：', out.mute.muteish, '｜`input[type=range]`：', out.mute.ranges, '｜`role=slider`：', out.mute.sliders);
log('  全部：', JSON.stringify(out.mute.items));

writeFileSync(new URL('./_tmp-b104e.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
