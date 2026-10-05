/**
 * 批次 215 清理 · 定点诊断：为什么 Backspace 删不掉这两个节点？
 *
 * 上一版清理在 4 条路径上全部失败，但每一版都做了同一件事 —— **按之前先 blur()**。
 * 🔴 假设：**blur 才是元凶**。批次 214 成功那次是「画布直点 → 直接按 Backspace」，
 *   焦点当时在 `rf__wrapper` 或节点 div 上；本轮把它强制成 BODY 之后按键就不生效了。
 *
 * 本脚本逐个试，每一步都读「节点数 / 状态行 / 焦点」：
 *   ① 缩放 50% → 画布直点（焦点应落在节点上）→ **不 blur** 直接按 Backspace
 *   ② 还���在 → 按 Delete
 *   ③ 还在 → 右键菜单找「删除」
 *   ④ 还在 → 读节点工具条上所有按钮的 aria（看有没有显式删除入口）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b215-diag.json';
const 前 = JSON.parse(fs.readFileSync('/tmp/b215.json', 'utf8'));
const 要删 = 前.自建清单 || [];
const 基线id = new Set((前.步骤0_前置 || {}).基线id || []);

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b215-diag', 要删, 步: {} };

const 清单 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => ({
  id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label') })));
const 状态行 = (p) => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes, (\d+) edges, (\d+) selected[^\n]*/) || [])[0] || null);
const 焦点 = (p) => p.evaluate(() => { const a = document.activeElement;
  return { tag: a ? a.tagName : null, testid: a ? a.getAttribute('data-testid') : null, aria: a ? a.getAttribute('aria-label') : null }; });
const 还在 = async (p, id) => (await 清单(p)).some((n) => n.id === id);
const 直点 = async (p, id) => p.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  for (let fy = 0.1; fy <= 0.95; fy += 0.142857) for (let fx = 0.1; fx <= 0.95; fx += 0.142857) {
    const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
    const h = document.elementFromPoint(x, y);
    if (h && h.closest(`.react-flow__node[data-id="${nid}"]`)) return [x, y];
  }
  return null;
}, id);

const browser = await chromium.connectOverCDP({ endpointURL: 'http://127.0.0.1:9444' });
const ctx = browser.contexts()[0];
const p = await ctx.newPage();
await p.setViewportSize({ width: 1280, height: 720 });
await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
await p.waitForSelector('.react-flow__node', { timeout: 45000 });
await p.waitForTimeout(5000);

out.前置 = { 数: (await 清单(p)).length, 状态行: await 状态行(p) };
log('【前置】' + out.前置.数 + ' ｜ ' + out.前置.状态行);

// 先缩到 50%，让节点有实体面积（26% 下它只有 148×83 且叠放）
const zb = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
if (zb) { await p.mouse.click(zb[0], zb[1]); await p.waitForTimeout(1200);
  await p.fill('[data-testid="canvas-zoom-percent-input"]', '50');
  await p.keyboard.press('Enter'); await p.waitForTimeout(2500); }
out.缩放后 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
log('【缩放】' + out.缩放后);

for (const id of 要删) {
  const 步 = { id, 尝试: [] };
  if (!await 还在(p, id)) { 步.备注 = '已不存在'; out.步[id] = 步; continue; }

  // ① 画布直点 → **不 blur** → Backspace
  const pt = await 直点(p, id);
  步.尝试.push({ 步: '直点', 点: pt });
  if (pt) {
    await p.mouse.click(pt[0], pt[1]);
    await p.waitForTimeout(1400);
    const f1 = await 焦点(p);
    const sel1 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
    步.尝试.push({ 步: '点后', 焦点: f1, 选中: sel1 });
    log(`  ${id} 直点 (${pt}) 焦点=${JSON.stringify(f1)} 选中=${JSON.stringify(sel1)}`);
    if (sel1.includes(id)) {
      await p.keyboard.press('Backspace');
      await p.waitForTimeout(2000);
      const r1 = { 还在: await 还在(p, id), 状态行: await 状态行(p) };
      步.尝试.push({ 步: 'Backspace(不blur)', ...r1 });
      log(`  ⇒ Backspace 后 还在=${r1.还在} ｜ ${r1.状态行}`);
    }
  }
  // ② Delete 键
  if (await 还在(p, id)) {
    await p.keyboard.press('Delete');
    await p.waitForTimeout(2000);
    const r2 = { 还在: await 还在(p, id), 状态行: await 状态行(p) };
    步.尝试.push({ 步: 'Delete键', ...r2 });
    log(`  ⇒ Delete 后 还在=${r2.还在} ｜ ${r2.状态行}`);
  }
  // ③ 右键菜单
  if (await 还在(p, id)) {
    const pt2 = await 直点(p, id);
    if (pt2) {
      await p.mouse.click(pt2[0], pt2[1], { button: 'right' });
      await p.waitForTimeout(1500);
      const 菜单 = await p.evaluate(() => Array.from(document.querySelectorAll('[role=menu] [role=menuitem], [role=menu] button, [role=menu] [role=menuitemradio]'))
        .map((e) => (e.innerText || e.getAttribute('aria-label') || '').trim()).filter(Boolean).slice(0, 20));
      步.尝试.push({ 步: '右键菜单', 菜单 });
      log(`  ⇒ 右键菜单 ${JSON.stringify(菜单)}`);
      await p.keyboard.press('Escape');
      await p.waitForTimeout(800);
    }
  }
  // ④ 读节点上的按钮
  if (await 还在(p, id)) {
    const 钮 = await p.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      if (!n) return null;
      return Array.from(n.querySelectorAll('button,[role=button]')).map((b) => ({
        aria: b.getAttribute('aria-label'), testid: b.getAttribute('data-testid'),
        逐字: (b.innerText || '').trim().slice(0, 20) })).slice(0, 30);
    }, id);
    步.尝试.push({ 步: '节点内按钮', 按钮: 钮 });
    log(`  ⇒ 节点内按钮 ${JSON.stringify(钮)}`);
  }
  步.最终还在 = await 还在(p, id);
  out.步[id] = 步;
}

const 末 = await 清单(p);
out.后置 = { 数: 末.length, 状态行: await 状态行(p),
  多出来: 末.filter((n) => !基线id.has(n.id)).map((n) => n.id + ' ' + n.aria),
  少了: [...基线id].filter((x) => !末.some((n) => n.id === x)) };
log('【后置】' + out.后置.数 + ' ｜ 多 ' + JSON.stringify(out.后置.多出来));
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
process.exit(0);
