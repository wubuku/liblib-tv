/**
 * 批次 220 收尾补丁：清掉**被取消的那次运行**留下的 2 个自建节点。
 *
 * 📌 为什么会有残留：b220 第一次跑时，节点名带了 `.mp4` 扩展名、而**搜索只命中不带扩展名的
 *   那种** ⇒ 全部臂无效 ⇒ 我 `task_stop` 掉了那个任务
 *   ⇒ **关掉页签 ≠ 撤销**（立规 94）：那两个节点**已在服务端**，必须显式删掉。
 *
 * 📌 顺带验证本批刚发现的一条：节点名**有时带扩展名、有时不带**，
 *   而搜索只命中不带的那种 ⇒ 清理路径也必须走**候选词表**。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b220-clean.json';
const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b220-clean' };

const 清单 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => ({
  id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label') })));
const 状态行 = (p) => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes, (\d+) edges, (\d+) selected[^\n]*/) || [])[0] || null);
const 积分 = (p) => p.evaluate(() => {
  const e = Array.from(document.querySelectorAll('*')).find((x) => (x.getAttribute('aria-label') || '').startsWith('Credits'));
  return e ? e.getAttribute('aria-label') : null;
});
const 焦点 = (p) => p.evaluate(() => {
  const a = document.activeElement;
  return { tag: a ? a.tagName : null, inRF: !!(a && a.closest && a.closest('.react-flow')) };
});
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

const browser = await chromium.connectOverCDP({ endpointURL: 'http://127.0.0.1:9444' });
const ctx = browser.contexts()[0];
const p = await ctx.newPage();
await p.setViewportSize({ width: 1280, height: 720 });
await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
await p.waitForSelector('.react-flow__node', { timeout: 45000 });
await p.waitForTimeout(5000);

const 全部 = await 清单(p);
out.前置 = { 数: 全部.length, 状态行: await 状态行(p), 积分: await 积分(p) };
// 只删**本会话自建**的：aria 命中探针文件名，或是与 `node_vbqnyxqrcd` 同名的空视频节点
const 要删 = 全部.filter((n) => /jimeng-b196-probe/.test(n.aria || '') || n.id === 'node_vbqnyxqrcd');
out.要删 = 要删;
log('【前置】' + 全部.length + ' ｜ ' + out.前置.状态行);
log('【要删】' + JSON.stringify(要删));

const zb = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
if (zb) { await p.mouse.click(zb[0], zb[1]); await p.waitForTimeout(1200);
  await p.fill('[data-testid="canvas-zoom-percent-input"]', '50');
  await p.keyboard.press('Enter'); await p.waitForTimeout(2500); }

out.步 = {};
for (const t of 要删) {
  const 步 = { id: t.id, aria: t.aria, 尝试: [] };
  for (let round = 1; round <= 3; round++) {
    const 现 = (await 清单(p)).find((n) => n.id === t.id);
    if (!现) { 步.备注 = '已不存在'; break; }
    const 记 = { 轮: round };
    const 钮 = await 搜索钮(p);
    if (!钮) { 记.失败 = '找不到搜索钮'; 步.尝试.push(记); break; }
    await p.mouse.click(钮[0], 钮[1]);
    await p.waitForTimeout(1500);
    const 有框 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('input'))
        .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
      if (!e) return false;
      e.focus(); e.select(); return true;
    });
    if (!有框) { 记.失败 = '找不到搜索输入框'; 步.尝试.push(记); break; }
    // 候选词表：全名 / 去扩展名
    const 去扩 = (现.aria || '').replace(/\.(mp4|mp3|mov|webm|png|jpg|jpeg)$/i, '');
    for (const 词 of [...new Set([去扩, 现.aria || ''].filter(Boolean))]) {
      await p.keyboard.press('Backspace');
      await p.waitForTimeout(200);
      await p.keyboard.type(词, { delay: 90 });
      await p.waitForTimeout(2200);
      const 行 = await 结果行点(p, t.id);
      记.试词 = (记.试词 || []).concat([{ 词, 有行: !!行 }]);
      if (!行) continue;
      await p.mouse.click(行[0], 行[1]);
      await p.waitForTimeout(2000);
      break;
    }
    记.框进来后焦点 = await 焦点(p);
    const 格 = await p.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      if (!n) return { 失败: '不在 DOM' };
      const r = n.getBoundingClientRect();
      if (r.right < 0 || r.x > innerWidth || r.bottom < 0 || r.y > innerHeight) return { 失败: '不在视口内' };
      for (let fy = 0.15; fy <= 0.9; fy += 0.125) for (let fx = 0.15; fx <= 0.9; fx += 0.125) {
        const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
        const h = document.elementFromPoint(x, y);
        if (h && h.closest(`.react-flow__node[data-id="${nid}"]`)) return { x, y };
      }
      return { 失败: '候选点全被盖' };
    }, t.id);
    if (格.x === undefined) { 记.失败 = '直点失败：' + 格.失败; 步.尝试.push(记); log(`  ${t.id} 轮${round} 直点失败 ${格.失败}`); continue; }
    await p.mouse.click(格.x, 格.y);
    await p.waitForTimeout(1500);
    记.直点后焦点 = await 焦点(p);
    记.选中集 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
    const 守卫过 = !!(记.选中集 && 记.选中集.includes(t.id) && 记.直点后焦点.inRF);
    记.守卫过 = 守卫过;
    if (!守卫过) { 记.失败 = '守卫没过'; 步.尝试.push(记); log(`  ${t.id} 轮${round} 守卫没过 ${JSON.stringify(记.直点后焦点)}`); continue; }
    await p.keyboard.press('Backspace');
    await p.waitForTimeout(2600);
    记.删后仍在 = (await 清单(p)).some((n) => n.id === t.id);
    步.尝试.push(记);
    log(`  ${t.id} 轮${round} → 删后仍在 ${记.删后仍在} ｜ 当前 ${(await 清单(p)).length} 个节点`);
    if (!记.删后仍在) break;
  }
  步.最终还在 = (await 清单(p)).some((n) => n.id === t.id);
  out.步[t.id] = 步;
}
try {
  const zb2 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
    if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (zb2) { await p.mouse.click(zb2[0], zb2[1]); await p.waitForTimeout(1200);
    await p.fill('[data-testid="canvas-zoom-percent-input"]', '26');
    await p.keyboard.press('Enter'); await p.waitForTimeout(2500); }
} catch (e) { log('🔴 缩放归位 ' + e.message); }
const 末 = await 清单(p);
out.后置 = { 数: 末.length, 状态行: await 状态行(p), 积分: await 积分(p),
  缩放: await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; }),
  残留探针: 末.filter((n) => /jimeng-b196-probe/.test(n.aria || '') || n.id === 'node_vbqnyxqrcd').map((n) => n.id + ' ' + n.aria) };
log('【后置】' + out.后置.数 + ' ｜ 残留探针 ' + JSON.stringify(out.后置.残留探针));
log('【后置】' + out.后置.状态行 + ' ｜ 缩放 ' + out.后置.缩放 + ' ｜ 积分 ' + out.后置.积分);
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
process.exit(0);
