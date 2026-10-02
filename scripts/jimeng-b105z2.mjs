// 批次 105 · z2 轮：把最后一个自建节点删干净。
//
// z 轮翻车复盘（值得单独立一条，因为差点伤到别人的节点）：
//   两个自建节点**部分重叠**（垃圾节点 `469,288 341×192`，视频靶子 `736,360 341×192`，
//   重叠区 x 736–810 / y 360–480）。z 轮的去程是
//   「点节点中心 → 右键 → 点菜单里的『删除』」，
//   其中**第一步的点击落点没有校验过命中的是谁**，结果
//   `node_p0brqdj8z0 删前 selected = false`，脚本仍继续走，
//   最后删掉的是 **`node_kk93zz7qzx`**（我自己的另一个），而垃圾节点纹丝不动。
//   ⇒ 幸好两个都是自己的，**否则这轮就是在删别人的节点**。
//
// 本轮加三道：
//   ① 落点必须先用 `elementFromPoint` 证明**最上层元素确实在目标节点内部**
//      （`el === t || t.contains(el)`），且落点**不在任何他人节点矩形内**；
//   ② 点击后**必须**读到 `selected` 才继续，读不到就中止；
//   ③ 删除后立刻核对该 id 是否真的消失。
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

out.idsBefore = (await allIds()).length;
log('起点节点数：', out.idsBefore, '｜目标仍在：', (await allIds()).includes(SELF));

// ---- ① 找一个「最上层就是目标节点、且不在任何他人节点矩形内」的落点 ----
const spot = await p.evaluate((i) => {
  const t = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!t) return { __err: 'gone' };
  const r = t.getBoundingClientRect();
  const others = Array.from(document.querySelectorAll('.react-flow__node'))
    .filter((e) => e.getAttribute('data-id') !== i)
    .map((e) => { const q = e.getBoundingClientRect();
      return { id: e.getAttribute('data-id'), x: q.x, y: q.y, w: q.width, h: q.height }; })
    .filter((o) => o.w > 0 && o.h > 0);
  const cands = [];
  for (let fy = 0.12; fy <= 0.5; fy += 0.06) {
    for (let fx = 0.12; fx <= 0.9; fx += 0.06) {
      const x = r.x + r.width * fx, y = r.y + r.height * fy;
      if (x < 2 || y < 2 || x > window.innerWidth - 2 || y > window.innerHeight - 2) continue;
      const el = document.elementFromPoint(x, y);
      if (!el || !(el === t || t.contains(el))) continue;
      const inOther = others.some((o) => x >= o.x && x <= o.x + o.w && y >= o.y && y <= o.y + o.h);
      if (inOther) continue;
      cands.push({ x: Math.round(x), y: Math.round(y), fx: +fx.toFixed(2), fy: +fy.toFixed(2),
        top: el.tagName + '.' + String(el.className || '').split(' ').slice(0, 2).join('.') });
    }
  }
  return { rect: { x: r.x, y: r.y, w: r.width, h: r.height }, others: others.length, cands: cands.slice(0, 12), total: cands.length };
}, SELF);
log('目标矩形：', JSON.stringify(spot.rect), '｜画布上他人节点：', spot.others, '｜可用落点：', spot.total);
log('落点候选：', JSON.stringify(spot.cands, null, 1));
out.spot = spot;
if (!spot.cands || !spot.cands.length) { log('🔴 找不到安全落点，中止'); writeFileSync(new URL('./_tmp-b105z2.json', import.meta.url), JSON.stringify(out, null, 1)); await b.close(); process.exit(1); }
const P = spot.cands[Math.floor(spot.cands.length / 2)];

// ---- ② 点击 → 必须读到 selected ----
await p.mouse.move(P.x, P.y); await p.waitForTimeout(450);
await p.mouse.click(P.x, P.y); await p.waitForTimeout(1100);
const sel = await p.evaluate((i) => { const e = document.querySelector(`.react-flow__node[data-id="${i}"]`); return e ? e.classList.contains('selected') : null; }, SELF);
log('\n点击后 selected =', sel);
out.selected = sel;
if (sel !== true) { log('🔴 没选中，中止（不猜、不硬删）'); writeFileSync(new URL('./_tmp-b105z2.json', import.meta.url), JSON.stringify(out, null, 1)); await b.close(); process.exit(1); }

// ---- ③ 右键同一个落点 → 删 ----
await p.mouse.move(P.x, P.y); await p.waitForTimeout(450);
await p.mouse.down({ button: 'right' }); await p.waitForTimeout(260); await p.mouse.up({ button: 'right' });
await p.waitForTimeout(1100);
const menu = await p.evaluate(() => {
  const all = Array.from(document.querySelectorAll('div,ul,section'));
  const m = all.find((e) => { const r = e.getBoundingClientRect();
    if (r.width < 60 || r.width > 600 || r.height < 60 || r.height > 900) return false;
    if (getComputedStyle(e).visibility === 'hidden') return false;
    const t = e.innerText.replace(/\s+/g, ' ').trim();
    return t.startsWith('复制 ⌘ C') && t.includes('删除 ⌫') && t.split('⌫').length === 2; });
  if (!m) return null;
  const r = m.getBoundingClientRect();
  return { w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.x), y: Math.round(r.y),
    text: m.innerText.replace(/\s+/g, ' ').trim(),
    rows: Array.from(m.querySelectorAll('button,[role=menuitem]')).map((e) => e.innerText.replace(/\s+/g, ' ').trim()).filter(Boolean) };
});
out.menu = menu;
log('菜单：', JSON.stringify(menu, null, 1));

const del = await p.evaluate(() => {
  const b = Array.from(document.querySelectorAll('button,[role=menuitem]')).find((e) => /^删除/.test(e.innerText.trim()));
  if (!b) return null; const r = b.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2, t: b.innerText.replace(/\s+/g, ' ') };
});
log('删除项：', JSON.stringify(del));
if (del) { await p.mouse.move(del.x, del.y); await p.waitForTimeout(350); await p.mouse.click(del.x, del.y); }
await p.waitForTimeout(1800);
const idsAfter = await allIds();
out.idsAfter = idsAfter.length;
out.gone = !idsAfter.includes(SELF);
log('\n节点数：', out.idsBefore, '→', out.idsAfter, '｜目标已消失 =', out.gone);
log('终态 sel =', await p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]),
    'scale =', await p.evaluate(() => (document.body.innerText.match(/(\d+)%/) || [])[1]));
writeFileSync(new URL('./_tmp-b105z2.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
