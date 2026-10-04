// 批次 156-f —— 用**抓手工具**平移（手册 `navigate-canvas.md:57-65,95` 已建档的机制）
//
// 🔴 156-e 为什么拖不动：手册写得很清楚 —— **选择工具**下空白处左键拖拽 = **框选**，
//    **不是平移**；要平移必须先点 dock 第一个按钮切到**抓手工具**。
//    实测与手册预测**完全一致**：transform 只在 y 上动了 -90px、x 零变化（框选不挪视口）。
//    ⇒ 📌 这条**再次印证**手册第 410 行那句「空白拖拽=框选（不平移）」，不是新发现。
//    📌 **立规 15：动手前先问「手册是不是已经写过这个机制了」** —— 我连着两轮自己瞎试。
//
// ✅ 本轮：切抓手 → 拖到目标 → 断言工具条与节点对齐 → 打开 tools 菜单 → 点「保存到主体库」
//    → 回主体库对账 → **撤回** → 切回选择工具 → 断言 transform 与起点逐字相同。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: '156f', 目的: '抓手工具平移 → tools 菜单 → 保存到主体库 → 验证 → 撤回' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b156f.json', import.meta.url), JSON.stringify(rec, null, 1));
const 串 = (x, n) => { const s = JSON.stringify(x, null, 1); return s === undefined ? 'undefined' : s.slice(0, n || 2000); };

const 读transform = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport'); return e ? e.style.transform : null; });
const 读节点屏上 = (id) => p.evaluate((i) => { const n = document.querySelector('.react-flow__node[data-id="' + i + '"]');
  if (!n) return null; const r = n.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; }, id);
const 读工具条 = () => p.evaluate(() => Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'))
  .map((e) => { const r = e.getBoundingClientRect(); return { 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)], 按钮数: e.querySelectorAll('button').length }; })
  .filter((z) => z.盒[0] > 0 && z.盒[1] > 0));
const 读抓手 = () => p.evaluate(() => Array.from(document.querySelectorAll('button,[role=button]'))
  .map((b) => { const r = b.getBoundingClientRect();
    return { aria: b.getAttribute('aria-label'), testid: b.getAttribute('data-testid'), 逐字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 10),
      盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)], 状态: b.getAttribute('data-state'), pressed: b.getAttribute('aria-pressed') }; })
  .filter((z) => z.盒[0] > 0 && /选择工具|抓手工具|抓手|选择/.test((z.aria || '') + z.逐字)));

const 找点 = (pred) => p.evaluate((pd) => {
  const cands = Array.from(document.querySelectorAll(pd.sel)).filter((b) => {
    if (pd.toolbarValue && b.getAttribute('data-toolbar-value') !== pd.toolbarValue) return false;
    if (pd.字面等于 && (b.innerText || '').replace(/\s+/g, ' ').trim() !== pd.字面等于) return false;
    const a = b.getAttribute('aria-label') || '';
    if (pd.ariaIncludes && a.indexOf(pd.ariaIncludes) < 0) return false;
    if (pd.角色 === 'menuitem' && b.getAttribute('role') !== 'menuitem') return false;
    return true;
  });
  const 全部 = [], 可用 = [];
  for (const b of cands) {
    const r = b.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) continue;
    const cx = Math.round(r.x + r.width / 2); const cy = Math.round(r.y + r.height / 2);
    const h = document.elementFromPoint(cx, cy);
    const btn = h && h.closest(pd.sel);
    const z = { x: cx, y: cy, 宽: Math.round(r.width), 高: Math.round(r.height), aria: b.getAttribute('aria-label'),
      testid: b.getAttribute('data-testid'), toolbarValue: b.getAttribute('data-toolbar-value'),
      逐字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30), disabled: b.getAttribute('aria-disabled'),
      在视口内: cx >= 0 && cy >= 0 && cx <= innerWidth && cy <= innerHeight, 中心是自己: btn === b };
    全部.push(z); if (z.在视口内 && z.中心是自己) 可用.push(z);
  }
  return { 候选数: cands.length, 全部, 可用 };
}, pred);

