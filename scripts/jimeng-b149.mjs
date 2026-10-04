// 批次 149 —— 复测**全册最陈旧的任务页** `10-tasks/director-node.md`（最新只到批次 89）。
//
// 🎯 选题来自一次静态元审计：17 个任务页按「最新批次号」排序，
//    `director-node.md` 排第一（**批次 89**，249 行），
//    第二名 `assets-and-upload.md` 已是 109。而批次 148 刚好实测到导演台的
//    `node-toolbar` 读数（两实例、`192×0`），与该页第 93–112 行记的**逐字吻合**
//    ⇒ 说明这一页的核心结论还活着，但**11 批没人再碰过它**。
//
// 本轮复测的是该页**最反直觉、最可能随版本变**的几条（全部零风险：
// **不点「进入导演台」**（会离开画布、3D 属需授权范围）、不点任何生成/扣费按钮）：
//   ① 「进入导演台」静息态是 `SPAN` 不可点、**选中后同一位置变 `BUTTON` 但 `aria-label` 变 `null`**
//      （批次 57 + 68 记的「没有任何一个选择器能同时命中两态」）—— **这条最可能已被修好**
//   ② `Rename 导演台` 只在选中时出现（静息→选中差集恰好 1），且**点了不进编辑态**
//   ③ `Add tags` 的边长（批次 89 记本节点 60% 下是 `29×29`，并给了乘法式）
//   ④ `node-toolbar` 两个实例**都是零高度**（批次 85 记 `192×0` + `0×0`）
//   ⑤ 节点内三样东西的**逐字文案**、canvas 恒 `320×320`
//   ⑥ 标签面板 `224×44` + 6 个按钮、**面板内无输入框**（批次 68 记）
//
// ⚠️ 标签只**打上**不点「全部清空」—— 批次 69/70 已实测该按钮点了不生效，
//    再点一次只是重复无效操作；节点当轮删除，标签随节点一起消失。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard, setZoom } from './jimeng-b135-lib.mjs';
import { 建N个, selCount, selIds, idsOf, canvasPos, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 149, 目的: '复测全册最陈旧任务页 director-node.md' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b149.json', import.meta.url), JSON.stringify(rec, null, 1));

/** 节点内全量普查：逐元素记身份与盒。 */
const 普查节点 = (id, 参照盒) => p.evaluate(([i, 参照盒]) => {
  const n = document.querySelector('.react-flow__node[data-id="' + i + '"]');
  if (!n) return { __err: 'not-found' };
  const r = n.getBoundingClientRect();
  const els = Array.from(n.querySelectorAll('*')).map((e) => {
    const q = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return { tag: e.tagName, cls: String(e.getAttribute('class') || '').slice(0, 46),
      aria: e.getAttribute('aria-label'), testid: e.getAttribute('data-testid'),
      逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30),
      盒: [Math.round(q.x * 10) / 10, Math.round(q.y * 10) / 10, Math.round(q.width * 10) / 10, Math.round(q.height * 10) / 10],
      可见: cs.display !== 'none' && cs.visibility !== 'hidden' && q.width > 0.01,
      cursor: cs.cursor, pe: cs.pointerEvents, opacity: cs.opacity };
  });
  return { class: n.className, selected: n.classList.contains('selected'),
    aria: n.getAttribute('aria-label'),
    盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10],
    transform: n.style.transform,
    元素数: els.length, 元素: els,
    testid清单: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
    进入导演台: (() => {
      // 🔴 页面第 57–59 行明写「**没有任何一个选择器能同时命中两态**」「唯一稳定的定位器是**位置**」。
      //   本 census 的第一版**又用了 aria** 去查 ⇒ 选中态必然扑空，**这本身恰好证明了那条结论**。
      //   第二版：**同时**按 aria 找、**并**在节点内按「与静息态同盒」的元素里找 —— 两条都记。
      const 按aria = Array.from(n.querySelectorAll('*')).find((x) => (x.getAttribute('aria-label') || '').includes('进入导演台'));
      const 读 = (e) => { const q = e.getBoundingClientRect(); const cs = getComputedStyle(e);
        return { tag: e.tagName, cls: String(e.getAttribute('class') || '').slice(0, 46), aria: e.getAttribute('aria-label'),
          逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20),
          盒: [Math.round(q.x * 10) / 10, Math.round(q.y * 10) / 10, Math.round(q.width * 10) / 10, Math.round(q.height * 10) / 10],
          cursor: cs.cursor, pe: cs.pointerEvents, 可见: cs.display !== 'none' && q.width > 0.01 }; };
      const out = { 按aria: 按aria ? 读(按aria) : { __err: 'aria 扑空（与页面记的「选中后 aria 变 null」一致）' } };
      const 参照 = (typeof 参照盒 !== 'undefined' && 参照盒) ? 参照盒 : null;
      if (参照) {
        const 按位置 = Array.from(n.querySelectorAll('*')).find((x) => { const q = x.getBoundingClientRect();
          return Math.abs(q.x - 参照[0]) < 1.5 && Math.abs(q.y - 参照[1]) < 1.5
            && Math.abs(q.width - 参照[2]) < 1.5 && Math.abs(q.height - 参照[3]) < 1.5; });
        out.按位置 = 按位置 ? 读(按位置) : { __err: '按位置也没找到' };
      }
      return out;
    })(),
    AddTags: (() => { const e = n.querySelector('[aria-label="Add tags"], [aria-label^="Edit tags"]');
      if (!e) return { __err: 'no-tag-btn' };
      const q = e.getBoundingClientRect();
      return { tag: e.tagName, aria: e.getAttribute('aria-label'), testid: e.getAttribute('data-testid'),
        盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width * 10) / 10, Math.round(q.height * 10) / 10] }; })(),
    Rename: (() => { const e = n.querySelector('[aria-label="Rename 导演台"]');
      if (!e) return { __err: '不在 DOM 里' };
      const q = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      return { tag: e.tagName, 盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width * 10) / 10, Math.round(q.height * 10) / 10],
        cursor: cs.cursor, pe: cs.pointerEvents, 逐字: (e.innerText || '').trim() }; })(),
    手柄: Array.from(n.querySelectorAll('[data-testid^="flow-node-"][data-testid$="-handle"]')).map((e) => {
      const q = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      return { testid: e.getAttribute('data-testid'), 盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width * 10) / 10, Math.round(q.height * 10) / 10],
        opacity: cs.opacity, pe: cs.pointerEvents }; }),
    连通按钮: Array.from(document.querySelectorAll('[aria-label^="Create connected node"]')).map((e) => e.getAttribute('aria-label')),
  };
}, [id, 参照盒 || null]);

