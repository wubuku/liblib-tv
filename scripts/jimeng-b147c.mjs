// 批次 147 c 轮 —— 收两个尾巴：
//   Q1 那枚「展开音频生成器」**到底是不是空操作**（b 轮点了两轮读数逐字不变，
//      但「读不到变化」与「点击没生效」是两件事，必须分开）
//   Q2 它**是不是音频专有**（其他节点类型有没有自己的 `展开…生成器`）
//   Q3 `[data-testid="node-toolbar"]` 那个 **192×0 的空壳实例**是否恒在
//
// ⚠️ 只碰这枚 toggle（aria 逐字含「展开」、**不是**生成/扣费按钮），不碰面板里的「生成」。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 147, 轮: 'c', 目的: 'toggle 是不是空操作 / 是否音频专有 / 空壳实例是否恒在' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };

/** 面板的「形状指纹」：只取可比较的结构字段，够判断有没有变化。 */
const 面板指纹 = () => p.evaluate(() => {
  const t = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'));
  return t.map((e, i) => { const r = e.getBoundingClientRect();
    const btn = Array.from(e.querySelectorAll('button,[role=button]'));
    return { i, 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10],
      按钮数: btn.length, svg数: e.querySelectorAll('svg').length,
      aria表: btn.map((b) => b.getAttribute('aria-label')),
      盒表: btn.map((b) => { const q = b.getBoundingClientRect(); return [Math.round(q.x), Math.round(q.y), Math.round(q.width * 10) / 10, Math.round(q.height * 10) / 10]; }),
      innerText长: (e.innerText || '').length, html长: e.innerHTML.length,
      可见输入面: e.querySelectorAll('textarea,input,[contenteditable]').length,
      逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 90) }; });
});

/** 全页所有「展开/收起…生成器」类按钮 + 它们的宿主类型。 */
const 搜toggle = () => p.evaluate(() => Array.from(document.querySelectorAll('button,[role=button]'))
  .map((b) => { const r = b.getBoundingClientRect();
    return { aria: b.getAttribute('aria-label'), testid: b.getAttribute('data-testid'),
      盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10],
      在nodeToolbar内: !!b.closest('[data-testid="node-toolbar"]'),
      在节点内: !!(b.closest('.react-flow__node') && b.closest('.react-flow__node') !== b.closest('[data-testid="node-toolbar"]')),
      逐字: (b.innerText || '').trim() }; })
  .filter((q) => /展开|收起|折叠|生成器/.test(q.aria || '')));

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

