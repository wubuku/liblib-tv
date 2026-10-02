// 批次 108 · e 轮：组的「背景色」色板 —— **有成员** vs **0 成员**并排读。
//
// 🔴 d 轮编组成功，但撞到一个**会骗过差集护栏**的东西：
//   `⌘G` 之后 **`.react-flow__node` 计数 78 → 80（+2）**，
//   而**状态行 78 → 79（+1）**。多出来的那一个是
//   **`__group-resize-chrome__node_0ctj8mcr3m`** ——
//   它带 `data-id`、**并且带 `.react-flow__node` 这个 class**，
//   但它**不是节点**，是组的外框控制点壳。
//   ⇒ 📌 **「`.react-flow__node` 数量」不等于「节点数」**。
//      批次 97 立的「差集恰好一个」护栏在**编组**这一类操作上会误判；
//      节点真伪的判据是**状态行的节点数**，或用 `__` 前缀把壳滤掉。
//
// 本轮要读的那一格：`organize-group-layout.md:347`
//   **仍未实测**：0 成员空组（只剩两项时）「背景色」展开的色板是否与有成员时相同。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), mine: ['node_d6cn9z91w6', 'node_8vwsfmqc24'] };
const [A, C] = out.mine;
out.groupId = 'node_0ctj8mcr3m';
const G = out.groupId;
const save = () => writeFileSync(new URL('./_tmp-b108e.json', import.meta.url), JSON.stringify(out, null, 1));

const status = () => p.evaluate(() => { const t = document.body.innerText;
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1],
    edges: (t.match(/(\d+) edges?/) || [])[1] }; });
const domIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));

// 只认「在动作那一刻可命中目标」的落点
const spotNow = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect();
  const c = [];
  for (let y = Math.ceil(r.y) + 2; y < r.y + r.height - 2; y += 4)
    for (let x = Math.ceil(r.x) + 2; x < r.x + r.width - 2; x += 4) {
      if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
      const el = document.elementFromPoint(x, y);
      if (el && (el === n || n.contains(el))) c.push({ x, y });
    }
  return { rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`, total: c.length, sample: c.slice(0, 6) };
}, id);

const groupInfo = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect();
  const inner = Array.from(n.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id'));
  return { aria: n.getAttribute('aria-label'), text: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 200),
    rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
    inner, innerCount: inner.length, sel: n.classList.contains('selected'),
    testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))) };
}, G);

// 组工具条 + 「背景色」点开后的色板
const readGroupBar = async (tag) => {
  const bars = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid]'))
    .filter((e) => /toolbar/i.test(e.getAttribute('data-testid') || ''))
    .map((e) => { const q = e.getBoundingClientRect();
      return { tid: e.getAttribute('data-testid'), w: Math.round(q.width), h: Math.round(q.height),
        x: Math.round(q.x), y: Math.round(q.y), vis: getComputedStyle(e).visibility,
        items: Array.from(e.querySelectorAll('button,[role=button]')).map((x) => {
          const r = x.getBoundingClientRect();
          return { a: x.getAttribute('aria-label'), t: (x.innerText || '').trim(),
            w: Math.round(r.width), h: Math.round(r.height), cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }) };
    }));
  out[tag] = bars;
  log(`\n──── ${tag} ────`);
  for (const b of bars) if (b.items.length) log(`  ${b.tid} ${b.w}×${b.h}@${b.x},${b.y} vis=${b.vis}：`, JSON.stringify(b.items.map((x) => x.a || x.t)));
  save();
  return bars;
};

const readPalette = () => p.evaluate(() => {
  const sw = Array.from(document.querySelectorAll('button,[role=button],div,span'))
    .filter((e) => { const q = e.getBoundingClientRect();
      return q.width >= 8 && q.width <= 40 && q.height >= 8 && q.height <= 40 && q.width === q.height; })
    .map((e) => { const q = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      return { tag: e.tagName, tid: e.getAttribute('data-testid'), a: e.getAttribute('aria-label'),
        t: (e.innerText || '').trim().slice(0, 12), w: Math.round(q.width), h: Math.round(q.height),
        x: Math.round(q.x), y: Math.round(q.y), bg: cs.backgroundColor, border: cs.borderColor, br: cs.borderRadius,
        cx: Math.round(q.x + q.width / 2), cy: Math.round(q.y + q.height / 2) }; });
  // 只取「浮层里」的那一批：找含多个同尺寸小圆点的容器
  const hosts = Array.from(document.querySelectorAll('div')).filter((e) => {
    const kids = Array.from(e.querySelectorAll('*')).filter((x) => { const q = x.getBoundingClientRect();
      return q.width >= 8 && q.width <= 40 && q.height === q.width; });
    return kids.length >= 4 && getComputedStyle(e).visibility !== 'hidden'; });
  return { squares: sw.slice(0, 40), hostCount: hosts.length,
    hosts: hosts.slice(0, 3).map((h) => { const q = h.getBoundingClientRect();
      return { cls: (h.className || '').toString().slice(0, 50), w: Math.round(q.width), h: Math.round(q.height),
        x: Math.round(q.x), y: Math.round(q.y),
        kids: Array.from(h.querySelectorAll('*')).filter((x) => { const r = x.getBoundingClientRect();
          return r.width >= 8 && r.width <= 40 && r.height === r.width; })
          .map((x) => { const r = x.getBoundingClientRect(); const cs = getComputedStyle(x);
            return { tag: x.tagName, tid: x.getAttribute('data-testid'), a: x.getAttribute('aria-label'),
              t: (x.innerText || '').trim().slice(0, 10), w: Math.round(r.width), bg: cs.backgroundColor,
              border: cs.borderColor, br: cs.borderRadius, cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }) }; }) };
});

out.s0 = await status();
out.g0 = await groupInfo();
log('\n起点状态行：', JSON.stringify(out.s0));
log('组读数：', JSON.stringify(out.g0, null, 1));
out.membersOk = JSON.stringify(out.g0.inner.slice().sort()) === JSON.stringify(out.mine.slice().sort());
log('成员核对 =', out.membersOk ? '✅ 恰好本轮那两个' : '🔴');
save();

// ① 选中组
const sg = await spotNow(G);
out.spotG = sg;
log('\n组落点：', JSON.stringify({ rect: sg.rect, total: sg.total }));
if (!sg.total) { log('🔴 组无落点'); save(); await b.close(); process.exit(1); }
const pg = sg.sample[Math.floor(sg.sample.length / 2)];
await p.mouse.move(pg.x, pg.y); await p.waitForTimeout(500);
await p.mouse.click(pg.x, pg.y); await p.waitForTimeout(1500);
out.afterSelectG = await status();
log('点组之后状态行：', JSON.stringify(out.afterSelectG));
out.barsMembers = await readGroupBar('A-有成员的组工具条');
save();