/** 工具条实例（批次 85 那条结论的复现点）。🔴 surface 单独放，**不混进实例计数**。 */
const 读工具条 = () => p.evaluate(() => ({
  实例: Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).map((e) => {
    const r = e.getBoundingClientRect();
    return { 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10],
      按钮数: e.querySelectorAll('button,[role=button]').length, svg数: e.querySelectorAll('svg').length };
  }),
  surface: (() => { const e = document.querySelector('[data-testid="selection-context-toolbar-surface"]');
    if (!e) return null; const r = e.getBoundingClientRect();
    return { 盒: [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10], 按钮数: e.querySelectorAll('button,[role=button]').length }; })(),
  featureHost: (() => { const e = document.querySelector('[data-testid="node-toolbar-feature-host"]');
    if (!e) return null; const r = e.getBoundingClientRect();
    return { 盒: [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10] }; })(),
}));

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

const 删一个 = async (id) => {
  await 清零();
  const 前 = await idsOf(p);
  const 落 = await 可点落点(p, `.react-flow__node[data-id="${id}"]`, 4, 4);
  if (落.__err) return { id, __err: 'no-point' };
  const 归属 = await p.evaluate(([x, y, i]) => { const h = document.elementFromPoint(x, y);
    const n = h && h.closest('.react-flow__node'); return { 对: !!(n && n.getAttribute('data-id') === i) }; }, [落.x, 落.y, id]);
  if (!归属.对) return { id, __err: 'wrong-target' };
  await p.mouse.click(落.x, 落.y, { button: 'right' }); await p.waitForTimeout(1800);
  const del = await p.evaluate(() => {
    const els = Array.from(document.querySelectorAll('[role=menuitem],[role=menu] button,li,button'))
      .filter((e) => /^删除/.test((e.innerText || '').replace(/\s+/g, '').trim()));
    if (!els.length) return { __err: 'no-delete-item' };
    const e = els[0]; const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2)
      for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) {
        const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y, 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim() }; }
    return { __err: 'no-point' };
  });
  if (del.__err) return { id, __err: del.__err };
  await p.mouse.click(del.x, del.y); await p.waitForTimeout(2500); await settle(p, R);
  const 后 = await idsOf(p);
  return { id, 消失: 前.filter((x) => !后.includes(x)), 删除项逐字: del.逐字 };
};

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p); await settle(p, R);
  await setZoom(p, 60); await p.waitForTimeout(900);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(), 积分: await R.credits() };
  const 基线canvas = await canvasPos(p);

  const 建 = await 建N个(p, '导演台', 1, null, (await idsOf(p)).length);
  rec.建 = { 护栏: 建.护栏.map((h) => [h.名, h.通过]), ids: 建.ids, ok: 建.ok };
  if (!建.ids || !建.ids.length) rec.中止 = '建节点未成';
  else {
    const SELF = 建.ids[0];
    rec.SELF = SELF;
    await p.waitForTimeout(2000); await settle(p, R);
    rec.缩放建后 = await R.zoom();
    // 静息态：先取消选中
    await 清零();
    rec.静息 = { 普查: await 普查节点(SELF), 工具条: await 读工具条(), 选中数: await selCount(p) };
    const 静息进入 = rec.静息.普查 && rec.静息.普查.进入导演台;
    const 参照盒 = 静息进入 && 静息进入.按aria && !静息进入.按aria.__err ? 静息进入.按aria.盒 : null;
    rec.参照盒 = 参照盒;
    // 选中态
    const 落 = await 可点落点(p, `.react-flow__node[data-id="${SELF}"]`, 4, 4);
    rec.选中落点 = 落;
    if (!落.__err) {
      const 归属 = await p.evaluate(([x, y, i]) => { const h = document.elementFromPoint(x, y);
        const n = h && h.closest('.react-flow__node'); return { 对: !!(n && n.getAttribute('data-id') === i) }; }, [落.x, 落.y, SELF]);
      if (归属.对) {
        await p.mouse.click(落.x, 落.y); await p.waitForTimeout(2200); await settle(p, R);
        rec.选中 = { 普查: await 普查节点(SELF, 参照盒), 工具条: await 读工具条(), 选中: await selIds(p) };
      } else rec.选中归属失败 = 归属;
    }

    // 标签面板：点 Add tags（安全：只是展开一个选择面板）
    const 钮 = rec.选中 && rec.选中.普查 && rec.选中.普查.AddTags;
    if (钮 && !钮.__err) {
      const 安全 = await p.evaluate(([x, y]) => { const h = document.elementFromPoint(x, y);
        return { 命中: h ? h.tagName + '|' + (h.getAttribute('aria-label') || '').slice(0, 20) : null,
          不是生成类: !/生成|generate/i.test((h && h.getAttribute('aria-label')) || '') }; }, [钮.盒[0] + Math.round(钮.盒[2] / 2), 钮.盒[1] + Math.round(钮.盒[3] / 2)]);
      rec.标签钮安全 = 安全;
      if (安全.命中 && 安全.不是生成类) {
        await p.mouse.click(钮.盒[0] + Math.round(钮.盒[2] / 2), 钮.盒[1] + Math.round(钮.盒[3] / 2));
        await p.waitForTimeout(2000); await settle(p, R);
        rec.标签面板 = await p.evaluate(() => {
          const p2 = document.querySelector('[data-testid="canvas-node-tag-selector"]');
          if (!p2) return { __err: 'no-panel' };
          const r = p2.getBoundingClientRect();
          return { 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10],
            按钮数: p2.querySelectorAll('button,[role=button]').length,
            逐字按钮: Array.from(p2.querySelectorAll('button,[role=button]')).map((b) => { const q = b.getBoundingClientRect();
              return { aria: b.getAttribute('aria-label'), value: b.getAttribute('data-toolbar-value'),
                盒: [Math.round(q.width * 10) / 10, Math.round(q.height * 10) / 10] }; }),
            输入面: p2.querySelectorAll('input,textarea,[contenteditable]').length };
        });
        // 关面板（Esc；不点「全部清空」—— 批次 69/70 已实测它不生效）
        await p.keyboard.press('Escape'); await p.waitForTimeout(1000);
        rec.关面板后 = await p.evaluate(() => !!document.querySelector('[data-testid="canvas-node-tag-selector"]'));
      }
    }
    rec.删除 = await 删一个(SELF);
  }
  const 末 = await idsOf(p);
  const 末c = await canvasPos(p);
  const 位移 = Object.keys(基线canvas).filter((k) => 末c[k] && (末c[k][0] !== 基线canvas[k][0] || 末c[k][1] !== 基线canvas[k][1]));
  rec.收尾检查 = { 节点数: 末.length, 位移节点: 位移 };
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); }

