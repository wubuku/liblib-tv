// 批次 156-a —— **纯只读探针**（唯一副作用是选中一个节点 + 开两个菜单又关掉）
//
// 🎯 靶子：`subject-node.md:336-345` 的「仍未验证（2026-10-01 批次 62）」两条：
//   ① 「保存到主体库」的**实际保存结果** —— 当时的阻塞理由是「会往主体库里写入持久数据，
//      没法干净地撤回，**在没有单独授权前不执行**」；
//   ② **@主体** 在提示词里的引用效果 —— 「引用是否拼进提示词**未测**，
//      同样卡在『要先有一个真实存在的主体』」。
//   ⇒ 🔑 2026-10-04 目标更新把「保存到主体库」列入解锁清单（测试帐号可做 CRUD），
//      **两条的阻塞理由都已经过期**。
//
// 🔑 本轮只回答「入口在哪、基线是什么」，一个写入动作都不做：
//   Q-a 画布上那个有媒体的图片节点（`node_gref4sw056`，aria 逐字「图片 node: b22-upload」）
//        的**浮动工具条「工具」菜单**里，到底有没有「保存到主体库」这一项、逐字与尺寸是什么。
//   Q-b **资产库 → 主体页**当前逐字是什么（建立「保存前基线」——主体库是**项目级持久数据**，
//        别人也在用，所以动手前必须先把基线记死，撤回时才谈得上「回到原样」）。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf, canvasPos, 可点落点, 组数 } from './jimeng-b139-lib.mjs';

