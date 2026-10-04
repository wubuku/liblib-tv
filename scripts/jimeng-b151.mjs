// 批次 151 —— 批次 150 的**判据修正版**，并把它留下的四个未决一次问清。
//
// 批次 150 拿到了硬结论（同族三节点 counter-scale 逐字相同；`Add tags` 12/12 恒 24×24），
// 但它自己留了 4 个尾巴，其中两个是**判据问题**、两个是**测量维度不够**：
//
//   🔴 未决①（判据）：a 轮断言「存在同族内尺寸不一致」判成成立，但 23 条里有 21 条是
//      `null,null,有值` —— 第 3 个节点处于**选中态**。判据没拆两态 ⇒ 必真的假阳性。
//      ⇒ 本轮把判据改成「**同族 × 同态**内不一致」，且**排除选中态独有元素**。
//   🔴 未决②（测量维度）：没记 `getComputedStyle().width` ⇒ 无法区分
//      「屏上定值」与「canvas 定值 × 缩放」。批次 150 因此对文本手柄 `36×72`
//      明确写了「**无法区分**是屏上定值还是按 1/scale 补偿后的值」—— 只测到 60% 一档。
//   🔴 未决③（测量维度）：没记 `flow-node-title` 的 `innerText` ⇒ 同一族三个节点的
//      标题宽（图片 55.5/58.1/58.1、音频 65.9/65.2/62.7）**成因未坐实**。
//   🔴 未决④（覆盖）：文本族本轮只在 `60%` 一档被测到 ⇒ 缩放对文本族的影响是空的。
//
// 本轮四问：
//   Q1 同族 × **同态**内，哪些元素的**屏上**尺寸真的不一致（修正后的真判据）
//   Q2 每个元素的 **CSS 宽度**（transform 之前）是多少 ⇒ 屏上 / CSS = ?
//      比值恒等于缩放 ⇒ CSS 定值；比值不随缩放 ⇒ 屏上定值
//   Q3 `flow-node-title` 三个节点的 `innerText` 逐字是什么
//   Q4 **文本族在 60% / 40% / 80% 三档缩放下**，屏上与 CSS 读数各是什么
//
// ⚠️ 建-删护栏全程生效。**全程零点击 UI**（只点左栏建节点、右键「删除 ⌫」、缩放菜单），
//    不点任何生成/扣费按钮、不输入一个字、不按任何字母键。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard, setZoom } from './jimeng-b135-lib.mjs';
import { 建N个, selCount, idsOf, canvasPos, 可点落点, 组数 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 151, 目的: '批次 150 的判据修正版：分离静息/选中两态 + 记 CSS 宽度与标题文字 + 文本族换三档缩放' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b151.json', import.meta.url), JSON.stringify(rec, null, 1));

// 实测缩放：`.react-flow__viewport` 的 transform matrix 里第 1 个数
const 实测scale = () => p.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  const t = v && getComputedStyle(v).transform;
  const m = t && t.match(/matrix\(([^)]+)\)/);
  return m ? Number(m[1].split(',')[0].trim()) : null;
});

/**
 * 量一个节点里每个可命名元素的读数。
 * 🔑 本轮比批次 150 多两列：
 *   css  = getComputedStyle(e).width / height  —— transform **之前**的 CSS 尺寸
 *   文字 = innerText（用来解释标题宽差异）
 * 另外把节点的 `选中态` 与 `counter-scale` 一起返回，供「同态」分组。
 */
