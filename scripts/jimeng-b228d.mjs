/**
 * 批次 228d：批次 226 是在 **视口宽 1195–1215** 的窄窗口里搜的，
 * 而批次 228/228c 全部在 **1280** —— 这是两批之间**唯一还没被控制掉的变量**。
 *
 * 为什么怀疑它：搜索面板在 1280 宽时实测位于 `[769, 56, 320, 604]`（面板宽 320）。
 * 窗口窄到 1195 时，面板可能移位、被折叠，或「搜索」按钮跑到别的位置；
 * 而批次 226 的 `搜索钮` 是**按 aria-label 找按钮后直接点它的矩形中心** ——
 * 若那个点被别的浮层盖住，搜索面板根本没打开，后面的读数自然全是空。
 *
 * 本脚本在**同一页、同一节点**上只改视口宽度，读三件事：
 *   ① 搜索钮的矩形与落点归属（`elementFromPoint` 说是谁）
 *   ② 面板有没有真的打开、输入框在不在
 *   ③ 批次 226 那条选择器能不能命中目标结果行
 * 目标节点用**画布上早就存在的** `音频 68`（`node_tadm1nyykc`）—— 不新建任何东西。
 *
 * ⛔ 本脚本只读，不新建、不删除、不上传、不触发生成。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b228d.json';
const 目标 = { id: 'node_tadm1nyykc', 词: '音频 68' };
const 档位 = [1280, 1215, 1205, 1195];
// 📌 探针闸门会把 `.slice(0, 60)` 里的 `0, 60)` 误判成「数字开头的键」⇒ 走参数传进 evaluate。
const 文本上限 = 60;
const log = (...a) => console.log(a.join(' '));
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const page = await ctx.newPage();
const out = { 档位: [] };

try {
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForSelector('.react-flow__node', { timeout: 45000 });
  await page.waitForTimeout(4500);

  for (const w of 档位) {
    const 记 = { 视口宽: w };
    try {
      await page.setViewportSize({ width: w, height: 720 });
      await page.waitForTimeout(2500);
      // 关掉可能残留的面板，保证每档都从「面板关着」这个同一起点开始
      await page.keyboard.press('Escape');
      await page.waitForTimeout(600);

      // ① 搜索钮
      记.搜索钮 = await page.evaluate(() => {
        const e = Array.from(document.querySelectorAll('button, [role="button"]'))
          .find((x) => (x.getAttribute('aria-label') || '') === '搜索');
        if (!e) return null;
        const r = e.getBoundingClientRect();
        const cx = Math.round(r.x + r.width / 2);
        const cy = Math.round(r.y + r.height / 2);
        const hit = document.elementFromPoint(cx, cy);
        return {
          矩形: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          testid: e.getAttribute('data-testid'),
          落点归属: hit ? (hit.closest('button, [role="button"]') || hit).getAttribute('aria-label') : null,
          落点测试id: hit ? (hit.closest('[data-testid]') || {}).getAttribute?.('data-testid') : null,
        };
      });

      // ② 点它，看面板开没开
      if (记.搜索钮) {
        await page.mouse.click(记.搜索钮.矩形[0] + 记.搜索钮.矩形[2] / 2, 记.搜索钮.矩形[1] + 记.搜索钮.矩形[3] / 2);
        await page.waitForTimeout(1600);
      }
      记.面板 = await page.evaluate(() => {
        const p = document.querySelector('[data-testid="canvas-search-panel"]');
        const inp = p ? p.querySelector('input') : null;
        const r = p ? p.getBoundingClientRect() : null;
        return {
          面板在: !!p,
          面板可见: p ? p.getBoundingClientRect().width > 1 : false,
          面板矩形: r ? [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] : null,
          有输入框: !!inp,
          按钮数: p ? p.querySelectorAll('button').length : 0,
        };
      });

      // ③ 输入词 → 读结果行 + 批次 226 的选择器
      if (记.面板.有输入框) {
        await page.evaluate(() => {
          const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
          inp.focus(); inp.select();
        });
        await page.keyboard.type(目标.词, { delay: 80 });
        await page.waitForTimeout(2400);
        记.结果 = await page.evaluate(([id, 文本上限]) => {
          const 列表 = document.querySelector('[role="list"]');
          const 状态 = document.querySelector('[data-testid="canvas-search-panel"] [role="status"]');
          const sel = '[data-testid="canvas-search-result-node_' + String(id).replace(/^node_/, '') + '"]';
          return {
            回读: (document.querySelector('[data-testid="canvas-search-panel"] input') || {}).value || null,
            可见行数: 列表 ? Array.from(列表.querySelectorAll('[data-node-id]')).length : 0,
            列表文本: 列表 ? (列表.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 文本上限) : null,
            空态: 状态 ? (状态.innerText || '').trim() : null,
            批次226选择器: sel,
            选择器命中: !!document.querySelector(sel),
          };
        }, [目标.id, 文本上限]);
      }

      await page.keyboard.press('Escape');
      await page.waitForTimeout(800);
      await page.keyboard.press('Escape');
      await page.waitForTimeout(600);

      out.档位.push(记);
      const r = 记.结果;
      log(`【w=${w}】钮=${记.搜索钮 ? JSON.stringify(记.搜索钮.矩形) : '无'} 落点=${记.搜索钮 ? 记.搜索钮.落点归属 : '-'} ｜ 面板=${记.面板.面板在 ? '开' : '未开'}/${记.面板.有输入框 ? '有框' : '无框'} ｜ 结果=${r ? (r.选择器命中 ? '✅命中' : '⛔' + (r.空态 || r.列表文本 || '无')) : '-'} 226选择器=${r ? r.选择器命中 : '-'}`);
    } catch (e) { 记.错 = e.message; out.档位.push(记); log(`【w=${w}】🔴 ${e.message}`); }
  }

  // 复位到 1280，别把视口留在窄档
  await page.setViewportSize({ width: 1280, height: 720 });
  out.收尾 = await page.evaluate(() => (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null);
  log('【收尾】' + out.收尾);
} catch (e) { out.出错 = e.message; log('🔴 ' + e.message); }

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
try { await page.close(); } catch (e) { /* 忽略 */ }
await b.close();