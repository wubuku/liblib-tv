// 批次 134 · b 轮：**受控实验** —— 「用缩放输入框归位缩放」这一步是不是会关掉小地图？
//
// 🔑 线索：批次 131 与批次 134 **两次**都在「用缩放按钮输入态归位缩放」之后
//   发现静态 testid 从 174 掉到 171（差的恰好是小地图三层）。
//   批次 134 的证据更硬：a 轮收尾时 testid **就是 174（小地图开着）**，
//   中间只做了「点缩放按钮 → fill('60') → Enter → **Escape** → 移鼠标」这一串。
//   ⇒ 嫌疑锁定在这一串里的某一步。
//
// 📌 实验设计：开小地图 → 逐个只做其中一步 → 每步之后读小地图 `aria-pressed`。
//   **每一步都单独测**，不合并，这样才能定位到具体是哪个按键。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b' };
const save = () => writeFileSync(new URL('./_tmp-b134b.json', import.meta.url), JSON.stringify(out, null, 1));

const zoom = () => p.evaluate(() => document.querySelector('[data-testid="canvas-zoom-percent"]')?.getAttribute('aria-label'));
const mm = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-display-toggle-minimap"]');
  return e ? { pressed: e.getAttribute('aria-pressed'), dataState: e.getAttribute('data-state'),
    surface在: !!document.querySelector('[data-testid="canvas-minimap-surface"]'),
    tids: new Set(Array.from(document.querySelectorAll('[data-testid]')).map((x) => x.getAttribute('data-testid'))).size } : null; });
const ensureOpen = async () => { const s = await mm(); if (!s || s.pressed !== 'true') { const pt = await 点('[data-testid="canvas-display-toggle-minimap"]', '小地图'); await p.waitForTimeout(1300); } return mm(); };
const 点 = async (q) => { const pt = await p.evaluate((s) => { const e = document.querySelector(s); if (!e) return null;
  const r = e.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) { const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y }; }
  return null; }, q); if (pt) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1200); } return pt; };

out.start = { zoom: await zoom(), 小地图: await mm() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
await p.mouse.move(1276, 716); await p.waitForTimeout(700);
save();

const 步骤 = async (名, fn) => { const 前 = await mm(); await fn(); await p.waitForTimeout(1100); const 后 = await mm();
  const 变了 = 前 && 后 && 前.pressed !== 后.pressed;
  log(`  ${变了 ? '🔴' : '·'} ${名}：小地图 ${前 ? 前.pressed : '?'} → ${后 ? 后.pressed : '?'}${后 ? '（tids ' + 后.tids + '）' : ''}`);
  out.步骤 = out.步骤 || []; out.步骤.push({ 名, 前: 前 && 前.pressed, 后: 后 && 后.pressed, 变了, 前tids: 前 && 前.tids, 后tids: 后 && 后.tids });
  save(); return 后; };

log('\n=== 逐个单测归位序列里的每一步（每步前确保小地图是开的）===');
await ensureOpen();
log('  起点小地图：', JSON.stringify(await mm()));

await 步骤('① 点缩放按钮（只点，不输入）', async () => { await 点('[data-testid="canvas-zoom-percent"]'); });
await ensureOpen();
await 步骤('② 在输入框里 fill("60")（不按 Enter）', async () => {
  const inp = await p.$('[data-testid="canvas-zoom-percent-input"]');
  if (inp) { await inp.click({ clickCount: 3 }); await p.waitForTimeout(250); await inp.fill('60'); }
});
await 步骤('③ 按 Enter 提交', async () => { await p.keyboard.press('Enter'); });
await 步骤('④ 按一次 Escape', async () => { await p.keyboard.press('Escape'); });
await 步骤('⑤ 按第二次 Escape', async () => { await p.keyboard.press('Escape'); });
await 步骤('⑥ 移动鼠标到 (1276,716)', async () => { await p.mouse.move(1276, 716); });

log('\n  此刻 zoom =', await zoom(), '｜小地图 =', JSON.stringify(await mm()));
save();

// ---- 对照：单纯点缩放菜单里的「缩放至100%」会不会关小地图 ----
log('\n=== 对照组：走菜单项（不是输入框）改缩放，看小地图 ===');
await ensureOpen();
log('  对照起点小地图：', JSON.stringify(await mm()));
{
  await 点('[data-testid="canvas-zoom-percent"]'); await p.waitForTimeout(1200);
  const it = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[role=menuitem]')).find((x) => /^缩放至100%/.test((x.innerText || '').replace(/\s+/g, '')));
    if (!e) return null; const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2) for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) { const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y }; }
    return null; });
  if (it) { await p.mouse.click(it.x, it.y); await p.waitForTimeout(1500); }
  const 后 = await mm();
  log(`  · 菜单切到 100%（不按 Escape）后：zoom=${await zoom()}｜小地图 ${后 ? 后.pressed : '?'} ${后 && 后.pressed !== 'true' ? '🔴 被关了' : '· 仍在'}`);
  out.对照组 = { zoom: await zoom(), 小地图: 后 };
  save();
}

// ---- 收尾：缩放归位 60%（这次**不按 Escape**，只点 pane）+ 小地图开 ----
log('\n=== 收尾归位 ===');
{
  // 缩放：用输入框，且**不按 Escape**，改用点画布空白处退出编辑态
  if ((await zoom()) !== 'Zoom options, 60%') {
    await 点('[data-testid="canvas-zoom-percent"]'); await p.waitForTimeout(1100);
    const inp = await p.$('[data-testid="canvas-zoom-percent-input"]');
    if (inp) { await inp.click({ clickCount: 3 }); await p.waitForTimeout(200); await inp.fill('60'); await p.keyboard.press('Enter'); await p.waitForTimeout(1400); }
    // 退出编辑态：点画布空白（不按 Escape）
    const pp = await p.evaluate(() => { for (let y = 300; y < 640; y += 7) for (let x = 300; x < 760; x += 7) { const h = document.elementFromPoint(x, y); if (h && h.classList && h.classList.contains('react-flow__pane')) return { x, y }; } return null; });
    if (pp) { await p.mouse.click(pp.x, pp.y); await p.waitForTimeout(1200); }
  }
  await ensureOpen();
  await p.mouse.move(1276, 716); await p.waitForTimeout(800);
  const fin = await p.evaluate(() => ({ zoom: document.querySelector('[data-testid="canvas-zoom-percent"]')?.getAttribute('aria-label'),
    editing: document.querySelector('[data-testid="canvas-zoom-percent"]')?.getAttribute('data-editing'),
    minimap: document.querySelector('[data-testid="canvas-display-toggle-minimap"]')?.getAttribute('aria-pressed'),
    sidecar: getComputedStyle(document.querySelector('[data-testid="canvas-feature-sidecar"]')).opacity,
    sel: document.querySelectorAll('.react-flow__node.selected').length,
    ov: Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length,
    nodes: document.querySelectorAll('.react-flow__node').length,
    tids: new Set(Array.from(document.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid'))).size,
    line: (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0],
    credits: document.querySelector('[data-testid="canvas-commerce-entry"]')?.getAttribute('aria-label') }));
  out.收尾 = fin;
  log('收尾：', JSON.stringify(fin));
  save();
}
log('\nDONE b');
process.exit(0);
