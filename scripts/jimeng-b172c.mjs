// 批次 172 c 轮：攻「生成尺寸面板」`max-w-canvas-generation-size-panel-viewport`。
//
// 🔴 b 轮的两个失误：
//   ① 建的是**文本**节点 ⇒ 生成面板**不自动展开**（批次 134 的结论是**图片**节点才自动弹表单）
//      ⇒ 文本节点的生成面板要么是「空节点」态才有，要么根本没这个态。
//   ② 清理时**按标题猜**该删哪个，结果删错了对象（删了原有的「文本 1」，留下新建的「文本 4」）。
//      ⇒ 清理**必须按 node id 认人**，删完再按 id 验一次「它不在了」。
//      （已用 ⌘Z 找回「文本 1」，画布复原到 76 节点、文本 1/2/3 的 id 与本批最初普查一致。）
//
// 本轮先试**已有的图片节点**（`b22-upload`，带 IMG 317px）能否唤出生成面板 —— 不行再按批次 134 建一个。
// ⛔ 只打开下拉看尺寸，不点任何选项、不点生成。
import fs from 'node:fs';
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const DIR = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url).pathname;
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '172c' };

const pin = async (w, h) => {
  await p.context().newCDPSession(p).then(async (s) => {
    await s.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
  });
  await p.waitForTimeout(600);
  const vp = await p.evaluate(() => [innerWidth, innerHeight]);
  if (vp[0] !== w || vp[1] !== h) throw new Error(`钉视口失败 ${JSON.stringify(vp)}`);
};

const 扫描 = () => p.evaluate(() => {
  const C = ['max-w-canvas-generation-size-panel-viewport', 'max-w-canvas-mask-operation-status'];
  const out = {};
  for (const c of C) {
    const live = Array.from(document.querySelectorAll('.' + c))
      .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 || r.height > 0; });
    out[c] = live.map((e) => {
      const cs = getComputedStyle(e), r = e.getBoundingClientRect();
      return { testid: e.getAttribute('data-testid'), role: e.getAttribute('role'), aria: e.getAttribute('aria-label'),
        盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        布局: [e.offsetWidth, e.offsetHeight], scrollW: e.scrollWidth, clientW: e.clientWidth,
        class: e.getAttribute('class'), style: e.getAttribute('style'),
        computed: { w: cs.width, h: cs.height, maxW: cs.maxWidth, maxH: cs.maxHeight, ovfX: cs.overflowX },
        文字: (e.innerText || '').trim().split('\n').filter(Boolean).slice(0, 18),
        直接子: Array.from(e.children).map((k) => { const kr = k.getBoundingClientRect();
          return { tag: k.tagName, role: k.getAttribute('role'), aria: k.getAttribute('aria-label'),
            盒: [Math.round(kr.width), Math.round(kr.height)] }; }) };
    });
  }
  return out;
});

const 找下拉 = () => p.evaluate(() => {
  const out = [];
  for (const e of document.querySelectorAll('button,[role=button],[role=combobox],[role=listbox]')) {
    const r = e.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) continue;
    const a = e.getAttribute('aria-label') || (e.innerText || '').trim().split('\n').slice(0, 2).join('⏎');
    if (/比例|分辨率|尺寸|数量|模型|options/i.test(a)) {
      out.push({ a: a.slice(0, 40), testid: e.getAttribute('data-testid'), role: e.getAttribute('role'),
        盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        pt: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] });
    }
  }
  return out;
});

// ① 试已有图片节点
rec.基线 = { status: await R.status(), credits: await R.credits() };
console.log('基线:', JSON.stringify(rec.基线));
const imgId = await p.evaluate(() => {
  const n = document.querySelector('.react-flow__node-image');
  if (!n) return null;
  n.scrollIntoView({ block: 'center', inline: 'center' });
  return n.getAttribute('data-id');
});
await p.waitForTimeout(800);
const imgPt = await p.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  const r = n.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
}, imgId);
console.log('图片节点:', imgId, imgPt);
await p.mouse.click(imgPt[0], imgPt[1]);
await p.waitForTimeout(2000);
rec.点图片后 = { sel: await R.selCount(), 面板: await 扫描(), 下拉: await 找下拉() };
console.log('点图片节点后 → 下拉:', JSON.stringify(rec.点图片后.下拉));
console.log('  视口类:', JSON.stringify(Object.fromEntries(Object.entries(rec.点图片后.面板).map(([k, v]) => [k, v.length]))));

// ② 逐个点下拉
let 命中 = null;
for (const d of rec.点图片后.下拉) {
  await p.mouse.click(d.pt[0], d.pt[1]);
  await p.waitForTimeout(1100);
  const s = await 扫描();
  const k = Object.keys(s).find((c) => s[c].length);
  if (k) { 命中 = { 入口: d, 类: k, 读数: s[k][0] }; console.log(`\n点「${d.a}」→ 命中 ${k}`); break; }
  await p.keyboard.press('Escape'); await p.waitForTimeout(300);
}

