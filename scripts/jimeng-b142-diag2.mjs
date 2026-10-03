// 批次 142 诊断二：**未选中态的组卡片，到底有哪些方式能把它选中**（归位通道的最后一块拼图）。
//
// 🔴 现状：救援脚本连栽两次 ——
//   ① 「精确定位标题叶子 + 校验命中」→ 有时命中、有时 `title-unreachable`（被上层节点压住）；
//   ② 「无预校验直点标题中心」→ **点了也没选中**（`选中真身组数: 0`）
//      ⇒ 手册 §3.35「未选中时点标题文字可正常选中组」**在当前构建 + 标题被压住时已不成立**；
//   ③ `⌘⇧G` 兜底 → 需要组先选中 ⇒ 死锁。
//
// 本轮把「怎么选中一个未选中的组」**穷举一遍**，每条路径都单独记录结果，
// 找到**至少一条稳定可用**的，才能写进救援脚本。
// 候选路径：
//   P1 点标题文字中心（已证伪一次，但要确认是不是**坐标**问题）
//   P2 点标题带的**不同位置**（左端/中/右端）
//   P3 点组卡片**上沿外侧**的窄带（标题带在卡片之上 17px）
//   P4 点**组内某个成员节点** ⇒ 选中成员（不是组）→ 再看组是否联动
//   P5 先点空白取消一切，再点标题
//   P6 缩放改变 ⇒ 组是否自动进入可选状态
//   P7 右键组卡片 ⇒ 是否弹菜单（能删就够归位）
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { 组数, selCount, idsOf } from './jimeng-b139-lib.mjs';
import { findEmptyPane } from './jimeng-b136-lib.mjs';
import fs from 'node:fs';

const rec = { 路径: {} };
const { b, p } = await openCanvas();
const R = readers(p);
const 快照 = async (tag) => rec.路径[tag] = {
  组数: await 组数(p), 选中: await selCount(p),
  选中真身组: await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node-group'))
    .filter((g) => !/^__group-resize-chrome__/.test(g.getAttribute('data-id') || ''))
    .filter((g) => g.classList.contains('selected')).length),
};
const 组几何 = () => p.evaluate(() => {
  const g = document.querySelector('.react-flow__node-group:not([data-id^="__group-resize-chrome__"])');
  if (!g) return null;
  const r = g.getBoundingClientRect();
  const 叶子 = Array.from(g.querySelectorAll('span,div')).filter((e) => {
    if (!(e.textContent || '').trim()) return false;
    if (e.querySelector('span,div')) return false;
    const er = e.getBoundingClientRect();
    return er.width > 1 && er.height > 1 && er.width < 200 && er.height < 60;
  }).map((e) => { const er = e.getBoundingClientRect();
    return { 逐字: (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 12),
      屏上: { x: Math.round(er.x), y: Math.round(er.y), w: Math.round(er.width), h: Math.round(er.height) } }; });
  return { 卡片: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
    pe: getComputedStyle(g).pointerEvents, z: getComputedStyle(g).zIndex, 叶子 };
});