const 拖 = async (dx, dy) => {
  const 起 = await p.evaluate(() => { const 坏 = (x, y) => { const h = document.elementFromPoint(x, y); if (!h) return 1;
    if (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button],[role=menuitem]')) return 1;
    if (h.closest('.react-flow__node') || h.closest('[data-testid="node-toolbar"]') || h.closest('[role=dialog],[role=menu],[role=listbox]')) return 1;
    return !(h.classList && h.classList.contains('react-flow__pane')); };
    for (let y = 130; y < innerHeight - 130; y += 10) for (let x = 400; x < innerWidth - 400; x += 10) if (!坏(x, y)) return { x, y };
    return { __err: 'no-free-pane' }; });
  if (起.__err) return { __err: 'no-free-pane' };
  await p.mouse.move(起.x, 起.y); await p.mouse.down();
  for (let k = 1; k <= 12; k++) { await p.mouse.move(起.x + Math.round(dx * k / 12), 起.y + Math.round(dy * k / 12)); await p.waitForTimeout(45); }
  await p.mouse.up(); await p.waitForTimeout(1500);
  return { 落点: 起 };
};

const 读主体库 = () => p.evaluate(() => {
  const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x), Math.round(r.y)]; };
  const d = Array.from(document.querySelectorAll('[role=dialog]')).find((x) => x.getBoundingClientRect().width > 200);
  if (!d) return { 命中: false };
  return { 命中: true, 逐字: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 500),
    testid清单: Array.from(new Set(Array.from(d.querySelectorAll('[data-testid]')).map((x) => x.getAttribute('data-testid')))).sort(),
    可见按钮: Array.from(d.querySelectorAll('button,[role=button]')).map((x) => ({ aria: x.getAttribute('aria-label'), testid: x.getAttribute('data-testid'),
      逐字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18), 盒: 盒(x), disabled: x.getAttribute('aria-disabled') })).filter((z) => z.盒[0] > 0) };
});

