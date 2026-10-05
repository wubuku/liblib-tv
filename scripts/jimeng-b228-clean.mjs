/**
 * 批次 228 收尾：删掉 b228 留下的 2 个节点，并顺手测清「**哪个按键能删节点**」。
 *
 * 🔴 为什么必须单独写一个脚本：b228 主脚本收尾用的是 `Delete` 键，
 *    两个节点**都没删掉**（日志逐字「删后仍在」，收尾 `78 节点`）。
 *    对照批次 226/222 的删除链，用的是 **`Backspace`**，而且**按之前要过焦点守卫**
 *    （`document.activeElement` 必须落在 `.react-flow` 里）。
 *    ⇒ 差别有三个变量：**键名**、**焦点守卫**、**点击方式**。一次只改一个才知道是谁的锅，
 *    所以本脚本对每个节点**依次**试 `Delete` → `Backspace`，并把每一步的
 *    「选中集 / 焦点 / 删后仍在」逐条记下来 ⇒ 结论有读数支撑，不靠猜。
 *
 * ⚠️ 这个结果对用户有直接价值：**手册里写的删节点快捷键到底哪个是真的**，必须实测。
 *
 * ⛔ 只删本会话自己创建的两个节点：`node_s02fd833rv`（视频）、`node_gywtnhgyv7`（文本）。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b228-clean.json';
const 目标 = ['node_s02fd833rv', 'node_gywtnhgyv7'];
const log = (...a) => console.log(a.join(' '));

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const page = await ctx.newPage();
const out = { 尝试: [] };

const 清单 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')));
const 状态行 = (p) => p.evaluate(() => (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null);
const 积分 = (p) => p.evaluate(() => {
  const e = Array.from(document.querySelectorAll('*')).find((x) => (x.getAttribute('aria-label') || '').startsWith('Credits'));
  return e ? e.getAttribute('aria-label') : null;
});
const 焦点 = (p) => p.evaluate(() => {
  const a = document.activeElement;
  return { tag: a ? a.tagName : null, inRF: !!(a && a.closest && a.closest('.react-flow')) };
});
const 选中集 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));

/** 找一个**确实落在该节点上**、且不在任何浮层上的屏幕点。 */
const 找点 = (p, id) => p.evaluate((nid) => {
  const el = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!el) return { 失败: '节点不在' };
  const r = el.getBoundingClientRect();
  const cx = r.x + r.width / 2;
  const cy = r.y + r.height / 2;
  for (let dy = -r.height / 4; dy <= r.height / 4; dy += 6) {
    for (let dx = -r.width / 4; dx <= r.width / 4; dx += 6) {
      const x = Math.round(cx + dx);
      const y = Math.round(cy + dy);
      const h = document.elementFromPoint(x, y);
      if (h && h.closest(`.react-flow__node[data-id="${nid}"]`) && !h.closest('[role="dialog"], button, a, input, textarea')) return { x, y };
    }
  }
  return { 失败: '候选点全被盖' };
}, id);

try {
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForSelector('.react-flow__node', { timeout: 45000 });
  await page.waitForTimeout(4500);
  out.基线 = { 状态行: await 状态行(page), 节点数: (await 清单(page)).length };
  log('【基线】' + JSON.stringify(out.基线));

  for (const id of 目标) {
    const 记 = { id, 轮次: [] };
    for (const 键 of ['Delete', 'Backspace']) {
      for (let round = 1; round <= 2; round++) {
        await page.keyboard.press('Escape');
        await page.waitForTimeout(400);
        const 点 = await 找点(page, id);
        if (点.失败) { 记.轮次.push({ 键, round, 失败: 点.失败 }); break; }
        await page.mouse.click(点.x, 点.y);
        await page.waitForTimeout(1200);
        const 轮 = {
          键, round,
          点: [点.x, 点.y],
          焦点: await 焦点(page),
          选中集: await 选中集(page),
        };
        轮.选中中 = (轮.选中集 || []).includes(id);
        轮.守卫过 = 轮.选中中 && 轮.焦点.inRF;
        await page.keyboard.press(键);
        await page.waitForTimeout(2400);
        轮.删后仍在 = (await 清单(page)).includes(id);
        轮.当前数 = (await 清单(page)).length;
        记.轮次.push(轮);
        log(`  ${id} 键=${键} 轮${round}：选中中=${轮.选中中} 焦点inRF=${轮.焦点.inRF} → 删后仍在=${轮.删后仍在} ｜ 当前 ${轮.当前数}`);
        if (!轮.删后仍在) break;
      }
      if (!(await 清单(page)).includes(id)) break;
    }
    记.最终还在 = (await 清单(page)).includes(id);
    out.尝试.push(记);
    log(`【${id}】最终还在=${记.最终还在}`);
  }
} catch (e) { out.出错 = e.message; log('🔴 ' + e.message); }

try {
  await page.keyboard.press('Escape');
  await page.waitForTimeout(400);
  out.收尾 = { 状态行: await 状态行(page), 节点数: (await 清单(page)).length, 积分: await 积分(page), 目标仍在: (await 清单(page)).filter((n) => 目标.includes(n)) };
  log('【收尾】' + JSON.stringify(out.收尾));
} catch (e) { log('🔴 收尾 ' + e.message); }

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
try { await page.close(); } catch (e) { /* 页签可能被别的会话关掉 */ }
await b.close();