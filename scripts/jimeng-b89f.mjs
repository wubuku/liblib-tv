// 批次 89 · F：`Add tags` 是不是**两态**（静息 / 选中）。
//
// e 轮已把机制钉死：屏上边长 = CSS `24px` × 视口 `0.6` × 逐节点的
// `--octo-canvas-node-chrome-counter-scale`，20/20 预测命中。
// 但那个变量在**同一画布同一缩放下有三个取值**：1.66666（9 个）/ 1.93435（4 个）/ 2（7 个）。
//
// 🔴 由此撞上一个**手册里的既有记录**：
//     批次 28 与批次 88 都写「`Add tags` **24×24**」，
//     批次 88 量的正是**导演台**那个 —— 而 e 轮量到导演台现在是 **29×29**（counter=2）。
//     差别只可能来自**状态**：批次 88 那一轮自伤里写明「静息态根本没静息」，
//     三档 `sel` 全是 1 ⇒ **它量的是选中态**。
//
// ⇒ 可证伪预测 **P1f**：导演台的 `Add tags` 在**选中时是 24×24**、
//   **取消选中后回到 29×29**。
//   若两态一样 ⇒ 差异另有来源，批次 88 的读数站不住，得另找机制。
//
// ⚠️ 同时把「counter-scale 到底按什么取值」再逼近一步：
//    若三组的分界与**节点是否在视口内**无关（都在视口内/外两种都有），
//    就不是「懒加载」而是**节点自带的固定值**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, canvasBaseline, diffNodePositions } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const selCount = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const status = async () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });

const readTag = async (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { found: false };
  const t = n.querySelector('[data-testid="flow-node-selected-tag"]');
  if (!t) return { found: false, why: '节点内无该 testid' };
  const r = t.getBoundingClientRect();
  const cs = getComputedStyle(t);
  const nr = n.getBoundingClientRect();
  return { found: true, tag: `${Math.round(r.width)}×${Math.round(r.height)}`,
    counter: cs.getPropertyValue('--octo-canvas-node-chrome-counter-scale').trim(),
    nodeSel: n.className.includes('selected'), nodeBox: `${Math.round(nr.width)}×${Math.round(nr.height)}`,
    inViewport: nr.right > 0 && nr.bottom > 0 && nr.left < 1280 && nr.top < 720 };
}, id);

const ID = 'node_pxvkay973v';   // 基线导演台，别人建的，不动它
out.start = { sel: await selCount(), status: await status(), credits: await credits() };
out.rest = { sel: await selCount(), ...(await readTag(ID)) };
log('静息（未选中）：', JSON.stringify(out.rest));

// 选中它：点节点本体（不点任何按钮、不点热区）
const box = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  const r = n.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; }, ID);
if (!box) { log('🔴 找不到导演台节点'); }
else {
  await p.mouse.click(box.x, box.y);
  await p.waitForTimeout(1200);
  out.selected = { sel: await selCount(), ...(await readTag(ID)) };
  log('选中后：    ', JSON.stringify(out.selected));
  await p.keyboard.press('Escape');
  await p.waitForTimeout(1000);
  out.back = { sel: await selCount(), ...(await readTag(ID)) };
  log('再取消选中：', JSON.stringify(out.back));
}
out.p1f = { rest: out.rest?.tag, selected: out.selected?.tag, back: out.back?.tag,
  verdict: out.rest?.tag !== out.selected?.tag ? '两态不同' : (out.selected?.tag === out.back?.tag ? '选中态与静息态相同' : '读数不稳定') };
log('P1f 判定：', JSON.stringify(out.p1f));

out.end = { sel: await selCount(), status: await status(), credits: await credits() };
log('终态：', JSON.stringify(out.end), '｜积分未变 =', out.start.credits === out.end.credits);
writeFileSync(new URL('./_tmp-b89f.json', import.meta.url), JSON.stringify(out, null, 1));
log('已写 _tmp-b89f.json');
await b.close();
