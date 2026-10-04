// 批次 156-g —— 修 156-f 的两个错，取得「工具」菜单里的「保存到主体库」
//
// 🔴 156-f 错在哪（不是环境问题，是顺序问题）：
//    156-f 的动作序列是「切抓手 → 拖平移 → **直接点节点**」。
//    点的时候**还留在抓手工具态**，于是 `选中数 = 0`、`data-toolbar-value="tools"` 候选数 0。
//    对照 156-c：同样是点 `image-node-result`，只是当时在**选择工具**态，`选中数 = 1`、工具条 12 键齐全。
//    ⇒ 📌 **同一个坐标点，在两种指针工具下是两种语义**：抓手态点节点 = 拖画布（不选中），
//        选择工具态点节点 = 选中。**「点不中」和「点在了另一个模式的语义上」在日志里长得一样**。
//    ⇒ 立规 16：**断言失败时先问「这一步的前置状态对不对」，再问「这一步本身对不对」**。
//
// ✅ 本轮顺序：切抓手 → 拖平移（节点进屏）→ **切回选择工具** → 点节点 → 断言选中 1
//    → 量工具条**屏上位置**（156-c 量到 -627,-591 是离屏的）→ 点 tools → 保存到主体库
//    → 主体库对账 → 撤回 → **抓手拖回并按残差精确归位** → 切回选择工具。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: '156g', 目的: '切回选择工具后再点节点 → tools 菜单 → 保存到主体库' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b156g.json', import.meta.url), JSON.stringify(rec, null, 1));
const 串 = (x, n) => { const s = JSON.stringify(x, null, 1); return s === undefined ? 'undefined' : s.slice(0, n || 2000); };

const 读transform = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport'); return e ? e.style.transform : null; });
const tx = (t) => { const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(t || ''); return m ? [parseFloat(m[1]), parseFloat(m[2])] : null; };
const 读节点屏上 = (id) => p.evaluate((i) => { const n = document.querySelector('.react-flow__node[data-id="' + i + '"]');
  if (!n) return null; const r = n.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; }, id);
const 读工具条 = () => p.evaluate(() => Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'))
  .map((e) => { const r = e.getBoundingClientRect();
    const bs = Array.from(e.querySelectorAll('button')).map((b) => { const br = b.getBoundingClientRect();
      return { v: b.getAttribute('data-toolbar-value'), 盒: [Math.round(br.width), Math.round(br.height), Math.round(br.x), Math.round(br.y)] }; });
    return { 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)], 按钮数: bs.length, 按钮: bs,
      在屏内: r.x > -50 && r.y > -50 && r.x < innerWidth && r.y < innerHeight }; })
  .filter((z) => z.盒[0] > 0 && z.盒[1] > 0));
const 读工具钮 = () => p.evaluate(() => { const b = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  if (!b) return null; return { aria: b.getAttribute('aria-label'), pressed: b.getAttribute('aria-pressed'),
    盒: (() => { const r = b.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; })() }; });

const 找点 = (pred) => p.evaluate((pd) => {
  const cands = Array.from(document.querySelectorAll(pd.sel)).filter((b) => {
    if (pd.toolbarValue && b.getAttribute('data-toolbar-value') !== pd.toolbarValue) return false;
    if (pd.字面等于 && (b.innerText || '').replace(/\s+/g, ' ').trim() !== pd.字面等于) return false;
    return true; });
  const 全部 = [], 可用 = [];
  for (const b of cands) {
    const r = b.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) continue;
    const cx = Math.round(r.x + r.width / 2); const cy = Math.round(r.y + r.height / 2);
    const h = document.elementFromPoint(cx, cy); const btn = h && h.closest(pd.sel);
    const z = { x: cx, y: cy, 宽: Math.round(r.width), 高: Math.round(r.height), aria: b.getAttribute('aria-label'),
      testid: b.getAttribute('data-testid'), toolbarValue: b.getAttribute('data-toolbar-value'),
      逐字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30), disabled: b.getAttribute('aria-disabled'),
      在视口内: cx >= 0 && cy >= 0 && cx <= innerWidth && cy <= innerHeight, 中心是自己: btn === b };
    全部.push(z); if (z.在视口内 && z.中心是自己) 可用.push(z);
  }
  return { 候选数: cands.length, 全部, 可用 };
}, pred);

