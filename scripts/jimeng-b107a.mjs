// 批次 107 · a 轮：备弹药 —— 建**自己的**文本节点与时间线节点。
//
// 🎯 靶子：`help-and-shortcuts.md` 快捷键表里**唯一两项**「未验证」：
//   ① **文本「三级标题」`⌘ ⌥ 3`** —— 🔴「面板声明了、本页全表照抄了，
//      但**没有任何实测结论**」。它也是仓库自带的
//      `scripts/jimeng-shortcut-reconcile.mjs` **唯一**标记为
//      「除照抄全表外正文找不到任何结论」的那一项。
//   ② **时间线「缩放时间线」`⌘ scroll`** —— ❓「未单独实测，
//      只验证过**画布侧**的同一按键」。
//
// 弹药从批次 102 来：`.txt`/`.md` 上传会变成**文本节点**（免费），
// 所以 ① **根本不需要生成**。② 需要一个**自己的**时间线节点
// —— ⛔ 不用画布上那两个 `时间线 1` / `时间线 2`，它们是**别人的**，
//   在别人的时间线上按 `⌘ scroll` 是**改别人的数据**。
//
// 🔴 批次 105 立了**第四道护栏**（点之前用 `elementFromPoint` 证明命中、
//   点之后必须读到 `selected === true`），本轮全程按它走。
//   画布此刻已被别人堆到 ~76 个节点，框选是公认的头号陷阱，本轮**一律不用框选**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString() };
const DOC = '/tmp/jimeng-b107-h3.md';
const save = () => writeFileSync(new URL('./_tmp-b107a.json', import.meta.url), JSON.stringify(out, null, 1));

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const selIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
const status = () => p.evaluate(() => {
  const t = document.body.innerText;
  const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1],
    edges: (t.match(/(\d+) edges?/) || [])[1],
    zoom: z ? z.getAttribute('aria-label') : null,
    tool: (document.querySelector('[data-testid="canvas-pointer-tool-toggle"]') || { getAttribute: () => null }).getAttribute('aria-label'),
    credits: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label') };
});
const safeEval = async (fn, arg, tries = 8) => {
  for (let k = 0; k < tries; k++) { const r = await p.evaluate(fn, arg); if (!r || !r.__err) return r; await p.waitForTimeout(700); }
  return { __err: 'gave-up' }; };

/** 建一个节点：做完动作后取「本轮新增的 id」，并核验差集恰好一个且同时 selected */
async function makeNode(label, act, waitMs = 1500, tries = 24) {
  const before = await allIds();
  await act();
  for (let k = 1; k <= tries; k++) {
    await p.waitForTimeout(waitMs);
    const created = (await allIds()).filter((id) => !before.includes(id));
    if (created.length) {
      await p.waitForTimeout(1200);
      const newSel = (await selIds()).filter((id) => !before.includes(id));
      const ok = created.length === 1 && newSel.length === 1 && newSel[0] === created[0];
      log(`  ${label}：新增 ${created.length} 个，新选中 ${newSel.length} 个 ⇒ ${ok ? '✅' : '🔴 护栏不通过'}`);
      log(`    id=${created[0]}  sel=${JSON.stringify(newSel)}`);
      return ok ? created[0] : null;
    }
  }
  log(`  ${label}：🔴 没等到新节点`);
  return null;
}

// ================= 起点 =================
out.start = await status();
log('起点：', JSON.stringify(out.start));
out.idsBefore = (await allIds()).length;
out.creditsBefore = out.start.credits;
log('起点 id 数：', out.idsBefore, '｜积分', out.start.credits);

// ================= ① 文本节点 =================
log('\n===== ① 上传 .md 建文本节点 =====');
let chooserSeen = null;
p.on('filechooser', async (fc) => { chooserSeen = { isMultiple: fc.isMultiple() };
  try { await fc.setFiles(DOC); log('  setFiles：', DOC); } catch (e) { log('  setFiles 失败：', e.message); } });
const up = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button,[role=button]'))
  .find((x) => x.getAttribute('aria-label') === '上传'); if (!e) return null;
  const r = e.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
