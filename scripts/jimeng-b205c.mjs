/**
 * 批次 205 c 轮：找出「w ≤ 1210 用 50% + 落点Y=360；w ≥ 1212 用别缩放 + 落点Y≈259.8」
 * 这件事的**几何来源**。
 *
 * b 轮长采样已经把「动画没跑完」排除掉了（每档第 2 帧起就稳定）：
 *   宽      缩放aria   落点中心Y
 *   1206    50%        360
 *   1208    50%        360
 *   1210    50%        360
 *   1212    26%        259.8285   🔴 两件事同时在这两档之间切换
 *   1214    28%        259.7059
 *   ...
 *   1230    49%        257.353
 *   1232    50%        259.8451
 *   1234    50%        259.7843
 *
 * ⇒ 落点Y ≈ 259.8 等价于「节点被放在一个中心在 259.8 的区域里」，
 *   而 360 = 720/2 是**整个视口**的中心 ⇒ **两者之间一定有个元素改变了画布的可用区域**。
 *   259.8 × 2 = 519.6 ⇒ 若可用区是 [0, 519.6]，那底下多出一条 **200.4px** 的东西。
 *
 * 本轮只做一件事：**逐元素 diff**。
 * 在 1210 / 1211 / 1212 / 1213 四档上、取景落定之后，把页面上所有可见元素的
 * 「testid（或 tag+class 前缀）+ 屏上盒子」列出来，做逐档差集。
 * 差集里出现/消失的那个元素，就是「可用区域改变」的载体。
 *
 * 只读：不新建/删除节点，不生成，不下载。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const 搜索词 = '音频';
const 目标 = 'canvas-search-result-node_tadm1nyykc';
const H = 720;
const 宽集 = [1210, 1211, 1212, 1213];

const log = (...a) => console.log(a.join(' '));

/** 列全页面「可见元素」的指纹：键 = testid 或 tag+class 前两段，值 = 盒子。 */
const 指纹 = (p) => p.evaluate(() => {
  const m = new Map();
  for (const e of document.querySelectorAll('body *')) {
    const r = e.getBoundingClientRect();
    if (r.width < 8 || r.height < 8) continue;
    if (r.bottom < 0 || r.top > innerHeight || r.right < 0 || r.left > innerWidth) continue;
    const cs = getComputedStyle(e);
    if (cs.visibility === 'hidden' || cs.display === 'none' || Number(cs.opacity) === 0) continue;
    const tid = e.getAttribute('data-testid');
    const key = tid ? `tid:${tid}` : `${e.tagName}.${String(e.className || '').trim().split(/\s+/).slice(0, 2).join('.')}`;
    if (m.has(key)) continue;
    m.set(key, [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]);
  }
  return Object.fromEntries(m);
});

/** 直接问「画布可用区域」：视口内、有面积的元素里，谁的下边界最靠下且横跨全宽。 */
const 底部带 = (p) => p.evaluate(() => {
  const 候选 = [];
  for (const e of document.querySelectorAll('body *')) {
    const r = e.getBoundingClientRect();
    if (r.height < 20 || r.width < 300) continue;
    if (r.top > innerHeight || r.bottom < innerHeight - 400) continue;
    if (r.width < innerWidth * 0.6) continue;
    const cs = getComputedStyle(e);
    if (cs.position !== 'fixed' && cs.position !== 'absolute') continue;
    if (Number(cs.opacity) === 0 || cs.display === 'none') continue;
    候选.push({ testid: e.getAttribute('data-testid'), tag: e.tagName,
      class前二: String(e.className || '').split(/\s+/).slice(0, 2).join('.'),
      盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      position: cs.position, zIndex: cs.zIndex, pointerEvents: cs.pointerEvents });
  }
  return 候选.slice(0, 14);
});

const out = { 轮次: 'b205c', 宽集, 档: {} };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

for (const w of 宽集) {
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: w, height: H });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(4500);

    const 搜索钮 = await p.evaluate(() => {
      const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
        || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    });
    if (!搜索钮) { out.档[w] = { 无效臂: '找不到搜索钮' }; await p.close(); continue; }
    await p.mouse.click(搜索钮[0], 搜索钮[1]);
    await p.waitForTimeout(1500);
    const 有输入框 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
      if (!e) return false;
      e.focus(); e.select(); return true;
    });
    if (!有输入框) { out.档[w] = { 无效臂: '找不到搜索输入框' }; await p.close(); continue; }
    await p.keyboard.press('Backspace');
    await p.waitForTimeout(250);
    await p.keyboard.type(搜索词, { delay: 90 });
    await p.waitForTimeout(2200);

    const 输入回读 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
      return e ? e.value : null;
    });
    const 前置 = await p.evaluate((tid) => {
      const e = document.querySelector(`[data-testid="${tid}"]`);
      if (!e) return { 存在: false };
      const r = e.getBoundingClientRect();
      return { 存在: true, 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
    }, 目标);
    if (!前置.存在 || 输入回读 !== 搜索词) {
      out.档[w] = { 无效臂: !前置.存在 ? '目标行不在' : '输入没进去', 输入回读 };
      log(`${w} ⛔ 无效臂`);
      await p.close(); continue;
    }

    await p.mouse.click(前置.点[0], 前置.点[1]);
    await p.waitForTimeout(3500);

    const 终 = await p.evaluate((tid) => {
      const id = tid.replace('canvas-search-result-node_', 'node_');
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      const r = n ? n.getBoundingClientRect() : null;
      const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
      return { 中心: r ? [Math.round((r.x + r.width / 2) * 1000) / 1000, Math.round((r.y + r.height / 2) * 1000) / 1000] : null,
        vp: m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null,
        缩放aria: z ? z.getAttribute('aria-label') : null };
    }, 目标);

    out.档[w] = { 前置, 输入回读, 终, 指纹: await 指纹(p), 底部带: await 底部带(p) };
    log(`${w} | 中心=${JSON.stringify(终.中心)} | 缩放=${终.缩放aria} | 指纹元素数=${Object.keys(out.档[w].指纹).length}`);
  } catch (e) {
    out.档[w] = { 出错: e.message };
    log(`${w} 🔴 ${e.message}`);
  } finally { await p.close(); }
}

// —— 逐档差集 ——
const 有效 = 宽集.filter((w) => out.档[w] && out.档[w].指纹);
out.差集 = [];
for (let i = 1; i < 有效.length; i++) {
  const a = 有效[i - 1], c = 有效[i];
  const A = out.档[a].指纹, C = out.档[c].指纹;
  const 新增 = Object.keys(C).filter((k) => !(k in A));
  const 消失 = Object.keys(A).filter((k) => !(k in C));
  const 移动 = Object.keys(C).filter((k) => k in A && JSON.stringify(C[k]) !== JSON.stringify(A[k]));
  out.差集.push({ 从: a, 到: c, 新增, 消失, 移动数: 移动.length,
    移动样本: 移动.slice(0, 10).map((k) => ({ k, 从: A[k], 到: C[k] })) });
  log(`\n${a} → ${c}：新增 ${新增.length} ／ 消失 ${消失.length} ／ 移动 ${移动.length}`);
  if (新增.length) log('   新增: ' + JSON.stringify(新增.slice(0, 12)));
  if (消失.length) log('   消失: ' + JSON.stringify(消失.slice(0, 12)));
}

fs.writeFileSync('/tmp/b205c.json', JSON.stringify(out, null, 1));
log('\n写入 /tmp/b205c.json');
process.exit(0);
