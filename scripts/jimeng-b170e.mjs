// 批次 170 e 轮：诊断「点音频节点没选中」。
// 假设清单：① 点被浮层挡了（elementFromPoint 不是节点）② 选中态不落在 .selected
//          ③ 节点在 react-flow 变换层里，鼠标事件被 pane 吃掉 ④ 点错了部位（标题/空态区不可选）
import { openCanvas, readers } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);

await p.evaluate(() => {
  const n = Array.from(document.querySelectorAll('.react-flow__node'))
    .find((x) => x.querySelector('[data-testid="audio-node-empty"]'));
  n && n.scrollIntoView({ block: 'center', inline: 'center' });
});
await p.waitForTimeout(600);

const probe = await p.evaluate(() => {
  const n = Array.from(document.querySelectorAll('.react-flow__node'))
    .find((x) => x.querySelector('[data-testid="audio-node-empty"]'));
  const r = n.getBoundingClientRect();
  const pts = {
    center: [r.x + r.width / 2, r.y + r.height / 2],
    title: [r.x + r.width / 2, r.y + 12],
    empty: null,
  };
  const e = n.querySelector('[data-testid="audio-node-empty"]');
  if (e) { const er = e.getBoundingClientRect(); pts.empty = [er.x + er.width / 2, er.y + er.height / 2]; }
  const at = {};
  for (const [k, [x, y]] of Object.entries(pts)) {
    if (!x) continue;
    const hit = document.elementFromPoint(x, y);
    at[k] = hit ? {
      tag: hit.tagName, testid: hit.getAttribute('data-testid'),
      cls: (hit.getAttribute('class') || '').split(/\s+/).slice(0, 3).join(' '),
      inNode: !!hit.closest('.react-flow__node'),
      isNodeItself: hit === n,
    } : null;
  }
  return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], nodeId: n.getAttribute('data-id'), at };
});
console.log(JSON.stringify(probe, null, 1));

// 逐点试点，每点后读选中数
for (const k of ['title', 'empty', 'center']) {
  const [x, y] = k === 'title' ? [probe.rect[0] + probe.rect[2] / 2, probe.rect[1] + 12]
    : k === 'empty' ? (await p.evaluate(() => {
        const e = document.querySelector('.react-flow__node [data-testid="audio-node-empty"]');
        const r = e.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2];
      }))
    : [probe.rect[0] + probe.rect[2] / 2, probe.rect[1] + probe.rect[3] / 2];
  await p.mouse.click(x, y);
  await p.waitForTimeout(900);
  const sel = await R.selCount();
  const cls = await p.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    return n ? n.getAttribute('class') : null;
  }, probe.nodeId);
  console.log(`click@${k} (${Math.round(x)},${Math.round(y)}) → selected=${sel}  cls=${String(cls).slice(0, 120)}`);
  if (sel > 0) break;
}
console.log('status:', await R.status());
await b.close();
