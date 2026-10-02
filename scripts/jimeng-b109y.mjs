// 批次 109 · y 轮：收尾归位 —— 把缩放从 59% 改回 60%。
//
// z 轮开工时读到的就是 `Zoom options, 59%`（不是我这一轮改的：本轮只点过节点、右键菜单、
// 「删除」这一项，以及上传入口；点右下角的空白处会误触缩放菜单，但本轮没有那次点击）。
// 共享画布上别人也会动，按纪律**只归位、不追责**，把它调回批次 108 的基线 60%。
//
// 归位手法（批次 106 结清的那条）：缩放菜单打开后会出现
// `[data-testid="canvas-zoom-percent-input"]`（`INPUT type=text`、值即当前百分比、
// 与按钮同矩形、此时按钮文字变空）⇒ **键入数字 + 按 Enter**；
// 只键入不回车的话值会变而画面不动。
//
// 收尾判据：`aria-label` 逐字 `Zoom options, 60%`，且**连读两次相同**（批次 105/106 教训）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'y', target: 'Zoom options, 60%' };
const save = () => writeFileSync(new URL('./_tmp-b109y.json', import.meta.url), JSON.stringify(out, null, 1));

const zoomRead = () => p.evaluate(() => {
  const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
  const inp = document.querySelector('[data-testid="canvas-zoom-percent-input"]');
  const t = document.body.innerText;
  return { aria: z ? z.getAttribute('aria-label') : null,
    btnText: z ? (z.innerText || '').trim() : null,
    inputPresent: !!inp, inputValue: inp ? inp.value : null,
    nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1],
    tool: (document.querySelector('[data-testid="canvas-pointer-tool-toggle"]') || { getAttribute: () => null }).getAttribute('aria-label'),
    credits: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label') };
});
const zoomBtn = () => p.evaluate(() => { const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
  if (!z) return null; const r = z.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });

out.before = await zoomRead();
log('归位前：', JSON.stringify(out.before));
save();
if (out.before.aria === out.target) { log('已经是 60%，什么都不用做'); out.noop = true; save(); await b.close(); process.exit(0); }

const g = await keyGuard(p);
log('焦点守卫：', g.safe ? '✅' : '⛔', g.where || '');
if (!g.safe) { log('⛔ 中止'); await b.close(); process.exit(2); }

const bt = await zoomBtn();
log('缩放按钮位置：', JSON.stringify(bt));
await p.mouse.click(bt.x, bt.y); await p.waitForTimeout(900);
out.menuOpen = await zoomRead();
log('菜单打开后：', JSON.stringify(out.menuOpen));
save();

if (!out.menuOpen.inputPresent) { log('🔴 输入框没出现 ⇒ 中止，不硬来'); await p.keyboard.press('Escape'); await b.close(); process.exit(3); }

const inp = await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-zoom-percent-input"]');
  if (!i) return null; i.focus(); const r = i.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
log('输入框位置：', JSON.stringify(inp));
await p.mouse.click(inp.x, inp.y); await p.waitForTimeout(400);
await p.keyboard.press('ControlOrMeta+a'); await p.waitForTimeout(200);
await p.keyboard.type('60', { delay: 120 });
await p.waitForTimeout(500);
out.beforeEnter = await zoomRead();
log('键入后（未回车）：', JSON.stringify(out.beforeEnter));
save();
await p.keyboard.press('Enter'); await p.waitForTimeout(1600);
out.afterEnter = await zoomRead();
log('回车后：', JSON.stringify(out.afterEnter));
save();

// 连读两次（批次 105/106 教训：单次读数不作数）
await p.waitForTimeout(900);
out.read2 = await zoomRead();
log('连读第二次：', JSON.stringify(out.read2));
out.ok = out.afterEnter.aria === out.target && out.read2.aria === out.target;
out.stable = out.afterEnter.aria === out.read2.aria;
log('归位成功 =', out.ok, '｜两次读数一致 =', out.stable);
save();
log('\nDONE y');
process.exit(0);