const 选一个 = async (id) => {
  await 清零();
  for (let k = 0; k < 3 && (await R.overlays()) > 0; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
  const 落 = await 可点落点(p, `.react-flow__node[data-id="${id}"]`, 4, 4);
  if (落.__err) return { __err: 'no-point:' + 落.__err };
  const 归属 = await p.evaluate(([x, y, i]) => { const h = document.elementFromPoint(x, y);
    const n = h && h.closest('.react-flow__node');
    return { 命中: n ? n.getAttribute('data-id') : null, 对: !!(n && n.getAttribute('data-id') === i),
      是按钮: !!(h && (h.tagName === 'BUTTON' || h.closest('button,[role=button]'))) }; }, [落.x, 落.y, id]);
  if (!归属.对 || 归属.是按钮) return { __err: 'bad-landing', 归属 };
  await p.mouse.click(落.x, 落.y); await p.waitForTimeout(2400); await settle(p, R);
  return { 落, 归属 };
};

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p); await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(), 积分: await R.credits() };

  // 按 testid 前缀给所有节点分类，再各自找「有独占像素」的代表
  rec.分类 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const t = Array.from(n.querySelectorAll('[data-testid]')).map((q) => q.getAttribute('data-testid'));
    const 组 = t.find((x) => /^(audio|video|image|text|timeline|subject|director)/.test(x || '')) || '?';
    const r = n.getBoundingClientRect(); let 好 = 0;
    for (let y = Math.ceil(r.y) + 4; y <= r.y + r.height - 4; y += 4)
      for (let x = Math.ceil(r.x) + 4; x <= r.x + r.width - 4; x += 4) {
        if (x < 1 || y < 1 || x >= innerWidth || y >= innerHeight) continue;
        const h = document.elementFromPoint(x, y); if (h && (h === n || n.contains(h))) 好++; }
    return { id: n.getAttribute('data-id'), 族: 组.split('-')[0], 首个testid: 组, 独占像素: 好,
      aria: (n.getAttribute('aria-label') || '').slice(0, 22) };
  }));
  rec.族分布 = rec.分类.reduce((m, q) => { m[q.族] = (m[q.族] || 0) + 1; return m; }, {});
  rec.可点族 = rec.分类.filter((q) => q.独占像素 > 0).reduce((m, q) => { m[q.族] = (m[q.族] || 0) + 1; return m; }, {});

  // ============ 逐族普查：每族取独占像素最多的一个 ============
  rec.逐族 = [];
  const 族列表 = [...new Set(rec.分类.map((q) => q.族))].filter((f) => f !== '?');
  for (const 族 of 族列表) {
    const 候选 = rec.分类.filter((q) => q.族 === 族 && q.独占像素 > 0).sort((a, b2) => b2.独占像素 - a.独占像素);
    if (!候选.length) { rec.逐族.push({ 族, __err: '无可点节点' }); continue; }
    const t = 候选[0];
    const 选 = await 选一个(t.id);
    if (选.__err) { rec.逐族.push({ 族, id: t.id, __err: 选.__err }); continue; }
    rec.逐族.push({ 族, id: t.id, aria: t.aria, 独占像素: t.独占像素,
      工具条实例: (await 面板指纹()).map((q) => ({ i: q.i, 盒: q.盒, 按钮数: q.按钮数, svg数: q.svg数 })),
      toggle: await 搜toggle() });
  }

  // ============ Q1：toggle 是不是空操作 ============
  // 🔴 c 轮第一版把 Q1 放在族循环**之后**，结果族循环最后选中的是**图片**节点，
  //    音频面板早已消失 ⇒ `Q1安全` 读成 `gone`、Q1 整段没跑。
  //    改法：**重新选一次音频节点**再测，并把「重新选中」这件事本身记进证据。
  const 音频候选 = rec.分类.filter((q) => q.族 === 'audio' && q.独占像素 > 0).sort((a, b2) => b2.独占像素 - a.独占像素)[0];
  rec.Q1重选 = 音频候选 ? { id: 音频候选.id, 独占像素: 音频候选.独占像素 } : null;
  let 重选 = null;
  if (音频候选) {
    重选 = await 选一个(音频候选.id);
    rec.Q1重选结果 = 重选.__err ? 重选 : { 落: 重选.落, 命中: 重选.归属.命中 };
    if (!重选.__err) rec.Q1选中后toggle = await 搜toggle();
  }
  if (重选 && !重选.__err) {
    const 安全 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('button,[role=button]')).find((b) => b.getAttribute('aria-label') === '展开音频生成器');
      if (!e) return { __err: 'gone' };
      const a = e.getAttribute('aria-label');
      const r = e.getBoundingClientRect();
      return { tag: e.tagName, 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        含展开: /展开/.test(a), 含生成: /生成/.test(a),
        是生成类: /生成/.test(a) && !/展开|收起|折叠/.test(a),
        在视口内: r.x >= 0 && r.y >= 0 && r.x + r.width <= innerWidth && r.y + r.height <= innerHeight };
    });
    rec.Q1安全 = 安全;
    if (安全 && !安全.__err && 安全.tag === 'BUTTON' && !安全.是生成类 && 安全.在视口内) {
      rec.Q1 = { 前: await 面板指纹() };
      // ① 真实鼠标点击面板正中（走真实输入路径）
      await p.mouse.click(安全.盒[0] + 20, 安全.盒[1] + 20);
      await p.waitForTimeout(2200); await settle(p, R);
      rec.Q1.鼠标点击后 = await 面板指纹();
      // ② 再来一次 JS click（绕过坐标，排除「鼠标没点中」这个替代解释）
      await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button,[role=button]'))
        .find((b) => b.getAttribute('aria-label') === '展开音频生成器'); if (e) e.click(); });
      await p.waitForTimeout(2200); await settle(p, R);
      rec.Q1.JS点击后 = await 面板指纹();
      // ③ 再点两次鼠标，看有没有「两次才生效」的可能
      await p.mouse.click(安全.盒[0] + 20, 安全.盒[1] + 20); await p.waitForTimeout(1500);
      await p.mouse.click(安全.盒[0] + 20, 安全.盒[1] + 20); await p.waitForTimeout(2200); await settle(p, R);
      rec.Q1.再点两次后 = await 面板指纹();
    }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); }