const 量节点 = (id, 态) => p.evaluate(([i, 态名]) => {
  const n = document.querySelector('.react-flow__node[data-id="' + i + '"]');
  if (!n) return { __err: 'not-found' };
  const r = n.getBoundingClientRect();
  const cs = getComputedStyle(n);
  const 变量 = {};
  for (let k = 0; k < cs.length; k++) { const 名 = cs[k];
    if (名.startsWith('--octo-canvas')) 变量[名] = cs.getPropertyValue(名).trim(); }
  const 元素 = {};
  for (const e of n.querySelectorAll('[data-testid], .flow-node-title, [aria-label^="Add tags"], [aria-label^="Edit tags"], [aria-label^="Create connected node"]')) {
    const q = e.getBoundingClientRect(); const s = getComputedStyle(e);
    const key = e.getAttribute('data-testid') || ('aria:' + (e.getAttribute('aria-label') || '').slice(0, 18)) || e.tagName;
    if (元素[key]) continue;
    元素[key] = {
      屏上: [Math.round(q.width * 100) / 100, Math.round(q.height * 100) / 100],
      css: [s.width, s.height],
      文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40),
      字体: s.fontSize, 行高: s.lineHeight, padding: s.padding,
      pointerEvents: s.pointerEvents, visibility: s.visibility, opacity: s.opacity,
      变量: (() => { const v = {}; for (let k = 0; k < s.length; k++) { const 名 = s[k];
        if (名.startsWith('--octo-canvas')) v[名] = s.getPropertyValue(名).trim(); } return v; })(),
    };
  }
  return { 态: 态名, 选中: n.classList.contains('selected'),
    节点屏上: [Math.round(r.width * 100) / 100, Math.round(r.height * 100) / 100],
    节点css: [cs.width, cs.height],
    class: n.className, aria: n.getAttribute('aria-label'), 变量, 元素 };
}, [id, 态]);

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

/** 同态分组比对：只比较**同一个选中态**内的节点，且**排除选中态独有元素**。 */
const 同态比对 = (量) => {
  const 静 = 量.filter((m) => !m.选中);
  const 选中集 = 量.filter((m) => m.选中);
  const 静独有键 = new Set(静.flatMap((m) => Object.keys(m.元素 || {})));
  const 选中独有键 = new Set(选中集.flatMap((m) => Object.keys(m.元素 || {})));
  const 共有键 = [...静独有键].filter((k) => 选中独有键.has(k));
  const 选中态独有 = [...选中独有键].filter((k) => !静独有键.has(k));
  const 出 = { 静息节点数: 静.length, 选中节点数: 选中集.length, 共有键, 选中态独有元素: 选中态独有, 比对: [] };
  for (const k of 共有键) {
    const 屏集 = [...静, ...选中集].map((m) => (m.元素[k] ? JSON.stringify(m.元素[k].屏上) : 'null'));
    const 静屏 = 静.map((m) => (m.元素[k] ? m.元素[k].屏上 : null));
    出.比对.push({
      元素: k,
      静息态屏上: 静屏,
      静息态是否全同: new Set(静屏.map((x) => JSON.stringify(x))).size === 1,
      两态全部屏上: [...静, ...选中集].map((m) => (m.元素[k] ? m.元素[k].屏上 : null)),
      是否全同: new Set(屏集).size === 1,
      文字: [...静, ...选中集].map((m) => (m.元素[k] ? m.元素[k].文字 : null)),
    });
  }
  return 出;
};

