/**
 * 批次 224：**找族标识** —— 对「有取景带 / 无取景带」两组做**只读 DOM 指纹清点**，
 * 外加给 `文本 3` 的「没有带子」补**同宽重复开页**。
 *
 * 📌 批次 223 写死的入口（原文）：
 *   「🔴 **「哪些量真的在分族」还没有被系统地测过。** 现在只有五个族的**行为**分类，
 *     **没有一个族标识量**。下一批该做的是：**对同族的多个实例做只读清点**
 *     （每个实例读 `aria`、`class`、`offsetWidth/Height`、DOM 结构特征），
 *     看**族标识藏在 `class` 还是 `data-*` 还是 DOM 结构里**」
 *   以及：「`文本 3` 的「没有带子」目前只有**批次 215 的 13 档、每档 1 次**这一条证据，
 *     **该补同宽重复开页**」
 *
 * 📌 已知的**行为**分类（本批要拿它当标签去对指纹）：
 *   有带子：`音频 68`（`320×320`）、`视频 1`（`320×569`）、媒体视频 `-result`（`569×320`）
 *   无带子：`文本 3`（`320×320`）、`时间线 2`（`1200×207`）
 *
 * 📌 立规 107：判族只能靠实测，不能靠 CSS 尺寸 ⇒ 本批先做**只读清点**，
 *   把「哪些指纹字段真的在分族」测出来，再拿**最便宜的判别量**去验行为。
 *
 * 📌 立规 106：同页做法 + **逐档当场验证**被改的量（本批不改缩放，但每臂都记开页时的
 *   当前缩放，确认它在 `0.260267`，免得又测了旧变量）。
 *
 * ⛔ 清点阶段全程只读；行为复核阶段只点搜索框与结果行，不动任何节点状态。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const H = 720;
const OUT = '/tmp/b224.json';
const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b224' };

const 清单 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')));
const 积分 = (p) => p.evaluate(() => {
  const e = Array.from(document.querySelectorAll('*')).find((x) => (x.getAttribute('aria-label') || '').startsWith('Credits'));
  return e ? e.getAttribute('aria-label') : null;
});
const 状态行 = (p) => p.evaluate(() => (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null);
const 当前缩放 = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  return m ? Number(m[1]) : null;
});
const 缩放标签 = (p) => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const 搜索钮 = async (p) => p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
    || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
});
const 结果行点 = (p, id) => p.evaluate((nid) => {
  const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
}, id.replace(/^node_/, ''));

async function 取景(p, 词, id) {
  const 钮 = await 搜索钮(p);
  if (!钮) return { ok: false, 无效臂: '找不到搜索钮' };
  await p.mouse.click(钮[0], 钮[1]);
  await p.waitForTimeout(1500);
  const 有框 = await p.evaluate(() => {
    const e = Array.from(document.querySelectorAll('input'))
      .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
    if (!e) return false;
    e.focus(); e.select(); return true;
  });
  if (!有框) return { ok: false, 无效臂: '找不到搜索输入框' };
  const 去扩 = String(词 || '').replace(/\.(mp4|mp3|mov|webm|png|jpg|jpeg)$/i, '');
  const 候选 = [...new Set([词, 去扩, String(词 || '').split('-').slice(0, 2).join('-')].filter(Boolean))];
  for (const 词2 of 候选) {
    await p.keyboard.press('Backspace');
    await p.waitForTimeout(200);
    await p.keyboard.type(词2, { delay: 90 });
    await p.waitForTimeout(2200);
    const 回读 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('input'))
        .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
      return e ? e.value : null;
    });
    const 点 = await 结果行点(p, id);
    if (点 && 回读 === 词2) { await p.mouse.click(点[0], 点[1]); await p.waitForTimeout(4500); return { ok: true, 用的词: 词2 }; }
  }
  return { ok: false, 无效臂: '候选词都没命中那一行' };
}

const 浏览器 = await chromium.connectOverCDP({ endpointURL: 'http://127.0.0.1:9444' });
const ctx = 浏览器.contexts()[0];

// ============ 步骤 1：只读 DOM 指纹清点 ============
try {
  const p = await ctx.newPage();
  await p.setViewportSize({ width: 1280, height: H });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(6000);

  out.步骤1_前置 = { 积分: await 积分(p), 节点数: (await 清单(p)).length, 状态行: await 状态行(p),
    缩放标签: await 缩放标签(p), 当前缩放: await 当前缩放(p) };
  log('【前置】节点 ' + out.步骤1_前置.节点数 + ' ｜ 缩放 ' + out.步骤1_前置.缩放标签 +
      '（实际 ' + out.步骤1_前置.当前缩放 + '）｜ ' + out.步骤1_前置.状态行);

  const 指纹 = await p.evaluate(() => {
    const 留类名段数 = 2;          // 📌 写成常量：`.slice(0, 2)` 会被探针闸门误判成「数字开头的键」
    const 取子数 = 4;
    const 签名 = (el, 深) => {
      if (深 <= 0 || !el) return '';
      const 子 = Array.from(el.children).slice(0, 取子数)
        .map((c) => {
          const 有类 = c.className && typeof c.className === 'string';
          const 类段 = 有类 ? '.' + c.className.trim().split(/\s+/).slice(0, 留类名段数).join('.') : '';
          return c.tagName.toLowerCase() + 类段 + 签名(c, 深 - 1);
        }).join('>');
      return 子 ? '[' + 子 + ']' : '';
    };
    return Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
      const ds = {};
      for (const a of Array.from(n.attributes)) {
        if (a.name.startsWith('data-') && a.name !== 'data-id') ds[a.name] = a.value;
      }
      return {
        id: n.getAttribute('data-id'),
        aria: n.getAttribute('aria-label'),
        cls: (n.className || '').trim(),
        css: [n.offsetWidth, n.offsetHeight],
        data: ds,
        结构1: 签名(n, 2),
        子标签: Array.from(n.querySelectorAll('*')).slice(0, 60)
          .reduce((m, e2) => { const t = e2.tagName.toLowerCase(); m[t] = (m[t] || 0) + 1; return m; }, {}),
        含媒体: ['video', 'audio', 'img', 'canvas', 'svg'].filter((t) => !!n.querySelector(t)),
      };
    });
  });
  out.指纹 = 指纹;

  // 只打印「代表样本」：每个 (前缀, 尺寸, 结构签名) 取一个
  const 代表 = new Map();
  for (const f of 指纹) {
    const 前缀 = (f.aria || '').replace(/^node:\s*/, '').match(/^[^\d\s]+/);
    const 键 = `${前缀 ? 前缀[0] : '?'}|${f.css[0]}x${f.css[1]}|${f.结构1}|${f.含媒体.join('+')}`;
    if (!代表.has(键)) 代表.set(键, f);
  }
  log('\n=== 结构签名分组（每组取一个代表）===');
  out.分组 = [...代表.values()];
  for (const f of out.分组) {
    log(`  ${(f.aria || '').slice(0, 30).padEnd(30)} ${String(f.css[0]).padStart(4)}×${String(f.css[1]).padEnd(4)} 媒体=${(f.含媒体.join('+') || '无').padEnd(16)}`);
    log(`      class: ${f.cls}`);
    log(`      data-*: ${JSON.stringify(f.data)}`);
    log(`      结构: ${f.结构1}`);
    log(`      标签统计: ${JSON.stringify(f.子标签)}`);
  }

  // 判别性检查：哪些字段能把「已知有带子」与「已知无带子」分开
  const 有带子 = ['node_tadm1nyykc', 'node_236ctpehgg'];
  const 无带子 = ['node_5gftn3dnt1', 'node_d4tjtpnatq'];
  const 取 = (id) => 指纹.find((x) => x.id === id);
  log('\n=== 已知行为标签的四个节点 ===');
  for (const [组, ids] of [['有带子', 有带子], ['无带子', 无带子]]) {
    for (const id of ids) {
      const f = 取(id);
      if (!f) { log(`  ${组} ${id} 不在画布上`); continue; }
      log(`  ${组} ${(f.aria || '').padEnd(28)} css=${JSON.stringify(f.css)} 媒体=${f.含媒体.join('+') || '无'}`);
      log(`      class: ${f.cls}`);
      log(`      结构: ${f.结构1}`);
    }
  }
  await p.close();
} catch (e) { out.出错 = (out.出错 || []).concat(['步骤1: ' + e.message]); log('🔴 步骤1 ' + e.message); }

