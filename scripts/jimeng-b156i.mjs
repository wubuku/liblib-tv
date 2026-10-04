// 批次 156-i —— 主体库对账 + **撤回**（156-h 已经点过「保存到主体库」，共享数据不能留残留）
//
// 🔴 156-h 的两个错（本轮要写进 AUDIT）：
//   ① **按 innerText 找「资产库」按钮找不到** —— 它的**可见文字是空的**，`aria-label` 才逐字是「资产库」。
//      156-a 找得到是因为那边的 `字面等于` 判的是 **aria**；我在 156-h 把它改成了判 innerText。
//      ⇒ 📌 **立规 18：改脚本时逐字照抄原脚本的判据，不要凭印象重写**。
//         「同一个谓词名在不同脚本里判的东西不一样」—— 这类漂移比 bug 更难发现，因为两边都"能跑"。
//   ② 由此导致 ①⑥ 两条断言读成空串，**看起来像「主体库没反应」，实际是「对话框压根没打开」**。
//      两者都表现为 `命中:false`，日志上无法区分 ⇒ 必须额外记一条「按钮点没点上」。
//
// ✅ 本轮只做对账与撤回：开库 → 主体页 → 读当前逐字 → 与 156-a 的基线比 → 找删除入口 → 删 → 断言回到基线。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: '156i', 目的: '主体库对账 + 撤回 156-h 写入的主体' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b156i.json', import.meta.url), JSON.stringify(rec, null, 1));
const 串 = (x, n) => { const s = JSON.stringify(x, null, 1); return s === undefined ? 'undefined' : s.slice(0, n || 2000); };

// 🔑 逐字照抄 156-a 的找点判据：字面等于判的是 **aria-label**
const 找点 = (pred) => p.evaluate((pd) => {
  const cands = Array.from(document.querySelectorAll(pd.sel)).filter((b) => {
    const a = b.getAttribute('aria-label') || ''; const t = (b.innerText || '').replace(/\s+/g, ' ').trim();
    if (pd.ariaIncludes && a.indexOf(pd.ariaIncludes) < 0) return false;
    if (pd.字面等于 && a !== pd.字面等于) return false;
    if (pd.文字Includes && t.indexOf(pd.文字Includes) < 0) return false;
    if (pd.角色 === 'menuitem' && b.getAttribute('role') !== 'menuitem') return false;
    return true; });
  const 全部 = [], 可用 = [];
  for (const b of cands) {
    const r = b.getBoundingClientRect(); if (!(r.width > 0 && r.height > 0)) continue;
    const cx = Math.round(r.x + r.width / 2); const cy = Math.round(r.y + r.height / 2);
    const h = document.elementFromPoint(cx, cy); const btn = h && h.closest(pd.sel);
    const t2 = (b.innerText || '').replace(/\s+/g, ' ').trim();
    const z = { x: cx, y: cy, 宽: Math.round(r.width), 高: Math.round(r.height), 左: Math.round(r.x), 上: Math.round(r.y),
      aria: b.getAttribute('aria-label'), testid: b.getAttribute('data-testid'), 逐字: t2.slice(0, 22), disabled: b.getAttribute('aria-disabled'),
      在视口内: cx >= 0 && cy >= 0 && cx <= innerWidth && cy <= innerHeight, 中心是自己: btn === b };
    全部.push(z); if (z.在视口内 && z.中心是自己) 可用.push(z);
  }
  return { 候选数: cands.length, 全候选: 全部, 可用 };
}, pred);

const 读库 = (标签) => p.evaluate((tag) => {
  const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x), Math.round(r.y)]; };
  const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
  if (!d) return { 命中: false, 阶段: tag };
  const 主体面板 = d.querySelector('[data-testid="canvas-asset-library-subjects-panel"]');
  const 空态 = d.querySelector('[data-testid="canvas-subject-import-empty"]');
  return { 命中: true, 阶段: tag,
    逐字: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 800),
    盒: 盒(d),
    testid清单: Array.from(new Set(Array.from(d.querySelectorAll('[data-testid]')).map((x) => x.getAttribute('data-testid')))).sort(),
    有主体面板: !!主体面板, 主体面板盒: 主体面板 ? 盒(主体面板) : null,
    空态在: !!空态, 空态逐字: 空态 ? (空态.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120) : null,
    主体面板逐字: 主体面板 ? (主体面板.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 500) : null,
    可点: Array.from(d.querySelectorAll('button,[role=button],[role=menuitem]')).map((x) => { const r = x.getBoundingClientRect();
      return { role: x.getAttribute('role'), aria: x.getAttribute('aria-label'), testid: x.getAttribute('data-testid'),
        逐字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24), 盒: 盒(x), disabled: x.getAttribute('aria-disabled') }; }).filter((z) => z.盒[0] > 0),
    图: Array.from(d.querySelectorAll('img')).map((x) => { const r = x.getBoundingClientRect();
      return { alt: x.getAttribute('alt'), src前: (x.getAttribute('src') || '').slice(0, 40), 盒: 盒(x) }; }).filter((z) => z.盒[0] > 0) };
}, 标签);