if (!命中) {
  console.log('\n❌ 图片节点也开不出尺寸面板；按批次 134 建一个图片节点再试');
  await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  const 图钮 = await p.evaluate(() => {
    const e = Array.from(document.querySelectorAll('button,[role=button]'))
      .find((x) => (x.getAttribute('aria-label') || '') === '图片' && !x.closest('.react-flow__node'));
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  });
  console.log('左栏「图片」:', JSON.stringify(图钮));
  rec.新建图片节点 = { 按钮: 图钮, 前节点数: Number((await R.status()).match(/(\d+) nodes/)[1]) };
  if (图钮) {
    await p.mouse.click(图钮[0], 图钮[1]);
    await p.waitForTimeout(3500);
    const dl = await 找下拉();
    rec.新建图片节点.下拉 = dl;
    console.log('建图片节点后 → 下拉:', JSON.stringify(dl));
    console.log('  视口类:', JSON.stringify(Object.fromEntries(Object.entries(await 扫描()).map(([k, v]) => [k, v.length]))));
    for (const d of dl) {
      await p.mouse.click(d.pt[0], d.pt[1]);
      await p.waitForTimeout(1100);
      const s = await 扫描();
      const k = Object.keys(s).find((c) => s[c].length);
      if (k) { 命中 = { 入口: d, 类: k, 读数: s[k][0] }; console.log(`\n点「${d.a}」→ 命中 ${k}`); break; }
      await p.keyboard.press('Escape'); await p.waitForTimeout(300);
    }
  }
}

if (命中) {
  rec.命中 = 命中;
  console.log(JSON.stringify(命中.读数, null, 1));
  const hl = await p.evaluate((c) => {
    document.querySelectorAll('.__b172hl').forEach((e) => e.remove());
    const e = document.querySelector('.' + c);
    if (!e) return { 失败: '不在 DOM' };
    const r = e.getBoundingClientRect();
    const d = document.createElement('div');
    d.className = '__b172hl';
    d.style.cssText = `position:fixed;left:${r.x - 4}px;top:${r.y - 4}px;width:${r.width + 8}px;height:${r.height + 8}px;` +
      `border:3px solid #ff8c00;border-radius:12px;pointer-events:none;z-index:2147483646`;
    document.body.appendChild(d);
    return { 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  }, 命中.类);
  console.log('高亮框:', JSON.stringify(hl));
  if (!hl.失败) {
    await p.waitForTimeout(300);
    await p.screenshot({ path: DIR + '135-generation-size-panel-viewport.png' });
    rec.图 = 'screenshots/135-generation-size-panel-viewport.png';
  }
  // 立规 43：只改视口
  console.log('\n--- 只改视口（立规 43）---');
  rec.档位 = [];
  for (const [w, h] of [[1280, 720], [900, 720], [600, 720], [400, 720], [300, 720], [1280, 400], [1280, 300]]) {
    await pin(w, h);
    const s = await 扫描();
    const arr = s[命中.类];
    if (!arr.length) { rec.档位.push({ 视口: [w, h], 还在: false }); console.log(`  ${w}×${h}: 面板没了`); continue; }
    const x = arr[0];
    rec.档位.push({ 视口: [w, h], 盒: x.盒, 布局: x.布局, computed: x.computed, scrollW: x.scrollW, clientW: x.clientW });
    console.log(`  ${w}×${h}: ${x.盒[2]}×${x.盒[3]}  布局 ${x.布局[0]}×${x.布局[1]}  maxW=${x.computed.maxW}  scrollW=${x.scrollW}/client=${x.clientW}`);
  }
  await pinViewport(p);
  console.log('视口已复原:', JSON.stringify(await pinViewport(p)));
}
await p.evaluate(() => document.querySelectorAll('.__b172hl').forEach((e) => e.remove()));
await p.keyboard.press('Escape'); await p.waitForTimeout(500);

// ③ 清理：若本批建过图片节点，**按 id** 删掉并验明
const snap = () => p.evaluate(() => ({
  节点数: document.querySelectorAll('.react-flow__node').length,
  图片: Array.from(document.querySelectorAll('.react-flow__node-image')).map((n) => n.getAttribute('data-id')),
}));
const s1 = await snap();
rec.清理前 = s1;
if (s1.图片.length > 1) {
  const 新 = s1.图片[s1.图片.length - 1];
  rec.要删的id = 新;
  await p.evaluate((id) => document.querySelector(`.react-flow__node[data-id="${id}"]`).scrollIntoView({ block: 'center', inline: 'center' }), 新);
  await p.waitForTimeout(800);
  const pt = await p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 新);
  await p.keyboard.press('Escape'); await p.waitForTimeout(300);
  await p.mouse.click(pt[0], pt[1], { button: 'right' });
  await p.waitForTimeout(1000);
  const d = await p.evaluate(() => {
    const e = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"] [role=menuitem]'))
      .find((x) => (x.innerText || '').trim().startsWith('删除'));
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  });
  if (d) { await p.mouse.click(d[0], d[1]); await p.waitForTimeout(2000); }
  const s2 = await snap();
  rec.清理后 = { ...s2, 目标还在: s2.图片.includes(新), status: await R.status() };
  console.log('清理:', JSON.stringify(rec.清理后));
} else {
  rec.清理后 = { 说明: '没建过图片节点', status: await R.status() };
}
await p.keyboard.press('Escape'); await p.waitForTimeout(400);
const bp = await p.evaluate(() => {
  for (let y = 30; y < innerHeight - 30; y += 10)
    for (let x = 30; x < innerWidth - 30; x += 10) {
      const e = document.elementFromPoint(x, y);
      if (e && e.closest('.react-flow__pane') && !e.closest('.react-flow__node')) return [x, y];
    }
  return null;
});
if (bp) { await p.mouse.click(bp[0], bp[1]); await p.waitForTimeout(500); }
await p.keyboard.press('Escape'); await p.waitForTimeout(300);
rec.收尾 = { status: await R.status(), sel: await R.selCount(), credits: await R.credits() };
console.log('收尾:', JSON.stringify(rec.收尾));
fs.writeFileSync(new URL('./_tmp-b172c.json', import.meta.url), JSON.stringify(rec, null, 1));
await b.close();
