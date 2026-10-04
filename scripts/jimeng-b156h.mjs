// 批次 156-h —— 「保存到主体库」的真实入口在**右键菜单**，不在浮动工具条的「工具」菜单里
//
// 🔴 156-g 的证伪：`data-toolbar-value="tools"` 菜单逐字只有「编辑 / 消除笔 / 裁剪 / 宫格切分 / 标注」
//    —— 4 个 menuitem + 1 个分组标题「编辑」，**没有「保存到主体库」**。
//    手册 `PROGRESS.md:235 / :269` 早就写明它在 `[data-testid="canvas-context-menu"]`（200×372 九项）。
//    ⇒ 📌 **立规 17：动手前先查「手册把这个功能记在哪一页」**。
//        我连着三轮（f/g/h 之前的规划）都默认它在工具条菜单里，而手册三处写着它在右键菜单。
//
// ✅ 本轮：抓手平移 → 切回选择工具 → 点中带媒体的图片节点 → 右键 → 逐项 dump 9 项
//    → 点「保存到主体库」→ 轮询 → 打开资产库「主体」页对账 → **找删除入口并撤回** → 断言回到基线「没有可用主体」。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: '156h', 目的: '右键菜单 → 保存到主体库 → 主体库对账 → 撤回' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b156h.json', import.meta.url), JSON.stringify(rec, null, 1));
const 串 = (x, n) => { const s = JSON.stringify(x, null, 1); return s === undefined ? 'undefined' : s.slice(0, n || 2000); };

const 读transform = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport'); return e ? e.style.transform : null; });
const tx = (t) => { const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(t || ''); return m ? [parseFloat(m[1]), parseFloat(m[2])] : null; };
const 读节点屏上 = (id) => p.evaluate((i) => { const n = document.querySelector('.react-flow__node[data-id="' + i + '"]');
  if (!n) return null; const r = n.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; }, id);

const 空点 = (ya, yb, xa, xb, s) => p.evaluate(([ya2, yb2, xa2, xb2, st]) => {
  const 坏 = (x, y) => { const h = document.elementFromPoint(x, y); if (!h) return 1;
    if (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button],[role=menuitem]')) return 1;
    if (h.closest('.react-flow__node') || h.closest('[data-testid="node-toolbar"]') || h.closest('[role=dialog],[role=menu],[role=listbox]')) return 1;
    return !(h.classList && h.classList.contains('react-flow__pane')); };
  for (let y = ya2; y < yb2; y += st) for (let x = xa2; x < xb2; x += st) if (!坏(x, y)) return { x, y };
  return { __err: 'no-free-pane' };
}, [ya, yb, xa, xb, s]);

const 拖 = async (dx, dy) => {
  if (!dx && !dy) return { 跳过: '零位移' };
  const 起 = await 空点(130, 600, 400, 880, 10);
  if (起.__err) return 起;
  await p.mouse.move(起.x, 起.y); await p.mouse.down();
  for (let k = 1; k <= 12; k++) { await p.mouse.move(起.x + Math.round(dx * k / 12), 起.y + Math.round(dy * k / 12)); await p.waitForTimeout(45); }
  await p.mouse.up(); await p.waitForTimeout(1400);
  return { 落点: 起, 请求: [dx, dy] };
};

const 切工具 = async (想要) => {
  const g = () => p.evaluate(() => { const b = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
    if (!b) return null; const r = b.getBoundingClientRect();
    return { aria: b.getAttribute('aria-label'), pressed: b.getAttribute('aria-pressed'),
      盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; });
  const b = await g(); if (!b) return { 错: 'no-toggle' };
  if (b.aria === 想要) return { 已就位: true, 态: b };
  await p.mouse.click(b.盒[2] + b.盒[0] / 2, b.盒[3] + b.盒[1] / 2); await p.waitForTimeout(1300);
  const 后 = await g(); return { 前: b, 后, 成功: !!(后 && 后.aria === 想要) };
};

const 读ctx = () => p.evaluate(() => {
  const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x), Math.round(r.y)]; };
  const d = document.querySelector('[data-testid="canvas-context-menu"]');
  if (!d) return { 命中: false };
  const r = d.getBoundingClientRect();
  return { 命中: true, role: d.getAttribute('role'), aria: d.getAttribute('aria-label'), 盒: 盒(d),
    逐字: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400),
    有面积: r.width > 0 && r.height > 0,
    项: Array.from(d.querySelectorAll('[role=menuitem]')).map((it) => { const ir = it.getBoundingClientRect();
      return { 逐字: (it.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30), aria: it.getAttribute('aria-label'),
        盒: 盒(it), disabled: it.getAttribute('aria-disabled'), 分隔线: 0 }; }),
    子元素role: Array.from(new Set(Array.from(d.children).map((c) => c.getAttribute('role') || c.tagName))) };
});

