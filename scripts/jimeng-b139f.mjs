// 批次 139 d 轮收尾：解除编组 → 断言组消失、3 个成员节点回来 → 删掉 3 个 → 救援确认基线。
//
// 📌 本轮顺带第一次验「解除编组」按钮在**组工具条**上的可点性（前面所有轮次组都是选中态，
//   但从没点过这个按钮；批次 130/133 反复证明「工具条按钮的落点必须先扫出真能点到它的点」）。
//
// 护栏：解组前后逐个核对 3 个成员 id **回来且仍在 DOM**；删除按批次 137 护栏走
//   **右键 → 上下文菜单 →「删除」**（不走键盘），删后「建后 ids」做差消失集合恰好那 3 个。
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { 点解除编组, 可点落点, 读组态全, idsOf, selIds, selCount, 组数, canvasPos } from './jimeng-b139-lib.mjs';
import { findEmptyPane } from './jimeng-b136-lib.mjs';
import fs from 'node:fs';

const rec = { 轮: '139d', 成员: ['node_ywws1ng9bk', 'node_sbczb38yf9', 'node_24njfrersn'] };
let 全过 = true;
const 断言 = (名, ok, 详情) => { (rec.断言 = rec.断言 || []).push({ 名, 通过: !!ok, 详情 }); if (!ok) 全过 = false; };

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p);
  await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p),
    zoom: await R.zoom(), 选中数: await selCount(p) };

  // 解组前的组真身（成员 id 用 a 轮记下的三个，不靠 DOM 父子关系反推 ——
  //   🔴 d 轮第一版用 `parentElement` 找成员，读到 `[]`：`顶层节点: 0`，
  //   说明 React Flow 把**所有**节点都包在某个祖先 `.react-flow__node` 里，判据找错了层）
  const 解组前 = await p.evaluate(() => {
    const 真身 = Array.from(document.querySelectorAll('.react-flow__node-group'))
      .filter((g) => !/^__group-resize-chrome__/.test(g.getAttribute('data-id') || ''));
    const g = 真身[0];
    return { 真身数: 真身.length, 组id: g ? g.getAttribute('data-id') : null,
      选中: g ? g.classList.contains('selected') : false };
  });
  rec.解组前 = 解组前;
  断言('①起始有 1 个真身组且选中', 解组前.真身数 === 1 && 解组前.选中, 解组前);
  // 记下成员 canvas 坐标（解组后要核对位置没被动过）
  const 成员canvas前 = await canvasPos(p);
  rec.成员canvas前 = Object.fromEntries(Object.entries(成员canvas前).filter(([k]) => rec.成员.includes(k)));
  const 成员都在 = rec.成员.every((id) => 成员canvas前[id] !== undefined);
  断言('①b 三个成员 id 此刻都在 DOM 里', 成员都在, { 成员: rec.成员, 找到: Object.keys(rec.成员canvas前) });

  // ---- 点「解除编组」
  const un = await 点解除编组(p);
  rec.解除编组 = un;
  断言('②点解除编组后组消失', un.ok, un);
  rec.解组后 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p), 选中: await selIds(p) };

  // ---- 断言 3 个成员**都回来了**且 id 逐个一致
  const 解组后ids = await idsOf(p);
  const 都回来 = rec.成员.every((id) => 解组后ids.includes(id));
  断言('③解组后 3 个成员 id 逐个回来', 都回来, { 成员: rec.成员, 缺失: rec.成员.filter((id) => !解组后ids.includes(id)) });
  // 成员 canvas 位置没被动过
  const 成员canvas后 = await canvasPos(p);
  const 位置变了 = rec.成员.filter((id) => JSON.stringify(成员canvas前[id]) !== JSON.stringify(成员canvas后[id]));
  断言('④成员 canvas 坐标零位移', 位置变了.length === 0, { 位置变了 });

  // ---- 记录解组后「多选工具条」的状态（解组后成员恢复选中 ⇒ 回多选态）
  rec.解组后工具条 = await p.evaluate(() => {
    const tb = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'));
    const 排 = tb.map((e) => ({ e, w: e.getBoundingClientRect().width })).sort((a, b) => b.w - a.w);
    const e = 排[0] ? 排[0].e : null;
    const inner = e ? e.querySelector('[data-testid="selection-context-toolbar"]') : null;
    return e ? { 屏上宽: 排[0].w, 逐字: inner ? (inner.innerText || '').replace(/\s+/g, ' ').trim() : null,
      按钮: Array.from(e.querySelectorAll('button,[role=button]')).map((b2) => b2.getAttribute('data-toolbar-value') || b2.getAttribute('aria-label')) } : null;
  });

  // ---- 删掉 3 个成员（右键 → 删除，不用键盘）
  const 建后ids = await idsOf(p);
  rec.删除 = [];
  for (const id of rec.成员) {
    const 落 = await 可点落点(p, `.react-flow__node[data-id="${id}"]`, 4, 4);
    if (落.__err) { rec.删除.push({ id, 失败: 落 }); 全过 = false; continue; }
    await p.mouse.click(落.x, 落.y, { button: 'right' });
    await p.waitForTimeout(1600);
    const del = await p.evaluate(() => {
      const els = Array.from(document.querySelectorAll('[role=menuitem],[role=menu] button,li,button'))
        .filter((e) => /^删除/.test((e.innerText || '').replace(/\s+/g, '').trim()));
      if (!els.length) return { __err: 'no-delete-item' };
      const e = els[0]; const r = e.getBoundingClientRect();
      for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2)
        for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) {
          const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y, 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim() };
        }
      return { __err: 'no-point' };
    });
    if (del.__err) { rec.删除.push({ id, 失败: del }); 全过 = false; continue; }
    await p.mouse.click(del.x, del.y);
    await p.waitForTimeout(2200);
    await settle(p, R);
    const 还在 = (await idsOf(p)).includes(id);
    rec.删除.push({ id, 菜单逐字: del.逐字, 已消失: !还在 });
  }
  const 删后ids = await idsOf(p);
  const 消失 = 建后ids.filter((x) => !删后ids.includes(x));
  rec.删后 = { 节点数: 删后ids.length, 消失, 消失数: 消失.length };
  断言('⑤删除后消失集合恰好是那 3 个成员', 消失.length === 3 && rec.成员.every((x) => 消失.includes(x)), rec.删后);
  // 其余节点 canvas 零位移
  const 其余 = 建后ids.filter((x) => !rec.成员.includes(x));
  const 删后canvas = await canvasPos(p);
  const 被移动 = 其余.filter((id) => JSON.stringify(成员canvas前[id]) !== JSON.stringify(删后canvas[id]));
  断言('⑥其余节点 canvas 零位移', 被移动.length === 0, { 被移动 });
} catch (e) { rec.异常 = String(e && e.stack || e).slice(0, 600); 全过 = false; }

// 收尾读数
try {
  await settle(p, R);
  rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p),
    选中: await selCount(p), 浮层: await R.overlays(), zoom: await R.zoom(), minimap: await R.minimap() };
} catch (e) { rec.收尾异常 = String(e && e.message).slice(0, 200); }

rec.断言全过 = 全过;
fs.writeFileSync(new URL('./_tmp-b139d.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify({ 断言: rec.断言, 解组后工具条: rec.解组后工具条, 删后: rec.删后, 收尾: rec.收尾 }, null, 1));
console.log('断言全过', 全过);
await b.close();
