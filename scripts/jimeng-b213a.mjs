/**
 * 批次 213 a 轮：给「中招集合」建立**交叉表的基础数据**。
 *
 * 批次 212 的结论「中招 = `audio`(68) + `video`(1)、不中招 = `text`/`timeline`/`image`/`external`」
 * ⚠️ **每类型只有 1 个被点过的样本**（text 3 / timeline 1 / image 1 / video 1 / external 1），
 * 只有 audio 有 7 个样本 ⇒ **「类型」这个判据本身的样本量不足**。
 *
 * 本轮先取**不需要点击**的那一半数据：在 `26%` 与 `50%` 两档，
 * 把**全部 76 个节点**的渲染变体逐个读出来。
 * 📌 变体 testid 已在批次 203/211 见过：
 *   `26%` 档：`text-flow-node-compact` / `image-node-compact` / `video-node-compact` / `audio-node-compact`
 *   `50%` 档：`text-flow-node-full` / `image-node-result` / `video-node-empty` / `audio-node-empty`
 *   以及不变的两族：`timeline-flow-node`、`director-stage-flow-node-shell`
 *
 * 拿到全表之后就能回答两个问题，而**不用再点一次**：
 *   ① 「中招集合 == `50%` 档渲染 `*-node-empty` 的那一族」吗？
 *   ② 「中招集合 == `26%` 档渲染 `*-node-compact` 的那一族」吗？
 *      （🔴 批次 203 已经知道**文本节点在 `26%` 也是 compact**，
 *        而批次 212 实测文本节点**不中招** ⇒ 这一族若成立就会被当场否掉）
 *
 * 只读：只读 DOM，不点任何东西。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';
import { openCanvas, readers, settle, setZoom, endState, PORT } from './jimeng-b135-lib.mjs';

const OUT = '/tmp/b213a.json';

/** 读全部 76 个节点：画布坐标 + 它子树里所有「节点体」类 testid + 自身尺寸。 */
const 读全部 = (p) => p.evaluate(() => {
  const 变体候选 = [
    'text-flow-node-compact', 'text-flow-node-full',
    'image-node-compact', 'image-node-result', 'image-node-empty',
    'video-node-compact', 'video-node-empty', 'video-node-result',
    'audio-node-compact', 'audio-node-empty', 'audio-node-result',
    'timeline-flow-node', 'director-stage-flow-node-shell',
    'timeline-flow-node-surface',
  ];
  const 类型判定 = (ids) => {
    const 有 = (t) => ids.includes(t);
    if (有('audio-node-compact') || 有('audio-node-empty') || 有('audio-node-result')) return 'audio';
    if (有('video-node-compact') || 有('video-node-empty') || 有('video-node-result')) return 'video';
    if (有('image-node-compact') || 有('image-node-result') || 有('image-node-empty')) return 'image';
    if (有('text-flow-node-compact') || 有('text-flow-node-full')) return 'text';
    if (有('timeline-flow-node')) return 'timeline';
    if (有('director-stage-flow-node-shell')) return 'external';
    return '未知';
  };
  return Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const t = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
    const r = n.getBoundingClientRect();
    const ids = [];
    for (const c of 变体候选) if (n.querySelector(`[data-testid="${c}"]`)) ids.push(c);
    return {
      id: n.getAttribute('data-id'),
      aria: (n.getAttribute('aria-label') || '').replace(/^(\S+) node: /, '$1 | '),
      类型: 类型判定(ids),
      变体: ids,
      画布: t ? [Number(t[1]), Number(t[2])] : null,
      屏上: [Math.round(r.width), Math.round(r.height)],
    };
  }).sort((a, b) => (a.画布 && b.画布 ? a.画布[0] - b.画布[0] : 0));
});

const browser = await chromium.connectOverCDP({ endpointURL: `http://127.0.0.1:${PORT}` });
const ctx = browser.contexts()[0];
let p = ctx.pages().find((x) => /jimeng\.jianying\.com/.test(x.url())) || ctx.pages()[0];
const R = readers(p);

const out = { 轮次: 'b213a', 档: {} };
await openCanvas();
await settle(p, R);
out.基线 = { ids: await R.ids(), testids: await R.testids() };

for (const z of [26, 50]) {
  const s = await setZoom(p, z);
  if (!s.scale已追平) console.error(`⚠️ ${z}% 没追平`);
  await p.waitForTimeout(900);
  const 节点 = await 读全部(p);
  const 按类型 = {};
  for (const n of 节点) {
    按类型[n.类型] = 按类型[n.类型] || { 数: 0, 变体分布: {} };
    按类型[n.类型].数++;
    const k = n.变体.join('+') || '(无)';
    按类型[n.类型].变体分布[k] = (按类型[n.类型].变体分布[k] || 0) + 1;
  }
  out.档[z] = { 实测scale: s.实测scale, 节点数: 节点.length, 按类型, 节点 };
  console.error(`\n【${z}%】共 ${节点.length} 个节点`);
  for (const [k, v] of Object.entries(按类型)) console.error(`  ${k.padEnd(9)} ${v.数} 个 ｜ 变体 ${JSON.stringify(v.变体分布)}`);
}

const fin = await setZoom(p, 26);
out.收尾 = await endState(p, R, out.基线);
out.收尾.归位scale = fin.实测scale;
out.收尾.末尾选中 = await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
console.error(`\n写入 ${OUT}`);
console.log(JSON.stringify(Object.fromEntries(Object.entries(out.档).map(([z, g]) => [z + '%', g.按类型])), null, 1));
process.exit(0);
