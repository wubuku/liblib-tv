/**
 * 批次 203 h 轮：e 轮与 g 轮的读数互相矛盾，先把状态量对齐再判哪一条对。
 *
 * 矛盾点（同一个 26% 档）：
 *   e 轮：全局 `text-flow-node-compact` = 3、`text-flow-node-full` = 0
 *   g 轮：`node_5gftn3dnt1` 的 aria-describedby 宿主 testid = `text-flow-node-full`，
 *         且它就在该节点子树里（子树 full 计数 = 1）
 * ⇒ 两个读数**不可能同时成立** ⇒ 说明有一个自变量没被控制住。
 *
 * 最可能的嫌疑自变量有两个：① 缩放档 ② **节点是否处于选中态**
 *   （g 轮跑的时候画布上残留着 1 个选中节点，class 里有 `selected`；e 轮跑的时候没有）
 *
 * 本轮跑 2×2 矩阵：{26%, 50%} × {未选中, 已选中}，每格读同一组量：
 *   全局 compact/full 计数、
 *   每个文本节点的 describedby 宿主 testid、
 *   宿主在不在节点子树内、父元素是不是节点根、
 *   以及**全局那几个 compact 元素到底挂在谁下面**。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';
import { openCanvas, readers, settle, setZoom, endState, PORT } from './jimeng-b135-lib.mjs';

const OUT = '/tmp/b203h.json';
const TEXT_IDS = ['node_5gftn3dnt1', 'node_aw29cp094x', 'node_3bfb9r79qe'];

const 读 = (p, ids) => p.evaluate((IDS) => {
  const cnt = (t) => document.querySelectorAll(`[data-testid="${t}"]`).length;
  const 宿主链 = (host, node) => {
    const c = []; for (let e = host; e && e !== node && e !== document.body; e = e.parentElement) c.push(e.getAttribute('data-testid') || '.' + String(e.className || '').split(' ')[0]); return c;
  };
  return {
    scale: (() => { const vp = document.querySelector('.react-flow__viewport'); const m = vp ? /scale\(([-\d.]+)\)/.exec(vp.style.transform || '') : null; return m ? parseFloat(m[1]) : null; })(),
    全局: {
      'text-flow-node-compact': cnt('text-flow-node-compact'),
      'text-flow-node-full': cnt('text-flow-node-full'),
      'image-node-compact': cnt('image-node-compact'),
      'image-node-result': cnt('image-node-result'),
      'text-editor-node-overlay': cnt('text-editor-node-overlay'),
    },
    全局compact挂谁: Array.from(document.querySelectorAll('[data-testid="text-flow-node-compact"]')).map((e) => {
      const owner = e.closest('.react-flow__node');
      return { 所属节点: owner ? owner.getAttribute('data-id') : null, 屏上: (() => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })(), 在视口内: (() => { const r = e.getBoundingClientRect(); return r.right > 0 && r.x < innerWidth && r.bottom > 0 && r.y < innerHeight; })() };
    }),
    选中集: Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')),
    文本节点: IDS.map((id) => {
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      if (!n) return { id, 缺失: true };
      const db = n.getAttribute('aria-describedby');
      const host = db ? document.getElementById(db) : null;
      return {
        id,
        选中态: n.classList.contains('selected'),
        节点根testid: n.getAttribute('data-testid'),
        宿主testid: host ? host.getAttribute('data-testid') : null,
        宿主tag: host ? host.tagName : null,
        宿主在节点子树内: host ? !!n.contains(host) : null,
        宿主父就是节点根: host ? host.parentElement === n : null,
        宿主到节点根的层数: host ? 宿主链(host, n).length : null,
        子树compact: n.querySelectorAll('[data-testid="text-flow-node-compact"]').length,
        子树full: n.querySelectorAll('[data-testid="text-flow-node-full"]').length,
      };
    }),
  };
}, ids);

/** 在节点内找一个真能命中的点。 */
const 点 = (p, id) => p.evaluate((tid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${tid}"]`);
  const r = n.getBoundingClientRect();
  for (let fy = 0.15; fy <= 0.9; fy += 0.15) for (let fx = 0.15; fx <= 0.9; fx += 0.15) {
    const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
    const h = document.elementFromPoint(x, y);
    if (h && h.closest(`.react-flow__node[data-id="${tid}"]`)) return { x, y };
  }
  return null;
}, id);

const browser = await chromium.connectOverCDP({ endpointURL: `http://127.0.0.1:${PORT}` });
const ctx = browser.contexts()[0];
let p = ctx.pages().find((x) => /jimeng\.jianying\.com/.test(x.url())) || ctx.pages()[0];
const R = readers(p);

const out = { 轮次: 'b203h', 矩阵: [] };
await openCanvas();
await settle(p, R);
out.基线 = { ids: await R.ids(), testids: await R.testids() };

for (const z of [26, 50]) {
  const s = await setZoom(p, z);
  if (!s.scale已追平) console.error(`⚠️ ${z}% 没追平`);
  await p.waitForTimeout(400);

  // 格 A：未选中 —— 先点画布空白清选中，再断言选中集为空
  await p.mouse.click(1276, 716);
  await p.waitForTimeout(900);
  const a = await 读(p, TEXT_IDS);
  out.矩阵.push({ 缩放: z, 选中态: '无', ...a });
  console.error(`  ${z}% 无选中 → compact=${a.全局['text-flow-node-compact']} full=${a.全局['text-flow-node-full']} 宿主=${a.文本节点.map((t) => t.宿主testid).join('/')}`);

  // 格 B：选中第一个文本节点
  const pt = await 点(p, TEXT_IDS[0]);
  if (!pt) { console.error(`  ⚠️ ${z}% 找不到节点内可点位置，跳过选中格`); continue; }
  await p.mouse.click(pt.x, pt.y);
  await p.waitForTimeout(900);
  const b = await 读(p, TEXT_IDS);
  const 真选中 = b.选中集.includes(TEXT_IDS[0]);
  out.矩阵.push({ 缩放: z, 选中态: 真选中 ? '选中 node_5gftn3dnt1' : '无效臂（点没选中）', 断言: { 判据: '选中集含 node_5gftn3dnt1', 通过: 真选中 }, ...b });
  console.error(`  ${z}% 已选中=${真选中} → compact=${b.全局['text-flow-node-compact']} full=${b.全局['text-flow-node-full']} 宿主=${b.文本节点.map((t) => t.宿主testid).join('/')}`);
}

const fin = await setZoom(p, 26);
out.收尾 = await endState(p, R, out.基线);
out.收尾.归位scale = fin.实测scale;
out.收尾.末尾选中 = await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
console.error(`写入 ${OUT}`);
console.log(JSON.stringify(out.矩阵.map((r) => ({
  缩放: r.缩放, 选中态: r.选中态, 实测scale: r.scale, 选中集: r.选中集,
  全局compact: r.全局['text-flow-node-compact'], 全局full: r.全局['text-flow-node-full'],
  editorOverlay: r.全局['text-editor-node-overlay'],
  compact挂谁: r.全局compact挂谁,
  逐节点: r.文本节点.map((t) => ({ id: t.id && t.id.slice(-6), 选中: t.选中态, 宿主: t.宿主testid, 在子树内: t.宿主在节点子树内, 父即根: t.宿主父就是节点根, 层数: t.宿主到节点根的层数, 子树compact: t.子树compact, 子树full: t.子树full })),
})), null, 1));
process.exit(0);