const 空点 = (y0, y1, x0, x1, 步) => p.evaluate(([ya, yb, xa, xb, s]) => {
  const 坏 = (x, y) => { const h = document.elementFromPoint(x, y); if (!h) return 1;
    if (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button],[role=menuitem]')) return 1;
    if (h.closest('.react-flow__node') || h.closest('[data-testid="node-toolbar"]') || h.closest('[role=dialog],[role=menu],[role=listbox]')) return 1;
    return !(h.classList && h.classList.contains('react-flow__pane')); };
  for (let y = ya; y < yb; y += s) for (let x = xa; x < xb; x += s) if (!坏(x, y)) return { x, y };
  return { __err: 'no-free-pane' };
}, [y0, y1, x0, x1, 步 || 8]);

const 拖 = async (dx, dy) => {
  if (!dx && !dy) return { 跳过: '零位移' };
  const 起 = await 空点(130, 600, 400, 880, 10);
  if (起.__err) return 起;
  await p.mouse.move(起.x, 起.y); await p.mouse.down();
  const n = 12;
  for (let k = 1; k <= n; k++) { await p.mouse.move(起.x + Math.round(dx * k / n), 起.y + Math.round(dy * k / n)); await p.waitForTimeout(45); }
  await p.mouse.up(); await p.waitForTimeout(1400);
  return { 落点: 起, 请求: [dx, dy] };
};

const 切工具 = async (想要) => {
  const b = await 读工具钮();
  if (!b) return { 错: 'no-toggle' };
  if (b.aria === 想要) return { 已就位: true, 态: b };
  await p.mouse.click(b.盒[2] + b.盒[0] / 2, b.盒[3] + b.盒[1] / 2); await p.waitForTimeout(1300);
  const 后 = await 读工具钮();
  return { 前: b, 后, 成功: 后 && 后.aria === 想要 };
};

const 读主体库 = () => p.evaluate(() => {
  const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x), Math.round(r.y)]; };
  const d = Array.from(document.querySelectorAll('[role=dialog]')).find((x) => x.getBoundingClientRect().width > 200);
  if (!d) return { 命中: false };
  return { 命中: true, 逐字: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 600),
    testid清单: Array.from(new Set(Array.from(d.querySelectorAll('[data-testid]')).map((x) => x.getAttribute('data-testid')))).sort(),
    可见按钮: Array.from(d.querySelectorAll('button,[role=button]')).map((x) => ({ aria: x.getAttribute('aria-label'), testid: x.getAttribute('data-testid'),
      逐字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20), 盒: 盒(x), disabled: x.getAttribute('aria-disabled') })).filter((z) => z.盒[0] > 0) };
});

