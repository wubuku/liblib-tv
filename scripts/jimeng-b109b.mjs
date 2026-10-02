// 批次 109 · b 轮：把「Upload complete」这条状态串的结构与生命周期读透（本轮仍只读，不建节点）。
//
// a 轮的三条硬读数：
//   ① 判据可用：全量取 `.sr-only,[role=status],[aria-live]` 的 textContent（**不按子元素过滤**）
//      能命中 `b22-upload.png: Upload complete` ✅（批次 102 的失败版正是多了一条「排掉有匹配子元素的」）
//   ② 同一句话在**文本节点层面出现 25 次**，承载者是 `SPAN`，盒 `256×23`，
//      x 依次 -1 / 255 / 510 / 766 / 1021 / 1277 … 6265 ⇒ **步长恒为 256**（= 自身宽度）
//      ⇒ 这是一条**横向无缝循环的跑马灯**，不是一条独立文案
//   ③ 它的父 `DIV role=status`（class `sr-only`）是 `1×1 @-1,-1`，
//      `kids=25` ⇒ 活区域本身不可见，可见性全靠那 25 个 SPAN
//
// 🔴 本轮要回答三个问题，全部只读：
//   Q1 那 25 个 SPAN 是不是**可见的**？跑马灯在不在屏上？（截图 + 逐个 SPAN 的可见性读数）
//   Q2 它在**动**吗？（连采两次 x，间隔 1.2s；批次 104 的老教训：状态要等落定、要连读）
//   Q3 为什么页面上只剩 png 这一条、批次 101 传过的 mp4 那条不见了？
//      两个候选解释：(a) 同一时刻只保留最新一条 (b) 状态串**随节点删除而消失**
//      —— 本轮只列证据，不下结论；b/c 轮用「传一个新媒体」来分辨
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b', readonly: true };
const save = () => writeFileSync(new URL('./_tmp-b109b.json', import.meta.url), JSON.stringify(out, null, 1));

const status = () => p.evaluate(() => {
  const t = document.body.innerText;
  return {
    nodes: (t.match(/(\d+) nodes?/) || [])[1],
    sel: (t.match(/(\d+) selected/) || [])[1],
    zoom: (document.querySelector('[data-testid="canvas-zoom-percent"]') || { getAttribute: () => null }).getAttribute('aria-label'),
    credits: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'),
  };
});

out.start = await status();
log('起点：', JSON.stringify(out.start));
save();

// ================= Q1：跑马灯可见吗 =================
out.q1 = await p.evaluate(() => {
  const live = Array.from(document.querySelectorAll('[role=status]'));
  const rows = live.map((e) => {
    const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    const kids = Array.from(e.children);
    return {
      text: (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 60),
      cls: (e.className || '').toString().slice(0, 40),
      box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
      kids: kids.length,
      clip: cs.clip, position: cs.position, overflow: cs.overflow, zIndex: cs.zIndex,
      kidBoxes: kids.slice(0, 4).map((k) => { const kr = k.getBoundingClientRect();
        const ks = getComputedStyle(k);
        return { box: `${Math.round(kr.x)},${Math.round(kr.y)} ${Math.round(kr.width)}×${Math.round(kr.height)}`,
          display: ks.display, visibility: ks.visibility, opacity: ks.opacity, position: ks.position, color: ks.color, bg: ks.backgroundColor }; }),
    };
  });
  return { n: live.length, rows };
});
log(`\n=== Q1 [role=status] 共 ${out.q1.n} 个 ===`);
out.q1.rows.forEach((r, i) => {
  log(`  [${i}] "${r.text}"`);
  log(`      cls=${r.cls} box=${r.box} kids=${r.kids} clip=${r.clip} pos=${r.position} overflow=${r.overflow} z=${r.zIndex}`);
  r.kidBoxes.forEach((k) => log(`      kid ${k.box} ${k.position} vis=${k.visibility} op=${k.opacity} color=${k.color} bg=${k.bg}`));
});
save();

// 截图：顶部 40px 的横条，看跑马灯到底在不在屏上
await p.screenshot({ path: '/tmp/b109-b-topleft.png', clip: { x: 0, y: 0, width: 1280, height: 40 } });
await p.screenshot({ path: '/tmp/b109-b-full.png' });
log('\n已截图 /tmp/b109-b-topleft.png（顶部 40px）与 /tmp/b109-b-full.png');
save();

// ================= Q2：它在动吗（连采两次） =================
const marquee = () => p.evaluate(() => {
  const sp = Array.from(document.querySelectorAll('[role=status] > span')).filter((s) => /Upload complete/i.test(s.textContent || ''));
  if (!sp.length) return { n: 0 };
  const boxes = sp.map((s) => { const r = s.getBoundingClientRect(); return { x: Math.round(r.x * 10) / 10, y: Math.round(r.y), w: Math.round(r.width) }; });
  const parent = sp[0].parentElement;
  const pr = parent.getBoundingClientRect();
  const pcs = getComputedStyle(parent);
  return { n: sp.length, first: boxes[0], last: boxes[boxes.length - 1],
    span: Math.round((boxes[1] ? boxes[1].x - boxes[0].x : 0) * 10) / 10,
    parentBox: `${Math.round(pr.x)},${Math.round(pr.y)} ${Math.round(pr.width)}×${Math.round(pr.height)}`,
    parentOverflow: pcs.overflow, parentTransform: pcs.transform, parentLeft: pcs.left, parentW: pcs.width,
    // 可见的那一段：x 落在视口内的
    onScreen: boxes.filter((b2) => b2.x + b2.w > 0 && b2.x < innerWidth).length,
  };
});
out.q2a = await marquee();
log('\n=== Q2 采样 A ===\n ', JSON.stringify(out.q2a));
save();
await p.waitForTimeout(1200);
out.q2b = await marquee();
log('=== Q2 采样 B（1.2s 后）\n ', JSON.stringify(out.q2b));
out.q2moved = JSON.stringify(out.q2a.first) !== JSON.stringify(out.q2b.first);
log('首帧 x 是否变化 =', out.q2moved, '｜', JSON.stringify(out.q2a.first), '→', JSON.stringify(out.q2b.first));
save();

// ================= Q3：活区域里都有谁 =================
out.q3 = await p.evaluate(() => {
  // 所有 role=status / aria-live 的完整清单（含空的），以及各自在 DOM 里的位置
  const live = Array.from(document.querySelectorAll('[role=status],[aria-live],[role=log]'));
  return live.map((e) => {
    const r = e.getBoundingClientRect();
    const path = [];
    let a = e;
    for (let d = 0; a && d < 4; d++, a = a.parentElement) path.push(a.tagName + (a.getAttribute('data-testid') ? '#' + a.getAttribute('data-testid') : ''));
    return { text: (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 70),
      role: e.getAttribute('role'), live: e.getAttribute('aria-live'), atomic: e.getAttribute('aria-atomic'),
      kids: e.children.length, box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
      path: path.join(' < ') };
  });
});
log(`\n=== Q3 活区域清单（${out.q3.length} 个） ===`);
out.q3.forEach((r, i) => log(`  [${i}] role=${r.role} live=${r.live} atomic=${r.atomic} kids=${r.kids} box=${r.box} "${r.text}"\n        ${r.path}`));
save();

out.end = await status();
log('\n终点：', JSON.stringify(out.end));
save();
log('\nDONE b');
process.exit(0);