const { b, p } = await openCanvas();
const R = readers(p);
const 族表 = ['音频', '图片', '视频', '文本'];
// ⚠️ 变量提到 try 外（批次 148 白跑一轮的教训：声明在 try 内、块外收尾段引用 ⇒ ReferenceError，证据整个没写出来）
let 基线canvas = null;
const 缩放档 = [60, 40, 80];
try {
  await keyGuard(p); await settle(p, R);
  await setZoom(p, 60); await p.waitForTimeout(900);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(),
    实测scale: await 实测scale(), 积分: await R.credits(), 组数: await 组数(p), 选中: await selCount(p) };
  基线canvas = await canvasPos(p);

  // ============ 第一部分：四族 × 3 节点，**两态各量一遍** ============
  rec.族 = [];
  for (const 族 of 族表) {
    const 条 = { 族, 缩放建前: await R.zoom() };
    const 建 = await 建N个(p, 族, 3, null, (await idsOf(p)).length);
    条.护栏 = 建.护栏.map((h) => [h.名, h.通过]);
    条.护栏全过 = 建.护栏.every((h) => h.通过);
    条.ids = 建.ids;
    if (!建.ids || !建.ids.length) { 条.__err = '建节点未成'; rec.族.push(条); 落盘(); continue; }
    await p.waitForTimeout(1500); await settle(p, R);
    条.缩放建后 = await R.zoom();
    条.实测scale = await 实测scale();

    // 态 A：护栏建完，第 3 个节点处于选中态
    条.量_选中态 = [];
    for (const id of 建.ids) 条.量_选中态.push(await 量节点(id, 'A-建完'));
    条.建完后选中数 = 条.量_选中态.filter((m) => m.选中).length;

    // 🔑 判据修正：清掉选中，再量一遍 —— 这才是**真正的「同态」对照**
    条.清零后选中数 = await 清零();
    条.量_静息态 = [];
    for (const id of 建.ids) 条.量_静息态.push(await 量节点(id, 'B-清零后'));

    条.同态比对 = 同态比对(条.量_静息态);
    // 🔴 自身 bug（a 轮第一版）：两态差异原先比的是 `量_静息态[0]` 与 `量_选中态[0]` ——
    //    **同一下标 0**，而它两遍都是**非选中**（选中的是下标 2）
    //    ⇒ 「选中态独有元素 = []」是**无效结论**。
    // ✅ 改法：**按同一下标**逐节点比对 A/B 两遍 —— 那个节点在 A 里选中了、在 B 里没选中，
    //    两态差异就落在**它自己身上**。
    条.两态差异 = (() => {
      const 出 = [];
      条.量_选中态.forEach((a, k) => {
        const b = 条.量_静息态[k];
        if (!a || !b || !a.元素 || !b.元素) { 出.push({ 下标: k, __err: 'no-elements' }); return; }
        const ka = Object.keys(a.元素), kb = Object.keys(b.元素);
        出.push({
          下标: k, A选中: a.选中, B选中: b.选中,
          只在建完态出现: ka.filter((x) => !kb.includes(x)),
          只在清零后出现: kb.filter((x) => !ka.includes(x)),
          共有但尺寸变: ka.filter((x) => kb.includes(x) && JSON.stringify(a.元素[x].屏上) !== JSON.stringify(b.元素[x].屏上))
            .map((x) => ({ 元素: x, 建完: a.元素[x].屏上, 清零后: b.元素[x].屏上 })),
        });
      });
      return 出;
    })();
    条.节点变量 = 条.量_静息态.map((m) => m.变量);
    条.节点屏上 = 条.量_静息态.map((m) => m.节点屏上);
    条.节点css = 条.量_静息态.map((m) => m.节点css);

    条.删除 = [];
    for (const id of 建.ids) 条.删除.push(await 删一个(id));
    rec.族.push(条);
    await setZoom(p, 60); await p.waitForTimeout(800); await 清零();
    落盘(); // 🔑 每族落盘一次（批次 148 教训）
  }

  // ============ 第二部分：Q4 —— **文本族在 60% / 40% / 80% 三档缩放下** ============
  rec.缩放档 = { 族: '文本', 档: [] };
  {
    const 建 = await 建N个(p, '文本', 3, null, (await idsOf(p)).length);
    rec.缩放档.ids = 建.ids;
    rec.缩放档.护栏全过 = 建.护栏.every((h) => h.通过);
    if (建.ids && 建.ids.length) {
      for (const pct of 缩放档) {
        await setZoom(p, pct); await p.waitForTimeout(1400); await settle(p, R);
        await 清零();
        const 条 = { 设: pct, aria: await R.zoom(), 实测scale: await 实测scale(), 量: [] };
        for (const id of 建.ids) 条.量.push(await 量节点(id, 'zoom' + pct));
        条.三节点是否全同 = (() => {
          const 键 = [...new Set(条.量.flatMap((m) => Object.keys(m.元素 || {})))];
          return 键.map((k) => ({ 元素: k, 屏上: 条.量.map((m) => m.元素[k] && m.元素[k].屏上), css: 条.量.map((m) => m.元素[k] && m.元素[k].css),
            是否全同: new Set(条.量.map((m) => JSON.stringify(m.元素[k] && m.元素[k].屏上))).size === 1 }));
        })();
        rec.缩放档.档.push(条);
        落盘();
      }
      await setZoom(p, 60); await p.waitForTimeout(900); await 清零();
      for (const id of 建.ids) rec.缩放档.删除 = (rec.缩放档.删除 || []).concat([await 删一个(id)]);
    }
    await setZoom(p, 60); await p.waitForTimeout(800);
  }
  rec.缩放档.缩放档计划 = 缩放档;
  落盘();

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
  残留自建: (await idsOf(p)).filter((x) => (rec.族 || []).some((q) => (q.ids || []).includes(x)) || ((rec.缩放档 || {}).ids || []).includes(x)) };