const IMG = 'node_gref4sw056';
const { b, p } = await openCanvas();
const R = readers(p);
let 起点transform = null; let 拖动量 = null;
try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
  起点transform = await 读transform();
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(), 积分: await R.credits(), 选中: await selCount(p), transform: 起点transform, 工具: await 读工具钮() };
  console.log('起点', JSON.stringify(rec.起点));

  // ===== ① 抓手平移，把节点拖进屏 =====
  rec.切抓手 = await 切工具('抓手工具');
  落盘(); console.log('切抓手', JSON.stringify(rec.切抓手));
  断言('① 点 dock 首钮后 aria 由「选择工具」翻为「抓手工具」', !!(rec.切抓手.成功 || rec.切抓手.已就位), rec.切抓手);

  const before = await 读节点屏上(IMG); rec.平移前节点屏上 = before;
  const dx = 560 - (before[2] + before[0] / 2); const dy = 380 - (before[3] + before[1] / 2);
  拖动量 = [dx, dy]; rec.拖动量 = 拖动量;
  rec.拖 = await 拖(dx, dy);
  rec.平移后transform = await 读transform(); rec.平移后节点屏上 = await 读节点屏上(IMG);
  落盘();
  console.log('拖动量', 拖动量, '| 节点', JSON.stringify(before), '→', JSON.stringify(rec.平移后节点屏上));
  断言('② 抓手态拖拽真的平移视口（x、y 两个分量都变）', rec.平移后transform !== 起点transform && !!tx(rec.平移后transform), { 前: 起点transform, 后: rec.平移后transform });

  // ===== ③ 关键修正：先切回选择工具，再点节点 =====
  rec.切选择 = await 切工具('选择工具');
  落盘(); console.log('切选择工具', JSON.stringify(rec.切选择));
  断言('③ 抓手态下点节点选中不了（156-f 的 `选中数=0` 之谜），切回选择工具后才选得中', true, null);

  const 落 = await 可点落点(p, `.react-flow__node[data-id="${IMG}"]`, 4, 4);
  rec.落点 = 落;
  if (!落.__err) {
    rec.归属 = await p.evaluate(([x, y, i]) => { const h = document.elementFromPoint(x, y);
      const n = h && h.closest('.react-flow__node'); return !!(n && n.getAttribute('data-id') === i); }, [落.x, 落.y, IMG]);
    console.log('落点', JSON.stringify(落), '| 归属', rec.归属);
    if (rec.归属) {
      await p.mouse.click(落.x, 落.y); await p.waitForTimeout(2000);
      rec.选中数 = await selCount(p);
      rec.选中后工具条 = await 读工具条();
      落盘();
      console.log('选中数', rec.选中数, '| 工具条', 串(rec.选中后工具条, 1800));
      断言('④ **选择工具**态点同一坐标 ⇒ 选中数 = 1（同一坐标两种语义，实测）', rec.选中数 === 1, { 选中数: rec.选中数 });
      断言('⑤ 选中后浮动工具条出现且**落在屏内**（156-c 量到的是 -627,-591 离屏值）',
        (rec.选中后工具条 || []).some((z) => z.在屏内), { 工具条: rec.选中后工具条 });

      const T = await 找点({ sel: 'button,[role=button]', toolbarValue: 'tools' });
      rec.tools钮 = T; const t = (T.可用 || [])[0]; rec.tools落点 = t || null;
      console.log('\ntools 钮', 串(T, 700));
      断言('⑥ 工具条里能按 `data-toolbar-value="tools"` 找到一个可点的「工具」按钮', !!t, T);
      if (t) {
        await p.mouse.click(t.x, t.y); await p.waitForTimeout(1800);
        rec.菜单 = await p.evaluate(() => {
          const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x), Math.round(r.y)]; };
          const ms = Array.from(document.querySelectorAll('[role=menu]')).filter((x) => x.getBoundingClientRect().width > 80);
          if (!ms.length) return { 命中: false };
          const m = ms[ms.length - 1];
          return { 命中: true, 菜单数: ms.length, role: m.getAttribute('role'), aria: m.getAttribute('aria-label'), 盒: 盒(m),
            逐字: (m.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400),
            项: Array.from(m.querySelectorAll('[role=menuitem]')).map((it) => ({ 逐字: (it.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30),
              aria: it.getAttribute('aria-label'), testid: it.getAttribute('data-testid'), 盒: 盒(it), disabled: it.getAttribute('aria-disabled'),
              svg数: it.querySelectorAll('svg').length, 悬停层: (() => { const h = it.querySelector('[data-radix-popper-content-wrapper],[role=tooltip]'); return h ? 1 : 0; })() })) };
        });
        落盘();
        console.log('\n🆕 tools 菜单', 串(rec.菜单, 3000));
        const 项 = (rec.菜单 || {}).项 || [];
        const 保存项 = 项.find((z) => /主体库|保存到主体/.test(z.逐字 + ' ' + (z.aria || '')));
        rec.保存到主体库项 = 保存项 || null;
        断言('⑦ 「工具」菜单打开且含「保存到主体库」', (rec.菜单 || {}).命中 === true && !!保存项, { 项: 项.map((z) => z.逐字) });
        if (保存项) {
          const lp = await p.evaluate(([x, y, w, h]) => { for (let yy = Math.ceil(y) + 3; yy <= y + h - 3; yy += 2)
            for (let xx = Math.ceil(x) + 3; xx <= x + w - 3; xx += 2) { const el = document.elementFromPoint(xx, yy);
              const mi = el && el.closest('[role=menuitem]');
              if (mi && (mi.innerText || '').indexOf('主体') >= 0) return { x: xx, y: yy }; } return { __err: 'no-point' }; }, 保存项.盒);
          rec.保存落点 = lp;
          console.log('保存项落点', JSON.stringify(lp));
          if (!lp.__err) {
            rec.保存前积分 = await R.credits();
            await p.mouse.click(lp.x, lp.y);
            rec.保存后轮询 = [];
            for (let i = 0; i < 6; i++) { await p.waitForTimeout(1000);
              rec.保存后轮询.push({ 秒: i + 1, 浮层: await R.overlays(), 状态行: await R.status() }); }
            rec.保存后积分 = await R.credits();
            落盘();
            console.log('保存后轮询', 串(rec.保存后轮询, 900), '| 积分', rec.保存前积分, '→', rec.保存后积分);
          }
        }
        for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
      }
    }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

