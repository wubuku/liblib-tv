// 批次 101 · c5 轮：三个**手册写了但从未在本节点上验过**的状态转换。
//
// c4 轮的收获与教训：
//   · **进度条点击跳转成立且很准**：点 25/50/80/5%，实测 ct = frac×6 + 0.65s（点击后还在播 650ms），
//     四次误差都 <0.03s。⚠️ 我第一版的判据 `|Δct|>0.4` **判错了**：
//     点 25% 是**往回跳**（2.44→1.5），650ms 后再前进到 2.13，净值只有 -0.31 ⇒ 被误判为「没落点」。
//     **判据必须把「采样间隔里它继续播了」算进去**，否则往回跳的点击会被误杀。
//     进度条真身：`slider-track`，屏上 `469,477 341×3`（**只有 3 px 高**，canvas 约 `568×5`）。
//   · **双击画面没有归零**：ct 4.19 → 5.81，一直在往前走 ⇒ 暂停态下会不会不同？本轮验。
//
// 本轮三问：
//   ① 手册第 37 行「**选中即播**：单击卡片选中，视频自动开始播放」—— 成立吗？
//   ② 双击重播：**暂停态**下双击会不会归零？
//   ③ 手册第 92 行「点击空白取消选中，播放停止」—— 成立吗？
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), selfId: 'node_fxhrsbbfrz' };
const SELF = out.selfId;

const probe = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { gone: true };
  const v = n.querySelector('video');
  const t = n.querySelector('[data-testid="video-node-player-clock"]');
  return {
    hasBar: !!n.querySelector('[data-testid="video-node-player-bar"]'),
    hasSimple: !!n.querySelector('[data-testid="video-simple-player"]'),
    ct: v ? v.currentTime : null, paused: v ? v.paused : null, ended: v ? v.ended : null,
    clock: t ? t.innerText.replace(/\s+/g, ' ').trim() : null,
    toggleAria: (n.querySelector('[data-testid="video-node-playback-toggle"]') || {}).getAttribute?.('aria-label') || null,
    sel: (document.body.innerText.match(/(\d+) selected/) || [])[1],
  };
}, SELF);

const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);

// ---- 找一个**真空白点**：不在任何 .react-flow__node 里、也不在左栏/顶栏/底栏里 ----
async function findBlank() {
  return p.evaluate(() => {
    const bad = (x, y) => {
      const el = document.elementFromPoint(x, y);
      if (!el) return true;
      if (el.closest('.react-flow__node')) return true;
      // 左栏 160 宽 / 顶栏 / 底栏 / 右侧 dock 都排除
      if (x < 190 || y < 60 || y > 640 || x > 1120) return true;
      if (el.closest('button,[role=button],input,a,[role=menu],nav,aside')) return true;
      return false;
    };
    for (let y = 300; y < 620; y += 24) for (let x = 260; x < 1100; x += 24) if (!bad(x, y)) return [x, y];
    return null;
  });
}

async function clickBlank(tag) {
  const pt = await findBlank();
  if (!pt) { log(`  [${tag}] 🔴 找不到空白点`); return false; }
  const land = await p.evaluate(([x, y]) => { const el = document.elementFromPoint(x, y);
    return { hitTag: el ? el.tagName : null, hitCls: (el && el.className || '').toString().slice(0, 60),
      inNode: !!(el && el.closest('.react-flow__node')) }; }, pt);
  log(`  [${tag}] 空白点 @${pt} →`, JSON.stringify(land));
  if (land.inNode) return false;
  await p.mouse.move(pt[0], pt[1]); await p.waitForTimeout(400); await p.mouse.click(pt[0], pt[1]);
  return true;
}

async function clickCard(tag) {
  const pt = await p.evaluate((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const v = n.querySelector('video,img'); const r = v.getBoundingClientRect();
    const x = Math.round(r.x + r.width * 0.5), y = Math.round(r.y + r.height * 0.25);
    const el = document.elementFromPoint(x, y);
    return { point: [x, y], insideSelf: !!(el && el.closest(`.react-flow__node[data-id="${i}"]`)), hitTag: el ? el.tagName : null };
  }, SELF);
  log(`  [${tag}] 卡片落点 @${pt.point} →`, JSON.stringify({ insideSelf: pt.insideSelf, hitTag: pt.hitTag }));
  if (!pt.insideSelf) return false;
  await p.mouse.move(pt.point[0], pt.point[1]); await p.waitForTimeout(400); await p.mouse.click(pt.point[0], pt.point[1]);
  return true;
}