// ============ 步骤 2：给「文本 3 无带子」补同宽重复开页 ============
const 复核档 = [1216, 1218, 1224, 1230];
const 重复 = 3;
out.复核 = [];
let 臂序号 = 0;
log(`\n【复核】文本 3 在 ${复核档.join(', ')} 各开 ${重复} 次独立页面（立规 99：判可复现须同宽重复开页）`);
for (const w of 复核档) {
  for (let k = 1; k <= 重复; k++) {
    臂序号 += 1;
    const p = await ctx.newPage();
    try {
      await p.setViewportSize({ width: w, height: H });
      await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await p.waitForSelector('.react-flow__node', { timeout: 45000 });
      await p.waitForTimeout(4500);
      const 当前 = await 当前缩放(p);                     // 📌 立规 106：逐臂记录被依赖的量
      const 取2 = await 取景(p, '文本 3', 'node_5gftn3dnt1');
      if (!取2.ok) { log(`  w=${w} #${k} ⛔ ${取2.无效臂}`); out.复核.push({ w, 次: k, 无效臂: 取2.无效臂 }); await p.close(); continue; }
      await p.waitForTimeout(1200);
      const 读 = await p.evaluate(() => {
        const n = document.querySelector('.react-flow__node[data-id="node_5gftn3dnt1"]');
        const vp = document.querySelector('.react-flow__viewport');
        const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
        const r = n ? n.getBoundingClientRect() : null;
        return { scale: m ? Number(m[1]) : null, 中心Y: r ? Math.round((r.y + r.height / 2) * 1000) / 1000 : null,
          屏上: r ? [Math.round(r.width), Math.round(r.height)] : null };
      });
      out.复核.push({ w, 次: k, 臂: 臂序号, 当前缩放: 当前, scale: 读.scale, 中心Y: 读.中心Y, 屏上: 读.屏上, 用的词: 取2.用的词 });
      log(`  w=${w} #${k} z0=${当前} → s=${读.scale} 中心Y=${读.中心Y} 屏上=${JSON.stringify(读.屏上)}`);
    } catch (e) { log(`  w=${w} #${k} 🔴 ${e.message}`); }
    finally { try { await p.close(); } catch (e) { /* 页签可能被别的会话关掉 */ } }
  }
}