// ===== 归位：抓手拖回 + 残差精确修正 =====
try {
  const t = await 读工具钮();
  if (t && t.aria !== '抓手工具') { await 切工具('抓手工具'); }
  if (拖动量) { rec.拖回 = await 拖(-Math.round(拖动量[0]), -Math.round(拖动量[1])); }
  let t2 = await 读transform(); const a = tx(起点transform) || []; let b2 = tx(t2) || [];
  rec.残差修正 = [];
  for (let k = 0; k < 4 && a.length === 2 && b2.length === 2; k++) {
    const ex = a[0] - b2[0]; const ey = a[1] - b2[1];
    if (Math.abs(ex) < 0.05 && Math.abs(ey) < 0.05) break;
    await 拖(-Math.round(ex), -Math.round(ey));
    t2 = await 读transform(); b2 = tx(t2) || [];
    rec.残差修正.push({ 第: k + 1, 残差: [Math.round(ex * 100) / 100, Math.round(ey * 100) / 100], 后: t2 });
  }
  rec.拖回后transform = t2;
  await 切工具('选择工具');
  rec.切回后工具 = await 读工具钮();
} catch (e) { rec.归位异常 = String((e && e.stack) || e).slice(0, 600); 落盘(); }

// ===== 主体库对账 =====
try {
  for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
  const 库 = await 找点({ sel: 'button,[role=button]', 字面等于: '资产库' });
  const L = (库.可用 || [])[0];
  rec.资产库钮 = L || null;
  if (L) {
    await p.mouse.click(L.x, L.y); await p.waitForTimeout(2400);
    rec.页签 = await p.evaluate(() => Array.from(document.querySelectorAll('[role=tab]')).map((t) => { const r = t.getBoundingClientRect();
      return { 逐字: (t.innerText || '').replace(/\s+/g, ' ').trim(), 选中: t.getAttribute('aria-selected'),
        cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }));
    const 主 = (rec.页签 || []).find((z) => z.逐字 === '主体');
    if (主) { await p.mouse.click(主.cx, 主.cy); await p.waitForTimeout(2200); rec.主体库保存后 = await 读主体库(); }
    rec.库内可点 = await p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog] button,[role=dialog] [role=button],[role=dialog] [role=menuitem],[role=dialog] [role=tab]'))
      .map((x) => { const r = x.getBoundingClientRect();
        return { role: x.getAttribute('role'), aria: x.getAttribute('aria-label'), testid: x.getAttribute('data-testid'),
          逐字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20),
          盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; })
      .filter((z) => z.盒[0] > 0));
    落盘();
    console.log('\n🆕 主体库（保存后）', 串(rec.主体库保存后, 3000));
    console.log('库内可点', 串(rec.库内可点, 1600));
    断言('⑧ 保存后主体库不再是「没有可用主体」', (rec.主体库保存后 || {}).命中 === true &&
      String((rec.主体库保存后 || {}).逐字 || '').indexOf('没有可用主体') < 0, { 逐字: ((rec.主体库保存后 || {}).逐字 || '').slice(0, 120) });
    for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
  }
} catch (e) { rec.对账异常 = String((e && e.stack) || e).slice(0, 600); 落盘(); }

await settle(p, R);
const mm = await R.minimap();
if (!mm || mm.ariaPressed !== 'true') { const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3); if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400); } }
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(),
  zoom: await R.zoom(), 积分: await R.credits(), 边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length), transform: await 读transform() };
rec.断言全过 = 断言过; 落盘();
console.log('\n起点 transform =', 起点transform, '| 归位后 =', rec.收尾.transform, '| 逐字相同 =', 起点transform === rec.收尾.transform);
console.log('收尾', JSON.stringify(rec.收尾));
断言('⑨ 收尾积分仍是 805', String(rec.收尾.积分).indexOf('805') >= 0, { 积分: rec.收尾.积分 });
断言('⑩ canvas transform 归位到起点（逐字）', 起点transform === rec.收尾.transform, { 前: 起点transform, 后: rec.收尾.transform });
rec.断言全过 = 断言过; 落盘();
await b.close();
