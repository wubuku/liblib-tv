// 批次 147 a 轮 —— 结清「音频节点面板到底几个按钮」这个从批次 29 挂到 137 的未决项。
//
// 🔴 三批给了三个互不相同的数，而且没有任何一批记下**它是怎么数的**：
//   批次 29（2026-10-01）：面板 `node-toolbar` **680×204**，**11 个 svg**；控件表里
//                        **有**「折叠 / aria 逐字 `展开音频生成器` / 40×40」
//   批次 131（2026-10-03）：单选 1 个音频节点 `680×204`，**10 个按钮**
//   批次 137（2026-10-03）：**两次都没出现**折叠按钮，实测 **9 个按钮**，「少的正是它」
//
// 本轮要回答的是**一个方法问题**：这三个数到底是**同一族的三个读数**，
// 还是**量的是不同的东西**。四个可分辨的假设：
//   H1 按钮在、但逐字是**「收起」而不是「展开」**（面板默认就是展开态 ⇒ 批次 29 测的是收起态）
//   H2 它在 DOM 里但**尺寸为 0 / 不可见**（批次 29 数 svg 数到了它，按钮普查数不到）
//   H3 **量的不是同一个 `node-toolbar` 实例** —— 画布上有 68 个音频节点，
//      DOM 里可能同时存在多个 `node-toolbar` 实例（批次 144 在只有 1 个选中的情况下
//      就测到 3 个实例：1 可见 + 2 常驻 0×0）⇒「数哪个实例」直接决定答案
//   H4 **只有部分音频节点有**（有资源 vs 空态）
//
// 🔑 画布上音频节点有 **68 个**，样本量足够大到「中间态」不可能出现 ——
//    若 5 个不同节点的读数完全一致，H4 被排除；若分成两堆，H4 成立。
//
// ⚠️ 全程**只读 + 纯面板开合**（选节点、展开/收起面板、Esc、点空白），
//    不建节点、不删节点、不按生成/扣费按钮、不输入一个字。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { selIds, selCount, idsOf, canvasPos, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 147, 轮: 'a', 目的: '结清「音频节点面板几个按钮」' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };

/** 全页所有 `node-toolbar` 实例的普查（不预设有几个）。 */
const 普查工具条 = () => p.evaluate(() => {
  const 出 = [];
  for (const t of document.querySelectorAll('[data-testid="node-toolbar"]')) {
    const r = t.getBoundingClientRect();
    const cs = getComputedStyle(t);
    const btn = Array.from(t.querySelectorAll('button,[role=button]'));
    出.push({
      盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10],
      可见: cs.display !== 'none' && cs.visibility !== 'hidden' && r.width > 0.01,
      有面积: r.width > 0.01,
      display: cs.display, visibility: cs.visibility, opacity: cs.opacity,
      aria: t.getAttribute('aria-label'), testid: t.getAttribute('data-testid'),
      逐字: (t.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80),
      按钮数: btn.length, svg数: t.querySelectorAll('svg').length,
      在节点内: !!t.closest('.react-flow__node'),
      所属节点: t.closest('.react-flow__node') ? t.closest('.react-flow__node').getAttribute('data-id') : null,
    });
  }
  return 出;
});

/** 指定实例的逐按钮明细。 */
const 读按钮 = (idx) => p.evaluate((i) => {
  const t = document.querySelectorAll('[data-testid="node-toolbar"]')[i];
  if (!t) return { __err: 'no-instance-' + i };
  return Array.from(t.querySelectorAll('button,[role=button]')).map((b, k) => {
    const r = b.getBoundingClientRect(); const cs = getComputedStyle(b);
    return { 序: k, tag: b.tagName, aria: b.getAttribute('aria-label'), testid: b.getAttribute('data-testid'),
      dataDisabled: b.getAttribute('data-disabled'), ariaDisabled: b.getAttribute('aria-disabled'),
      disabled: b.disabled === true, pe: cs.pointerEvents, display: cs.display,
      盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10],
      逐字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24),
      svg数: b.querySelectorAll('svg').length };
  });
}, idx);

/** 全页搜「折叠类」措辞 —— H1：逐字到底是「展开」还是「收起」。 */
const 搜折叠词 = () => p.evaluate(() => {
  const 词 = ['展开音频生成器', '收起音频生成器', '折叠', '收起', '展开'];
  const 命中 = {};
  for (const w of 词) {
    const a = Array.from(document.querySelectorAll('[aria-label]')).filter((e) => (e.getAttribute('aria-label') || '').includes(w));
    命中[w] = a.map((e) => { const r = e.getBoundingClientRect();
      return { tag: e.tagName, aria: e.getAttribute('aria-label'), testid: e.getAttribute('data-testid'),
        在工具条内: !!e.closest('[data-testid="node-toolbar"]'),
        盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10] }; });
  }
  return 命中;
});

