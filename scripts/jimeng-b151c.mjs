// 批次 151 · c 轮 —— 按 **id 精确作用域**重测，并加上「画布原有节点」这一组。
//
// b 轮（`_tmp-b151b.json`）自己撞出了一个比原计划更值钱的发现，**但也带一个作用域 bug**：
//
//   🔴 bug：`量3()` 用 `document.querySelector('.react-flow__node-text')` 取变量、
//      用 `querySelectorAll('.react-flow__node-text [data-testid="flow-node-title"]')` 取元素 ——
//      两者都拿到的是 **DOM 顺序里的第一个文本节点**，而画布上**本来就有 3 个**文本节点
//      （`读.节点数 = 6` = 原有 3 + 新建 3）⇒ **量的一直是原有节点，不是本轮建的**。
//      证据：`[data-testid="flow-node-title"]` 读到 **0 个**，而本轮建的 3 个明明都有标题。
//
//   🆕 但「量错了对象」这件事本身给出了线索：**原有那 3 个文本节点的
//      `--octo-canvas-node-chrome-counter-scale` 在 60%→25% 六档缩放下逐字恒为 `2`**，
//      而 a 轮量到**本轮新建的**节点 k 会随缩放变（1.6667 / 2.0 / 1.25）。
//
// ⇒ 假设：节点内那枚 counter-scale **是不是分「两类」**——
//    新建节点会随缩放重算，原有节点被冻在它自己历史上的那个值？
//    若是，批次 88 的 `1.66666 / 1.93435 / 2` 三档就有了统一解释：
//    **那 20 个元素全是历史节点，各自冻着各自的 k**；
//    而批次 150「新建节点上 `Add tags` 恒 24×24」与之并不矛盾 —— **不是同一批节点**。
//
// 本轮三问（全部按 **data-id** 取，不依赖 DOM 顺序）：
//   ① 新建组：k 在 6 档缩放上各是多少，是否 `min(1/s, 2)`
//   ② 原有组：k 在同样 6 档缩放上各是多少，是否恒定
//   ③ 两组在**同一时刻同一缩放**下的屏上读数差多少（这才是「同一画布 60% 下三种尺寸」的对照）
//
// ⚠️ 建-删护栏全程生效；不点任何生成/扣费按钮、不输入一个字、不按任何字母键。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard, setZoom } from './jimeng-b135-lib.mjs';
import { 建N个, selCount, idsOf, canvasPos, 可点落点, 组数 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 151, 轮次: 'c', 目的: '按 id 精确作用域测「新建组 vs 原有组」的 counter-scale 行为差异' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b151c.json', import.meta.url), JSON.stringify(rec, null, 1));

const 实测scale = () => p.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  const t = v && getComputedStyle(v).transform;
  const m = t && t.match(/matrix\(([^)]+)\)/);
  return m ? Number(m[1].split(',')[0].trim()) : null;
});

/** 🔑 按给定的 data-id 列表量读数。**绝不用 `document.querySelector` 取第一个** —— b 轮就栽在这。 */
const 量组 = (ids) => p.evaluate((list) => {
  const 出 = [];
  for (const i of list) {
    const n = document.querySelector('.react-flow__node[data-id="' + i + '"]');
    if (!n) { 出.push({ id: i, __err: 'not-found' }); continue; }
    const cs = getComputedStyle(n);
    const 变量 = {};
    for (let k = 0; k < cs.length; k++) { const 名 = cs[k];
      if (名.startsWith('--octo-canvas')) 变量[名] = cs.getPropertyValue(名).trim(); }
    const r = n.getBoundingClientRect();
    const 读 = (sel) => {
      const e = n.querySelector(sel);
      if (!e) return null;
      const q = e.getBoundingClientRect(); const s = getComputedStyle(e);
      return { 屏上: [Math.round(q.width * 1000) / 1000, Math.round(q.height * 1000) / 1000],
        css: [s.width, s.height], 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20) };
    };
    出.push({ id: i, aria: n.getAttribute('aria-label'), class: n.className,
      节点屏上: [Math.round(r.width * 100) / 100, Math.round(r.height * 100) / 100],
      节点css: [cs.width, cs.height], 变量,
      标题: 读('[data-testid="flow-node-title"]'), 标签: 读('[data-testid="flow-node-selected-tag"]') });
  }
  return 出;
}, ids);