const { b, p } = await openCanvas();
const R = readers(p);
let 起点transform = null; let 切了抓手 = false; let 拖动量 = null;
try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
  起点transform = await 读transform();
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(), 积分: await R.credits(), 选中: await selCount(p), transform: 起点transform };

  // ===== 切抓手工具 =====
  rec.抓手钮 = await 读抓手();
  console.log('dock 工具钮', 串(rec.抓手钮, 900));
  const G = (rec.抓手钮 || [])[0];
  if (G) {
    const cx = G.盒[2] + G.盒[0] / 2; const cy = G.盒[3] + G.盒[1] / 2;
    const ok = await p.evaluate(([x, y, a]) => { const h = document.elementFromPoint(x, y); const b = h && h.closest('button,[role=button]');
      return { 对: !!(b && (b.getAttribute('aria-label') || '') === a), 中心是谁: b ? b.getAttribute('aria-label') : null }; }, [cx, cy, G.aria]);
    rec.抓手落点校验 = ok;
    if (ok.对) {
      await p.mouse.click(cx, cy); await p.waitForTimeout(1200);
      rec.抓手切后 = await 读抓手();
      切了抓手 = true;
      console.log('抓手切后', 串(rec.抓手切后, 600));
      断言('⓪ 点 dock 首钮后 aria 在「选择工具 ⇄ 抓手工具」之间翻转', JSON.stringify(rec.抓手切后) !== JSON.stringify(rec.抓手钮), { 前: rec.抓手钮, 后: rec.抓手切后 });
    }
  }

  // ===== 抓手态下拖平移 =====
  const IMG = 'node_gref4sw056';
  const before = await 读节点屏上(IMG);
  rec.平移前节点屏上 = before;
  const dx = 560 - (before ? before[2] + before[0] / 2 : 0);
  const dy = 380 - (before ? before[3] + before[1] / 2 : 0);
  拖动量 = [dx, dy]; rec.拖动量 = 拖动量;
  rec.拖 = await 拖(dx, dy);
  rec.平移后transform = await 读transform();
  rec.平移后节点屏上 = await 读节点屏上(IMG);
  rec.平移后工具条 = await 读工具条();
  落盘();
  console.log('\n拖动量', 拖动量, '| transform', 起点transform, '→', rec.平移后transform);
  console.log('节点屏上', JSON.stringify(before), '→', JSON.stringify(rec.平移后节点屏上), '| 工具条', JSON.stringify(rec.平移后工具条));
  断言('① 抓手态下拖拽**真的平移了视口**（transform 变了且 x 分量也变）', /translate\((-?[\d.]+)px/.test(rec.平移后transform || '') && rec.平移后transform !== 起点transform, { 前: 起点transform, 后: rec.平移后transform });

  if (rec.平移后节点屏上 && rec.平移后节点屏上[2] >= 0) {
    const 落 = await 可点落点(p, `.react-flow__node[data-id="${IMG}"]`, 4, 4);
    rec.落点 = 落;
    if (!落.__err) {
      const 归属 = await p.evaluate(([x, y, i]) => { const h = document.elementFromPoint(x, y);
        const n = h && h.closest('.react-flow__node'); return !!(n && n.getAttribute('data-id') === i); }, [落.x, 落.y, IMG]);
      rec.归属 = 归属;
      if (归属) {
        await p.mouse.click(落.x, 落.y); await p.waitForTimeout(1800);
        rec.选中数 = await selCount(p);
        rec.选中后工具条 = await 读工具条();
        const T = await 找点({ sel: 'button,[role=button]', toolbarValue: 'tools' });
        rec.tools钮 = T;
        const t = (T.可用 || [])[0];
        rec.tools落点 = t || null;
        console.log('\ntools 钮', 串(T, 900));
        if (t) {
          await p.mouse.click(t.x, t.y); await p.waitForTimeout(1800);
          rec.菜单 = await p.evaluate(() => {
            const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x), Math.round(r.y)]; };
            const ms = Array.from(document.querySelectorAll('[role=menu],[role=listbox]')).filter((x) => x.getBoundingClientRect().width > 100);
            if (!ms.length) return { 命中: false };
            const m = ms[ms.length - 1];
            return { 命中: true, 菜单数: ms.length, role: m.getAttribute('role'), aria: m.getAttribute('aria-label'), 盒: 盒(m),
              逐字: (m.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400),
              项: Array.from(m.querySelectorAll('[role=menuitem]')).map((it) => ({ 逐字: (it.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 26),
                aria: it.getAttribute('aria-label'), 盒: 盒(it), disabled: it.getAttribute('aria-disabled'), svg数: it.querySelectorAll('svg').length })) };
          });
          落盘();
          console.log('\n🆕 tools 菜单', 串(rec.菜单, 2800));
          const 项 = (rec.菜单 || {}).项 || [];
          const 保存项 = 项.find((z) => /主体库|保存到主体/.test(z.逐字));
          rec.保存到主体库项 = 保存项 || null;
          断言('② 「工具」菜单打开且含「保存到主体库」', (rec.菜单 || {}).命中 === true && !!保存项, { 项: 项.map((z) => z.逐字) });
          if (保存项) {
            const lp = await p.evaluate(([x, y, w, h]) => { for (let yy = Math.ceil(y) + 2; yy <= y + h - 2; yy += 2)
              for (let xx = Math.ceil(x) + 2; xx <= x + w - 2; xx += 2) { const el = document.elementFromPoint(xx, yy);
                if (el && el.closest('[role=menuitem]')) return { x: xx, y: yy }; } return { __err: 'no-point' }; }, 保存项.盒);
            rec.保存落点 = lp;
            if (!lp.__err) {
              await p.mouse.click(lp.x, lp.y);
              rec.保存后轮询 = [];
              for (let i = 0; i < 6; i++) { await p.waitForTimeout(1000); rec.保存后轮询.push({ 秒: i + 1, 浮层: await R.overlays() }); }
              rec.保存后积分 = await R.credits();
              落盘();
              console.log('\n保存后轮询', 串(rec.保存后轮询, 500), '| 积分', rec.保存后积分);
            }
          }
          for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
        }
      }
    }
  }

  // ===== 拖回 + 切回选择工具 =====
  if (切了抓手 && 拖动量) { await 拖(-拖动量[0], -拖动量[1]); rec.拖回后transform = await 读transform(); }
  const 抓手后 = await 读抓手();
  if (切了抓手 && (抓手后 || []).length) {
    const h = (抓手后 || [])[0];
    await p.mouse.click(h.盒[2] + h.盒[0] / 2, h.盒[3] + h.盒[1] / 2); await p.waitForTimeout(1200);
    rec.切回后 = await 读抓手();
  }
  for (let k = 0; k < 3 && (await selCount(p)) > 0; k++) {
    const 空 = await p.evaluate(() => { const 坏 = (x, y) => { const h = document.elementFromPoint(x, y); if (!h) return 1;
      if (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button],[role=menuitem]')) return 1;
      if (h.closest('.react-flow__node') || h.closest('[data-testid="node-toolbar"]') || h.closest('[role=dialog],[role=menu],[role=listbox]')) return 1;
      return !(h.classList && h.classList.contains('react-flow__pane')); };
      for (let y = 90; y < innerHeight - 90; y += 8) for (let x = 360; x < innerWidth - 350; x += 8) if (!坏(x, y)) return { x, y };
      return { __err: 'no-free-pane' }; });
    if (空.__err) break; await p.mouse.click(空.x, 空.y); await p.waitForTimeout(900);
  }

  // ===== 主体库对账 =====
  const 库 = await 找点({ sel: 'button,[role=button]', 字面等于: '资产库' });
  const L = (库.可用 || [])[0];
  if (L) {
    await p.mouse.click(L.x, L.y); await p.waitForTimeout(2200);
    const 页签 = await p.evaluate(() => Array.from(document.querySelectorAll('[role=tab]')).map((t) => { const r = t.getBoundingClientRect();
      return { 逐字: (t.innerText || '').replace(/\s+/g, ' ').trim(), cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }));
    const 主 = 页签.find((z) => z.逐字 === '主体');
    if (主) { await p.mouse.click(主.cx, 主.cy); await p.waitForTimeout(2000); rec.主体库保存后 = await 读主体库(); }
    rec.删除候选 = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role=button],[role=menuitem]'))
      .map((x) => { const r = x.getBoundingClientRect();
        return { aria: x.getAttribute('aria-label'), testid: x.getAttribute('data-testid'),
          逐字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20), 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; })
      .filter((z) => z.盒[0] > 0 && z.盒[1] > 0 && /删除|移除|Delete|Remove|✕|×/i.test((z.aria || '') + z.逐字)));
    落盘();
    console.log('\n🆕 主体库（保存后）', 串(rec.主体库保存后, 2600));
    console.log('删除候选', 串(rec.删除候选, 1000));
    for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

await settle(p, R);
const mm = await R.minimap();
if (!mm || mm.ariaPressed !== 'true') { const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3); if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400); } }
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(),
  zoom: await R.zoom(), 积分: await R.credits(), 边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length) };
落盘();
console.log('\n起点 transform =', 起点transform, '| 拖回后 =', rec.拖回后transform, '| 逐字相同 =', 起点transform === rec.拖回后transform);
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');
断言('③ 收尾积分**仍是 805**', String(rec.收尾.积分).indexOf('805') >= 0, { 积分: rec.收尾.积分 });
rec.断言全过 = 断言过; 落盘();
await b.close();