log('左栏上传入口：', JSON.stringify(up));
if (!up) { log('🔴 找不到上传入口'); save(); await b.close(); process.exit(1); }
out.chooser = chooserSeen;
out.textId = await makeNode('文本节点', async () => {
  await p.mouse.move(up.x, up.y); await p.waitForTimeout(600);
  await p.mouse.click(up.x, up.y);
});
save();

if (out.textId) {
  await p.waitForTimeout(3500);
  out.textInfo = await safeEval((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!n) return { __err: 'gone' };
    const r = n.getBoundingClientRect();
    return { aria: n.getAttribute('aria-label'), text: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 200),
      screen: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
      transform: n.style.transform,
      testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
      // 🔴 第四道护栏的前置：落点是否安全（在不在别人节点矩形里、命中最上层是不是它）
      safeSpots: (() => {
        const others = Array.from(document.querySelectorAll('.react-flow__node'))
          .filter((e) => e.getAttribute('data-id') !== i)
          .map((e) => { const q = e.getBoundingClientRect(); return { x: q.x, y: q.y, w: q.width, h: q.height }; })
          .filter((o) => o.w > 0 && o.h > 0);
        const cands = [];
        for (let fy = 0.2; fy <= 0.5; fy += 0.1) for (let fx = 0.2; fx <= 0.8; fx += 0.1) {
          const x = r.x + r.width * fx, y = r.y + r.height * fy;
          if (x < 2 || y < 2 || x > window.innerWidth - 2 || y > window.innerHeight - 2) continue;
          const el = document.elementFromPoint(x, y);
          if (!el || !(el === n || n.contains(el))) continue;
          if (others.some((o) => x >= o.x && x <= o.x + o.w && y >= o.y && y <= o.y + o.h)) continue;
          cands.push({ x: Math.round(x), y: Math.round(y) });
        }
        return { total: cands.length, sample: cands.slice(0, 5) };
      })() };
  }, out.textId);
  log('\n文本节点读数：', JSON.stringify(out.textInfo, null, 1));
}

// ================= ② 时间线节点 =================
log('\n===== ② 左栏建时间线节点 =====');
const tlBtn = await p.evaluate(() => {
  const all = Array.from(document.querySelectorAll('button,[role=button]'))
    .map((e) => { const q = e.getBoundingClientRect();
      return { aria: e.getAttribute('aria-label'), x: Math.round(q.x), y: Math.round(q.y), w: Math.round(q.width), h: Math.round(q.height) }; })
    .filter((x) => /时间线/.test(x.aria || '') && x.w > 0 && x.h > 0);
  return all;
});
log('左栏里带「时间线」字样的按钮：', JSON.stringify(tlBtn));
if (tlBtn.length) {
  const t0 = tlBtn[0];
  out.timelineId = await makeNode('时间线节点', async () => {
    await p.mouse.move(t0.x + t0.w / 2, t0.y + t0.h / 2); await p.waitForTimeout(600);
    await p.mouse.click(t0.x + t0.w / 2, t0.y + t0.h / 2);
  });
  if (out.timelineId) {
    await p.waitForTimeout(2500);
    out.timelineInfo = await safeEval((i) => {
      const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      if (!n) return { __err: 'gone' };
      const r = n.getBoundingClientRect();
      return { aria: n.getAttribute('aria-label'), text: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 260),
        screen: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
        transform: n.style.transform,
        testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
        arias: Array.from(new Set(Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')))).slice(0, 20) };
    }, out.timelineId);
    log('\n时间线节点读数：', JSON.stringify(out.timelineInfo, null, 1));
  }
}

out.end = await status();
out.idsAfter = (await allIds()).length;
log('\n本轮终态：', JSON.stringify(out.end), '｜id 数', out.idsBefore, '→', out.idsAfter);
out.mine = [out.textId, out.timelineId].filter(Boolean);
log('本轮自建 id：', JSON.stringify(out.mine));
out.clean = out.mine.length === 2;
save();
log('已落盘');
await b.close();