/** 找出一组「文本节点」的 data-id（按 DOM 顺序返回）。 */
const 找文本ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node-text'))
  .map((n) => ({ id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label') })));

const 清零 = async () => {
  for (let k = 0; k < 4 && (await selCount(p)) > 0; k++) {
    const 空 = await p.evaluate(() => {
      const 坏 = (x, y) => { const h = document.elementFromPoint(x, y);
        if (!h) return 1;
        if (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button]')) return 1;
        if (h.closest('.react-flow__node') || h.closest('[data-testid="node-toolbar"]') || h.closest('[role=dialog],[role=menu],[role=listbox]')) return 1;
        return !(h.classList && h.classList.contains('react-flow__pane')); };
      for (let y = 90; y < innerHeight - 90; y += 8) for (let x = 360; x < innerWidth - 350; x += 8) if (!坏(x, y)) return { x, y };
      return { __err: 'no-free-pane' };
    });
    if (空.__err) break;
    await p.mouse.click(空.x, 空.y); await p.waitForTimeout(1000);
  }
  return selCount(p);
};

const 删一个 = async (id) => {
  await 清零();
  const 前 = await idsOf(p);
  const 落 = await 可点落点(p, `.react-flow__node[data-id="${id}"]`, 4, 4);
  if (落.__err) return { id, __err: 'no-point' };
  const 归属 = await p.evaluate(([x, y, i]) => { const h = document.elementFromPoint(x, y);
    const n = h && h.closest('.react-flow__node'); return { 对: !!(n && n.getAttribute('data-id') === i) }; }, [落.x, 落.y, id]);
  if (!归属.对) return { id, __err: 'wrong-target（被压住）' };
  await p.mouse.click(落.x, 落.y, { button: 'right' }); await p.waitForTimeout(1800);
  const del = await p.evaluate(() => {
    const els = Array.from(document.querySelectorAll('[role=menuitem],[role=menu] button,li,button'))
      .filter((e) => /^删除/.test((e.innerText || '').replace(/\s+/g, '').trim()));
    if (!els.length) return { __err: 'no-delete-item' };
    const e = els[0]; const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2)
      for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) {
        const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y, 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim() }; }
    return { __err: 'no-point' };
  });
  if (del.__err) return { id, __err: del.__err };
  await p.mouse.click(del.x, del.y); await p.waitForTimeout(2500); await settle(p, R);
  const 后 = await idsOf(p);
  return { id, 消失: 前.filter((x) => !后.includes(x)), 删除项逐字: del.逐字 };
};

const 档位 = [60, 50, 45, 40, 30, 25];

const { b, p } = await openCanvas();
const R = readers(p);
let 基线canvas = null;
try {
  await keyGuard(p); await settle(p, R);
  await setZoom(p, 60); await p.waitForTimeout(900);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(),
    实测scale: await 实测scale(), 积分: await R.credits(), 组数: await 组数(p), 选中: await selCount(p) };
  基线canvas = await canvasPos(p);

  // 建前先把画布上**原有的**文本节点 id 记下来
  rec.建前文本节点 = await 找文本ids();
  console.log('建前画布上的文本节点:', JSON.stringify(rec.建前文本节点));

  const 建 = await 建N个(p, '文本', 3, null, (await idsOf(p)).length);
  rec.ids = 建.ids;
  rec.护栏 = 建.护栏.map((h) => [h.名, h.通过]);
  rec.护栏全过 = 建.护栏.every((h) => h.通过);
  rec.档 = [];
  if (建.ids && 建.ids.length) {
    await p.waitForTimeout(1500); await settle(p, R);
    const 原有ids = (rec.建前文本节点 || []).map((x) => x.id);
    for (const pct of 档位) {
      await setZoom(p, pct); await p.waitForTimeout(1400); await settle(p, R);
      const s = await 实测scale();
      const 新 = await 量组(建.ids);
      const 原 = 原有ids.length ? await 量组(原有ids) : [];
      rec.档.push({ 设: pct, aria: await R.zoom(), 实测scale: s, 一比缩放: s ? Number((1 / s).toFixed(4)) : null,
        新建组: 新, 原有组: 原 });
      落盘();
    }
    await setZoom(p, 60); await p.waitForTimeout(900); await 清零();
    rec.删除 = [];
    for (const id of 建.ids) rec.删除.push(await 删一个(id));
  }
  const 末 = await idsOf(p); const 末c = await canvasPos(p);
  rec.收尾检查 = { 节点数: 末.length,
    位移节点: 基线canvas ? Object.keys(基线canvas).filter((k) => 末c[k] && (末c[k][0] !== 基线canvas[k][0] || 末c[k][1] !== 基线canvas[k][1])) : null };
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

await setZoom(p, 60); await p.waitForTimeout(900);
for (let k = 0; k < 3 && (await R.overlays()) > 0; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
await 清零();
const 小地图前 = await R.minimap();
if (!小地图前 || 小地图前.ariaPressed !== 'true') {
  const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3);
  if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400); }
}
rec.小地图后 = await R.minimap();
await settle(p, R);
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p),
  浮层: await R.overlays(), zoom: await R.zoom(), 实测scale: await 实测scale(), 积分: await R.credits(), 组数: await 组数(p),
  边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length),
  残留自建: (await idsOf(p)).filter((x) => (rec.ids || []).includes(x)) };

