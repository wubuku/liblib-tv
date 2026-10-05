// 批次 195 f 轮：Q1 的**有效臂** —— 「取消选中」到底停不停播？
//
// e 轮的教训（立规 65 的正向用法）：Q1 进臂前视频**已经播完**（t 恒 6、paused true），
//   「点播放钮想让它再动」这个动作**没生效**（16×16 canvas 的钮在 100% 档屏上只有约 10px，
//   手册自己就警告过「这是这一排里最难点的」）⇒ 整条 Q1 臂是**无效臂**，不能读成任何结论。
// 本轮：① 用**点正文起播**代替点播放钮（e 轮 Q2 第一次已证它 100% 有效）；
//   ② 起播后先采 4 帧做**阳性守卫**（必须看到 currentTime 在动），守卫不过就不往下走；
//   ③ 顺带验「播完后再点**控件行**的播放钮能不能重播」——点击前先读 elementFromPoint。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';

const SELF = 'node_anew4vmz06';
const { b, p } = await openCanvas();
const R = readers(p);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
await settle(p, R);
const log = (...a) => console.log(a.join(' '));
await setZoom(p, 100);

const 采 = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { 消失: true };
  const v = n.querySelector('video');
  return {
    选中: n.classList.contains('selected'),
    有video: !!v, paused: v ? v.paused : null,
    currentTime: v ? Math.round(v.currentTime * 1000) / 1000 : null,
    控件行: !!n.querySelector('[data-testid="video-node-player-bar"]'),
    播放钮aria: (n.querySelector('[data-testid="video-node-playback-toggle"]') || { getAttribute: () => null }).getAttribute('aria-label'),
    时钟: (n.querySelector('[data-testid="video-node-player-clock"]') || { innerText: '' }).innerText.trim(),
  };
}, SELF);
const 序列 = async (n, 间隔 = 350) => { const s = []; for (let k = 0; k < n; k++) { s.push(await 采()); await p.waitForTimeout(间隔); } return s; };
const 摘要 = (s) => `t: ${s[0].currentTime}→${s[s.length - 1].currentTime} | paused ${JSON.stringify([...new Set(s.map((x) => x.paused))])} | 选中 ${JSON.stringify([...new Set(s.map((x) => x.选中))])} | 控件行 ${JSON.stringify([...new Set(s.map((x) => x.控件行))])}`;

const 点空白 = async () => { const s = await p.evaluate(() => { const ns = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
  for (let x = 60; x < innerWidth - 340; x += 40) for (let y = 120; y < innerHeight - 140; y += 40) { const h = document.elementFromPoint(x, y);
    if (h && h.classList && h.classList.contains('react-flow__pane') && !ns.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return [x, y]; } return null; });
  if (s) { await p.mouse.click(s[0], s[1]); await p.waitForTimeout(250); } return s; };
const 点正文 = async () => { const s = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height * 0.55)]; }, SELF);
  if (s) { await p.mouse.click(s[0], s[1]); await p.waitForTimeout(250); } return s; };

const out = { 轮次: 'b195f', SELF, 假设: 'Q1 取消选中会停播（手册 138 行）；以及「播完点控件行播放钮能否重播」' };

// —— 起播：点空白取消 → 点正文起播 ——
await 点空白(); await p.waitForTimeout(700);
out.起点 = await 采();
out.点正文 = await 点正文();
await p.waitForTimeout(500);
const 守卫序列 = await 序列(4, 300);
out.阳性守卫 = { 序列: 守卫序列, 通过: 守卫序列.some((x) => x.currentTime > 0 && x.paused === false), 判据: '存在 currentTime>0 且 paused=false 的帧' };
log('阳性守卫：', JSON.stringify(out.阳性守卫.判据), '→', out.阳性守卫.通过 ? '✅ 通过' : '🔴 未过 ⇒ 下面不作结论');

if (out.阳性守卫.通过) {
  // —— Q1：点空白取消选中，立刻连采 ——
  out.Q1_点空白前 = await 采();
  out.Q1_点空白 = await 点空白();
  out.Q1_点空白后序列 = await 序列(12, 350);
  out.Q1_结论_还在动吗 = out.Q1_点空白后序列[out.Q1_点空白后序列.length - 1].currentTime !== out.Q1_点空白后序列[0].currentTime;
  log('Q1 点空白后：', 摘要(out.Q1_点空白后序列), '| 还在动吗 =', out.Q1_结论_还在动吗);
}

// —— 播完后点控件行的播放钮：先读 elementFromPoint 再点（立规 67/56）——
await 点空白(); await p.waitForTimeout(600);
out.复位后 = await 采();
const 播完条件 = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); const v = n.querySelector('video'); return v && v.duration && v.currentTime >= v.duration - 0.05; }, SELF);
out.已播完 = !!播完条件;
if (out.已播完) {
  const hit = await p.evaluate((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const e = n.querySelector('[data-testid="video-node-playback-toggle"]'); if (!e) return { 找到: false };
    const r = e.getBoundingClientRect(); const x = r.x + r.width / 2, y = r.y + r.height / 2;
    const h = document.elementFromPoint(x, y);
    return { 找到: true, 屏上: [x, y, r.width, r.height].map((z) => Math.round(z * 100) / 100),
             中心落点: h ? (h.tagName + '[' + (h.getAttribute('data-testid') || h.getAttribute('aria-label') || h.className.toString().slice(0, 30)) + ']') : null,
             中心落点是不是它: !!(h && (h === e || e.contains(h))) };
  }, SELF);
  out.播完后_点前命中读数 = hit;
  log('播完后 播放钮命中读数：', JSON.stringify(hit));
  if (hit.找到 && hit.中心落点是不是它) {
    await p.mouse.click(hit.屏上[0], hit.屏上[1]); await p.waitForTimeout(400);
    out.播完后_点播放钮后序列 = await 序列(8, 350);
    log('播完后点播放钮：', 摘要(out.播完后_点播放钮后序列));
  } else {
    out.播完后_跳过 = '点击未命中 ⇒ 标为无效臂，不下结论';
    log('🔴 点击未命中 ⇒ 无效臂');
  }
}

fs.writeFileSync('/tmp/b195f.json', JSON.stringify(out, null, 1));
out.收尾 = await endState(p, R, 基线);
log('收尾：', JSON.stringify(out.收尾));
await b.close();