const 清零 = async () => {
  for (let k = 0; k < 4 && (await selCount(p)) > 0; k++) {
    const 空 = await p.evaluate(() => {
      const 坏 = (x, y) => { const h = document.elementFromPoint(x, y);
        if (!h) return 1;
        if (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button]')) return 1;
        if (h.closest('.react-flow__node') || h.closest('.react-flow__node-toolbar') || h.closest('[role=dialog],[role=menu],[role=listbox]')) return 1;
        return !(h.classList && h.classList.contains('react-flow__pane')); };
      for (let y = 90; y < innerHeight - 90; y += 8) for (let x = 360; x < innerWidth - 350; x += 8) if (!坏(x, y)) return { x, y };
      return { __err: 'no-free-pane' };
    });
    if (空.__err) break;
    await p.mouse.click(空.x, 空.y); await p.waitForTimeout(1000);
  }
  return selCount(p);
};

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p);
  await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(), 积分: await R.credits() };

  // 音频节点全量清单（按 canvas 坐标排序，便于后面稳定取样）
  rec.音频清单 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const c = n.querySelector('[data-testid="audio-node-empty"]') ? 'empty' : (n.querySelector('[data-testid="audio-node-result"]') ? 'result' : '?');
    return { id: n.getAttribute('data-id'), 态: c, aria: (n.getAttribute('aria-label') || '').slice(0, 26),
      canvas: [Math.round(parseFloat((n.style.transform.match(/translate\(([-\d.]+)px,\s*([-\d.]+)px\)/) || [0, 0, 0])[1])),
        Math.round(parseFloat((n.style.transform.match(/translate\(([-\d.]+)px,\s*([-\d.]+)px\)/) || [0, 0, 0])[2]))] };
  }).filter((q) => q.态 !== '?'));
  rec.音频分布 = rec.音频清单.reduce((m, q) => { m[q.态] = (m[q.态] || 0) + 1; return m; }, {});

  // 🔴 a 轮第一版踩空：直接取 DOM 顺序前 6 个音频节点，**6 个全部 `no-point`** ——
  //    68 个音频节点在 60% 下是阶梯叠放的，前几个都被别的节点压住。
  //    改法：**先普查每个音频节点真正独占多少可点像素**，再从「有独占像素」的那些里取样，
  //    并按独占像素数降序 —— 落点最稳的那几个先测。
  rec.可点普查 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const r = n.getBoundingClientRect(); let 好 = 0; let 首个 = null;
    for (let y = Math.ceil(r.y) + 4; y <= r.y + r.height - 4; y += 4)
      for (let x = Math.ceil(r.x) + 4; x <= r.x + r.width - 4; x += 4) {
        if (x < 1 || y < 1 || x >= innerWidth || y >= innerHeight) continue;
        const h = document.elementFromPoint(x, y);
        if (h && (h === n || n.contains(h))) { 好++; if (!首个) 首个 = [x, y]; }
      }
    const c = n.querySelector('[data-testid="audio-node-empty"]') ? 'empty' : (n.querySelector('[data-testid="audio-node-result"]') ? 'result' : '?');
    return { id: n.getAttribute('data-id'), 态: c, 独占像素: 好, 首个可点: 首个,
      aria: (n.getAttribute('aria-label') || '').slice(0, 26), 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  }).filter((q) => q.态 !== '?' && q.独占像素 > 0).sort((a, b) => b.独占像素 - a.独占像素));
  rec.可点分布 = { 音频总数: rec.音频清单.length, 有独占像素: rec.可点普查.length };

  // ---- 逐个取样：每次选一个不同的音频节点，做完整普查 ----
  rec.样本 = [];
  const 目标 = rec.可点普查.slice(0, 6);
  for (const t of 目标) {
    await 清零();
    for (let k = 0; k < 3 && (await R.overlays()) > 0; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
    const 落 = await 可点落点(p, `.react-flow__node[data-id="${t.id}"]`, 4, 4);
    if (落.__err) { rec.样本.push({ id: t.id, 态: t.态, __err: 'no-point' }); continue; }
    // 🔴 每次点击前都重新断言落点归属
    const 归属 = await p.evaluate(([x, y, id]) => {
      const h = document.elementFromPoint(x, y); const n = h && h.closest('.react-flow__node');
      return { 命中: n ? n.getAttribute('data-id') : null, 是目标: !!(n && n.getAttribute('data-id') === id),
        落点是按钮: !!(h && (h.tagName === 'BUTTON' || h.closest('button,[role=button]'))) };
    }, [落.x, 落.y, t.id]);
    if (!归属.是目标) { rec.样本.push({ id: t.id, 态: t.态, __err: 'wrong-target', 归属 }); continue; }

    await p.mouse.click(落.x, 落.y);
    await p.waitForTimeout(2200); await settle(p, R);
    const 工具条 = await 普查工具条();
    const 可见 = 工具条.map((q, i) => ({ i, ...q })).filter((q) => q.可见);
    rec.样本.push({ id: t.id, 态: t.态, 独占像素: t.独占像素, 画布坐标: null,
      实例数: 工具条.length, 可见实例数: 可见.length,
      实例: 工具条.map((q, i) => ({ i, 盒: q.盒, 可见: q.可见, 按钮数: q.按钮数, svg数: q.svg数, 所属节点: q.所属节点, aria: q.aria, 逐字: q.逐字 })),
      可见实例按钮数: 可见.map((q) => q.按钮数), 可见实例svg数: 可见.map((q) => q.svg数),
      可见实例盒: 可见.map((q) => q.盒),
      折叠词: await 搜折叠词(),
      按钮明细: 可见.length === 1 ? await 读按钮(可见[0].i) : (可见.length ? await 读按钮(可见[0].i) : null) });
  }

  // ---- 出表 ----
  rec.表 = rec.样本.filter((q) => !q.__err).map((q) => ({
    id: q.id, 态: q.态, 实例数: q.实例数, 可见实例数: q.可见实例数,
    可见按钮数: q.可见实例按钮数, 可见svg数: q.可见实例svg数, 可见盒: q.可见实例盒,
    有展开音频生成器: (q.折叠词['展开音频生成器'] || []).length,
    有收起音频生成器: (q.折叠词['收起音频生成器'] || []).length,
    有折叠: (q.折叠词['折叠'] || []).length, 有收起: (q.折叠词['收起'] || []).length,
    aria清单: q.按钮明细 ? q.按钮明细.map((z) => z.aria) : null,
  }));
  console.log(JSON.stringify(rec.表, null, 1));

  // ---- 断言：只判互斥性与自洽性，不预设具体数值 ----
  断言('① 至少取到 3 个音频节点样本（防空集通过）', rec.表.length >= 3, { 实到: rec.表.length });
  if (rec.表.length >= 3) {
    const 按钮集 = new Set(rec.表.map((q) => JSON.stringify(q.可见按钮数)));
    const 形态集 = new Set(rec.表.map((q) => JSON.stringify(q.aria清单)));
    rec.按钮集 = [...按钮集]; rec.形态集 = [...形态集];
    断言('② 全部样本的**可见实例数**恒为 1', rec.表.every((q) => q.可见实例数 === 1), rec.表.map((q) => [q.id, q.可见实例数]));
    断言('③ 全部样本的**可见按钮数完全一致**（⇒ H4「有资源 vs 空态」被排除）',
      按钮集.size === 1, rec.表.map((q) => [q.id, q.态, q.可见按钮数]));
    断言('④ 全部样本的**按钮 aria 清单完全一致**', 形态集.size === 1, { 形态数: 形态集.size });
    断言('⑤ 「展开音频生成器」在全页**一次都没出现**', rec.表.every((q) => q.有展开音频生成器 === 0), rec.表.map((q) => [q.id, q.有展开音频生成器]));
    rec.唯一形态 = JSON.parse(rec.形态集[0]);
    rec.实例总数 = rec.表.map((q) => q.实例数);
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); }

await 清零();
for (let k = 0; k < 3 && (await R.overlays()) > 0; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p),
  浮层: await R.overlays(), zoom: await R.zoom(), 积分: await R.credits(),
  边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length) };
rec.断言全过 = 断言过;
fs.writeFileSync(new URL('./_tmp-b147a.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log('\n起点', JSON.stringify(rec.起点));
console.log('音频分布', JSON.stringify(rec.音频分布), '| 实例总数', JSON.stringify(rec.实例总数));
console.log('收尾', JSON.stringify(rec.收尾));
console.log('异常', rec.异常 || '无');
await b.close();