const kOf = (屏, cssv, s) => (屏 && cssv && s ? Number((parseFloat(屏) / (parseFloat(cssv) * s)).toFixed(4)) : null);
console.log('\n=== 按 id 作用域：新建组 vs 原有组（6 档缩放）===');
console.log('设   实测    1/s     | 新建 k_标签  新建 k_标题  新建变量 | 原有 k_标签  原有 k_标题  原有变量');
const 表 = [];
for (const d of (rec.档 || [])) {
  const 新0 = (d.新建组 || [])[0], 原0 = (d.原有组 || [])[0];
  const 行 = {
    设: d.设, 实测: d.实测scale, 一比: d.一比缩放,
    新k标签: kOf(新0 && 新0.标签 && 新0.标签.屏上[0], 新0 && 新0.标签 && 新0.标签.css[0], d.实测scale),
    新k标题: kOf(新0 && 新0.标题 && 新0.标题.屏上[0], 新0 && 新0.标题 && 新0.标题.css[0], d.实测scale),
    新变量: 新0 && 新0.变量 && 新0.变量['--octo-canvas-node-chrome-counter-scale'],
    新标签屏上: 新0 && 新0.标签 && 新0.标签.屏上,
    新标题屏上: 新0 && 新0.标题 && 新0.标题.屏上,
    新标题文字: 新0 && 新0.标题 && 新0.标题.文字,
    原k标签: kOf(原0 && 原0.标签 && 原0.标签.屏上[0], 原0 && 原0.标签 && 原0.标签.css[0], d.实测scale),
    原k标题: kOf(原0 && 原0.标题 && 原0.标题.屏上[0], 原0 && 原0.标题 && 原0.标题.css[0], d.实测scale),
    原变量: 原0 && 原0.变量 && 原0.变量['--octo-canvas-node-chrome-counter-scale'],
    原标签屏上: 原0 && 原0.标签 && 原0.标签.屏上,
    原有节点数: (d.原有组 || []).length,
    原有节点屏上: (d.原有组 || []).map((x) => x.节点屏上),
  };
  表.push(行);
  console.log(String(行.设).padEnd(4) + String(行.实测).padEnd(8) + String(行.一比).padEnd(8) + '| ' +
    String(行.新k标签).padEnd(11) + String(行.新k标题).padEnd(12) + String(行.新变量).padEnd(10) + '| ' +
    String(行.原k标签).padEnd(11) + String(行.原k标题).padEnd(12) + String(行.原变量));
}
rec.表 = 表;
console.log('\n原有组节点屏上:', JSON.stringify((表[0] || {}).原有节点屏上), '| 原有组节点数', (表[0] || {}).原有节点数);
console.log('新建组标题文字:', JSON.stringify((表[0] || {}).新标题文字));
console.log('删除', JSON.stringify((rec.删除 || []).map((d) => d.消失 || d.__err)));
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');

断言('① 建 3 个并全部删除', (rec.删除 || []).length === 3, (rec.删除 || []).length);
断言('② 建-删护栏全过', rec.护栏全过 === true, rec.护栏);
断言('③ 每个删除的消失集合恰好 {SELF}', (rec.删除 || []).every((d) => d.消失 && d.消失.length === 1), (rec.删除 || []).map((d) => d.消失 || d.__err));
断言('④ 6 档全部读到新建组读数（**非空**断言前置）', 表.length === 档位.length && 表.every((r) => r.新k标签 != null), 表.map((r) => [r.设, r.新k标签]));
断言('⑤ 6 档全部读到原有组读数', 表.every((r) => r.原k标签 != null || r.原k标题 != null), 表.map((r) => [r.设, r.原k标签, r.原k标题]));
const 新变量集 = [...new Set(表.map((r) => r.新变量))];
rec.新建组变量取值集 = 新变量集;
rec.原有组变量取值集 = [...new Set(表.map((r) => r.原变量))];
断言('⑥ 🔑 **原有组**的 counter-scale 在 6 档缩放下**恒定**', 新变量集.length >= 1 && [...new Set(表.map((r) => r.原变量))].length === 1, [...new Set(表.map((r) => r.原变量))]);
if (rec.收尾检查 && rec.收尾检查.位移节点) 断言('⑦ 其余节点零位移', rec.收尾检查.位移节点.length === 0, rec.收尾检查);

rec.断言全过 = 断言过; 落盘();
await b.close();
