/**
 * 批次 203 g 轮：核手册 20-reference.md:2558 那一行。
 *
 * 手册原话（描述宿主三套实现表，`text` 行）：
 *   宿主元素 `DIV[data-testid=text-flow-node-compact]`
 *   父壳的 data-testid 「就是 `rf__node-node_<id>`（描述宿主自己就是节点第一层）」
 *
 * 可疑两处：
 *  ① `rf__node-<id>` 看着像 **class**，不是 data-testid；
 *  ② 「就是节点第一层」—— 若描述宿主的**父元素**就是节点根，
 *     那宿主自己就是**第二层**；且 e 轮祖先链显示节点根**没有** data-testid。
 *
 * 本轮只问：三档缩放下，文本/图片节点的
 *   节点根有没有 data-testid / 它的 class 是什么 /
 *   aria-describedby 指向谁 / 那个宿主的父元素是不是节点根。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';
import { openCanvas, readers, settle, setZoom, endState, PORT } from './jimeng-b135-lib.mjs';

const OUT = '/tmp/b203g.json';

const 读 = (p) => p.evaluate(() => {
  const 一个 = (id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!n) return { id, 缺失: true };
    const db = n.getAttribute('aria-describedby');
    const host = db ? document.getElementById(db) : null;
    const box = (e) => { if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; };
    return {
      id,
      aria: n.getAttribute('aria-label'),
      节点根: {
        tag: n.tagName,
        自身dataTestid: n.getAttribute('data-testid'),
        class前四: (String(n.className) || '').split(' ').slice(0, 4),
        是否有rf__node类: Array.from(n.classList).some((c) => c.startsWith('rf__node-')),
        屏上: box(n),
      },
      describedby: db,
      宿主: host ? {
        tag: host.tagName,
        dataTestid: host.getAttribute('data-testid'),
        class前四: (String(host.className) || '').split(' ').slice(0, 4),
        屏上: box(host),
        父元素就是节点根: host.parentElement === n,
        父元素dataTestid: host.parentElement ? host.parentElement.getAttribute('data-testid') : null,
        父元素class前二: host.parentElement ? (String(host.parentElement.className) || '').split(' ').slice(0, 2) : null,
        文本逐字: (host.innerText || host.getAttribute('alt') || '').replace(/\s+/g, ' ').trim().slice(0, 90),
      } : null,
      子树里compact数: n.querySelectorAll('[data-testid$="-node-compact"]').length,
      子树里full数: n.querySelectorAll('[data-testid$="-node-full"]').length,
      子树里result数: n.querySelectorAll('[data-testid$="-node-result"]').length,
      子树里empty数: n.querySelectorAll('[data-testid$="-node-empty"]').length,
    };
  };
  return {
    scale: (() => { const vp = document.querySelector('.react-flow__viewport'); const m = vp ? /scale\(([-\d.]+)\)/.exec(vp.style.transform || '') : null; return m ? parseFloat(m[1]) : null; })(),
    文本3: 一个('node_5gftn3dnt1'),
    文本1: 一个('node_3bfb9r79qe'),
    图片: 一个([...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')).find((x) => /^node_/.test(x) && /image/.test(String(document.querySelector(`.react-flow__node[data-id="${x}"] .react-flow__node-image, .react-flow__node[data-id="${x}"]`)?.className || '')) ) || 'node_tadm1nyykc'),
  };
});

const browser = await chromium.connectOverCDP({ endpointURL: `http://127.0.0.1:${PORT}` });
const ctx = browser.contexts()[0];
let p = ctx.pages().find((x) => /jimeng\.jianying\.com/.test(x.url())) || ctx.pages()[0];
const R = readers(p);

const out = { 轮次: 'b203g', 各档: [] };
await openCanvas();
await settle(p, R);
out.基线 = { ids: await R.ids(), testids: await R.testids() };

for (const z of [26, 50, 100]) {
  const s = await setZoom(p, z);
  if (!s.scale已追平) console.error(`⚠️ ${z}% 没追平`);
  await p.waitForTimeout(500);
  const rd = await 读(p);
  out.各档.push({ 缩放: z, 实测scale: rd.scale, 文本3: rd.文本3, 文本1: rd.文本1, 图片: rd.图片 });
  console.error(`  ${z}% 宿主 testid：文本3=${rd.文本3.宿主 && rd.文本3.宿主.dataTestid} 父就是根=${rd.文本3.宿主 && rd.文本3.宿主.父元素就是节点根} 图片=${rd.图片.宿主 && rd.图片.宿主.dataTestid}`);
}

const fin = await setZoom(p, 26);
out.收尾 = await endState(p, R, out.基线);
out.收尾.归位scale = fin.实测scale;

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
console.error(`写入 ${OUT}`);
console.log(JSON.stringify(out.各档.map((r) => ({
  缩放: r.缩放,
  节点根自身testid: r.文本3.节点根.自身dataTestid,
  节点根class前四: r.文本3.节点根.class前四,
  有rf__node类: r.文本3.节点根.是否有rf__node类,
  describedby: r.文本3.describedby,
  宿主tag: r.文本3.宿主 && r.文本3.宿主.tag,
  宿主testid: r.文本3.宿主 && r.文本3.宿主.dataTestid,
  父就是节点根: r.文本3.宿主 && r.文本3.宿主.父元素就是节点根,
  父元素testid: r.文本3.宿主 && r.文本3.宿主.父元素dataTestid,
  图片宿主testid: r.图片.宿主 && r.图片.宿主.dataTestid,
  子树compact: [r.文本3.子树里compact数, r.图片.子树里compact数],
  子树full: [r.文本3.子树里full数, r.图片.子树里full数],
  子树result: [r.文本3.子树里result数, r.图片.子树里result数],
  子树empty: [r.文本3.子树里empty数, r.图片.子树里empty数],
})), null, 1));
process.exit(0);
