// 批次 202 a 轮：🔴 换无头之后，**先验读数没变**，再继续工作。
//
// 背景：批次 197~200 的全部读数都取自一个**有头**实例（进程命令行没有 --headless）。
//   批次 201 换成无头（`scripts/jimeng-headless.mjs`）之后，**这些读数还成立吗？**
//   ⇒ 布局理论上与 headless 无关（同一个 Chromium、同一份页面），但**必须实测**，
//      而且要拿**可逐字比对的量**去比，不是「看起来差不多」。
//
// 📌 挑的对比项（每一条都是前几批写进手册的**逐字契约**）：
//   ① 画布初始平移与缩放        —— 批次 199：12 档逐字 `translate(97.1509px, -30.4641px) scale(0.260267)`
//   ② 搜索面板的 dialog 几何      —— 批次 52/86/102/196：`801×620@240,50`
//   ③ 资产库的空态文案 + 几何     —— 批次 196：四个二级页签的空态逐字
//   ④ 文本节点选中态的工具条 testid —— 批次 194：`node-toolbar`，编辑态 `text-editor-toolbar`
//   ⑤ 取景后的 tx/ty            —— 批次 198/200：`tx = 宽/2 − 1138.064`；`ty` 分两支
//   ⑥ pinViewport 后的视口与 dpr
//
// 🔴 只读，不新建/删除任何节点、不点任何会扣费的动作。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b202a', 目的: '验证无头与有头的读数逐字一致' };

// ① 视口 + 初始平移
out['①视口与初始平移'] = await p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  return { 视口: [innerWidth, innerHeight, devicePixelRatio],
    vpTransform原文: vp ? vp.style.transform : null,
    dpr: devicePixelRatio, ua: navigator.userAgent.slice(0, 60) };
});
log('① 视口与初始平移：', JSON.stringify(out['①视口与初始平移']));

await settle(p, R);
await setZoom(p, 50);

// ② 搜索面板 dialog 几何
const 搜索钮 = await p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
    || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
  if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
if (搜索钮) {
  await p.mouse.click(搜索钮[0], 搜索钮[1]); await p.waitForTimeout(1600);
  out['②搜索面板'] = await p.evaluate(() => {
    const d = document.querySelector('[data-testid="canvas-search-panel"],[role="dialog"]');
    const e = d || document.querySelector('[data-testid^="canvas-search"]');
    if (!e) return { 找到: false };
    const r = e.getBoundingClientRect();
    return { 找到: true, testid: e.getAttribute('data-testid'), 屏上: [r.x, r.y, r.width, r.height].map(Math.round),
      结果行数: document.querySelectorAll('[data-testid^="canvas-search-result-node_"]').length,
      第一个结果testid: (document.querySelector('[data-testid^="canvas-search-result-node_"]') || { getAttribute: () => null }).getAttribute('data-testid') };
  });
  log('② 搜索面板：', JSON.stringify(out['②搜索面板']));
} else out['②搜索面板'] = { 找到: false, 说明: '找不到搜索钮' };
await p.keyboard.press('Escape'); await p.waitForTimeout(1200);

// ③ 资产库 dialog 几何 + 空态
const 资产钮 = await p.evaluate(() => {
  const e = Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '资产库' && x.getBoundingClientRect().width > 0);
  if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
if (资产钮) {
  await p.mouse.click(资产钮[0], 资产钮[1]); await p.waitForTimeout(2000);
  out['③资产库'] = await p.evaluate(() => {
    const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
    if (!d) return { 在: false };
    const r = d.getBoundingClientRect();
    return { 在: true, 屏上: [r.x, r.y, r.width, r.height].map(Math.round), 文本: d.innerText.replace(/\s+/g, ' ').trim().slice(0, 160) };
  });
  log('③ 资产库：', JSON.stringify(out['③资产库']));
} else out['③资产库'] = { 在: false };
await p.keyboard.press('Escape'); await p.waitForTimeout(1200);

// ④ 文本节点选中态 / 编辑态的工具条 testid
const 文本节点 = 'node_5gftn3dnt1';
out['④文本节点工具条'] = await p.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  if (!n) return { 找不到: true };
  const r = n.getBoundingClientRect();
  return { 节点id: id, aria: n.getAttribute('aria-label'), 屏上: [r.x, r.y, r.width, r.height].map(Math.round) };
}, 文本节点);
if (!out['④文本节点工具条'].找不到) {
  const pt = await p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); const r = n.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height * 0.55)]; }, 文本节点);
  await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(1200);
  out['④文本节点工具条'].选中后 = await p.evaluate(() => ({
    nodeToolbar: document.querySelectorAll('[data-testid="node-toolbar"]').length,
    textEditorToolbar: document.querySelectorAll('[data-testid="text-editor-toolbar"]').length,
    选中数: document.querySelectorAll('.react-flow__node.selected').length,
  }));
  log('④ 文本节点选中后：', JSON.stringify(out['④文本节点工具条'].选中后));
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);
}

// ⑤ 取景后的 tx / ty
if (搜索钮) {
  await p.mouse.click(搜索钮[0], 搜索钮[1]); await p.waitForTimeout(1500);
  await p.evaluate(() => { const e = document.querySelector('input[aria-label*="搜索"],input[type="text"]');
    if (e) { Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(e, '');
      e.dispatchEvent(new Event('input', { bubbles: true })); } });
  await p.keyboard.type('音频', { delay: 90 }); await p.waitForTimeout(2200);
  const 行 = await p.evaluate(() => { const e = document.querySelector('[data-testid^="canvas-search-result-node_"]');
    if (!e) return null; const r = e.getBoundingClientRect();
    return { testid: e.getAttribute('data-testid'), 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; });
  out['⑤取景'] = { 点的行: 行 && 行.testid };
  if (行) {
    await p.mouse.click(行.点[0], 行.点[1]);
    const 帧 = [];
    for (let k = 0; k < 6; k++) {
      帧.push(await p.evaluate(() => { const vp = document.querySelector('.react-flow__viewport');
        const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
        return m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null; }));
      await p.waitForTimeout(600);
    }
    out['⑤取景'].vp序列 = 帧;
    out['⑤取景'].tx取值 = [...new Set(帧.map((f) => f && f[0]))];
    out['⑤取景'].ty取值 = [...new Set(帧.map((f) => f && f[1]))];
    out['⑤取景'].scale取值 = [...new Set(帧.map((f) => f && f[2]))];
    log('⑤ 取景 tx 取值：', JSON.stringify(out['⑤取景'].tx取值), '| ty 取值：', JSON.stringify(out['⑤取景'].ty取值), '| scale：', JSON.stringify(out['⑤取景'].scale取值));
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(1000);
}

fs.writeFileSync('/tmp/b202a.json', JSON.stringify(out, null, 1));
out.收尾 = await endState(p, R, 基线);
log('收尾：', JSON.stringify(out.收尾));
await b.close();