await setZoom(p, 60); await p.waitForTimeout(900);
for (let k = 0; k < 3 && (await R.overlays()) > 0; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
await 清零();
const 小地图前 = await R.minimap();
if (!小地图前 || 小地图前.ariaPressed !== 'true') {
  const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3);
  if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400); }
}
rec.小地图后 = await R.minimap();
await settle(p, R);
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p),
  浮层: await R.overlays(), zoom: await R.zoom(), 积分: await R.credits(),
  边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length) };

// ---- 断言（只判互斥性/自洽性；复测类则判「与老读数是否逐字一致」）----
const 静 = rec.静息 && rec.静息.普查, 选 = rec.选中 && rec.选中.普查;
断言('① 走完 静息 → 选中 → 标签面板 → 删除 全流程（无一中止）', !rec.中止 && 静 && 选, { 中止: rec.中止 });
if (静 && 选) {
  断言('② ✅ 「进入导演台」**静息是 SPAN、选中后按位置找到的同一处变成 BUTTON**（批次 68 逐字复现）',
    !!(静.进入导演台.按aria && 选.进入导演台.按位置) && 静.进入导演台.按aria.tag === 'SPAN' && 选.进入导演台.按位置.tag === 'BUTTON',
    { 静息: 静.进入导演台, 选中: 选.进入导演台 });
  断言('③ 🔴 「进入导演台」**选中后按 aria 查必然扑空**（= aria 已变 null，批次 57/68 那条）',
    !!(选.进入导演台.按aria && 选.进入导演台.按位置) && !!选.进入导演台.按aria.__err && 选.进入导演台.按位置.aria === null,
    { 按aria: 选.进入导演台.按aria, 按位置: 选.进入导演台.按位置 });
  断言('④ 两态的「进入导演台」**盒逐字相同**（页面记「唯一稳定的定位器是位置」）',
    !!(静.进入导演台.按aria && 选.进入导演台.按位置) && JSON.stringify(静.进入导演台.按aria.盒) === JSON.stringify(选.进入导演台.按位置.盒),
    { 静息: 静.进入导演台.按aria.盒, 选中: 选.进入导演台.按位置.盒 });
  断言('⑤ ✅ `Rename 导演台` **静息不在 DOM 里、选中后出现**',
    !!静.Rename.__err && !选.Rename.__err, { 静息: 静.Rename, 选中: 选.Rename });
  断言('⑥ ✅ `Add tags` 两态都在、边长逐字相同', !静.AddTags.__err && !选.AddTags.__err
    && 静.AddTags.盒[2] === 选.AddTags.盒[2], { 静息: 静.AddTags, 选中: 选.AddTags });
  断言('⑦ ✅ `node-toolbar` **两个实例、全部零高度**（批次 85 的 `192×0`+`0×0` 逐字复现）',
    rec.选中.工具条.实例.length === 2 && rec.选中.工具条.实例.every((q) => q.盒[3] === 0 && q.按钮数 === 0),
    rec.选中.工具条);
  断言('⑧ ✅ 导演台**没有 ⊕ 连接按钮**（批次 69 逐字复现：`Create connected node` 命中 0）',
    选.连通按钮.length === 0, { 命中: 选.连通按钮 });
}
if (rec.标签面板 && !rec.标签面板.__err) {
  断言('⑨ ✅ 标签面板 `224×44` + **6 个按钮** + 面板内 **0 个输入框**（批次 68 逐字复现）',
    rec.标签面板.盒[2] === 224 && rec.标签面板.盒[3] === 44 && rec.标签面板.按钮数 === 6 && rec.标签面板.输入面 === 0,
    { 盒: rec.标签面板.盒, 按钮数: rec.标签面板.按钮数, 输入面: rec.标签面板.输入面 });
}
if (rec.删除) 断言('⑩ ✅ 删除后**消失集合恰好是 {SELF}**', rec.删除.消失 && rec.删除.消失.length === 1, rec.删除);
if (rec.收尾检查) 断言('⑪ 终态节点数回到基线、其余节点零位移', rec.收尾检查.位移节点.length === 0, rec.收尾检查);

rec.断言全过 = 断言过; 落盘();
console.log('收尾', JSON.stringify(rec.收尾), '| 中止', rec.中止 || '无', '| 异常', rec.异常 || '无');
await b.close();