const 开库 = async () => {
  const K = await 找点({ sel: 'button,[role=button]', 字面等于: '资产库' });
  const L = (K.可用 || [])[0];
  rec.库钮 = { 候选数: K.候选数, 可用: K.可用 };
  if (!L) return { 点上了: false, 候选数: K.候选数, 全候选: K.全候选 };
  await p.mouse.click(L.x, L.y); await p.waitForTimeout(2400);
  const 页签 = await p.evaluate(() => Array.from(document.querySelectorAll('[role=tab]')).map((t) => { const r = t.getBoundingClientRect();
    return { 逐字: (t.innerText || '').replace(/\s+/g, ' ').trim(), 选中: t.getAttribute('aria-selected'),
      x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; }));
  const 主 = (页签 || []).find((z) => z.逐字 === '主体');
  if (主) { await p.mouse.click(主.x, 主.y); await p.waitForTimeout(2200); }
  return { 点上了: true, 页签, 主体选中: 主 ? 主.选中 : null };
};

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 积分: await R.credits() };
  console.log('起点', JSON.stringify(rec.起点));

  // ===== 对账 =====
  rec.开库 = await 开库();
  rec.当前 = await 读库('当前');
  落盘();
  console.log('\n🆕 主体库（当前）', 串(rec.当前, 3200));
  const 基线逐字 = 'Import assets Choose assets from Dreamina and import them into this canvas. 资产 主体 全部 没有可用主体 已选择 0 个素材 确认 请先选择素材';
  const 当前逐字 = String((rec.当前 || {}).逐字 || '');
  rec.基线逐字 = 基线逐字;
  rec.与基线相同 = 当前逐字 === 基线逐字;
  断言('① 点得到「资产库」钮（aria 判据，不是 innerText）', rec.开库.点上了 === true, rec.开库);
  断言('② 对话框真的打开了（`canvas-asset-library-dialog` 在）', (rec.当前 || {}).命中 === true, rec.开库);
  断言('③ 「保存到主体库」**确实改变了主体库**：当前逐字 ≠ 156-a 记下的空态基线',
    (rec.当前 || {}).命中 === true && rec.与基线相同 === false,
    { 基线: 基线逐字.slice(0, 90), 当前: 当前逐字.slice(0, 160) });
  断言('④ 空态标记 `canvas-subject-import-empty` 已消失', (rec.当前 || {}).空态在 === false,
    { 空态在: (rec.当前 || {}).空态在, 主体面板盒: (rec.当前 || {}).主体面板盒 });

  // ===== 找删除入口 =====
  rec.删除候选 = ((rec.当前 || {}).可点 || []).filter((z) => /删除|移除|delete|remove|✕|×|清空/i.test((z.aria || '') + z.逐字));
  console.log('可点清单', 串((rec.当前 || {}).可点, 2200));
  console.log('删除候选', 串(rec.删除候选, 900));

  if (!rec.删除候选.length) {
    // 悬停主体卡片，看是否浮出操作钮
    const 卡片 = await p.evaluate(() => {
      const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
      if (!d) return { 错: 'no-dialog' };
      const pan = d.querySelector('[data-testid="canvas-asset-library-subjects-panel"]');
      if (!pan) return { 错: 'no-panel' };
      return { 盒: (() => { const r = pan.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; })(),
        子: Array.from(pan.querySelectorAll('*')).slice(0, 60).map((e) => { const r = e.getBoundingClientRect();
          return { tag: e.tagName, role: e.getAttribute('role'), aria: e.getAttribute('aria-label'), testid: e.getAttribute('data-testid'),
            cls: (e.className || '').toString().slice(0, 50), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24),
            盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; })
          .filter((z) => z.盒[0] > 0 && z.盒[1] > 0 && z.盒[2] > 250 && z.盒[3] > 90) };
    });
    rec.主体面板DOM = 卡片;
    console.log('主体面板 DOM', 串(卡片, 2600));
  } else {
    const D = rec.删除候选[0];
    rec.删除落点 = await p.evaluate(([x, y, w, h]) => { const cx = Math.round(x + w / 2); const cy = Math.round(y + h / 2);
      const el = document.elementFromPoint(cx, cy); return { x: cx, y: cy, 命中: !!(el && el.closest('button,[role=button],[role=menuitem]')) }; }, D.盒);
    if (rec.删除落点.命中) {
      await p.mouse.click(rec.删除落点.x, rec.删除落点.y); await p.waitForTimeout(2200);
      rec.删除后浮层 = await p.evaluate(() => Array.from(document.querySelectorAll('[role=alertdialog],[role=dialog]'))
        .map((x) => ({ role: x.getAttribute('role'), testid: x.getAttribute('data-testid'),
          逐字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200),
          盒: (() => { const r = x.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; })() }))
        .filter((z) => z.盒[0] > 0));
      落盘(); console.log('删除后浮层', 串(rec.删除后浮层, 1000));
      rec.删除后库 = await 读库('删除后');
      console.log('删除后库', 串(rec.删除后库, 1600));
    }
  }
  for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
  rec.关库后浮层 = await R.overlays();
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

await settle(p, R);
const mm = await R.minimap();
if (!mm || mm.ariaPressed !== 'true') { const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3); if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400); } }
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(),
  zoom: await R.zoom(), 积分: await R.credits(), 边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length) };
rec.断言全过 = 断言过; 落盘();
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');
await b.close();
