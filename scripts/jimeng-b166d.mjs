// 批次 166-d —— 只拍两张图，不取新读数（读数已由 166-c 全部拿到）。
//   ① `124-project-info-dialog-sections.png`：1280×720 基线（**四段结构一眼可见**）
//   ② `124-project-info-dialog-short-viewport.png`：1280×600 —— 被 80vh 压到 480 高，
//      **中段滚动区先让步**（382 → 316），标题/页签/页脚三段不变。
// ⛔ 只读：开对话框 → 拍 → Esc；新页签内跑，收尾复位共享视口。
import fs from 'node:fs';
import { PORT } from './jimeng-b135-lib.mjs';

const URL_ = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const 出图 = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const rec = { 批次: '166d', 目的: '补两张项目信息对话框的证据图（基线 + 被 80vh 压矮）' };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b166d.json', import.meta.url), JSON.stringify(rec, null, 1));

const 读共享 = async (p) => p.evaluate(() => ({
  视口: [innerWidth, innerHeight],
  状态行: (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0],
  节点数: document.querySelectorAll('.react-flow__node').length,
  选中: document.querySelectorAll('.react-flow__node.selected').length,
  浮层: Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length,
  积分: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'),
}));

const { chromium } = await import('playwright');
const b = await chromium.connectOverCDP(`http://127.0.0.1:${PORT}`);
const ctx = b.contexts()[0];
const shared = ctx.pages().find((x) => x.url().includes('ai-canvas'));
rec.共享起点 = await 读共享(shared);
let p2 = null;
try {
  p2 = await ctx.newPage();
  await p2.goto(URL_, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p2.waitForTimeout(9500);
  const s2 = await p2.context().newCDPSession(p2);
  rec.图 = [];
  for (const [w, h, 文件] of [[1280, 720, '124-project-info-dialog-sections.png'],
                              [1280, 600, '124-project-info-dialog-short-viewport.png']]) {
    await s2.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
    await p2.waitForTimeout(1600);
    const 更多 = await p2.evaluate(() => { const e = Array.from(document.querySelectorAll('button,[role=button]'))
      .find((x) => (x.getAttribute('aria-label') || '').includes('更多')); if (!e) return null;
      const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    if (!更多) { console.log('⛔ 没找到「更多」'); continue; }
    await p2.mouse.click(更多[0], 更多[1]); await p2.waitForTimeout(1300);
    const 项 = await p2.evaluate(() => { const it = Array.from(document.querySelectorAll('[role=menuitem]')).find((x) => (x.innerText || '').trim() === '项目信息');
      if (!it) return null; const r = it.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    if (!项) { console.log('⛔ 菜单里没有「项目信息」'); await p2.keyboard.press('Escape'); continue; }
    await p2.mouse.click(项[0], 项[1]); await p2.waitForTimeout(2600);
    const 读 = await p2.evaluate(() => { const d = document.querySelector('[data-testid="workspace-project-info-dialog"]');
      if (!d) return null; const r = d.getBoundingClientRect();
      return { 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
        子: Array.from(d.children).map((c) => Math.round(c.getBoundingClientRect().height)) }; });
    console.log(`[${w}×${h}] 盒 ${JSON.stringify(读 && 读.盒)} 四段高 ${JSON.stringify(读 && 读.子)}`);
    if (读) {
      await p2.screenshot({ path: new URL(文件, 出图).pathname });
      rec.图.push({ 文件: 'screenshots/' + 文件, 视口: [w, h], 盒: 读.盒, 四段高: 读.子 });
      console.log('  已拍 ' + 文件);
    }
    for (let k = 0; k < 3; k++) { await p2.keyboard.press('Escape'); await p2.waitForTimeout(600); }
    落盘();
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 600); console.log('异常', rec.异常); }
finally {
  try { if (p2) await p2.close(); } catch (e) {}
  try {
    rec.共享收尾 = await 读共享(shared);
    const { pinViewport } = await import('./jimeng-safe-keys.mjs');
    rec.复位 = await pinViewport(shared);
    console.log('共享视口已复位', JSON.stringify(rec.复位), '｜ 数据', JSON.stringify(rec.共享收尾));
  } catch (e) {}
  落盘();
}
process.exit(0);
