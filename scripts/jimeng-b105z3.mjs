// 批次 105 · z3 轮：把画布缩到 40% 让节点散开，再找落点删掉最后一个自建节点。
//
// z2 轮诊断结果：**可用落点 0 个**，而画布上已有 **66 个他人节点**。
// 逐点拆开看两道关卡各挡掉多少，再决定怎么退让 —— 不要盲改判据。
// 手法沿用批次 101/104 的老办法：**逐级缩小画布（节点会散开）→ 每档重扫落点**，
// 删完再把缩放**回读验证**归位到 60%。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), selfId: 'node_p0brqdj8z0' };
const SELF = out.selfId;
const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const scale = () => p.evaluate(() => (document.body.innerText.match(/(\d+)%/) || [])[1]);

// ---- 诊断：两道关卡分别挡掉多少 ----
const diagnose = () => p.evaluate((i) => {
  const t = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!t) return { __err: 'gone' };
  const r = t.getBoundingClientRect();
  const others = Array.from(document.querySelectorAll('.react-flow__node'))
    .filter((e) => e.getAttribute('data-id') !== i)
    .map((e) => { const q = e.getBoundingClientRect(); return { x: q.x, y: q.y, w: q.width, h: q.height }; })
    .filter((o) => o.w > 0 && o.h > 0);
  let total = 0, passHit = 0, passBoth = 0;
  const hits = [];
  for (let fy = 0.1; fy <= 0.9; fy += 0.05) {
    for (let fx = 0.08; fx <= 0.92; fx += 0.04) {
      const x = r.x + r.width * fx, y = r.y + r.height * fy;
      if (x < 2 || y < 2 || x > window.innerWidth - 2 || y > window.innerHeight - 2) continue;
      total++;
      const el = document.elementFromPoint(x, y);
      if (!el || !(el === t || t.contains(el))) continue;
      passHit++;
      const inOther = others.some((o) => x >= o.x && x <= o.x + o.w && y >= o.y && y <= o.y + o.h);
      if (inOther) { hits.push({ x: Math.round(x), y: Math.round(y), inOther: true }); continue; }
      passBoth++;
      hits.push({ x: Math.round(x), y: Math.round(y), inOther: false });
    }
  }
  return { rect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
    others: others.length, total, passHit, passBoth, clean: hits.filter((h) => !h.inOther).slice(0, 10) };
}, SELF);

out.idsBefore = (await allIds()).length;
out.diag60 = await diagnose();
log('60% 诊断：', JSON.stringify(out.diag60, null, 1));

// ---- 缩到 40% ----
async function setScale(target) {
  for (let k = 0; k < 4; k++) {
    const cur = await scale();
    if (cur === String(target)) return cur;
    const btn = await p.evaluate(() => {
      const b = Array.from(document.querySelectorAll('button,[role=button]')).find((e) => /^\d+%$/.test((e.innerText || '').trim()) && e.getBoundingClientRect().width < 90);
      if (!b) return null; const r = b.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2, t: b.innerText.trim() };
    });
    if (!btn) return null;
    await p.mouse.click(btn.x, btn.y); await p.waitForTimeout(700);
    const opt = await p.evaluate((tg) => {
      const o = Array.from(document.querySelectorAll('button,[role=menuitem],[role=option]')).find((e) => (e.innerText || '').trim() === tg + '%');
      if (!o) return null; const r = o.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
    }, target);
    if (!opt) { log('  找不到 ' + target + '% 选项'); return null; }
    await p.mouse.move(opt.x, opt.y); await p.waitForTimeout(300); await p.mouse.click(opt.x, opt.y);
    await p.waitForTimeout(1400);
  }
  return await scale();
}
out.to40 = await setScale(40);
log('\n缩放后读数：', out.to40, '（连读两次相同才算静止）', await scale());
out.diag40 = await diagnose();
log('\n40% 诊断：', JSON.stringify(out.diag40, null, 1));

if (out.diag40.clean && out.diag40.clean.length) {
  const P = out.diag40.clean[0];
  log('\n用落点：', JSON.stringify(P));
  await p.mouse.move(P.x, P.y); await p.waitForTimeout(450);
  await p.mouse.click(P.x, P.y); await p.waitForTimeout(1100);
  const sel = await p.evaluate((i) => { const e = document.querySelector(`.react-flow__node[data-id="${i}"]`); return e ? e.classList.contains('selected') : null; }, SELF);
  log('点击后 selected =', sel);
  out.selected = sel;
  if (sel === true) {
    await p.mouse.move(P.x, P.y); await p.waitForTimeout(450);
    await p.mouse.down({ button: 'right' }); await p.waitForTimeout(260); await p.mouse.up({ button: 'right' });
    await p.waitForTimeout(1100);
    const del = await p.evaluate(() => {
      const b = Array.from(document.querySelectorAll('button,[role=menuitem]')).find((e) => /^删除/.test(e.innerText.trim()));
      if (!b) return null; const r = b.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
    });
    log('删除项：', JSON.stringify(del));
    if (del) { await p.mouse.move(del.x, del.y); await p.waitForTimeout(350); await p.mouse.click(del.x, del.y); }
    await p.waitForTimeout(1800);
    out.gone = !(await allIds()).includes(SELF);
    log('目标已消失 =', out.gone);
  }
}

// ---- 归位 60% ----
out.back60 = await setScale(60);
out.back60b = await scale();
log('\n归位读数：', out.back60, '/', out.back60b, out.back60 === out.back60b && out.back60 === '60' ? '✅' : '🔴 需重试');
out.idsAfter = (await allIds()).length;
out.sel = await p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
log('节点数：', out.idsBefore ?? '?', '→', out.idsAfter, '｜sel =', out.sel);
writeFileSync(new URL('./_tmp-b105z3.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