const 读主体库 = (标签) => p.evaluate((tag) => {
  const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x), Math.round(r.y)]; };
  const d = Array.from(document.querySelectorAll('[role=dialog]')).find((x) => x.getBoundingClientRect().width > 200);
  if (!d) return { 命中: false, 阶段: tag };
  return { 命中: true, 阶段: tag, 逐字: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 700),
    testid清单: Array.from(new Set(Array.from(d.querySelectorAll('[data-testid]')).map((x) => x.getAttribute('data-testid')))).sort(),
    可点: Array.from(d.querySelectorAll('button,[role=button],[role=menuitem],[role=tab]')).map((x) => { const r = x.getBoundingClientRect();
      return { role: x.getAttribute('role'), aria: x.getAttribute('aria-label'), testid: x.getAttribute('data-testid'),
        逐字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 22), 盒: 盒(x), disabled: x.getAttribute('aria-disabled') }; }).filter((z) => z.盒[0] > 0) };
}, 标签);

const IMG = 'node_gref4sw056';
const { b, p } = await openCanvas();
const R = readers(p);
let 起点transform = null; let 拖动量 = null;
try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
  起点transform = await 读transform();
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(), 积分: await R.credits(), transform: 起点transform };
  console.log('起点', JSON.stringify(rec.起点));

  // ===== 保存前基线：主体库当前逐字 =====
  const 开库 = async () => {
    const F = await p.evaluate(() => { const b = Array.from(document.querySelectorAll('button,[role=button]'))
      .find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '资产库');
      if (!b) return null; const r = b.getBoundingClientRect();
      return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; });
    if (!F) return { 错: 'no-资产库钮' };
    await p.mouse.click(F.x, F.y); await p.waitForTimeout(2400);
    const 页签 = await p.evaluate(() => Array.from(document.querySelectorAll('[role=tab]')).map((t) => { const r = t.getBoundingClientRect();
      return { 逐字: (t.innerText || '').replace(/\s+/g, ' ').trim(), 选中: t.getAttribute('aria-selected'),
        x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; }));
    const 主 = (页签 || []).find((z) => z.逐字 === '主体');
    if (主) { await p.mouse.click(主.x, 主.y); await p.waitForTimeout(2200); }
    return { 钮: F, 页签, 主体选中: 主 ? 主.选中 : null };
  };
  rec.开库前 = await 开库();
  rec.基线主体库 = await 读主体库('基线');
  for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
  落盘();
  console.log('\n🆕 主体库基线', 串(rec.基线主体库, 1800));
  断言('① 保存前基线是「没有可用主体」', String((rec.基线主体库 || {}).逐字 || '').indexOf('没有可用主体') >= 0, { 逐字: ((rec.基线主体库 || {}).逐字 || '').slice(0, 150) });

  // ===== 平移 → 选中 → 右键 =====
  await 切工具('抓手工具');
  const before = await 读节点屏上(IMG);
  const dx = 560 - (before[2] + before[0] / 2); const dy = 380 - (before[3] + before[1] / 2);
  拖动量 = [dx, dy]; rec.拖 = await 拖(dx, dy);
  rec.平移后transform = await 读transform(); rec.平移后节点 = await 读节点屏上(IMG);
  await 切工具('选择工具');
  console.log('平移后节点', JSON.stringify(rec.平移后节点));

  const 落 = await 可点落点(p, `.react-flow__node[data-id="${IMG}"]`, 4, 4);
  rec.落点 = 落;
  if (!落.__err) {
    rec.归属 = await p.evaluate(([x, y, i]) => { const h = document.elementFromPoint(x, y);
      const n = h && h.closest('.react-flow__node'); return !!(n && n.getAttribute('data-id') === i); }, [落.x, 落.y, IMG]);
    if (rec.归属) {
      await p.mouse.click(落.x, 落.y); await p.waitForTimeout(1800);
      rec.选中数 = await selCount(p);
      落盘(); console.log('选中数', rec.选中数);
      断言('② 点中带媒体的图片节点后选中数 = 1', rec.选中数 === 1, { 选中数: rec.选中数 });

      // ===== 右键 =====
      await p.mouse.click(落.x, 落.y, { button: 'right' }); await p.waitForTimeout(1600);
      rec.右键菜单 = await 读ctx();
      落盘();
      console.log('\n🆕 右键菜单', 串(rec.右键菜单, 2600));
      const 项 = (rec.右键菜单 || {}).项 || [];
      const 保存项 = 项.find((z) => /保存到主体库/.test(z.逐字));
      rec.保存项 = 保存项 || null;
      断言('③ 右键菜单逐字复现手册：**200×372、九项**', (rec.右键菜单 || {}).命中 === true &&
        rec.右键菜单.盒[0] === 200 && rec.右键菜单.盒[1] === 372 && 项.length === 9,
        { 盒: (rec.右键菜单 || {}).盒, 项数: 项.length, 逐字: 项.map((z) => z.逐字) });
      断言('④ 九项里含「保存到主体库」且**可用**（无 aria-disabled）', !!保存项 && 保存项.disabled == null,
        { 保存项: 保存项 || null });

      if (保存项) {
        const lp = await p.evaluate(([x, y, w, h]) => { for (let yy = Math.ceil(y) + 4; yy <= y + h - 4; yy += 2)
          for (let xx = Math.ceil(x) + 4; xx <= x + w - 4; xx += 2) { const el = document.elementFromPoint(xx, yy);
            const mi = el && el.closest('[role=menuitem]');
            if (mi && (mi.innerText || '').indexOf('保存到主体库') >= 0) return { x: xx, y: yy }; } return { __err: 'no-point' }; }, 保存项.盒);
        rec.保存落点 = lp;
        console.log('保存落点', JSON.stringify(lp));
        if (!lp.__err) {
          rec.保存前积分 = await R.credits();
          rec.保存前节点数 = (await idsOf(p)).length;
          await p.mouse.click(lp.x, lp.y);
          rec.保存后轮询 = [];
          for (let i = 0; i < 8; i++) { await p.waitForTimeout(1000);
            rec.保存后轮询.push({ 秒: i + 1, 浮层: await R.overlays(), 状态行: await R.status(), 积分: await R.credits() }); }
          rec.保存后积分 = await R.credits();
          rec.保存后节点数 = (await idsOf(p)).length;
          落盘();
          console.log('保存后轮询', 串(rec.保存后轮询, 1200));
          console.log('积分', rec.保存前积分, '→', rec.保存后积分, '| 节点数', rec.保存前节点数, '→', rec.保存后节点数);
          断言('⑤ 点「保存到主体库」**不扣积分**、**不增删画布节点**（它写的是主体库不是画布）',
            rec.保存后积分 === rec.保存前积分 && rec.保存后节点数 === rec.保存前节点数,
            { 积分: [rec.保存前积分, rec.保存后积分], 节点数: [rec.保存前节点数, rec.保存后节点数] });
        }
      }
      for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
    }
  }

  // ===== 保存后主体库对账 =====
  rec.开库后 = await 开库();
  rec.保存后主体库 = await 读主体库('保存后');
  落盘();
  console.log('\n🆕 主体库（保存后）', 串(rec.保存后主体库, 3200));
  const 后逐字 = String((rec.保存后主体库 || {}).逐字 || '');
  断言('⑥ 保存后主体库不再空态（「没有可用主体」消失）', (rec.保存后主体库 || {}).命中 === true && 后逐字.indexOf('没有可用主体') < 0,
    { 逐字: 后逐字.slice(0, 200) });

  // ===== 找删除入口并撤回 =====
  rec.删除候选 = ((rec.保存后主体库 || {}).可点 || []).filter((z) => /删除|移除|Delete|Remove|✕|×|清空/i.test((z.aria || '') + z.逐字));
  console.log('删除候选', 串(rec.删除候选, 1200));
  if (rec.删除候选.length) {
    const D = rec.删除候选[0];
    rec.删除落点 = await p.evaluate(([x, y, w, h]) => { const cx = Math.round(x + w / 2); const cy = Math.round(y + h / 2);
      const el = document.elementFromPoint(cx, cy); return { x: cx, y: cy, 命中: !!(el && el.closest('button,[role=button],[role=menuitem]')) }; }, D.盒);
    if (rec.删除落点.命中) {
      await p.mouse.click(rec.删除落点.x, rec.删除落点.y); await p.waitForTimeout(2000);
      rec.删除后 = await p.evaluate(() => ({ 逐字: (Array.from(document.querySelectorAll('[role=dialog]')).find((x) => x.getBoundingClientRect().width > 200) || {}).innerText || '',
        role列表: Array.from(document.querySelectorAll('[role=dialog] [role=alertdialog],[role=dialog] [role=dialog]')).map((x) => (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160)) }));
      落盘(); console.log('删除后浮层', 串(rec.删除后, 900));
    }
  } else {
    // 悬停主体卡片，看是否浮出删除钮
    rec.悬停找删除 = await p.evaluate(() => {
      const d = Array.from(document.querySelectorAll('[role=dialog]')).find((x) => x.getBoundingClientRect().width > 200);
      if (!d) return { 错: 'no-dialog' };
      const cards = Array.from(d.querySelectorAll('img,[class*=subject],[class*=Subject],[role=listitem],li,div'))
        .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 40 && r.height > 40 && r.x > 40 && r.y > 90 && r.y < 600; }).slice(0, 8);
      return cards.map((e) => { const r = e.getBoundingClientRect();
        return { tag: e.tagName, cls: (e.className || '').toString().slice(0, 60), testid: e.getAttribute('data-testid'),
          alt: e.getAttribute('alt'), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40),
          盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; });
    });
    console.log('悬停候选', 串(rec.悬停找删除, 1400));
  }
  for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

