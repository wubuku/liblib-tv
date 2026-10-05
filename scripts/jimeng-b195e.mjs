// 批次 195 e 轮：受控臂，分开「点正文」与「取消选中」两个变量
//
// d 轮读数留下的三个待答问题：
//   Q1 「取消选中」到底停不停播？手册 138 行逐字写「点击空白取消选中，**播放停止**…
//      `currentTime` 冻住」，而臂 3 的 currentTime 从 5.386 继续走到 6。
//   Q2 「已选中状态下点卡片正文」会不会重播？（c 轮档 C 读到 paused=true / currentTime=0）
//   Q3 取消选中后控件行在不在？（手册说「整条控件行消失」）
//
// 每条都配**阳性守卫**：先证明「视频确实在动」，再读那一拍。
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
    大播放键: !!n.querySelector('[data-testid="video-simple-player"]'),
    播放钮aria: (n.querySelector('[data-testid="video-node-playback-toggle"]') || { getAttribute: () => null }).getAttribute('aria-label'),
    状态行selected: (document.body.innerText.match(/(\d+) selected/) || [])[1],
  };
}, SELF);

const 序列 = async (n = 10, 间隔 = 350) => {
  const 序 = [];
  for (let k = 0; k < n; k++) { 序.push(await 采()); await p.waitForTimeout(间隔); }
  return 序;
};
const 动了吗 = (序) => 序[序.length - 1].currentTime !== 序[0].currentTime;
const 摘要 = (序) => `t: ${序[0].currentTime}→${序[序.length - 1].currentTime} | paused集合 ${JSON.stringify([...new Set(序.map((x) => x.paused))])} | 选中集合 ${JSON.stringify([...new Set(序.map((x) => x.选中))])} | 控件行集合 ${JSON.stringify([...new Set(序.map((x) => x.控件行))])}`;

const 点空白 = async () => {
  const s = await p.evaluate(() => {
    const ns = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
    for (let x = 60; x < innerWidth - 340; x += 40) for (let y = 120; y < innerHeight - 140; y += 40) {
      const h = document.elementFromPoint(x, y);
      if (h && h.classList && h.classList.contains('react-flow__pane') && !ns.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return [x, y];
    }
    return null; });
  if (s) { await p.mouse.click(s[0], s[1]); await p.waitForTimeout(250); }
  return s;
};
const 点正文 = async () => { const s = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height * 0.55)]; }, SELF);
  if (s) { await p.mouse.click(s[0], s[1]); await p.waitForTimeout(250); } return s; };
const 点播放钮 = async () => { const s = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); const e = n.querySelector('[data-testid="video-node-playback-toggle"]'); if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, SELF);
  if (s) { await p.mouse.click(s[0], s[1]); await p.waitForTimeout(250); } return s; };

const out = { 轮次: 'b195e', SELF, 假设: 'Q1 取消选中会停播 / Q2 已选中点正文会重播 / Q3 取消选中后控件行消失' };

// ===== Q2 受控：未选中点正文起播（阳性对照，必须动）→ 再点正文（已选中）=====
await 点空白(); await p.waitForTimeout(600);
out.Q2_未选中点正文 = await 点正文();
await p.waitForTimeout(700);
out.Q2_第一次_起播对照 = await 序列(8);
log('Q2 第一次（未选中点正文，应动）:', 摘要(out.Q2_第一次_起播对照), '| 动了吗 =', 动了吗(out.Q2_第一次_起播对照));
out.Q2_第二次_已选中点正文 = await 点正文();
out.Q2_第二次序列 = await 序列(8);
log('Q2 第二次（已选中再点正文）:', 摘要(out.Q2_第二次序列), '| 动了吗 =', 动了吗(out.Q2_第二次序列));
out.Q2_第二次是否从0重播 = out.Q2_第二次序列[0].currentTime < out.Q2_第一次_起播对照[out.Q2_第一次_起播对照.length - 1].currentTime;

// ===== Q1 受控：确保在播 → 点空白 → 立刻连采 =====
if (!动了吗(out.Q2_第二次序列)) { await 点播放钮(); await p.waitForTimeout(600); }
out.Q1_点空白前 = await 采();
const 动1 = await 序列(5, 300);
out.Q1_点空白前序列 = 动1;
log('Q1 点空白前（应动）:', 摘要(动1), '| 动了吗 =', 动了吗(动1));
out.Q1_点空白 = await 点空白();
out.Q1_点空白后序列 = await 序列(10, 350);
log('Q1 点空白后:', 摘要(out.Q1_点空白后序列), '| 动了吗 =', 动了吗(out.Q1_点空白后序列));

// ===== Q3：取消选中后控件行在不在（并让 video 再起来一次以确保非播完静止态）=====
await 点正文(); await p.waitForTimeout(700);
out.Q3_点空白前 = await 采();
out.Q3_点空白 = await 点空白();
out.Q3_点空白后 = await 采();
log('Q3 点空白后 控件行=', out.Q3_点空白后.控件行, '| 有video=', out.Q3_点空白后.有video, '| 大播放键=', out.Q3_点空白后.大播放键, '| 选中=', out.Q3_点空白后.选中);

fs.writeFileSync('/tmp/b195e.json', JSON.stringify(out, null, 1));
out.收尾 = await endState(p, R, 基线);
log('收尾：', JSON.stringify(out.收尾));
await b.close();
