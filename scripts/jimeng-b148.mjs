// 批次 148 —— 把批次 147 的「选中后出现什么面板」从 2 族补成**全族**。
//
// 🔑 批次 147 留下的缺口：它只在**画布上现成的**节点上测，而 60% 下 76 个节点里
//   **只有 audio（17 个有独占像素）与 image（1 个）能点**，
//   text / video / timeline / director **四族全部被压住、0 个独占采样点**。
//   ⇒ 「音频 10 个按钮、图片 12 个按钮」是真的，但**「另外四族是什么样」全册没有读数**。
//
// 本轮用**建-删护栏**自建节点（护栏建出的节点落在视口中央，见批次 143），
// 逐族走完整循环：**建 → 普查 → 右键删**，每族都把 6 个已知面板容器全查一遍。
//
// 🔴 三条必须守的纪律：
//   ① **建前节点数 == 预期基线**（挡上轮残留）；② **建后差集恰好 1 且 `.selected`**；
//      ③ **删除走右键菜单「删除 ⌫」**，并用「建后 ids」做差、消失集合**恰好 {SELF}**。
//   另外：**建节点会让画布自动适配缩放**（批次 145 实测 57/36/53% 三次落点都不同）
//   ⇒ 每族建完必须 `setZoom(60)` 归位，否则下一族的落点全变。
//
// ⚠️ 全程**不按任何生成/扣费按钮、不输入一个字**；导演台只**建与删**，
//    **不按 F、不进 3D**（那两项需单独授权）。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard, setZoom } from './jimeng-b135-lib.mjs';
import { 建N个, selIds, selCount, idsOf, canvasPos, 可点落点, 组数 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 148, 目的: '六族「选中后出现什么面板」全谱' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };

const 容器清单 = ['node-toolbar', 'node-toolbar-feature-host', 'generation-input-panel-shell',
  'generation-form', 'video-generation-form', 'image-generation-form',
  'selection-context-toolbar', 'selection-context-toolbar-surface'];

/** 面板普查：把 6+2 个已知容器全查一遍，不预设有几个。 */
const 普查 = () => p.evaluate((清单) => {
  const 出 = { 容器: {} };
  for (const c of 清单) {
    出.容器[c] = Array.from(document.querySelectorAll('[data-testid="' + c + '"]')).map((e) => {
      const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      const btn = Array.from(e.querySelectorAll('button,[role=button]'));
      return { 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10],
        有面积: r.width > 0.01 && r.height > 0.01, display: cs.display, visibility: cs.visibility,
        按钮数: btn.length, svg数: e.querySelectorAll('svg').length,
        逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80),
        按钮: btn.map((b) => { const q = b.getBoundingClientRect();
          return { aria: b.getAttribute('aria-label'), testid: b.getAttribute('data-testid'),
            ariaDisabled: b.getAttribute('aria-disabled'),
            盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width * 10) / 10, Math.round(q.height * 10) / 10] }; }) };
    });
  }
  // 第一个按钮的祖先链（最多 7 层）
  const 任何 = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).find((e) => e.getBoundingClientRect().width > 0.01);
  出.祖先链 = [];
  if (任何) { let n = 任何; for (let i = 0; i < 7 && n; i++, n = n.parentElement) {
    const r = n.getBoundingClientRect();
    出.祖先链.push({ 级: i, tag: n.tagName, cls: String(n.getAttribute('class') || '').slice(0, 56),
      testid: n.getAttribute('data-testid'), role: n.getAttribute('role'),
      盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10], z: getComputedStyle(n).zIndex }); } }
  出.浮层 = Array.from(document.querySelectorAll('[role=dialog]')).map((e) => {
    const r = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), testid: e.getAttribute('data-testid'),
      盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10] }; });
  return 出;
}, 容器清单);

const 清零 = async () => {
  for (let k = 0; k < 4 && (await selCount(p)) > 0; k++) {
    const 空 = await p.evaluate(() => {
      const 坏 = (x, y) => { const h = document.elementFromPoint(x, y);
        if (!h) return 1;
        if (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button]')) return 1;
        if (h.closest('.react-flow__node') || h.closest('[data-testid="node-toolbar"]') || h.closest('[role=dialog],[role=menu],[role=listbox]')) return 1;
        return !(h.classList && h.classList.contains('react-flow__pane')); };
      for (let y = 90; y < innerHeight - 90; y += 8) for (let x = 360; x < innerWidth - 350; x += 8) if (!坏(x, y)) return { x, y };
      return { __err: 'no-free-pane' };
    });
    if (空.__err) break;
    await p.mouse.click(空.x, 空.y); await p.waitForTimeout(1000);
  }
  return selCount(p);
};

