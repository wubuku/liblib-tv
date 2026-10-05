// 批次 198 a 轮：🔴 把「屏幕落点」翻译成「画布平移量」，看 `−166` 与纵向的 `−100` 是不是同一件事。
//
// 批次 197 留下两个尾巴：
//   Q1 纵向读数带小数、同视口两次差半像素（1280×720 读到 258.47 与 258.94）
//   Q2 纵向偏移**跟宽走不跟高走**（1280 宽三档都 −100 上下，≤1200 宽三档都是 0）
//
// 📌 本轮的假设：这两条其实是**同一件事** —— React Flow 的屏幕变换是
//      屏幕坐标 = (画布坐标 − translate) × scale
//   节点画布坐标与视口无关、横向 scale 恒为 0.5，**所以屏幕上的一切差异都来自 `translate`**。
//   若 `translateX` 随视口宽线性变化 ⇒ `−166` 只是 `(宽−332)/2` 在 translate 上的投影。
//
// 🔴 验证方式：每档同时读 **① 落点屏幕坐标 ② .react-flow__viewport 的 transform ③ 节点画布坐标**，
//    然后**机器验算** `屏幕x === (画布x − tx) × s`。验算不过就是读数口径不对，先修口径再谈机制。
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const 搜索词 = '音频';
const 视口集 = [
  { 名: '800x720', w: 800, h: 720 }, { 名: '1000x720', w: 1000, h: 720 },
  { 名: '1200x720', w: 1200, h: 720 }, { 名: '1280x720', w: 1280, h: 720 },
  { 名: '1280x600', w: 1280, h: 600 }, { 名: '1280x840', w: 1280, h: 840 },
  { 名: '1600x900', w: 1600, h: 900 },
];
// 同一个 1280×720 **重复测两次**，专门看那半像素差能不能复现（Q1）
const 视口集2 = [{ 名: '1280x720(重复1)', w: 1280, h: 720 }, { 名: '1280x720(重复2)', w: 1280, h: 720 }];

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b198a', 假设: '屏幕落点的一切差异都来自 .react-flow__viewport 的 translate' };

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const 共享页 = ctx.pages().find((x) => x.url().includes('ai-canvas'));
out.共享页_前 = await 共享页.evaluate(() => [innerWidth, innerHeight, devicePixelRatio]);

// 每档量一次，返回 {transform, 落点, 画布坐标, 验算}
const 量一档 = async (p) => {
  const 搜索钮 = await p.evaluate(() => {
    const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
      || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
    if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (!搜索钮) return { 中止: '找不到搜索钮' };
  await p.mouse.click(搜索钮[0], 搜索钮[1]); await p.waitForTimeout(1400);
  await p.evaluate(() => { const e = document.querySelector('input[aria-label*="搜索"],input[type="text"]');
    if (e) { Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(e, '');
      e.dispatchEvent(new Event('input', { bubbles: true })); } });
  await p.keyboard.type(搜索词, { delay: 90 });
  await p.waitForTimeout(2100);
  const 行数 = await p.evaluate(() => document.querySelectorAll('[data-testid^="canvas-search-result-node_"]').length);
  if (!行数) return { 中止: '没有结果行' };
  const 行 = await p.evaluate(() => { const e = document.querySelector('[data-testid^="canvas-search-result-node_"]');
    const r = e.getBoundingClientRect(); return { id: e.getAttribute('data-testid'), 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; });
  await p.mouse.click(行.点[0], 行.点[1]);

  // 📌 关键：点完**连采 6 帧**（每帧 600ms），看读数是「稳定在一个值」还是「还在动」
  const 帧 = [];
  for (let k = 0; k < 6; k++) {
    帧.push(await p.evaluate((rid) => {
      const id = rid.replace('canvas-search-result-node_', 'node_');
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return { 找不到: true };
      const r = n.getBoundingClientRect();
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      const tr = n.style.transform || '';
      const cm = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(tr);
      return {
        屏上: [r.x, r.y, r.width, r.height].map((q) => Math.round(q * 10000) / 10000),
        中心: [Math.round((r.x + r.width / 2) * 10000) / 10000, Math.round((r.y + r.height / 2) * 10000) / 10000],
        画布坐标: cm ? [Math.round(parseFloat(cm[1]) * 10000) / 10000, Math.round(parseFloat(cm[2]) * 10000) / 10000] : null,
        vpTransform原文: vp ? vp.style.transform : null,
        vp平移缩放: m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null,
      };
    }, 行.id));
    await p.waitForTimeout(600);
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(600);
  return { 结果行: 行.id, 帧 };
};

const 跑 = async (集) => {
  const 表 = {};
  for (const v of 集) {
    const p = await ctx.newPage();
    try {
      await p.setViewportSize({ width: v.w, height: v.h });
      await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await p.waitForSelector('.react-flow__node', { timeout: 45000 });
      await p.waitForTimeout(4500);
      const r = await 量一档(p);
      if (r.中止) { 表[v.名] = r; log(v.名, '🔴', r.中止); continue; }
      const 末 = r.帧[r.帧.length - 1];
      // 6 帧里中心值有几种取值？⇒ 回答 Q1「读数稳不稳」
      const cx = [...new Set(r.帧.map((f) => f.中心 && f.中心[0]))];
      const cy = [...new Set(r.帧.map((f) => f.中心 && f.中心[1]))];
      const vp = 末.vp平移缩放;
      const 验算 = vp && 末.画布坐标 ? {
        tx: vp[0], ty: vp[1], s: vp[2],
        算x: Math.round((末.画布坐标[0] - vp[0]) * vp[2] * 10000) / 10000,
        算y: Math.round((末.画布坐标[1] - vp[1]) * vp[2] * 10000) / 10000,
        实x: 末.中心[0], 实y: 末.中心[1],
        x对: Math.abs((末.画布坐标[0] - vp[0]) * vp[2] - 末.中心[0]) < 0.02,
        y对: Math.abs((末.画布坐标[1] - vp[1]) * vp[2] - 末.中心[1]) < 0.02,
      } : null;
      表[v.名] = { 视口: [v.w, v.h], 实际: await p.evaluate(() => [innerWidth, innerHeight]), 末, 中心x取值: cx, 中心y取值: cy, 验算 };
      log(v.名, '| 中心x 取值', JSON.stringify(cx), '| 中心y 取值', JSON.stringify(cy));
      log('     vp transform =', 末.vpTransform原文, '| 画布坐标 =', JSON.stringify(末.画布坐标), '| 验算', 验算 ? `x对=${验算.x对} y对=${验算.y对}` : '—');
    } catch (e) { 表[v.名] = { 出错: e.message }; log(v.名, '🔴', e.message); }
    finally { await p.close(); }
  }
  return 表;
};

out.主表 = await 跑(视口集);
out.重复测 = await 跑(视口集2);

fs.writeFileSync('/tmp/b198a.json', JSON.stringify(out, null, 1));
out.共享页_后 = await 共享页.evaluate(() => [innerWidth, innerHeight, devicePixelRatio]);
log('\n共享页 前/后：', JSON.stringify(out.共享页_前), '→', JSON.stringify(out.共享页_后));
await b.close();