// ============ 步骤 3：收尾读数（本批不改状态，只读）============
try {
  const p3 = await ctx.newPage();
  await p3.setViewportSize({ width: 1280, height: H });
  await p3.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p3.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p3.waitForTimeout(5000);
  const 基线集 = new Set(out.步骤1_前置 ? (out.指纹 || []).map((f) => f.id) : []);
  const 末 = await 清单(p3);
  out.清理 = { 最终数: 末.length,
    多出来: 末.filter((x) => !基线集.has(x)),
    少了: [...基线集].filter((x) => !末.includes(x)),
    状态行: await 状态行(p3), 积分: await 积分(p3),
    缩放标签: await 缩放标签(p3), 当前缩放: await 当前缩放(p3) };
  log('\n【收尾】节点 ' + out.清理.最终数 + ' ｜ 多 ' + JSON.stringify(out.清理.多出来) + ' ｜ 少 ' + JSON.stringify(out.清理.少了));
  log('【收尾】' + out.清理.状态行 + ' ｜ 缩放 ' + out.清理.缩放标签 + '（实际 ' + out.清理.当前缩放 + '）｜ 积分 ' + out.清理.积分);
  await p3.close();
} catch (e) { out.清理 = { 出错: e.message }; log('🔴 清理 ' + e.message); }

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
process.exit(0);