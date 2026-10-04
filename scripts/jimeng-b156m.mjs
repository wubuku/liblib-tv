// 批次 156-m —— **只读**：打开头像菜单（`canvas-user-menu-trigger`），找账号级「主体库」管理入口
//
// 156-l 的结论：全局 chrome 里唯一的「主体」入口是左栏第 6 个（40×40@16,403），
//   而它**建的是主体节点**，不是主体库管理器。⇒ 管理入口不在主 chrome 上。
// 顶栏有一个此前从未被本册记录过的 testid：`canvas-user-menu-trigger`（28×28@1236,16）
//   配 `canvas-user-avatar-image` / `canvas-user-avatar-hover-mask` —— 头像菜单，账号级设置的标准落点。
//
// 🔴 本轮**仍然只读**：只打开菜单、只 dump，**一个菜单项都不点**（点进「设置」可能改配置）。
//    目标只有一个：回答「账号级 Dreamina Subjects 有没有可管理的入口」⇒ 决定敢不敢真存一个主体。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: '156m', 目的: '只读：头像菜单里找账号级主体库管理入口' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b156m.json', import.meta.url), JSON.stringify(rec, null, 1));
const 串 = (x, n) => { const s = JSON.stringify(x, null, 1); return s === undefined ? 'undefined' : s.slice(0, n || 2000); };

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1000);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 积分: await R.credits() };
  console.log('起点', JSON.stringify(rec.起点));

  const 头 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-user-menu-trigger"]');
    if (!e) return null; const r = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), state: e.getAttribute('data-state'), expanded: e.getAttribute('aria-expanded'),
      haspopup: e.getAttribute('aria-haspopup'), 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; });
  rec.头 = 头;
  console.log('头像钮', JSON.stringify(头));
  断言('① 头像菜单钮存在（`canvas-user-menu-trigger`）', !!头, 头);

  if (头) {
    const cx = 头.盒[2] + 头.盒[0] / 2; const cy = 头.盒[3] + 头.盒[1] / 2;
    rec.落点校验 = await p.evaluate(([x, y, t]) => { const h = document.elementFromPoint(x, y);
      const e = h && h.closest('[data-testid="canvas-user-menu-trigger"]'); return !!e; }, [cx, cy]);
    await p.mouse.click(cx, cy); await p.waitForTimeout(1800);
    rec.菜单 = await p.evaluate(() => {
      const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x), Math.round(r.y)]; };
      const cs = Array.from(document.querySelectorAll('[role=menu],[data-radix-menu-content],[data-radix-popper-content-wrapper]'))
        .filter((x) => x.getBoundingClientRect().width > 60);
      if (!cs.length) return { 命中: false, 浮层: Array.from(document.querySelectorAll('[data-state=open]')).map((x) => (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200)).filter(Boolean) };
      const m = cs[cs.length - 1];
      return { 命中: true, 层数: cs.length, role: m.getAttribute('role'), 盒: 盒(m),
        逐字: (m.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 500),
        testid: m.getAttribute('data-testid'),
        项: Array.from(m.querySelectorAll('[role=menuitem],[role=button],button,a')).map((x) => { const r = x.getBoundingClientRect();
          return { role: x.getAttribute('role'), aria: (x.getAttribute('aria-label') || '').slice(0, 40), href: x.getAttribute('href'),
            逐字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30), 盒: 盒(x) }; }).filter((z) => z.盒[0] > 0) };
    });
    落盘();
    console.log('\n🆕 头像菜单', 串(rec.菜单, 2600));
    rec.命中主体 = ((rec.菜单 || {}).项 || []).filter((z) => /主体|素材|设置|账号|账户|个人|Subject/i.test((z.aria || '') + z.逐字 + (z.href || '')));
    console.log('菜单里主体/设置相关', 串(rec.命中主体, 1000));
    断言('② 头像菜单能打开且列出可点项', (rec.菜单 || {}).命中 === true && ((rec.菜单 || {}).项 || []).length > 0, { 命中: (rec.菜单 || {}).命中 });
    断言('③ 菜单里有「主体库 / 账号设置」类入口 ⇒ 存进去**清得掉**', rec.命中主体.length > 0,
      { 全部项: ((rec.菜单 || {}).项 || []).map((z) => z.逐字 + '|' + (z.aria || '')) });
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
await settle(p, R);
const mm = await R.minimap();
if (!mm || mm.ariaPressed !== 'true') { const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3); if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400); } }
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(),
  zoom: await R.zoom(), 积分: await R.credits(), 边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length) };
rec.断言全过 = 断言过; 落盘();
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');
await b.close();
