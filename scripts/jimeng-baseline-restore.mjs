// 归基线通用脚本：保留指定标题的节点，其余逐个用「选中 → 右键 → 删除 ⌫」移除
import { chromium } from 'playwright';

const KEEP = process.argv[2] || '视频 1';
const browser = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = browser.contexts()[0];
const page = ctx.pages().find((p) => p.url().includes('jimeng.jianying.com'));
const cdp = await ctx.newCDPSession(page);
await cdp.send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 720, deviceScaleFactor: 2, mobile: false });
await page.waitForTimeout(600);
const vp = await page.evaluate(() => ({ w: innerWidth, h: innerHeight }));
if (vp.w !== 1280 || vp.h !== 720) { console.error('VIEWPORT POLLUTED'); process.exit(2); }
for (let i = 0; i < 3; i++) { await page.keyboard.press('Escape'); await page.waitForTimeout(350); }

const g = await page.evaluate(() => document.querySelectorAll('.react-flow__node-group').length);
if (g > 0) { console.error('ABORT: 存在编组，删除语义不同'); process.exit(3); }

const names = () => page.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node'))
  .map((n) => (n.innerText || '').split('\n')[0].trim()));
console.log('清理前 =', (await names()).length);

for (let round = 0; round < 20; round++) {
  const list = await names();
  const victim = list.find((n) => n !== KEEP);
  if (!victim) break;
  const pre = list.length;
  // 选中：派发完整指针序列 + 兜底 mouse.click
  const box = await page.evaluate((v) => {
    const n = Array.from(document.querySelectorAll('.react-flow__node')).find((x) => (x.innerText || '').split('\n')[0].trim() === v);
    if (!n) return null;
    n.scrollIntoView({ block: 'center' });
    const r = n.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + 20) };
  }, victim);
  if (!box) { console.log(`找不到「${victim}」`); break; }
  await page.mouse.click(box.x, box.y);
  await page.waitForTimeout(800);
  let sel = await page.evaluate(() => {
    const s = document.querySelector('.react-flow__node.selected');
    return s ? (s.innerText || '').split('\n')[0].trim() : null;
  });
  if (sel !== victim) {
    // 兜底：直接派发
    await page.evaluate((v) => {
      const n = Array.from(document.querySelectorAll('.react-flow__node')).find((x) => (x.innerText || '').split('\n')[0].trim() === v);
      if (!n) return;
      const r = n.getBoundingClientRect(); const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + 20);
      for (const t of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) n.dispatchEvent(new MouseEvent(t, { bubbles: true, cancelable: true, clientX: cx, clientY: cy }));
    }, victim);
    await page.waitForTimeout(800);
    sel = await page.evaluate(() => {
      const s = document.querySelector('.react-flow__node.selected');
      return s ? (s.innerText || '').split('\n')[0].trim() : null;
    });
  }
  if (sel !== victim) { console.log(`选中「${victim}」失败（当前选中=${sel}），停止`); break; }
  await page.evaluate(() => {
    const s = document.querySelector('.react-flow__node.selected');
    const r = s.getBoundingClientRect();
    s.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 14) }));
  });
  await page.waitForTimeout(700);
  const clicked = await page.evaluate(() => {
    const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]'))
      .filter((e) => e.getBoundingClientRect().width > 1).pop();
    if (!m) return false;
    const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || ''));
    if (!it) return false;
    it.click();
    return true;
  });
  await page.waitForTimeout(1100);
  const post = (await names()).length;
  console.log(`删除「${sel}」click=${clicked} ${pre} -> ${post}`);
  if (post !== pre - 1) { console.error(`ABORT: 节点数未按预期 -1（${pre} -> ${post}）`); process.exit(4); }
  await page.keyboard.press('Escape');
  await page.waitForTimeout(450);
}

const end = await page.evaluate(() => {
  const raf = document.querySelector('.react-flow__renderer');
  return {
    nodes: document.querySelectorAll('.react-flow__node').length,
    edges: document.querySelectorAll('.react-flow__edge').length,
    groups: document.querySelectorAll('.react-flow__node-group').length,
    selected: document.querySelectorAll('.react-flow__node.selected').length,
    popups: Array.from(document.querySelectorAll('[role="menu"],[role="listbox"]')).filter((e) => e.getBoundingClientRect().width > 1).length,
    names: Array.from(document.querySelectorAll('.react-flow__node')).map((n) => (n.innerText || '').split('\n')[0].trim()),
    transform: raf ? getComputedStyle(raf).transform : null,
    credits: (document.body.innerText.match(/(\d[\d,]*)\s*基础会员/) || [])[1] || null,
    status: (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['(none)'])[0],
  };
});
console.log('END', JSON.stringify(end, null, 1));
await browser.close();
