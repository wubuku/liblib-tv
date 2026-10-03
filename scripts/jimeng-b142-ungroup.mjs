// 批次 142 归位 c 轮：**最后手段** —— 用键盘把组选中并解组。
//
// 🔴 前四版归位策略全部失败（详见本轮注释）。当前画布已叠到 **2 个组**，
//   必须用**不依赖任何点击落点**的办法清掉。
//
// 📌 唯一还没试过的路：**`Tab` 键在 React Flow 里循环选中节点**。
//   若能把焦点/选中移到组上，`⌘⇧G` 就成立（手册明确：取消编组需选中组）。
//   本轮逐次按 `Tab`，每步都**回读「哪个 data-id 被选中」**，
//   命中组就立刻按 `⌘⇧G`。
//
// ⚠️ 纪律：按字母键前必须过 `keyGuard`；`Tab` 虽非字母键，
//   但它会移动焦点，**每步之后都要重新读焦点与选中态**。
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { 组数, selCount, idsOf, selIds } from './jimeng-b139-lib.mjs';
import { findEmptyPane } from './jimeng-b136-lib.mjs';
import fs from 'node:fs';

const 基线 = fs.readFileSync('/tmp/b120-baseline-ids.txt', 'utf8').split('\n').map((s) => s.trim()).filter(Boolean);
const rec = { 尝试: [] };
const { b, p } = await openCanvas();
const R = readers(p);

const 当前选中 = () => p.evaluate(() => ({
  选中节点: Array.from(document.querySelectorAll('.react-flow__node.selected'))
    .filter((n) => !/^__group-resize-chrome__/.test(n.getAttribute('data-id') || ''))
    .map((n) => n.getAttribute('data-id')),
  选中真身组: Array.from(document.querySelectorAll('.react-flow__node-group'))
    .filter((g) => !/^__group-resize-chrome__/.test(g.getAttribute('data-id') || ''))
    .filter((g) => g.classList.contains('selected')).length,
  组id: Array.from(document.querySelectorAll('.react-flow__node-group'))
    .filter((g) => !/^__group-resize-chrome__/.test(g.getAttribute('data-id') || ''))
    .map((g) => g.getAttribute('data-id')),
  焦点: (() => { const a = document.activeElement;
    return a ? { tag: a.tagName, testid: a.getAttribute('data-testid'), label: a.getAttribute('aria-label') } : null; })(),
}));

try {
  await keyGuard(p);
  await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p) };
  await p.mouse.move(1276, 716); await p.waitForTimeout(600);

  // ---- 逐次 Tab，找选中态落到组上的那一刻
  for (let i = 0; i < 40; i++) {
    const g = await keyGuard(p);
    if (!g.safe) { rec.尝试.push({ i, keyGuard: g }); break; }
    await p.keyboard.press('Tab');
    await p.waitForTimeout(320);
    const s = await 当前选中();
    rec.尝试.push({ i, ...s });
    if (s.选中真身组 > 0) {
      // 命中组 ⇒ 立刻 ⌘⇧G
      rec.命中组 = { i, ...s };
      const g2 = await keyGuard(p);
      if (!g2.safe) { rec.失败 = 'keyGuard 不通过'; break; }
      await p.keyboard.press('Meta+Shift+KeyG');
      await p.waitForTimeout(2500);
      await settle(p, R);
      rec.解组后 = { 组数: await 组数(p), 状态行: await R.status() };
      if ((await 组数(p)) > 0) {
        // 一次只解掉一个 ⇒ 继续循环
        rec.继续 = true;
        continue;
      }
      break;
    }
  }

  // ---- 若还有组，再试一轮「点空白 → Tab 循环」
  if ((await 组数(p)) > 0) {
    rec.第二轮 = [];
    for (let k = 0; k < 3 && (await 组数(p)) > 0; k++) {
      const 空 = await findEmptyPane(p);
      if (空) { await p.mouse.click(空.x, 空.y); await p.waitForTimeout(900); }
      for (let i = 0; i < 40 && (await 组数(p)) > 0; i++) {
        const g = await keyGuard(p);
        if (!g.safe) break;
        await p.keyboard.press('Tab');
        await p.waitForTimeout(280);
        const s = await 当前选中();
        if (s.选中真身组 > 0) {
          rec.第二轮.push({ k, i, 命中: true });
          const g2 = await keyGuard(p);
          if (g2.safe) {
            await p.keyboard.press('Meta+Shift+KeyG');
            await p.waitForTimeout(2200);
            await settle(p, R);
          }
        }
      }
    }
  }

  // ---- 删孤儿
  const 当前 = await idsOf(p);
  rec.多余 = 当前.filter((x) => !基线.includes(x) && !/^__group-resize-chrome__/.test(x));
  rec.删除 = [];
  for (const id of rec.多余) {
    // 组成员被组卡片罩住可能点不到 ⇒ 先看它是否还在某个组里
    const 在组里 = await p.evaluate((i) => {
      const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      if (!n) return 'gone';
      return !!(n.closest('.react-flow__node-group'));
    }, id);
    rec.删除.push({ id, 在组里 });
  }
} catch (e) { rec.异常 = String(e && e.stack || e).slice(0, 500); }
fs.writeFileSync(new URL('./_tmp-b142-ungroup.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log('命中组:', JSON.stringify(rec.命中组));
console.log('解组后:', JSON.stringify(rec.解组后));
console.log('第二轮命中数:', (rec.第二轮 || []).length);
console.log('多余:', JSON.stringify(rec.多余));
console.log('尝试样例:', JSON.stringify((rec.尝试 || []).slice(0, 6)));
await b.close();