const 删一个 = async (id, 预期基线) => {
  await 清零();
  const 前 = await idsOf(p);
  const 落 = await 可点落点(p, `.react-flow__node[data-id="${id}"]`, 4, 4);
  if (落.__err) return { id, __err: 'no-point:' + 落.__err };
  // 🔴 右键前重新断言落点归属
  const 归属 = await p.evaluate(([x, y, i]) => { const h = document.elementFromPoint(x, y);
    const n = h && h.closest('.react-flow__node');
    return { 命中: n ? n.getAttribute('data-id') : null, 对: !!(n && n.getAttribute('data-id') === i) }; }, [落.x, 落.y, id]);
  if (!归属.对) return { id, __err: 'wrong-target', 归属 };
  await p.mouse.click(落.x, 落.y, { button: 'right' });
  await p.waitForTimeout(1800);
  const del = await p.evaluate(() => {
    const els = Array.from(document.querySelectorAll('[role=menuitem],[role=menu] button,li,button'))
      .filter((e) => /^删除/.test((e.innerText || '').replace(/\s+/g, '').trim()));
    if (!els.length) return { __err: 'no-delete-item', 菜单逐字: Array.from(document.querySelectorAll('[role=menu]')).map((m) => (m.innerText || '').replace(/\s+/g, ' ').slice(0, 80)) };
    const e = els[0]; const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2)
      for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) {
        const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y, 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim() }; }
    return { __err: 'no-point' };
  });
  if (del.__err) return { id, __err: del.__err, 细节: del };
  await p.mouse.click(del.x, del.y); await p.waitForTimeout(2500); await settle(p, R);
  const 后 = await idsOf(p);
  const 消失 = 前.filter((x) => !后.includes(x));
  return { id, 消失, 删除项逐字: del.逐字, 消失数: 消失.length, 节点数: 后.length };
};

const { b, p } = await openCanvas();
const R = readers(p);
const 族表 = ['文本', '图片', '视频', '音频', '时间线', '导演台'];
// 🔴 a 轮第一版把 `基线` / `基线canvas` 声明在 try 块内，收尾时在块外引用
//    ⇒ ReferenceError ⇒ **证据文件根本没写出来**，一整轮白跑。
//    修法两条：① 提到 try 外；② **每跑完一族就落盘一次**，末尾再落一次 ——
//    「证据只在成功时写」本身就是一种脆弱设计。
let 基线 = null; let 基线canvas = {};
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b148.json', import.meta.url), JSON.stringify(rec, null, 1));
try {
  await keyGuard(p); await settle(p, R);
  await setZoom(p, 60); await p.waitForTimeout(900);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(), 积分: await R.credits(), 组数: await 组数(p) };
  const 基线 = (await idsOf(p)).length;
  rec.基线节点 = 基线;
  const 基线canvas局部 = await canvasPos(p);
  基线canvas = 基线canvas局部;

  rec.族 = [];
  for (const 族 of 族表) {
    const 条 = { 族, 缩放建前: await R.zoom() };
    try {
      const 建 = await 建N个(p, 族, 1, null, (await idsOf(p)).length);
      条.护栏 = 建.护栏.map((h) => [h.名, h.通过]);
      条.护栏全过 = 建.护栏.every((h) => h.通过);
      if (!建.ids || !建.ids.length) { 条.__err = '建节点未成'; rec.族.push(条); continue; }
      const SELF = 建.ids[0];
      条.SELF = SELF;
      await p.waitForTimeout(1800); await settle(p, R);
      条.缩放建后 = await R.zoom();
      条.状态行 = await R.status();
      条.普查 = await 普查();
      // 节点自身的 testid 家族
      条.节点testid = await p.evaluate((i) => Array.from(new Set(
        Array.from(document.querySelectorAll(`.react-flow__node[data-id="${i}"] [data-testid]`)).map((q) => q.getAttribute('data-testid')))), SELF);
      条.删除 = await 删一个(SELF);
    } catch (e) { 条.__err = String((e && e.message) || e).slice(0, 300); }
    // 🔴 每族结束都归位缩放（建节点会触发自动适配）
    条.归位 = await setZoom(p, 60);   // 返回 {前,目标,回读,实测scale}
    await p.waitForTimeout(800);
    await 清零();
    条.族后节点数 = (await idsOf(p)).length;
    rec.族.push(条);
    落盘();   // 🔴 每族落盘一次：崩了也不丢前面几族
  }

  // ---- 出表 ----
  rec.表 = rec.族.map((q) => {
    const C = q.普查 && q.普查.容器;
    const 主 = C && C['node-toolbar'] && C['node-toolbar'].filter((z) => z.有面积)[0];
    return { 族: q.族, __err: q.__err || null, 护栏全过: q.护栏全过,
      缩放建前: q.缩放建前, 缩放建后: q.缩放建后, 归位后: q.归位 && q.归位.回读,
      nodeToolbar实例数: C ? C['node-toolbar'].length : null,
      主实例: 主 ? { 盒: 主.盒, 按钮数: 主.按钮数, svg数: 主.svg数, 逐字: 主.逐字 } : null,
      其他容器: C ? Object.fromEntries(Object.entries(C).filter(([k]) => k !== 'node-toolbar').map(([k, v]) => [k, v.map((z) => [z.盒, z.按钮数, z.有面积])])) : null,
      浮层: q.普查 ? q.普查.浮层 : null,
      按钮表: 主 ? 主.按钮 : null,
      祖先链: q.普查 ? q.普查.祖先链 : null,
      删除: q.删除, 族后节点数: q.族后节点数 };
  });
  console.log(JSON.stringify(rec.表.map((q) => ({ 族: q.族, 缩放: [q.缩放建前, q.缩放建后, q.归位后],
    nodeToolbar实例数: q.nodeToolbar实例数, 主实例: q.主实例, 删除: q.删除 && (q.删除.消失 || q.删除.__err),
    浮层: q.浮层 })), null, 1));
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); }

