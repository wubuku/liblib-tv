// 批次 176 c 轮：把 b 轮**没测到**的那一项测到 —— 描述会不会随「选中」变；
// 并钉死三条个别读数：导演台节点没有描述、两种「无资源」措辞、哪些描述是**看得见**的。
//
// 🔴 b 轮的自曝失误：b 轮点「视频 1」的标题想测「选中后描述变不变」，
//    结果 `选中: false` **两次都是 false** —— 那个点击**根本没选中**，
//    于是前后读数逐字相同，是一道**恒真门**（批次 174/175 同家族，第 N 次）。
//    ⇒ 本轮用**带非空守卫**的选中：读 `.react-flow__node.selected` 必须恰好含目标 id，
//    选不中就换落点，**绝不拿没选中当读数**。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '176c' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);

const 描述 = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const h = document.getElementById(`canvas-node-description-${i}`);
  const r = h ? h.getBoundingClientRect() : null;
  return { 选中: n?.classList.contains('selected') ?? null, 节点aria: n?.getAttribute('aria-label') ?? null,
    描述: h ? (h.innerText || '').trim() : null,
    描述有面积: r ? (r.width > 1 && r.height > 1) : null,
    描述盒: r ? [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] : null };
}, id);

/** 带非空守卫的选中：读 .selected 必须恰好是 [id]，否则换下一个候选落点。 */
const 守住选中 = async (id) => {
  const 落点 = await p.evaluate((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
    n.scrollIntoView({ block: 'center', inline: 'center' });
    const t = n.querySelector('[data-testid="flow-node-title"]');
    const 盒 = t ? t.getBoundingClientRect() : n.getBoundingClientRect();
    return { 标题: t ? [Math.round(盒.x + 盒.width / 2), Math.round(盒.y + 盒.height / 2)] : null,
             节点: [Math.round(盒.x + 盒.width / 2), Math.round(盒.y + 盒.height / 2)],
             盒: [Math.round(盒.x), Math.round(盒.y), Math.round(盒.width), Math.round(盒.height)] };
  }, id);
  if (!落点) return { 成功: false, 原因: '节点不在 DOM 里' };
  await p.waitForTimeout(900);
  const 试 = [];
  for (const pt of [落点.标题, 落点.节点].filter(Boolean)) {
    await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(900);
    const sel = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
    试.push({ 落点: pt, 选中集: sel });
    if (sel.length === 1 && sel[0] === id) return { 成功: true, 落点: pt, 尝试: 试 };
  }
  return { 成功: false, 原因: '两种落点都没选中', 尝试: 试 };
};

const 全部 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => ({
  id: n.getAttribute('data-id'),
  类型: (n.className.match(/react-flow__node-(\S+)/) || [])[1] || null,
  标题: (n.querySelector('[data-testid="flow-node-title"]')?.innerText || '').trim().split('\n')[0],
  有描述: !!document.getElementById(`canvas-node-description-${n.getAttribute('data-id')}`) })));

// ① 逐类核对「有没有描述」
rec.逐类 = {};
for (const t of [...new Set(全部.map((x) => x.类型))]) {
  const 们 = 全部.filter((x) => x.类型 === t);
  rec.逐类[t] = { 节点数: 们.length, 有描述: 们.filter((x) => x.有描述).length, 样例id: 们[0].id, 样例标题: 们[0].标题 };
}
rec.无描述的 = 全部.filter((x) => !x.有描述).map((x) => ({ id: x.id, 类型: x.类型, 标题: x.标题 }));

// ② 看得见的描述（画布上真的会显示的那些）
rec.看得见的描述 = await p.evaluate(() => {
  const 出 = [];
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const id = n.getAttribute('data-id');
    const h = document.getElementById(`canvas-node-description-${id}`); if (!h) continue;
    const r = h.getBoundingClientRect(); if (r.width < 1 || r.height < 1) continue;
    const t = n.querySelector('[data-testid="flow-node-title"]'); const tr = t?.getBoundingClientRect();
    出.push({ id, 类型: (n.className.match(/react-flow__node-(\S+)/) || [])[1] || null,
      标题: t ? (t.innerText || '').trim().split('\n')[0] : null,
      描述: (h.innerText || '').trim(), 描述盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      标题盒: tr ? [Math.round(tr.x), Math.round(tr.y), Math.round(tr.width), Math.round(tr.height)] : null,
      在标题下方: tr ? r.y >= tr.bottom - 2 : null, class: typeof h.className === 'string' ? h.className.slice(0, 70) : null });
  }
  return 出;
});

// ③ 选中态会不会改描述（带非空守卫）
rec.选中变化 = [];
for (const 类型 of ['text', 'video', 'image', 'timeline']) {
  const 节点 = 全部.find((x) => x.类型 === 类型);
  if (!节点) { rec.选中变化.push({ 类型, 说明: '没有这种节点' }); continue; }
  const 前 = await 描述(节点.id);
  const 选 = await 守住选中(节点.id);
  if (!选.成功) { rec.选中变化.push({ 类型, id: 节点.id, 标题: 节点.标题, 前: 前, 选中尝试: 选 }); continue; }
  const 中 = await 描述(节点.id);
  await p.mouse.click(640, 690); await p.waitForTimeout(1000);
  const 后 = await 描述(节点.id);
  rec.选中变化.push({ 类型, id: 节点.id, 标题: 节点.标题, 落点: 选.落点,
    前, 选中时: 中, 取消后: 后,
    描述在选中时变了: 前.描述 !== 中.描述,
    节点aria在选中时变了: 前.节点aria !== 中.节点aria,
    取消后复原: 后.描述 === 前.描述 && 后.节点aria === 前.节点aria });
}
await p.keyboard.press('Escape'); await p.waitForTimeout(600);
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(),
  选中: await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length) };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);