// ---- 出表 ----
console.log('=== Q1/Q2：同态（清零后，三个节点全静息）内哪些元素不一致 ===');
for (const q of (rec.族 || [])) {
  const cs = (q.实测scale || 0);
  console.log('\n【' + q.族 + '】缩放', q.缩放建后, '| 实测', cs, '| 护栏', q.护栏全过,
    '| 建完后选中数', q.建完后选中数, '| 清零后选中数', q.清零后选中数);
  console.log('   节点屏上', JSON.stringify(q.节点屏上), ' 节点 css', JSON.stringify(q.节点css));
  console.log('   counter-scale', JSON.stringify((q.节点变量 || []).map((v) => v && v['--octo-canvas-node-chrome-counter-scale'])));
  for (const bb of ((q.同态比对 || {}).比对 || []))
    if (!bb.静息态是否全同) console.log('   🔴 静息态不一致', bb.元素, JSON.stringify(bb.静息态屏上), '文字', JSON.stringify(bb.文字));
  console.log('   选中态独有元素', JSON.stringify((q.两态差异 || []).filter((x) => (x.只在建完态出现 || []).length).map((x) => [x.下标, x.只在建完态出现])));
  console.log('   两态共有但尺寸变:', JSON.stringify((q.两态差异 || []).flatMap((x) => (x.共有但尺寸变 || []).map((y) => [x.下标, y.元素, y.建完, y.清零后]))));
  console.log('   删除:', JSON.stringify((q.删除 || []).map((d) => d.消失 || d.__err)));
}
console.log('\n=== Q4：文本族三档缩放 ===');
for (const d of ((rec.缩放档 || {}).档 || [])) {
  console.log('\n设 ' + d.设 + '% | aria ' + d.aria + ' | 实测 ' + d.实测scale);
  for (const bb of (d.三节点是否全同 || []))
    console.log('   ', bb.是否全同 ? '✅全同' : '🔴不一致', bb.元素, '屏上', JSON.stringify(bb.屏上), 'css', JSON.stringify(bb.css));
}
console.log('\n收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');

断言('① 四族都建了 3 个并全部删除', (rec.族 || []).length === 4 && rec.族.every((q) => (q.删除 || []).length === 3), (rec.族 || []).map((q) => [q.族, (q.删除 || []).length]));
断言('② 每族的建-删护栏全过', (rec.族 || []).every((q) => q.护栏全过 === true), (rec.族 || []).map((q) => [q.族, q.护栏全过]));
断言('③ 每个删除的消失集合**恰好是 {SELF}**', (rec.族 || []).every((q) => (q.删除 || []).every((d) => d.消失 && d.消失.length === 1)), (rec.族 || []).map((q) => (q.删除 || []).map((d) => d.消失 || d.__err)));
// 🔑 修正后的判据：**同态**且**三个节点全非选中**时，才谈「同族内不一致」
const 真不一致 = (rec.族 || []).flatMap((q) => ((q.同态比对 || {}).比对 || [])
  .filter((bb) => !bb.静息态是否全同).map((bb) => ({ 族: q.族, 元素: bb.元素, 各: bb.静息态屏上, 文字: bb.文字 })));
rec.同态真不一致 = 真不一致;
断言('④ 清零后三个节点**全部非选中**（否则同态对照不成立）', (rec.族 || []).every((q) => q.清零后选中数 === 0), (rec.族 || []).map((q) => [q.族, q.清零后选中数]));
断言('⑤ 🔑 修正后判据：**同态内**是否存在屏上尺寸不一致的元素', 真不一致.length > 0, { 条数: 真不一致.length, 明细: 真不一致 });
if (rec.收尾检查 && rec.收尾检查.位移节点) 断言('⑥ 终态节点数回到基线、其余节点零位移', rec.收尾检查.位移节点.length === 0, rec.收尾检查);

rec.断言全过 = 断言过; 落盘();
await b.close();
