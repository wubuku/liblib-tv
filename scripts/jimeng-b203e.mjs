/**
 * 批次 203 e 轮：把 a 轮那条「双击没进编辑态」的无效臂追下去。
 *
 * a 轮的现象：26% 档下 node_5gftn3dnt1 屏上只有 83×83，双击没进编辑态。
 * 收尾 testid 差集里冒出来 4 个从没见过的 testid：*-node-compact。
 * 本轮只问一件事：**compact 变体是不是缩放的函数**，
 * 以及 **compact 变体能不能双击进编辑态**。
 *
 * 全部只读：不新建/删除节点，不生成，不下载。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';
import { openCanvas, readers, settle, setZoom, endState, PORT } from './jimeng-b135-lib.mjs';
import { keyGuard } from './jimeng-safe-keys.mjs';

const TARGET = 'node_5gftn3dnt1';
const OUT = '/tmp/b203e.json';

/** 读 compact 家族与目标节点的 testid 祖先链。 */
const probe = (p) => p.evaluate((tid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${tid}"]`);
  const chain = [];
  for (let e = n; e && e !== document.body; e = e.parentElement) {
    const c = [];
    if (e.getAttribute) { const t = e.getAttribute('data-testid'); if (t) c.push(t); }
    for (const cls of (e.className || '').toString().split(' ')) if (cls) c.push('.' + cls);
    if (c.length) chain.push(`${e.tagName.toLowerCase()}[${c.join('|')}]`);
  }
  const r = n ? n.getBoundingClientRect() : null;
  const cnt = (t) => document.querySelectorAll(`[data-testid="${t}"]`).length;
  const vp = document.querySelector('.react-flow__viewport');
  const ms = vp ? /scale\(([-\d.]+)\)/.exec(vp.style.transform || '') : null;
  return {
    scale: ms ? parseFloat(ms[1]) : null,
    目标屏上: r ? [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] : null,
    目标在视口内: r ? (r.right > 0 && r.x < innerWidth && r.bottom > 0 && r.y < innerHeight) : false,
    祖先链: chain.slice(0, 8),
    compact: {
      'text-flow-node-compact': cnt('text-flow-node-compact'),
      'image-node-compact': cnt('image-node-compact'),
      'video-node-compact': cnt('video-node-compact'),
      'audio-node-compact': cnt('audio-node-compact'),
    },
    非compact: {
      'text-flow-node-full': cnt('text-flow-node-full'),
      'image-node-result': cnt('image-node-result'),
      'video-node-empty': cnt('video-node-empty'),
      'audio-node-empty': cnt('audio-node-empty'),
    },
  };
}, TARGET);

/** 在目标节点正文中心双击，读编辑态。 */
const 双击 = async (p) => {
  const pt = await p.evaluate((tid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${tid}"]`);
    if (!n) return null;
    const r = n.getBoundingClientRect();
    const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2);
    const h = document.elementFromPoint(x, y);
    if (!h) return null;
    return { x, y, 命中: h.getAttribute('data-testid') || h.className || h.tagName, 在节点内: !!h.closest(`.react-flow__node[data-id="${tid}"]`) };
  }, TARGET);
  if (!pt) return { 无效: '目标节点不在 DOM 里' };
  if (!pt.在节点内) return { 无效: `中心点没落在节点内（命中 ${pt.命中}）`, 点位: pt };
  await p.mouse.dblclick(pt.x, pt.y);
  await p.waitForTimeout(1500);
  const 编辑面 = await p.evaluate(() => Array.from(document.querySelectorAll('[contenteditable="true"],textarea'))
    .filter((e) => e.offsetWidth > 0 || e.offsetHeight > 0).map((e) => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; }));
  const cnt = (t) => document.querySelectorAll(`[data-testid="${t}"]`).length;
  return { 点位: pt, 进入编辑态: 编辑面.length > 0, 编辑面, 编辑态工具条: cnt('text-editor-toolbar'), 节点工具条: cnt('node-toolbar') };
};

const b = (p, k) => { console.error('⚠️ ' + k); };

const browser = await chromium.connectOverCDP({ endpointURL: `http://127.0.0.1:${PORT}` });
const ctx = browser.contexts()[0];
let p = ctx.pages().find((x) => /jimeng\.jianying\.com/.test(x.url())) || ctx.pages()[0];
const R = readers(p);

const out = { 轮次: 'b203e', 目标: TARGET, 各档: [], 双击档: {} };

await openCanvas();
await settle(p, R);
const 基线 = { ids: await R.ids(), testids: await R.testids() };

for (const z of [26, 50, 100]) {
  const s = await setZoom(p, z);
  if (!s.scale已追平) b(p, `${z}% 没追平：实测 ${s.实测scale}`);
  const rd = await probe(p);
  out.各档.push({ 缩放: z, aria回读: s.回读, 实测scale: rd.scale, 屏上: rd.目标屏上, 在视口内: rd.目标在视口内, compact: rd.compact, 非compact: rd.非compact, 祖先链: rd.祖先链 });
}

// 双击测试：26%（compact 档，目标在视口内）→ 50%
for (const z of [26, 50]) {
  const s = await setZoom(p, z);
  await p.waitForTimeout(600);
  out.双击档[`${z}%`] = await 双击(p);
  console.error(`  ${z}% 双击 → ${JSON.stringify(out.双击档[`${z}%`])}`);
  await p.keyboard.press('Escape');
  await p.waitForTimeout(800);
}

// 归位：26%
const fin = await setZoom(p, 26);
out.收尾 = await endState(p, R, 基线);
out.收尾.归位scale = fin.实测scale;

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
console.error(`写入 ${OUT}`);
console.log(JSON.stringify(out.各档.map((r) => ({ 缩放: r.缩放, 实测scale: r.实测scale, 屏上: r.屏上, 在视口内: r.在视口内, compact: r.compact, 非compact: r.非compact })), null, 1));
console.log(JSON.stringify(out.双击档, null, 1));
await browser.close();
