// 批次 148 b 轮 —— 钉死三件事（a 轮留下的）：
//   Q1 **三个生成表单的 testid**：`audio-generation-form` 到底存不存在？
//       （批次 137 那张对照表写音频 testid = `audio-generation-form`，
//        但 a 轮的祖先链里音频表单那层只有 **class** `generation-input-panel-shell`，
//        其 testid 宿主是 `node-toolbar-feature-host` —— 需要一次穷举定案。）
//   Q2 **三族按钮数统一口径后的真值**：a 轮实测 7 / 9 / 10，而批次 137 的表写 7 / 8 / 9。
//       怀疑那张表**三行口径不一致**（图片含序 0 钮、视频不含）—— 逐族出按钮全表即可判定。
//   Q3 每个 `node-toolbar` 子树里**全部** `[data-testid]` 的穷举清单
//       （批次 144 对文本全屏编辑器做过同一件事，结论是「只有 4 个」，这里照做）
//
// ⚠️ 仍走**建-删护栏**，不按生成/扣费按钮、不输入一个字。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard, setZoom } from './jimeng-b135-lib.mjs';
import { 建N个, selCount, idsOf, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 148, 轮: 'b', 目的: '三族表单 testid 穷举 + 按钮数统一口径' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };

/** 把 `node-toolbar` 子树里每个 testid 穷举出来，并给出宿主链。 */
const 穷举testid = () => p.evaluate(() => {
  const 实例 = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'));
  return 实例.map((t, i) => {
    const r = t.getBoundingClientRect();
    const 全 = Array.from(t.querySelectorAll('[data-testid]'));
    const 计数 = {};
    for (const e of 全) { const v = e.getAttribute('data-testid'); 计数[v] = (计数[v] || 0) + 1; }
    // 直接子层：逐个 class/testid/盒
    const 直接子 = Array.from(t.children).map((c) => { const q = c.getBoundingClientRect();
      return { tag: c.tagName, cls: String(c.getAttribute('class') || '').slice(0, 60), testid: c.getAttribute('data-testid'),
        盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width * 10) / 10, Math.round(q.height * 10) / 10] }; });
    // 全页是否存在这些候选 testid（不管在不在工具条里）
    const 候选 = ['generation-form', 'video-generation-form', 'audio-generation-form', 'image-generation-form',
      'node-toolbar-feature-host', 'generation-input-panel-shell', 'audio-node-uploading'];
    const 候选计数 = Object.fromEntries(候选.map((c) => [c, document.querySelectorAll('[data-testid="' + c + '"]').length]));
    return { i, 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10],
      有面积: r.width > 0.01 && r.height > 0.01,
      testid种类: Object.keys(计数).length, 计数, 直接子, 候选计数 };
  });
});

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
    const n = h && h.closest('.react-flow__node');
    return { 对: !!(n && n.getAttribute('data-id') === i) }; }, [落.x, 落.y, id]);
  if (!归属.对) return { id, __err: 'wrong-target' };
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

const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b148b.json', import.meta.url), JSON.stringify(rec, null, 1));
const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p); await settle(p, R);
  await setZoom(p, 60); await p.waitForTimeout(900);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(), 积分: await R.credits() };

  rec.族 = [];
  for (const 族 of ['图片', '视频', '音频']) {
    const 条 = { 族 };
    try {
      const 建 = await 建N个(p, 族, 1, null, (await idsOf(p)).length);
      条.护栏全过 = 建.护栏.every((h) => h.通过);
      if (!建.ids || !建.ids.length) { 条.__err = '建节点未成'; rec.族.push(条); 落盘(); continue; }
      const SELF = 建.ids[0]; 条.SELF = SELF;
      await p.waitForTimeout(1800); await settle(p, R);
      条.缩放 = await R.zoom();
      条.实例 = await 穷举testid();
      // 按钮全表（统一口径：取有面积的那个实例，按 DOM 顺序）
      条.按钮全表 = await p.evaluate(() => {
        const t = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).find((e) => { const r = e.getBoundingClientRect(); return r.width > 0.01 && r.height > 0.01; });
        if (!t) return null;
        return Array.from(t.querySelectorAll('button,[role=button]')).map((b, k) => ({ 序: k,
          aria: b.getAttribute('aria-label'), ariaDisabled: b.getAttribute('aria-disabled'),
          盒: (() => { const q = b.getBoundingClientRect(); return [Math.round(q.x), Math.round(q.y), Math.round(q.width * 10) / 10, Math.round(q.height * 10) / 10]; })() }));
      });
      条.删除 = await 删一个(SELF);
    } catch (e) { 条.__err = String((e && e.message) || e).slice(0, 300); }
    await setZoom(p, 60); await p.waitForTimeout(800); await 清零();
    rec.族.push(条); 落盘();
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); }

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
  浮层: await R.overlays(), zoom: await R.zoom(), 积分: await R.credits(),
  边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length) };
rec.断言全过 = 断言过; 落盘();
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');
await b.close();
