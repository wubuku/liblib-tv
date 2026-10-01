// 精确删除指定 data-id 的节点，其余一律不碰。
// 背景：画布 64b58cd5 是共享的，9222 上另有一个 Chrome 可能也在操作它，
// 因此**绝不能**用 jimeng-baseline-restore.mjs 那种「除保留项外全删」的语义。
// 用法：node scripts/jimeng-node-cleanup.mjs node_xxxx node_yyyy
import { chromium } from 'playwright';

const IDS = process.argv.slice(2);
if (!IDS.length) { console.error('用法：node scripts/jimeng-node-cleanup.mjs <data-id> [data-id ...]'); process.exit(1); }
const SET = new Set(IDS);

const browser = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = browser.contexts()[0];
const page = ctx.pages().find((p) => p.url().includes('jimeng.jianying.com'));
if (!page) { console.error('ABORT: 找不到画布页面'); process.exit(2); }
const cdp = await ctx.newCDPSession(page);
await cdp.send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 720, deviceScaleFactor: 2, mobile: false });
await page.waitForTimeout(600);
const vp = await page.evaluate(() => ({ w: innerWidth, h: innerHeight }));
if (vp.w !== 1280 || vp.h !== 720) { console.error('VIEWPORT POLLUTED', JSON.stringify(vp)); process.exit(2); }
for (let i = 0; i < 3; i++) { await page.keyboard.press('Escape'); await page.waitForTimeout(400); }

const g = await page.evaluate(() => document.querySelectorAll('.react-flow__node-group').length);
if (g > 0) { console.error('ABORT: 存在编组，删除语义不同'); process.exit(3); }

// 删前全量清单（审计证据）
const all = () => page.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => ({
  id: n.getAttribute('data-id') || '',
  title: (n.innerText || '').split('\n').pop().trim() || (n.innerText || '').split('\n')[0].trim(),
})));
const before = await all();
console.log('删前清单 =', JSON.stringify(before, null, 1));
const protect = before.filter((n) => !SET.has(n.id));
if (!protect.length) { console.error('ABORT: 没有需要保护的既有节点？'); }

// 只删显式给出的 id
for (const id of IDS) {
  const inList = before.find((n) => n.id === id);
  if (!inList) { console.log(`跳过：${id} 不在画布上`); continue; }
  const box = await page.evaluate((vid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`);
    if (!n) return null;
    n.scrollIntoView({ block: 'center' });
    const r = n.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + 20) };
  }, id);
  if (!box) { console.log(`跳过：${id} 定位失败`); continue; }
  await page.mouse.click(box.x, box.y);
  await page.waitForTimeout(900);
  let selOk = await page.evaluate((vid) => { const s = document.querySelector('.react-flow__node.selected'); return !!s && s.getAttribute('data-id') === vid; }, id);
  if (!selOk) {
    // 节点重叠时 mouse.click 会命中上层节点 —— 改为在目标元素上直接派发完整指针序列
    await page.evaluate((vid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`);
      if (!n) return;
      const r = n.getBoundingClientRect();
      const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + 20);
      for (const t of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) {
        n.dispatchEvent(new MouseEvent(t, { bubbles: true, cancelable: true, clientX: cx, clientY: cy }));
      }
    }, id);
    await page.waitForTimeout(900);
    selOk = await page.evaluate((vid) => { const s = document.querySelector('.react-flow__node.selected'); return !!s && s.getAttribute('data-id') === vid; }, id);
  }
  if (!selOk) { console.log(`跳过：${id} 选中失败`); await page.keyboard.press('Escape'); await page.waitForTimeout(400); continue; }
  await page.evaluate((vid) => {
    const s = document.querySelector(`.react-flow__node.selected[data-id="${vid}"]`);
    const r = s.getBoundingClientRect();
    s.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 14) }));
  }, id);
  await page.waitForTimeout(700);
  const clicked = await page.evaluate(() => {
    const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
    if (!m) return false;
    const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || ''));
    if (!it) return false;
    it.click();
    return true;
  });
  await page.waitForTimeout(1200);
  const after = await all();
  console.log(`删除 ${id}（${inList.title}）click=${clicked}，${before.length} -> ${after.length}`);
  if (after.length !== before.length - 1) { console.error(`ABORT: 节点数未按预期 -1`); process.exit(4); }
  before.length = after.length; before.splice(0, before.length, ...after);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(450);
}

const end = await page.evaluate(() => {
  const raf = document.querySelector('.react-flow__renderer');
  return {
    nodes: document.querySelectorAll('.react-flow__node').length,
    edges: document.querySelectorAll('.react-flow__edge').length,
    selected: document.querySelectorAll('.react-flow__node.selected').length,
    titles: Array.from(document.querySelectorAll('.react-flow__node')).map((n) => (n.innerText || '').split('\n').pop().trim()),
    credits: (document.body.innerText.match(/(\d[\d,]*)\s*基础会员/) || [])[1] || null,
    status: (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['(none)'])[0],
    transform: raf ? getComputedStyle(raf).transform : null,
  };
});
console.log('END', JSON.stringify(end, null, 1));
await browser.close();