// ===== 归位 =====
try {
  const t = await p.evaluate(() => { const b = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]'); return b ? b.getAttribute('aria-label') : null; });
  if (t !== '抓手工具') await 切工具('抓手工具');
  if (拖动量) await 拖(-Math.round(拖动量[0]), -Math.round(拖动量[1]));
  let t2 = await 读transform(); const a = tx(起点transform) || []; let b2 = tx(t2) || [];
  rec.残差 = [];
  for (let k = 0; k < 4 && a.length === 2 && b2.length === 2; k++) {
    const ex = a[0] - b2[0]; const ey = a[1] - b2[1];
    if (Math.abs(ex) < 0.05 && Math.abs(ey) < 0.05) break;
    await 拖(-Math.round(ex), -Math.round(ey)); t2 = await 读transform(); b2 = tx(t2) || [];
    rec.残差.push({ 残差: [Math.round(ex * 100) / 100, Math.round(ey * 100) / 100], 后: t2 });
  }
  rec.归位后transform = t2;
  await 切工具('选择工具');
  for (let k = 0; k < 3 && (await selCount(p)) > 0; k++) {
    const e = await 空点(90, 600, 360, 930, 8); if (e.__err) break;
    await p.mouse.click(e.x, e.y); await p.waitForTimeout(800);
  }
} catch (e) { rec.归位异常 = String((e && e.stack) || e).slice(0, 600); 落盘(); }

await settle(p, R);
const mm = await R.minimap();
if (!mm || mm.ariaPressed !== 'true') { const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3); if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400); } }
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(),
  zoom: await R.zoom(), 积分: await R.credits(), 边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length), transform: await 读transform() };
rec.断言全过 = 断言过; 落盘();
console.log('\n起点', 起点transform, '| 归位后', rec.收尾.transform, '| 逐字相同 =', 起点transform === rec.收尾.transform);
console.log('收尾', JSON.stringify(rec.收尾));
断言('⑦ 收尾积分仍是 805', String(rec.收尾.积分).indexOf('805') >= 0, { 积分: rec.收尾.积分 });
rec.断言全过 = 断言过; 落盘();
await b.close();