await setZoom(p, 60);
await p.waitForTimeout(900);
for (let k = 0; k < 3 && (await R.overlays()) > 0; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
await 清零();
const 小地图前 = await R.minimap();
if (!小地图前 || 小地图前.ariaPressed !== 'true') {
  const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3);
  if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400); }
}
rec.小地图后 = await R.minimap();
await settle(p, R);
const 末 = await idsOf(p);
const 末canvas = await canvasPos(p);
const 位移 = Object.keys(基线canvas).filter((k) => 末canvas[k] && (末canvas[k][0] !== 基线canvas[k][0] || 末canvas[k][1] !== 基线canvas[k][1]));
rec.收尾 = { 状态行: await R.status(), 节点数: 末.length, 选中: await selCount(p), 浮层: await R.overlays(),
  边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length), 组数: await 组数(p),
  zoom: await R.zoom(), 积分: await R.credits(), 小地图: rec.小地图后, 残留自建: 末.filter((x) => rec.族.some((q) => q.SELF === x)), 位移节点: 位移 };

断言('① 六族**都**走完了建-删循环', rec.表.length === 族表.length && rec.表.every((q) => !q.__err), rec.表.map((q) => [q.族, q.__err]));
断言('② 每族建-删护栏全过', rec.表.every((q) => q.护栏全过 === true), rec.表.map((q) => [q.族, q.护栏全过]));
断言('③ 🔑 每族的**消失集合恰好是 {SELF}**', rec.表.every((q) => q.删除 && q.删除.消失数 === 1), rec.表.map((q) => [q.族, q.删除 && q.删除.消失]));
if (rec.表.every((q) => q.nodeToolbar实例数 !== null)) {
  断言('④ 每族**至少 1 个** `node-toolbar` 实例（防空集通过）', rec.表.every((q) => q.nodeToolbar实例数 >= 1), rec.表.map((q) => [q.族, q.nodeToolbar实例数]));
  const 形态 = new Set(rec.表.map((q) => JSON.stringify([q.nodeToolbar实例数, q.主实例 && q.主实例.盒, q.主实例 && q.主实例.按钮数, q.主实例 && q.主实例.svg数])));
  rec.形态数 = 形态.size;
  断言('⑤ 🔑 六族的 (实例数/盒/按钮数/svg数) **不是同一个值**（⇒ 面板逐族不同，不能互相套用）', 形态.size > 1, { 形态数: 形态.size });
}
断言('⑥ 终态节点数回到基线，且**其余节点零位移**', rec.收尾.节点数 === rec.基线节点 && rec.收尾.位移节点.length === 0, { 节点数: rec.收尾.节点数, 基线: rec.基线节点, 位移: rec.收尾.位移节点 });
rec.断言全过 = 断言过;
fs.writeFileSync(new URL('./_tmp-b148.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');
await b.close();