const rec = { 批次: '156a', 目的: '只读：找「保存到主体库」入口 + 记主体库基线' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b156a.json', import.meta.url), JSON.stringify(rec, null, 1));
const 串 = (x, n) => { const s = JSON.stringify(x, null, 1); return s === undefined ? 'undefined' : s.slice(0, n || 2000); };

// 🔑 立规 12：找点三条同时成立（有面积 / 落点在视口内 / elementFromPoint 命中自己）
const 找点 = (pred) => p.evaluate((pd) => {
  const cands = Array.from(document.querySelectorAll(pd.sel)).filter((b) => {
    const a = b.getAttribute('aria-label') || '';
    const t = (b.innerText || '').replace(/\s+/g, ' ').trim();
    if (pd.ariaIncludes && a.indexOf(pd.ariaIncludes) < 0) return false;
    if (pd.字面等于 && a !== pd.字面等于) return false;
    if (pd.文字Includes && t.indexOf(pd.文字Includes) < 0) return false;
    if (pd.testidIncludes && (b.getAttribute('data-testid') || '').indexOf(pd.testidIncludes) < 0) return false;
    if (pd.角色 === 'menuitem' && b.getAttribute('role') !== 'menuitem') return false;
    if (pd.角色 === 'tab' && b.getAttribute('role') !== 'tab') return false;
    return true;
  });
  const 全候选 = [];
  for (const b of cands) {
    const r = b.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) continue;
    const cx = Math.round(r.x + r.width / 2); const cy = Math.round(r.y + r.height / 2);
    const h = document.elementFromPoint(cx, cy);
    const btn = h && h.closest(pd.sel);
    全候选.push({ x: cx, y: cy, 宽: Math.round(r.width), 高: Math.round(r.height), 左: Math.round(r.x), 上: Math.round(r.y),
      aria: b.getAttribute('aria-label'), testid: b.getAttribute('data-testid'), role: b.getAttribute('role'),
      逐字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30), disabled: b.getAttribute('aria-disabled'),
      在视口内: cx >= 0 && cy >= 0 && cx <= innerWidth && cy <= innerHeight, 中心是自己: btn === b });
  }
  return { 候选数: cands.length, 全候选, 可用: 全候选.filter((z) => z.在视口内 && z.中心是自己) };
}, pred);

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(), 积分: await R.credits(), 选中: await selCount(p) };

  // ---------- Q-b1：资产库 → 主体页 基线 ----------
  const 库 = await 找点({ sel: 'button,[role=button]', 字面等于: '资产库' });
  rec.资产库钮 = 库;
  const L = (库.可用 || [])[0];
  if (L) {
    await p.mouse.click(L.x, L.y); await p.waitForTimeout(2200);
    rec.资产库层 = await p.evaluate(() => {
      const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x), Math.round(r.y)]; };
      const d = Array.from(document.querySelectorAll('[role=dialog]')).find((x) => x.getBoundingClientRect().width > 200);
      if (!d) return { 命中: false };
      return { 命中: true, testid: d.getAttribute('data-testid'), aria: d.getAttribute('aria-label'), 盒: 盒(d),
        逐字: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400),
        页签: Array.from(d.querySelectorAll('[role=tab]')).map((t) => ({ 逐字: (t.innerText || '').replace(/\s+/g, ' ').trim(), selected: t.getAttribute('aria-selected'), 盒: 盒(t) })),
        按钮: Array.from(d.querySelectorAll('button,[role=button]')).map((x) => ({ aria: x.getAttribute('aria-label'), testid: x.getAttribute('data-testid'), 逐字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16), 盒: 盒(x) })).filter((z) => z.盒[0] > 0),
        testid清单: Array.from(new Set(Array.from(d.querySelectorAll('[data-testid]')).map((x) => x.getAttribute('data-testid')))).sort() };
    });
    落盘();
    console.log('资产库层', 串(rec.资产库层, 2600));
    const 主体页 = (rec.资产库层 || {}).页签 || [];
    rec.主体页签 = 主体页;
    const 主 = 主体页.find((z) => /主体/.test(z.逐字));
    rec.主体页签命中 = 主 || null;
    if (主) {
      await p.mouse.click(Math.round(主.盒[2] + 主.盒[0] / 2), Math.round(主.盒[3] + 主.盒[1] / 2));
      await p.waitForTimeout(1800);
      rec.主体库基线 = await p.evaluate(() => {
        const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x), Math.round(r.y)]; };
        const d = Array.from(document.querySelectorAll('[role=dialog]')).find((x) => x.getBoundingClientRect().width > 200);
        if (!d) return { 命中: false };
        return { 命中: true, 逐字: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400),
          testid清单: Array.from(new Set(Array.from(d.querySelectorAll('[data-testid]')).map((x) => x.getAttribute('data-testid')))).sort(),
          可见按钮: Array.from(d.querySelectorAll('button,[role=button]')).map((x) => ({ aria: x.getAttribute('aria-label'), testid: x.getAttribute('data-testid'), 逐字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16), 盒: 盒(x) })).filter((z) => z.盒[0] > 0) };
      });
      落盘();
      console.log('\n🆕 主体库基线', 串(rec.主体库基线, 2600));
    }
    for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(900); }
    rec.关库后 = await p.evaluate(() => document.querySelectorAll('[role=dialog]').length);
  }

  // ---------- Q-a：那个图片节点的「工具」菜单 ----------
  const IMG = 'node_gref4sw056';
  rec.图片节点在 = (await idsOf(p)).includes(IMG);
  console.log('\n图片节点在画布上 =', rec.图片节点在);
  if (rec.图片节点在) {
    const 落 = await 可点落点(p, `.react-flow__node[data-id="${IMG}"]`, 4, 4);
    rec.落点 = 落;
    if (!落.__err) {
      const 归属 = await p.evaluate(([x, y, i]) => { const h = document.elementFromPoint(x, y);
        const n = h && h.closest('.react-flow__node'); return { 对: !!(n && n.getAttribute('data-id') === i) }; }, [落.x, 落.y, IMG]);
      rec.归属 = 归属;
      if (归属.对) {
        await p.mouse.click(落.x, 落.y); await p.waitForTimeout(1800);
        rec.选中后 = { 选中数: await selCount(p), 工具条: await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).map((e) => { const r = e.getBoundingClientRect(); return { 盒: [Math.round(r.width), Math.round(r.height)], 按钮: Array.from(e.querySelectorAll('button')).map((b) => (b.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim().slice(0, 14)) }; })) };
        // 点「工具」
        const 工 = await 找点({ sel: 'button,[role=button]', 字面等于: '工具' });
        rec.工具钮 = 工;
        const G = (工.可用 || [])[0];
        if (G) {
          await p.mouse.click(G.x, G.y); await p.waitForTimeout(1600);
          rec.工具菜单 = await p.evaluate(() => {
            const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x), Math.round(r.y)]; };
            const m = Array.from(document.querySelectorAll('[role=menu],[role=listbox]')).find((x) => x.getBoundingClientRect().width > 100);
            if (!m) return { 命中: false };
            return { 命中: true, role: m.getAttribute('role'), testid: m.getAttribute('data-testid'), aria: m.getAttribute('aria-label'), 盒: 盒(m),
              逐字: (m.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300),
              项: Array.from(m.querySelectorAll('[role=menuitem]')).map((it) => ({ 逐字: (it.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 22), aria: it.getAttribute('aria-label'), 盒: 盒(it), disabled: it.getAttribute('aria-disabled'), svg数: it.querySelectorAll('svg').length })) };
          });
          落盘();
          console.log('\n🆕 工具菜单', 串(rec.工具菜单, 2600));
          const 有 = ((rec.工具菜单 || {}).项 || []).some((z) => /主体库|保存到主体/.test(z.逐字));
          断言('⓪ 工具菜单里**有**「保存到主体库」这一项', 有, { 项: (rec.工具菜单 || {}).项 });
          断言('① 主体库基线已记下（撤回时要对账）', !!(rec.主体库基线 || {}).命中, rec.主体库基线);
          for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
        }
      }
    }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

// 收尾：清选中（不删任何东西）
for (let k = 0; k < 3 && (await selCount(p)) > 0; k++) {
  const 空 = await p.evaluate(() => { const 坏 = (x, y) => { const h = document.elementFromPoint(x, y); if (!h) return 1;
    if (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button],[role=menuitem]')) return 1;
    if (h.closest('.react-flow__node') || h.closest('[data-testid="node-toolbar"]') || h.closest('[role=dialog],[role=menu],[role=listbox]')) return 1;
    return !(h.classList && h.classList.contains('react-flow__pane')); };
    for (let y = 90; y < innerHeight - 90; y += 8) for (let x = 360; x < innerWidth - 350; x += 8) if (!坏(x, y)) return { x, y };
    return { __err: 'no-free-pane' }; });
  if (空.__err) break; await p.mouse.click(空.x, 空.y); await p.waitForTimeout(900);
}
await settle(p, R);
const mm = await R.minimap();
if (!mm || mm.ariaPressed !== 'true') { const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3); if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400); } }
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(),
  zoom: await R.zoom(), 积分: await R.credits(), 组数: await 组数(p),
  边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length) };
落盘();
console.log('\n收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');
rec.断言全过 = 断言过; 落盘();
await b.close();
