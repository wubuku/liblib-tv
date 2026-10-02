// 批次 97 · 事故恢复：把误删的**别人的**节点 `node_3p3sa1sgsv`（音频 31）放回去。
//
// 🔴🔴 **事故经过**（原样记录，不淡化）：
//   b 轮 Part 2 想「自建一个音频节点」做试听/多音色测试。左栏「音频」按钮
//   （`40×40@16,319`）点下去之后，**节点数 39 → 39 根本没变** —— 建节点**失败了**
//   （适配画布的 23% 档下左栏可能收起/命中了别的元素）。
//   而脚本的致命一步是：**没有校验「建前建后 id 集合的差集」**，而是退而取了
//   `document.querySelectorAll('.react-flow__node-audio')` 的**最后一个**当作「我建的」。
//   那最后一个是 **`node_3p3sa1sgsv` = 「音频 31」，别的会话建的**。
//   收尾时按 id 把它删了 ⇒ **节点数 39 → 38**。
//
//   同轮还有第二处误伤：`[aria-label^="Add "]` 匹配到 **39 个 `Add tags`**
//   （每个节点上的标签按钮），脚本把前两个 `Add tags` `.click()` 了 —— 点开了别人的标签编辑。
//
//   🔑 **两条教训（比这次事故本身更值钱）**：
//     ① **「我建的东西」必须用 id 集合差集锁定**，且**当场校验差集非空**。
//        绝不能用「取最后一个」或「取 selected 的」来猜 —— 共享画布上这两个都是别人的。
//     ② **建节点失败要当场判失败**，不能带着「假设建成功了」继续跑后半程。
//        本轮 `nodes` 明明没变，却继续跑完并进入删除流程。
//
// 恢复手段：批次 92 已证明 **⌘Z 能恢复删除的节点，且是同一个 id、同一个 canvas 坐标**。
// a 轮留了 `node_3p3sa1sgsv` 的 `translate`，恢复后要**逐字比对**才算数。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { readFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const VICTIM = 'node_3p3sa1sgsv';

// a 轮留存的原始坐标（恢复后逐字比对）
let recorded = null;
try {
  const a = JSON.parse(readFileSync(new URL('./_tmp-b97a.json', import.meta.url), 'utf8'));
  recorded = a.p1.find((r) => r.id === VICTIM) || null;
} catch (e) { log('⚠️ 读不到 a 轮证据：', e.message); }
out.recorded = recorded;
log('a 轮留存的受害者记录：', JSON.stringify(recorded));

const selN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const nodeN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });
const zoomLabel = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const toolAria = () => p.evaluate(() => { const t = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  return t ? t.getAttribute('aria-label') : null; });
const probe = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { present: false };
  const r = n.getBoundingClientRect();
  return { present: true, aria: n.getAttribute('aria-label'), translate: n.style.transform,
    screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` };
}, id);

out.before = { nodes: await nodeN(), sel: await selN(), credits: await credits(), victim: await probe(VICTIM) };
log('恢复前：', JSON.stringify(out.before));

if (out.before.victim.present) {
  log('✅ 受害者还在，无需恢复');
} else {
  // Esc 到底 + 确保没有输入焦点（否则 ⌘Z 可能变成打字）
  for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
  // ⌘Z 之前先检查有没有残留的标签编辑框 / 输入框（b 轮误点了两个 Add tags）
  out.strayUi = await p.evaluate(() => ({
    inputs: Array.from(document.querySelectorAll('input,textarea'))
      .map((e) => { const r = e.getBoundingClientRect();
        return { tag: e.tagName, type: e.getAttribute('type'), aria: e.getAttribute('aria-label'),
          w: Math.round(r.width), h: Math.round(r.height) }; })
      .filter((x) => x.w > 0 && x.h > 0),
    editable: document.querySelectorAll('[contenteditable="true"],.ProseMirror').length,
    menus: document.querySelectorAll('[role="menu"],[role="listbox"],[data-testid="canvas-context-menu"]').length }));
  log('恢复前残留 UI：', JSON.stringify(out.strayUi));

  const g = await keyGuard(p);
  out.keyGuard = g;
  log('keyGuard：', JSON.stringify(g));
  if (!g.safe) log('⛔ 焦点不安全，不按 ⌘Z（避免变成打字）');
  else {
    for (let k = 1; k <= 3; k++) {
      await p.keyboard.press('Meta+z');
      await p.waitForTimeout(1600);
      const v = await probe(VICTIM);
      out[`afterUndo${k}`] = v;
      log(`⌘Z 第 ${k} 次 →`, JSON.stringify(v));
      if (v.present) { out.restoredAt = k; break; }
    }
  }
}

out.after = { nodes: await nodeN(), sel: await selN(), credits: await credits(), victim: await probe(VICTIM) };
log('恢复后：', JSON.stringify(out.after));

// 逐字比对坐标
if (out.after.victim.present && recorded) {
  out.match = {
    id: out.after.victim.aria === recorded.aria,
    aria: out.after.victim.aria, recordedAria: recorded.aria,
    translate: out.after.victim.translate === recorded.translate,
    got: out.after.victim.translate, want: recorded.translate,
    screen: out.after.victim.screen === recorded.screen,
  };
  log('与 a 轮记录逐字比对：', JSON.stringify(out.match));
}

// 收尾：确保没有残留的编辑框 / 菜单，别把脏状态留给别人
for (let k = 0; k < 2; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
out.cleanUi = await p.evaluate(() => ({
  editable: document.querySelectorAll('[contenteditable="true"],.ProseMirror').length,
  menus: document.querySelectorAll('[role="menu"],[role="listbox"],[data-testid="canvas-context-menu"]').length,
  visibleInputs: Array.from(document.querySelectorAll('input,textarea'))
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .map((e) => e.getAttribute('aria-label') || e.type) }));
log('清理后残留 UI：', JSON.stringify(out.cleanUi));

if (await selN() !== '0') { await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
if (await toolAria() !== '选择工具') { await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1100); }
out.restore = {};
for (let k = 1; k <= 4; k++) {
  const zl = await zoomLabel();
  if (zl && /, 60%$/.test(zl)) { out.restore = { ok: true, tries: k - 1 }; break; }
  await p.click('[data-testid="canvas-zoom-percent"]'); await p.waitForTimeout(1000);
  if (await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'))) {
    await p.evaluate(() => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, '60');
      i.dispatchEvent(new Event('input', { bubbles: true }));
      i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); });
    await p.waitForTimeout(1700);
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);
  if (k === 4) out.restore = { ok: false, tries: 4 };
}
out.end = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), tool: await toolAria() };
log('缩放归位：', JSON.stringify(out.restore), out.restore.ok ? '✅' : '🔴');
log('终态：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b97c-restore.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
