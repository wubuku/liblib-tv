// 批次 142 归位 h 轮：组已进视口 ⇒ 现在**逐格扫组卡片**，找真正能命中「组真身」的像素。
//
// 🔑 进度：g 轮已把第一个组带进视口（`y=316..652`，`在视口内: true`，
//   且 `canvas位移数 0` 证明滚轮只改视图）。
//   但点卡片**中心**命中的是 `DIV.absolute` —— 那是组卡片自己的内层容器
//   （未选中态 `pointer-events: none`，会**穿透**，所以点它等于点空白）。
//
// ✅ 本轮：**在组卡片矩形内逐格 `elementFromPoint`**，
//   找出所有**命中组真身或其后代**的点；命中就点，然后查有没有出现组工具条。
//   （批次 133/136 立的纪律：返回值 ≠ 命中者；这里直接用命中测试当判据。）
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { 组数, idsOf, 可点落点 } from './jimeng-b139-lib.mjs';
import fs from 'node:fs';

const 基线 = fs.readFileSync('/tmp/b120-baseline-ids.txt', 'utf8').split('\n').map((s) => s.trim()).filter(Boolean);
const rec = { 扫描: [] };
const { b, p } = await openCanvas();
const R = readers(p);

try {
  await keyGuard(p);
  await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p) };

  for (let round = 0; round < 3 && (await 组数(p)) > 0; round++) {
    const 扫 = await p.evaluate(() => {
      const gs = Array.from(document.querySelectorAll('.react-flow__node-group'))
        .filter((g) => !/^__group-resize-chrome__/.test(g.getAttribute('data-id') || ''));
      if (!gs.length) return null;
      const g = gs[0];
      const gid = g.getAttribute('data-id');
      const r = g.getBoundingClientRect();
      const 命中组 = [];
      const 统计 = {};
      for (let y = Math.max(Math.ceil(r.y), 66); y <= Math.min(r.bottom, 690); y += 2)
        for (let x = Math.ceil(r.x); x <= Math.min(r.right, 1270); x += 2) {
          const h = document.elementFromPoint(x, y);
          const k = h ? (h.tagName + '.' + String(h.className || '').split(' ')[0]).slice(0, 42) : 'null';
          统计[k] = (统计[k] || 0) + 1;
          if (h && (h === g || g.contains(h))) 命中组.push([x, y]);
        }
      return { gid, 卡片: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
        命中组点数: 命中组.length, 命中组样例: 命中组.slice(0, 5), 统计 };
    });
    rec.扫描.push({ round, 扫 });
    if (!扫) break;
    if (扫.命中组点数 > 0) {
      const [x, y] = 扫.命中组样例[0];
      await p.mouse.click(x, y);
      await p.waitForTimeout(1500);
      const 选中组 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node-group'))
        .filter((q) => !/^__group-resize-chrome__/.test(q.getAttribute('data-id') || ''))
        .filter((q) => q.classList.contains('selected')).length);
      const 工具条 = await p.evaluate(() => {
        const e = document.querySelector('[data-toolbar-value="ungroup"]');
        if (!e) return null;
        const r = e.getBoundingClientRect();
        return { 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim(),
          矩形: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) } };
      });
      rec.扫描[rec.扫描.length - 1].点后 = { 点: [x, y], 选中组, 工具条 };
      if (选中组 > 0 && 工具条) {
        const 解 = await 可点落点(p, '[data-toolbar-value="ungroup"]', 3, 3);
        rec.扫描[rec.扫描.length - 1].解除编组落点 = 解;
        if (!解.__err) {
          await p.mouse.click(解.x, 解.y);
          await p.waitForTimeout(2500);
          await settle(p, R);
          rec.扫描[rec.扫描.length - 1].解后组数 = await 组数(p);
          if ((await 组数(p)) === 0) break;
          continue;
        }
      }
    } else {
      // 扫不到 ⇒ 先把这个组再滚一点，然后重扫
      await p.mouse.move(640, 400);
      await p.mouse.wheel(0, 240);
      await p.waitForTimeout(500);
    }
  }

  const 终 = await idsOf(p);
  rec.末尾 = { 状态行: await R.status(), 节点数: 终.length, 组数: await 组数(p) };
  rec.与基线差集 = { 多: 终.filter((x) => !基线.includes(x) && !/^__group-resize-chrome__/.test(x)), 少: 基线.filter((x) => !终.includes(x)) };
} catch (e) { rec.异常 = String(e && e.stack || e).slice(0, 500); }
fs.writeFileSync(new URL('./_tmp-b142-ungroup6.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify(rec.扫描, null, 1).slice(0, 3000));
console.log('末尾', JSON.stringify(rec.末尾), '| 差集', JSON.stringify(rec.与基线差集));
await b.close();