await 清零();
for (let k = 0; k < 3 && (await R.overlays()) > 0; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p),
  浮层: await R.overlays(), zoom: await R.zoom(), 积分: await R.credits(),
  边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length) };

console.log('族分布', JSON.stringify(rec.族分布), '| 可点族', JSON.stringify(rec.可点族));
console.log('逐族:', JSON.stringify(rec.逐族, null, 1));
if (rec.Q1) {
  const 键 = (x) => JSON.stringify(x.map((q) => [q.盒, q.按钮数, q.svg数, q.可见输入面, q.aria表]));
  console.log('Q1 前     ', 键(rec.Q1.前));
  console.log('Q1 鼠标后 ', 键(rec.Q1.鼠标点击后));
  console.log('Q1 JS后   ', 键(rec.Q1.JS点击后));
  console.log('Q1 再点后 ', 键(rec.Q1.再点两次后));
}
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');

// ⚠️ **可点性本身就是本轮的一条发现**：76 个节点里**只有 audio（17 个有独占像素）与 image（1 个）能取样**，
//    text / video / timeline / director 四个族**全部被别的节点压住、0 个独占采样点**
//    ⇒ 「toggle 是不是音频专有」这一问**只对 image 做了对照**，不是全族普查。如实标注。
断言('① 至少普查了 2 个节点族（实测只有 audio/image 有可点像素）', rec.逐族.filter((q) => !q.__err).length >= 2, { 实到: rec.逐族.filter((q) => !q.__err).length });
断言('⑥ 被压住因而**取不到样**的族，如实记下来（不假装普查过）',
  rec.逐族.filter((q) => q.__err === '无可点节点').map((q) => q.族).join(',') === 'video,text,timeline,director',
  rec.逐族.filter((q) => q.__err).map((q) => [q.族, q.__err]));
if (rec.Q1) {
  const 键 = (x) => JSON.stringify(x.map((q) => [q.盒, q.按钮数, q.svg数, q.可见输入面, q.aria表]));
  const 变 = (a, b) => 键(a) !== 键(b);
  断言('② 真实鼠标点击后面板**读不到任何变化**', !变(rec.Q1.前, rec.Q1.鼠标点击后), { 前: 键(rec.Q1.前), 后: 键(rec.Q1.鼠标点击后) });
  断言('③ JS click 后面板**仍读不到任何变化**（⇒ 排除「鼠标没点中」）', !变(rec.Q1.前, rec.Q1.JS点击后), { 后: 键(rec.Q1.JS点击后) });
  断言('④ 连点两次后仍**读不到任何变化**（⇒ 排除「要点两次」）', !变(rec.Q1.前, rec.Q1.再点两次后), { 后: 键(rec.Q1.再点两次后) });
}
const 非音频有toggle = rec.逐族.filter((q) => q.族 !== 'audio' && !q.__err && (q.toggle || []).length);
rec.非音频有toggle = 非音频有toggle.map((q) => [q.族, q.toggle.length]);
断言('⑤ 除音频外的族**都没有**「展开…生成器」类按钮', 非音频有toggle.length === 0, rec.非音频有toggle);
rec.断言全过 = 断言过;
fs.writeFileSync(new URL('./_tmp-b147c.json', import.meta.url), JSON.stringify(rec, null, 1));
await b.close();