// ================= ① 选中即播 =================
log('=== ① 选中即播 ===');
out.n0 = await nodeN();
// 先归位到一个确定状态：让它播完（现在应该在结尾附近）
await p.waitForTimeout(1500);
out.p0 = await probe();
log('  起点：', JSON.stringify(out.p0));
if (await clickBlank('取消选中')) {
  await p.waitForTimeout(900);
  out.p1 = await probe();
  log('  点空白后：', JSON.stringify({ sel: out.p1.sel, ct: out.p1.ct, paused: out.p1.paused, bar: out.p1.hasBar, simple: out.p1.hasSimple }));
  out.afterDeselect = { sel: out.p1.sel, ct: out.p1.ct, paused: out.p1.paused, bar: out.p1.hasBar, hasSimple: out.p1.hasSimple, hasVideo: out.p1.ct !== null };
  // 选回来
  if (await clickCard('重新选中')) {
    await p.waitForTimeout(1200);
    out.p2 = await probe();
    log('  再点卡片选中后：', JSON.stringify({ sel: out.p2.sel, ct: out.p2.ct, paused: out.p2.paused, clock: out.p2.clock, toggleAria: out.p2.toggleAria }));
    out.afterReselect = out.p2;
  }
}

// ================= ② 暂停态双击 =================
log('\n=== ② 暂停态双击 ===');
// 确认处于暂停
{
  const st = await probe();
  if (!st.paused) {
    const ok = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      const e = n.querySelector('[data-testid="video-node-playback-toggle"]'); if (!e) return null;
      const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, SELF);
    if (ok) { await p.mouse.move(ok[0], ok[1]); await p.waitForTimeout(300); await p.mouse.click(ok[0], ok[1]); await p.waitForTimeout(700); }
  }
  // 用进度条推到中段，确保「归零」有可观测差异
  const tr = await p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="slider-track"]`);
    if (!t) return null; const r = t.getBoundingClientRect();
    return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; }, SELF);
  if (tr) { const x = Math.round(tr.x + tr.w * 0.6), y = Math.round(tr.y + tr.h / 2);
    await p.mouse.move(x, y); await p.waitForTimeout(300); await p.mouse.click(x, y); await p.waitForTimeout(600); }
  out.d0 = await probe();
  log('  双击前：', JSON.stringify({ ct: out.d0.ct, paused: out.d0.paused, clock: out.d0.clock }));
  const d = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const v = n.querySelector('video'); const r = v.getBoundingClientRect();
    const x = Math.round(r.x + r.width * 0.35), y = Math.round(r.y + r.height * 0.3);
    const el = document.elementFromPoint(x, y);
    return { point: [x, y], insideSelf: !!(el && el.closest(`.react-flow__node[data-id="${i}"]`)) }; }, SELF);
  log('  双击落点：', JSON.stringify(d));
  if (d.insideSelf) {
    await p.mouse.move(d.point[0], d.point[1]); await p.waitForTimeout(350);
    await p.mouse.click(d.point[0], d.point[1], { clickCount: 2, delay: 80 });
    await p.waitForTimeout(800);
    out.d1 = await probe();
    log('  双击后：', JSON.stringify({ ct: out.d1.ct, paused: out.d1.paused, clock: out.d1.clock }));
    out.doubleClickWhilePaused = { before: out.d0.ct, after: out.d1.ct, pausedAfter: out.d1.paused,
      reset: out.d1.ct !== null && out.d0.ct !== null && out.d1.ct < out.d0.ct - 0.3 };
    log('  ⇒ 暂停态双击是否归零？', out.doubleClickWhilePaused.reset);
  }
}

out.end = { ...(await probe()), nodes: await nodeN() };
log('\n终态：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b101c5.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