try {
  await keyGuard(p);
  await settle(p, R);
  rec.起点 = await 快照('起点');
  rec.几何 = await 组几何();

  const 叶子 = rec.几何 && rec.几何.叶子[0];

  // P1 标题中心
  if (叶子) {
    const cx = Math.round(叶子.屏上.x + 叶子.屏上.w / 2), cy = Math.round(叶子.屏上.y + 叶子.屏上.h / 2);
    rec.路径.P1标题中心 = { 点: [cx, cy] };
    await p.mouse.click(cx, cy); await p.waitForTimeout(1300);
    rec.路径.P1标题中心.后 = await 快照('P1后');
  }
  // P2 标题带不同位置
  if (叶子 && (await 组数(p)) === 1) {
    rec.路径.P2标题带多点 = [];
    for (const dx of [0.1, 0.5, 0.9]) {
      const cx = Math.round(叶子.屏上.x + 叶子.屏上.w * dx), cy = Math.round(叶子.屏上.y + 叶子.屏上.h / 2);
      await p.mouse.click(cx, cy); await p.waitForTimeout(1000);
      const s = await 快照(`P2@${dx}`);
      rec.路径.P2标题带多点.push({ dx, 点: [cx, cy], 选中真身组: s.选中真身组 });
      if (s.选中真身组) break;
    }
  }
  // P5 先清空再点
  if ((await 组数(p)) === 1) {
    const 空 = await findEmptyPane(p);
    if (空) { await p.mouse.click(空.x, 空.y); await p.waitForTimeout(1000); }
    rec.路径.P5清空后 = await 快照('P5清空后');
    if (叶子) {
      const cx = Math.round(叶子.屏上.x + 叶子.屏上.w / 2), cy = Math.round(叶子.屏上.y + 叶子.屏上.h / 2);
      await p.mouse.click(cx, cy); await p.waitForTimeout(1300);
      rec.路径.P5清空后点标题 = await 快照('P5点后');
    }
  }
  // P4 点成员节点 → 看组是否联动
  if (叶子 && (await 组数(p)) === 1) {
    const r = rec.几何.卡片;
    const cx = Math.round(r.x + r.w / 2), cy = Math.round(r.y + r.h / 2);
    const 命中 = await p.evaluate(([x, y]) => { const h = document.elementFromPoint(x, y);
      return h ? { tag: h.tagName, 所属节点: h.closest('.react-flow__node') ? h.closest('.react-flow__node').getAttribute('data-id') : null } : null; }, [cx, cy]);
    rec.路径.P4成员中心 = { 点: [cx, cy], 命中 };
    await p.mouse.click(cx, cy); await p.waitForTimeout(1300);
    rec.路径.P4成员中心.后 = await 快照('P4后');
  }
  // P7 右键组卡片
  if (叶子 && (await 组数(p)) === 1) {
    const cx = Math.round(叶子.屏上.x + 叶子.屏上.w / 2), cy = Math.round(叶子.屏上.y + 叶子.屏上.h / 2);
    await p.mouse.click(cx, cy, { button: 'right' }); await p.waitForTimeout(1600);
    rec.路径.P7右键标题 = {
      菜单项: await p.evaluate(() => Array.from(document.querySelectorAll('[role=menuitem]'))
        .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim())),
      浮层数: await p.evaluate(() => Array.from(document.querySelectorAll('[role=menu]')).filter((m) => m.getBoundingClientRect().width > 1).length),
    };
    await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  }
  // P8 换缩放后是否自动可点
  if (叶子) {
    const { setZoom } = await import('./jimeng-b135-lib.mjs');
    await setZoom(p, 50);
    const g2 = await 组几何();
    rec.路径.P8换缩放50 = { 几何: g2, 后: await 快照('P8后') };
    if (g2 && g2.叶子[0]) {
      const l2 = g2.叶子[0];
      const cx = Math.round(l2.屏上.x + l2.屏上.w / 2), cy = Math.round(l2.屏上.y + l2.屏上.h / 2);
      const 命中 = await p.evaluate(([x, y]) => { const h = document.elementFromPoint(x, y);
        return h ? (h.tagName + '.' + String(h.className || '').split(' ')[0]).slice(0, 40) : null; }, [cx, cy]);
      rec.路径.P8命中 = { 点: [cx, cy], 命中 };
      await p.mouse.click(cx, cy); await p.waitForTimeout(1300);
      rec.路径.P8点后 = await 快照('P8点后');
    }
    await setZoom(p, 60);
  }
} catch (e) { rec.异常 = String(e && e.stack || e).slice(0, 500); }
fs.writeFileSync(new URL('./_tmp-b142-diag2.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify(rec, null, 1).slice(0, 3500));
await b.close();
